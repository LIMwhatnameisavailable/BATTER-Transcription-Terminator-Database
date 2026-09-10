#!/usr/bin/env python3
"""Build the BTED reference-contig provenance registry from existing JBrowse assets.

This is a metadata-only builder.  It does not download a reference sequence or
modify the v0.2 release.  It reads the IndexedFastaAdapter and FAI assets from
an already published JBrowse bundle, verifies the bundle SHA256SUMS inventory,
and joins those contigs to the canonical endpoint tables.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping


GENERATOR_VERSION = "bted-reference-contig-registry-0.1.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^BATTER_S1_[0-9]{3}$")
REFERENCE_CONTIG_COLUMNS = [
    "release_version",
    "assembly_accession",
    "contig_accession",
    "length_bp",
    "max_endpoint_position_1based",
    "supporting_source_ids",
    "fasta_asset_basename",
    "fasta_sha256",
    "fai_asset_basename",
    "fai_sha256",
    "bundle_sha256sums_sha256",
    "generator_version",
    "generated_at_utc",
]


class RegistryBuildError(Exception):
    """A reproducible input or cross-source conflict."""


def _validated_generated_at(value: str | None) -> str:
    """Return a valid provenance timestamp, requiring an explicit UTC offset."""

    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if not isinstance(value, str):
        raise RegistryBuildError(
            "generated_at_utc must be a timezone-aware ISO-8601 UTC timestamp (for example 2026-08-21T00:00:00Z)"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise RegistryBuildError(
            "generated_at_utc must be a timezone-aware ISO-8601 UTC timestamp (for example 2026-08-21T00:00:00Z)"
        ) from exc
    if parsed.tzinfo is None:
        raise RegistryBuildError(
            "generated_at_utc must include a timezone; use a trailing Z or +00:00"
        )
    if parsed.utcoffset() != timedelta(0):
        raise RegistryBuildError("generated_at_utc must use UTC (Z or an equivalent +00:00 offset)")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RegistryBuildError(f"{path}: JSON root must be an object")
    return value


def _safe_bundle_path(bundle_root: Path, uri: str, context: str) -> Path:
    if not isinstance(uri, str) or not uri:
        raise RegistryBuildError(f"{context}: missing URI")
    relative = Path(uri)
    if relative.is_absolute() or "://" in uri or ".." in relative.parts:
        raise RegistryBuildError(f"{context}: non-portable URI {uri!r}")
    path = (bundle_root / relative).resolve()
    try:
        path.relative_to(bundle_root.resolve())
    except ValueError as exc:
        raise RegistryBuildError(f"{context}: URI leaves bundle: {uri!r}") from exc
    if not path.is_file():
        raise RegistryBuildError(f"{context}: missing bundle asset {uri!r}")
    return path


def _parse_bundle_checksums(bundle_root: Path) -> tuple[dict[str, str], str]:
    path = bundle_root / "SHA256SUMS.txt"
    if not path.is_file():
        raise RegistryBuildError(f"missing bundle checksum inventory: {path}")
    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or not SHA256_RE.fullmatch(parts[0]):
            raise RegistryBuildError(f"{path}:{line_number}: malformed SHA256SUMS entry")
        digest, relative = parts
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise RegistryBuildError(f"{path}:{line_number}: unsafe checksum path {relative!r}")
        if relative in entries:
            raise RegistryBuildError(f"{path}:{line_number}: duplicate checksum path {relative!r}")
        entries[relative] = digest
    return entries, sha256_file(path)


def _verify_bundle_asset(
    bundle_root: Path,
    checksums: Mapping[str, str],
    path: Path,
    context: str,
) -> str:
    relative = path.relative_to(bundle_root).as_posix()
    expected = checksums.get(relative)
    if expected is None:
        raise RegistryBuildError(f"{context}: asset is absent from bundle SHA256SUMS.txt: {relative}")
    actual = sha256_file(path)
    if actual != expected:
        raise RegistryBuildError(
            f"{context}: checksum mismatch for {relative}: expected {expected}, actual {actual}"
        )
    return actual


def _fai_contigs(path: Path, context: str) -> dict[str, int]:
    contigs: dict[str, int] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        fields = raw_line.split("\t")
        if len(fields) < 2 or not fields[0]:
            raise RegistryBuildError(f"{context}:{line_number}: malformed FAI row")
        try:
            length = int(fields[1])
        except ValueError as exc:
            raise RegistryBuildError(f"{context}:{line_number}: FAI length is not an integer") from exc
        if length <= 0:
            raise RegistryBuildError(f"{context}:{line_number}: FAI length must be positive")
        if fields[0] in contigs:
            raise RegistryBuildError(f"{context}:{line_number}: duplicate FAI contig {fields[0]!r}")
        contigs[fields[0]] = length
    if not contigs:
        raise RegistryBuildError(f"{context}: FAI has no contigs")
    return contigs


def _endpoint_pairs(release_root: Path, source_id: str) -> dict[tuple[str, str], int]:
    endpoint_path = release_root / "records" / source_id / "endpoints.tsv"
    if not endpoint_path.is_file():
        raise RegistryBuildError(f"{source_id}: missing canonical endpoint table {endpoint_path}")
    result: dict[tuple[str, str], int] = {}
    with endpoint_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"reference_assembly", "reference_name", "biological_coordinate_1based"}
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise RegistryBuildError(f"{endpoint_path}: missing endpoint columns: {', '.join(missing)}")
        for line_number, row in enumerate(reader, start=2):
            assembly = row.get("reference_assembly", "")
            contig = row.get("reference_name", "")
            if not assembly or assembly == "NA" or not contig or contig == "NA":
                raise RegistryBuildError(f"{endpoint_path}:{line_number}: missing assembly/contig")
            try:
                position = int(row.get("biological_coordinate_1based", ""))
            except ValueError as exc:
                raise RegistryBuildError(f"{endpoint_path}:{line_number}: invalid endpoint coordinate") from exc
            if position < 1:
                raise RegistryBuildError(f"{endpoint_path}:{line_number}: endpoint coordinate must be positive")
            key = (assembly, contig)
            result[key] = max(result.get(key, 0), position)
    if not result:
        raise RegistryBuildError(f"{endpoint_path}: no endpoint assembly/contig pairs")
    return result


def _indexed_fasta_adapter(config: Mapping[str, Any], source_id: str) -> tuple[str, str, str]:
    adapters: list[tuple[str, str, str]] = []
    for assembly in config.get("assemblies", []):
        sequence = assembly.get("sequence", {}) if isinstance(assembly, dict) else {}
        adapter = sequence.get("adapter", {}) if isinstance(sequence, dict) else {}
        if adapter.get("type") != "IndexedFastaAdapter":
            continue
        fasta = adapter.get("fastaLocation", {}).get("uri")
        fai = adapter.get("faiLocation", {}).get("uri")
        if isinstance(fasta, str) and isinstance(fai, str):
            adapters.append((str(assembly.get("name", "")), fasta, fai))
    if len(adapters) != 1:
        raise RegistryBuildError(f"{source_id}: expected exactly one IndexedFastaAdapter, found {len(adapters)}")
    return adapters[0]


def build_reference_contig_registry(
    release_root: str | Path,
    jbrowse_bundle: str | Path,
    *,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Return the validated registry and provenance without writing files."""

    release_root = Path(release_root).expanduser().resolve()
    bundle_root = Path(jbrowse_bundle).expanduser().resolve()
    release = _json(release_root / "release_manifest.json")
    release_version = str(release.get("release_version", ""))
    if not release_version:
        raise RegistryBuildError("release manifest has no release_version")
    if not bundle_root.is_dir():
        raise RegistryBuildError(f"missing JBrowse bundle: {bundle_root}")
    checksums, bundle_checksums_sha256 = _parse_bundle_checksums(bundle_root)
    generated_at = _validated_generated_at(generated_at_utc)

    candidates: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    source_observations: list[dict[str, Any]] = []
    published_sources = sorted(
        source_id
        for source_id, entry in release.get("sources", {}).items()
        if isinstance(entry, dict) and entry.get("release_status") in {"published", "published_standardized"}
    )
    for source_id in published_sources:
        if not SOURCE_ID_RE.fullmatch(source_id):
            raise RegistryBuildError(f"invalid published source_id: {source_id}")
        config_path = bundle_root / f"{source_id}.config.json"
        if not config_path.is_file():
            raise RegistryBuildError(f"{source_id}: missing source config {config_path.name}")
        config_sha256 = _verify_bundle_asset(bundle_root, checksums, config_path, source_id)
        config = _json(config_path)
        assembly_name, fasta_uri, fai_uri = _indexed_fasta_adapter(config, source_id)
        fasta_path = _safe_bundle_path(bundle_root, fasta_uri, f"{source_id} FASTA")
        fai_path = _safe_bundle_path(bundle_root, fai_uri, f"{source_id} FAI")
        if not fasta_path.name.startswith(f"{source_id}__") or not fai_path.name.startswith(f"{source_id}__"):
            raise RegistryBuildError(f"{source_id}: reference assets must carry the source prefix")
        fasta_sha256 = _verify_bundle_asset(bundle_root, checksums, fasta_path, source_id)
        fai_sha256 = _verify_bundle_asset(bundle_root, checksums, fai_path, source_id)
        fai_contigs = _fai_contigs(fai_path, f"{source_id}:{fai_path.name}")
        endpoint_pairs = _endpoint_pairs(release_root, source_id)
        missing = sorted({contig for _, contig in endpoint_pairs} - set(fai_contigs))
        if missing:
            raise RegistryBuildError(f"{source_id}: endpoint contigs absent from FAI: {', '.join(missing)}")
        for (assembly, contig), max_position in endpoint_pairs.items():
            length_bp = fai_contigs[contig]
            if length_bp < max_position:
                raise RegistryBuildError(
                    f"{source_id}: FAI contig {contig} is shorter than the maximum endpoint "
                    f"position ({length_bp} < {max_position})"
                )
            candidates[(assembly, contig)].append(
                {
                    "source_id": source_id,
                    "assembly_name": assembly_name,
                    "length_bp": length_bp,
                    "max_endpoint_position_1based": max_position,
                    "fasta_asset_basename": fasta_path.name,
                    "fasta_sha256": fasta_sha256,
                    "fai_asset_basename": fai_path.name,
                    "fai_sha256": fai_sha256,
                    "config_asset_basename": config_path.name,
                    "config_sha256": config_sha256,
                }
            )
        source_observations.append(
            {
                "source_id": source_id,
                "config_asset_basename": config_path.name,
                "config_sha256": config_sha256,
                "assembly_name": assembly_name,
                "fasta_asset_basename": fasta_path.name,
                "fasta_sha256": fasta_sha256,
                "fai_asset_basename": fai_path.name,
                "fai_sha256": fai_sha256,
                "endpoint_pair_count": len(endpoint_pairs),
            }
        )

    rows: list[dict[str, str]] = []
    for (assembly, contig), observations in sorted(candidates.items()):
        lengths = {item["length_bp"] for item in observations}
        fasta_hashes = {item["fasta_sha256"] for item in observations}
        fai_hashes = {item["fai_sha256"] for item in observations}
        if len(lengths) != 1:
            raise RegistryBuildError(f"shared contig conflict {assembly}/{contig}: FAI lengths differ")
        if len(fasta_hashes) != 1:
            raise RegistryBuildError(f"shared contig conflict {assembly}/{contig}: FASTA checksums differ")
        if len(fai_hashes) != 1:
            raise RegistryBuildError(f"shared contig conflict {assembly}/{contig}: FAI checksums differ")
        ordered = sorted(observations, key=lambda item: item["source_id"])
        rows.append(
            {
                "release_version": release_version,
                "assembly_accession": assembly,
                "contig_accession": contig,
                "length_bp": str(next(iter(lengths))),
                "max_endpoint_position_1based": str(max(item["max_endpoint_position_1based"] for item in observations)),
                "supporting_source_ids": ";".join(item["source_id"] for item in ordered),
                "fasta_asset_basename": ordered[0]["fasta_asset_basename"],
                "fasta_sha256": ordered[0]["fasta_sha256"],
                "fai_asset_basename": ordered[0]["fai_asset_basename"],
                "fai_sha256": ordered[0]["fai_sha256"],
                "bundle_sha256sums_sha256": bundle_checksums_sha256,
                "generator_version": GENERATOR_VERSION,
                "generated_at_utc": generated_at,
            }
        )
    if not rows:
        raise RegistryBuildError("no endpoint contigs were matched to JBrowse FAI assets")
    return {
        "schema_version": "1.0",
        "generator_version": GENERATOR_VERSION,
        "generated_at_utc": generated_at,
        "release_version": release_version,
        "source_count": len(published_sources),
        "contig_count": len(rows),
        "jbrowse_bundle_basename": bundle_root.name,
        "bundle_sha256sums": {
            "asset_basename": "SHA256SUMS.txt",
            "sha256": bundle_checksums_sha256,
            "entry_count": len(checksums),
        },
        "source_observations": source_observations,
        "rows": rows,
    }


