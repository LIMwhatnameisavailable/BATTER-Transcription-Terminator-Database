#!/usr/bin/env python3
"""Build the small, checksum-addressed v0.3 JBrowse asset inventory.

The inventory is deliberately limited to assets that are already present in the
frozen v0.2 JBrowse bundle or the canonical v0.2 release.  It is an inventory
only: no files are copied, uploaded, normalized, or reinterpreted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BUNDLE = REPO_ROOT.parent / "bted-v0.2" / "dist" / "BTED-v0.2.0-jbrowse"
DEFAULT_RELEASE = REPO_ROOT / "data" / "public" / "v0.2.0"
DEFAULT_REGISTRY = REPO_ROOT / "data" / "registry" / "batter_s1_source_registry.tsv"
DEFAULT_SOURCE_MANIFESTS = REPO_ROOT / "data" / "registry" / "manifests"
DEFAULT_TSV = REPO_ROOT / "data" / "registry" / "jbrowse_assets.v0.2.0.tsv"
DEFAULT_JSON = REPO_ROOT / "data" / "registry" / "jbrowse_assets.v0.2.0.json"
DEFAULT_ASSET_POLICY = REPO_ROOT / "data" / "registry" / "batter_s1_asset_redistribution.v0.3.tsv"
RELEASE_VERSION = "v0.2.0"
GENERATOR_VERSION = "bted-jbrowse-asset-inventory-0.2.0"

TSV_COLUMNS = (
    "asset_id",
    "release_version",
    "source_id",
    "assembly_accession",
    "asset_role",
    "asset_kind",
    "bundle_path",
    "canonical_path",
    "object_path",
    "byte_size",
    "sha256",
    "mime_type",
    "supports_range",
    "redistribution_status",
    "is_public",
)

RAW_BIGWIG_SOURCES = {
    "BATTER_S1_001",
    "BATTER_S1_003",
    "BATTER_S1_004",
    "BATTER_S1_005",
}


def _asset_policy(path: Path = DEFAULT_ASSET_POLICY) -> dict[tuple[str, str], dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            (row["source_id"], row["asset_scope"]): row
            for row in csv.DictReader(handle, delimiter="\t")
        }


def _asset_decision(
    policies: dict[tuple[str, str], dict[str, str]],
    source_id: str,
    scope: str,
    fallback: str,
) -> tuple[str, bool]:
    row = policies.get((source_id, scope))
    if not row:
        return fallback, fallback == "verified_redistributable"
    status = row["redistribution_status"].strip()
    return status, row["is_public"].strip().lower() == "true"

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative_path(bundle: Path, uri: str) -> Path:
    value = Path(str(uri))
    if value.is_absolute() or ".." in value.parts:
        raise ValueError(f"unsafe bundle URI: {uri}")
    path = (bundle / value).resolve()
    try:
        path.relative_to(bundle.resolve())
    except ValueError as exc:
        raise ValueError(f"bundle URI escapes bundle: {uri}") from exc
    return path


def _walk_uris(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        uri = value.get("uri")
        if isinstance(uri, str):
            found.append(uri)
        for child in value.values():
            found.extend(_walk_uris(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_uris(child))
    return found


def _track_uri(track: dict[str, Any], key: str) -> str | None:
    value = track.get("adapter", {})
    if not isinstance(value, dict):
        return None
    if key == "bigwig":
        locations = _walk_uris(value)
        return locations[0] if len(locations) == 1 else None
    if value.get("type") != "Gff3TabixAdapter":
        return None
    location = value.get("gffGzLocation", {})
    index = value.get("index", {}).get("location", {})
    if key == "gff3":
        return location.get("uri") if isinstance(location, dict) else None
    if key == "tbi":
        return index.get("uri") if isinstance(index, dict) else None
    return None


def _manifest_redistribution(path: Path) -> str:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "to_review"
    redistribution = value.get("redistribution", {})
    if isinstance(redistribution, dict):
        status = str(redistribution.get("redistribution_status", "")).strip()
        if status:
            return status
    return "verified_redistributable"


def _source_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return {str(row["source_id"]): row for row in rows}


def _source_manifest_rows(path: Path) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for manifest_path in sorted(path.glob("BATTER_S1_*.json")):
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
        output[str(value["source_id"])] = value
    return output


def _make_row(
    *,
    asset_id: str,
    source_id: str,
    assembly_accession: str,
    asset_role: str,
    asset_kind: str,
    object_path: str,
    path: Path,
    bundle_path: str = "",
    canonical_path: str = "",
    redistribution_status: str,
    is_public: bool | None = None,
) -> dict[str, str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    suffix = path.name.lower()
    if asset_kind in {"fasta", "fai", "bed"}:
        mime_type = "text/plain"
    elif asset_kind == "gff3":
        mime_type = "application/gzip"
    elif asset_kind == "tbi":
        mime_type = "application/octet-stream"
    elif asset_kind == "bigwig":
        mime_type = "application/octet-stream"
    else:
        raise ValueError(f"unsupported asset kind: {asset_kind}")
    public = (
        redistribution_status == "verified_redistributable"
        if is_public is None
        else is_public
    )
    digest = sha256(path)
    return {
        "asset_id": asset_id,
        "release_version": RELEASE_VERSION,
        "source_id": source_id,
        "assembly_accession": assembly_accession,
        "asset_role": asset_role,
        "asset_kind": asset_kind,
        "bundle_path": bundle_path,
        "canonical_path": canonical_path,
        "object_path": object_path,
        "byte_size": str(path.stat().st_size),
        "sha256": digest,
        "mime_type": mime_type,
        "supports_range": "false",
        "redistribution_status": redistribution_status,
        "is_public": "true" if public else "false",
    }


def _assembly_candidates(
    bundle: Path,
    source_rows: dict[str, dict[str, str]],
    source_manifests: dict[str, dict[str, Any]],
    release_root: Path,
) -> dict[str, dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    for config_path in sorted(bundle.glob("BATTER_S1_*.config.json")):
        source_id = config_path.name.removesuffix(".config.json")
        if source_id == "BATTER_S1_002":
            continue
        if source_id not in source_rows or source_id not in source_manifests:
            raise ValueError(f"missing source mapping for {source_id}")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assemblies = config.get("assemblies", [])
        if len(assemblies) != 1:
            raise ValueError(f"{source_id}: expected one assembly adapter")
        assembly = assemblies[0]
        assembly_accession = source_rows[source_id]["reference_genome"]
        if source_manifests[source_id].get("reference_genome") != assembly_accession:
            raise ValueError(f"{source_id}: source manifest/registry assembly mismatch")
        sequence = assembly.get("sequence", {})
        adapter = sequence.get("adapter", {})
        if adapter.get("type") != "IndexedFastaAdapter":
            raise ValueError(f"{source_id}: expected IndexedFastaAdapter")
        fasta_uri = adapter.get("fastaLocation", {}).get("uri")
        fai_uri = adapter.get("faiLocation", {}).get("uri")
        gff_tracks = [track for track in config.get("tracks", []) if _track_uri(track, "gff3")]
        if len(gff_tracks) != 1:
            raise ValueError(f"{source_id}: expected one GFF3/TBI adapter")
        gff_uri = _track_uri(gff_tracks[0], "gff3")
        tbi_uri = _track_uri(gff_tracks[0], "tbi")
        if not all(isinstance(item, str) for item in (fasta_uri, fai_uri, gff_uri, tbi_uri)):
            raise ValueError(f"{source_id}: incomplete reference asset adapter")
        paths = {
            "fasta": _relative_path(bundle, fasta_uri),
            "fai": _relative_path(bundle, fai_uri),
            "gff3": _relative_path(bundle, gff_uri),
            "tbi": _relative_path(bundle, tbi_uri),
        }
        candidates[source_id] = {
            "source_id": source_id,
            "assembly_accession": assembly_accession,
            "paths": paths,
            "redistribution_status": _manifest_redistribution(
                release_root / "records" / source_id / "manifest.json"
            ),
        }
    return candidates


def _assembly_rows(
    bundle: Path,
    candidates: dict[str, dict[str, Any]],
    policies: dict[tuple[str, str], dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    by_assembly: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates.values():
        by_assembly.setdefault(candidate["assembly_accession"], []).append(candidate)
    rows: list[dict[str, str]] = []
    dedup: list[dict[str, Any]] = []
    for assembly_accession in sorted(by_assembly):
        group = sorted(by_assembly[assembly_accession], key=lambda item: item["source_id"])
        checksums = {
            kind: {sha256(item["paths"][kind]) for item in group}
            for kind in ("fasta", "fai", "gff3", "tbi")
        }
        if len(group) > 1 and all(len(values) == 1 for values in checksums.values()):
            selected = [group[0]]
            dedup.append({
                "assembly_accession": assembly_accession,
                "source_ids": [item["source_id"] for item in group],
                "representative_source_id": group[0]["source_id"],
                "reason": "byte-identical FASTA/FAI/GFF3/TBI shared reference bundle",
            })
        else:
            selected = group
        deduplicated = len(selected) == 1 and len(group) > 1
        for candidate in selected:
            source_id = candidate["source_id"]
            redistribution_status, is_public = _asset_decision(
                policies, source_id, "reference", candidate["redistribution_status"]
            )
            source_suffix = "" if deduplicated or len(group) == 1 else f"--{source_id}"
            for kind, role, filename in (
                ("fasta", "reference_fasta", "reference.fna"),
                ("fai", "reference_fai", "reference.fna.fai"),
                ("gff3", "reference_gff3", "genes.gff3.gz"),
                ("tbi", "reference_tbi", "genes.gff3.gz.tbi"),
            ):
                path = candidate["paths"][kind]
                bundle_path = path.relative_to(bundle).as_posix()
                object_path = f"assemblies/{assembly_accession}/reference/{filename}"
                if source_suffix:
                    object_path = f"assemblies/{assembly_accession}/reference/{source_id}/{filename}"
                rows.append(_make_row(
                    asset_id=(
                        f"{RELEASE_VERSION}--assembly-{assembly_accession}--{kind}{source_suffix}"
                    ),
                    source_id=source_id,
                    assembly_accession=assembly_accession,
                    asset_role=role,
                    asset_kind=kind,
                    object_path=object_path,
                    path=path,
                    bundle_path=bundle_path,
                    redistribution_status=redistribution_status,
                    is_public=is_public,
                ))
    return rows, dedup


def _canonical_rows(
    release: dict[str, Any],
    source_rows: dict[str, dict[str, str]],
    source_manifests: dict[str, dict[str, Any]],
    release_root: Path,
    policies: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id in sorted(release.get("sources", {})):
        if source_id == "BATTER_S1_002":
            continue
        entry = release["sources"][source_id]
        if entry.get("release_status") == "audit_only":
            continue
        canonical = release_root / "records" / source_id / "endpoints.bed"
        canonical_path = f"records/{source_id}/endpoints.bed"
        if not canonical.is_file():
            raise FileNotFoundError(canonical)
        fallback = _manifest_redistribution(release_root / "records" / source_id / "manifest.json")
        redistribution_status, is_public = _asset_decision(
            policies, source_id, "bted_standardized_output", fallback
        )
        rows.append(_make_row(
            asset_id=f"{RELEASE_VERSION}--source-{source_id}--endpoints-bed",
            source_id=source_id,
            assembly_accession=source_rows[source_id]["reference_genome"],
            asset_role="canonical_endpoints",
            asset_kind="bed",
            object_path=canonical_path,
            path=canonical,
            canonical_path=canonical_path,
            redistribution_status=redistribution_status,
            is_public=is_public,
        ))
    return rows


def _bigwig_rows(
    bundle: Path,
    source_rows: dict[str, dict[str, str]],
    source_manifests: dict[str, dict[str, Any]],
    release_root: Path,
    policies: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id in sorted(RAW_BIGWIG_SOURCES):
        config_path = bundle / f"{source_id}.config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        tracks = []
        for track in config.get("tracks", []):
            uri = _track_uri(track, "bigwig")
            if uri and str(uri).lower().endswith(".bw"):
                tracks.append((track, uri))
        if len(tracks) != 2:
            raise ValueError(f"{source_id}: expected two raw BigWig tracks")
        for track, uri in tracks:
            searchable = f"{track.get('trackId', '')} {track.get('name', '')}".lower()
            strand = "forward" if "forward" in searchable else "reverse" if "reverse" in searchable else ""
            if not strand:
                raise ValueError(f"{source_id}: BigWig track has no forward/reverse label")
            path = _relative_path(bundle, uri)
            bundle_path = path.relative_to(bundle).as_posix()
            fallback = _manifest_redistribution(release_root / "records" / source_id / "manifest.json")
            redistribution_status, is_public = _asset_decision(
                policies, source_id, "experimental_signal", fallback
            )
            rows.append(_make_row(
                asset_id=f"{RELEASE_VERSION}--source-{source_id}--signal-{strand}-bigwig",
                source_id=source_id,
                assembly_accession=source_rows[source_id]["reference_genome"],
                asset_role=f"raw_bigwig_{strand}",
                asset_kind="bigwig",
                object_path=f"tracks/{source_id}/signal.{strand}.bw",
                path=path,
                bundle_path=bundle_path,
                redistribution_status=redistribution_status,
                is_public=is_public,
            ))
    return rows


def build_inventory(
    *,
    bundle: Path = DEFAULT_BUNDLE,
    release_root: Path = DEFAULT_RELEASE,
    registry_path: Path = DEFAULT_REGISTRY,
    source_manifests_path: Path = DEFAULT_SOURCE_MANIFESTS,
    asset_policy_path: Path = DEFAULT_ASSET_POLICY,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    bundle = bundle.resolve()
    release_root = release_root.resolve()
    source_rows = _source_rows(registry_path)
    source_manifests = _source_manifest_rows(source_manifests_path)
    policies = _asset_policy(asset_policy_path)
    release = json.loads((release_root / "release_manifest.json").read_text(encoding="utf-8"))
    if release.get("release_version") != RELEASE_VERSION:
        raise ValueError("canonical release version is not v0.2.0")
    candidates = _assembly_candidates(bundle, source_rows, source_manifests, release_root)
    assembly_rows, dedup = _assembly_rows(bundle, candidates, policies)
    canonical_rows = _canonical_rows(release, source_rows, source_manifests, release_root, policies)
    bigwig_rows = _bigwig_rows(bundle, source_rows, source_manifests, release_root, policies)
    rows = sorted(
        assembly_rows + canonical_rows + bigwig_rows,
        key=lambda row: row["asset_id"],
    )
    counts = {
        "assembly_assets": len(assembly_rows),
        "canonical_endpoint_assets": len(canonical_rows),
        "raw_bigwig_assets": len(bigwig_rows),
        "total_assets": len(rows),
    }
    if counts != {
        "assembly_assets": 76,
        "canonical_endpoint_assets": 21,
        "raw_bigwig_assets": 8,
        "total_assets": 105,
    }:
        raise ValueError(f"unexpected inventory counts: {counts}")
    provenance = {
        "schema_version": "1.0",
        "generator": "scripts/build_v03_jbrowse_asset_inventory.py",
        "generator_version": GENERATOR_VERSION,
        "release_version": RELEASE_VERSION,
        "bundle_basename": bundle.name,
        "canonical_release_root": "data/public/v0.2.0",
        "counts": counts,
        "assembly_accessions": sorted({row["assembly_accession"] for row in assembly_rows}),
        "source_ids": sorted({row["source_id"] for row in canonical_rows}),
        "raw_bigwig_source_ids": sorted(RAW_BIGWIG_SOURCES),
        "asset_redistribution_policy": {
            "path": asset_policy_path.resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            "sha256": sha256(asset_policy_path),
        },
        "deduplicated_shared_references": dedup,
        "excluded": {
            "source_ids": ["BATTER_S1_002"],
            "asset_patterns": [
                "candidate BED/GFF",
                "signed-log/normalized display BigWig",
                "JBrowse UI files/config",
            ],
        },
        "supports_range": False,
        "deterministic": True,
    }
    return rows, provenance


def write_inventory(rows: list[dict[str, str]], provenance: dict[str, Any], tsv_path: Path, json_path: Path) -> None:
    tsv_path.parent.mkdir(parents=True, exist_ok=True)
    with tsv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    output = dict(provenance)
    try:
        output["tsv_path"] = tsv_path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        output["tsv_path"] = tsv_path.name
    output["tsv_sha256"] = sha256(tsv_path)
    output["tsv_byte_size"] = tsv_path.stat().st_size
    output["row_count"] = len(rows)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jbrowse-bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--source-manifests", type=Path, default=DEFAULT_SOURCE_MANIFESTS)
    parser.add_argument("--asset-policy", type=Path, default=DEFAULT_ASSET_POLICY)
    parser.add_argument("--output-tsv", type=Path, default=DEFAULT_TSV)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    args = parser.parse_args()
    rows, provenance = build_inventory(
        bundle=args.jbrowse_bundle,
        release_root=args.release_root,
        registry_path=args.registry,
        source_manifests_path=args.source_manifests,
        asset_policy_path=args.asset_policy,
    )
    write_inventory(rows, provenance, args.output_tsv, args.output_json)
    print(f"PASS {len(rows)} assets -> {args.output_tsv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