def write_registry(provenance: Mapping[str, Any], output_tsv: str | Path, output_json: str | Path) -> None:
    output_tsv = Path(output_tsv)
    output_json = Path(output_json)
    output_tsv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    rows = list(provenance["rows"])
    with output_tsv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REFERENCE_CONTIG_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    output_json.write_text(json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", default="data/public/v0.2.0")
    parser.add_argument("--jbrowse-bundle", required=True)
    parser.add_argument("--output-tsv", default="data/registry/reference_contigs.v0.2.0.tsv")
    parser.add_argument("--output-json", default="data/registry/reference_contigs.v0.2.0.json")
    parser.add_argument(
        "--generated-at-utc",
        default=None,
        help="固定 provenance 时间（ISO-8601 UTC，例如 2026-08-21T00:00:00Z）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        provenance = build_reference_contig_registry(
            args.release_root,
            args.jbrowse_bundle,
            generated_at_utc=args.generated_at_utc,
        )
        write_registry(provenance, args.output_tsv, args.output_json)
    except (OSError, UnicodeError, json.JSONDecodeError, RegistryBuildError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "release_version": provenance["release_version"],
                "source_count": provenance["source_count"],
                "contig_count": provenance["contig_count"],
                "output_tsv": str(Path(args.output_tsv)),
                "output_json": str(Path(args.output_json)),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
