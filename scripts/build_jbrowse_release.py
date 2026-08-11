#!/usr/bin/env python3
"""Build the minimal, versioned BTED v0.2.0 JBrowse release archive.

The archive contains the pinned JBrowse 2 static application, 21 source
configurations, and only assets referenced by those configurations.  Test data,
duplicate portal files, raw sequencing files, and BATTER_S1_002 are excluded.
Every copied asset is renamed with its source ID to prevent cross-source
collisions.  Lalanne 2018 literature-curated overlays are omitted because their
supplementary fields are external-link-only; the public browser retains the
GEO-derived signal and called-candidate tracks.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any


RELEASE_VERSION = "v0.2.0"
SOURCE_CONFIGS = {
    "BATTER_S1_001": "config.json",
    "BATTER_S1_003": "bsub.config.json",
    "BATTER_S1_004": "ccre.config.json",
    "BATTER_S1_005": "vnat.config.json",
    "BATTER_S1_006": "warrier2018_spne.config.json",
    "BATTER_S1_007": "lee2019_sliv.config.json",
    "BATTER_S1_008": "thomason2019_pao1.config.json",
    "BATTER_S1_009": "vera2020_zm4.config.json",
    "BATTER_S1_010": "lee2020_save.config.json",
    "BATTER_S1_011": "lee2020_sgri.config.json",
    "BATTER_S1_012": "lee2020_scoe.config.json",
    "BATTER_S1_013": "lee2020_sliv.config.json",
    "BATTER_S1_014": "lee2020_stsu.config.json",
    "BATTER_S1_015": "lee2020_scla.config.json",
    "BATTER_S1_016": "lee2020_satcc15439.config.json",
    "BATTER_S1_017": "hwang2021_scla.config.json",
    "BATTER_S1_018": "synecho2021_pcc7338.config.json",
    "BATTER_S1_019": "synecho2021_pcc6803.config.json",
    "BATTER_S1_020": "forquet2022_ddad.config.json",
    "BATTER_S1_021": "adams2023_b31.config.json",
    "BATTER_S1_022": "mtb2023_termseq.config.json",
}
LALANNE_SOURCES = {
    "BATTER_S1_001", "BATTER_S1_003", "BATTER_S1_004", "BATTER_S1_005",
}
RUNTIME_FILES = ["index.html", "manifest.json", "favicon.ico", "robots.txt", "version.txt"]
ASSEMBLY_GROUPS = {
    "GCF_000739105.1": ["BATTER_S1_007", "BATTER_S1_013"],
    "GCF_005519465.1": ["BATTER_S1_015", "BATTER_S1_017"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def walk_uris(value: Any) -> list[tuple[dict[str, Any], str]]:
    found: list[tuple[dict[str, Any], str]] = []
    if isinstance(value, dict):
        if isinstance(value.get("uri"), str):
            found.append((value, value["uri"]))
        for child in value.values():
            found.extend(walk_uris(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(walk_uris(child))
    return found


def is_restricted_lalanne_track(track: dict[str, Any]) -> bool:
    searchable = " ".join(
        [str(track.get("name", "")), str(track.get("trackId", ""))]
        + [str(item) for item in track.get("category", [])]
    ).lower()
    return "literature" in searchable or "curated_terminator" in searchable


def is_reference_annotation(track: dict[str, Any]) -> bool:
    searchable = " ".join(
        [str(track.get("name", "")), str(track.get("trackId", ""))]
        + [str(item) for item in track.get("category", [])]
    ).lower()
    return "reference annotation" in searchable or "gene annotation" in searchable


def reference_files(config: dict[str, Any], package_root: Path) -> tuple[Path, Path]:
    assembly = config.get("assemblies", [None])[0]
    if not isinstance(assembly, dict):
        raise ValueError("JBrowse config must contain one assembly")
    configured = [package_root / uri for _container, uri in walk_uris(assembly.get("sequence", {}))]
    fasta = [path for path in configured if path.suffix == ".fna"]
    fai = [path for path in configured if path.suffix == ".fai"]
    if len(fasta) != 1 or len(fai) != 1:
        raise ValueError("JBrowse assembly must reference one FASTA and one FAI")
    return fasta[0], fai[0]


def default_linear_session(
    accession: str,
    assembly_name: str,
    tracks: list[dict[str, Any]],
    package_root: Path,
    fai_path: Path,
) -> dict[str, Any]:
    """Create a deterministic initial view around the first published endpoint."""

    endpoint_tracks = [track for track in tracks if not is_reference_annotation(track)]
    bed_paths = [
        package_root / uri
        for track in endpoint_tracks
        for _container, uri in walk_uris(track)
        if uri.endswith(".bed")
    ]
    first_bed = next((path for path in bed_paths if path.is_file() and path.stat().st_size), None)
    if first_bed is None:
        raise ValueError(f"{accession}: cannot choose a default region without a BED track")
    first_fields = next(line for line in first_bed.read_text(encoding="utf-8").splitlines() if line).split("\t")
    ref_name, feature_start, feature_end = first_fields[0], int(first_fields[1]), int(first_fields[2])
    contig_lengths = {
        fields[0]: int(fields[1])
        for line in fai_path.read_text(encoding="utf-8").splitlines()
        if line and len(fields := line.split("\t")) >= 2
    }
    if ref_name not in contig_lengths:
        raise ValueError(f"{accession}: BED contig {ref_name} is absent from the shared FAI")
    view_start = max(0, feature_start - 5_000)
    view_end = min(contig_lengths[ref_name], feature_end + 5_000)

    session_tracks = []
    for index, track in enumerate(tracks, start=1):
        track_id = str(track["trackId"])
        track_type = str(track.get("type", "FeatureTrack"))
        display_type = "LinearWiggleDisplay" if track_type == "QuantitativeTrack" else "LinearBasicDisplay"
        session_tracks.append({
            "id": f"bted_track_{index}",
            "type": track_type,
            "configuration": track_id,
            "minimized": False,
            "displays": [{
                "id": f"bted_display_{index}",
                "type": display_type,
                "configuration": f"{track_id}-{display_type}",
            }],
        })
    return {
        "name": f"BTED {accession} · independent source tracks",
        "views": [{
            "id": "bted_linear_genome_view",
            "type": "LinearGenomeView",
            "offsetPx": 0,
            "bpPerPx": max((view_end - view_start) / 1_000, 1),
            "displayedRegions": [{
                "refName": ref_name,
                "start": view_start,
                "end": view_end,
                "reversed": False,
                "assemblyName": assembly_name,
            }],
            "tracks": session_tracks,
        }],
    }


def copy_runtime(viewer_root: Path, package_root: Path) -> None:
    for name in RUNTIME_FILES:
        source = viewer_root / name
        if not source.is_file():
            raise FileNotFoundError(f"Missing JBrowse runtime file: {source}")
        shutil.copy2(source, package_root / name)
    static_source = viewer_root / "static"
    if not static_source.is_dir():
        raise FileNotFoundError(f"Missing JBrowse runtime directory: {static_source}")
    shutil.copytree(static_source, package_root / "static")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True, help="Local BGIRNA working tree")
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    args = parser.parse_args()
    input_root = args.input_root.expanduser().resolve()
    viewer_root = input_root / "browser/jbrowse2/viewer"
    output_dir = args.output_dir.expanduser().resolve()
    package_name = "BTED-v0.2.0-jbrowse"
    package_root = output_dir / package_name
    archive_path = output_dir / "BTED-v0.2.0-jbrowse-assets.tar.gz"

    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True)
    (package_root / "assets").mkdir()
    copy_runtime(viewer_root, package_root)

    catalog: dict[str, Any] = {
        "release_version": RELEASE_VERSION,
        "jbrowse_version": (viewer_root / "version.txt").read_text(encoding="utf-8").strip(),
        "source_count": len(SOURCE_CONFIGS),
        "excluded_sources": ["BATTER_S1_002"],
        "sources": {},
        "assemblies": {},
    }
    seen_destination_names: set[str] = set()

    for source_id, config_name in SOURCE_CONFIGS.items():
        config_path = viewer_root / config_name
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if source_id in LALANNE_SOURCES:
            config["tracks"] = [track for track in config.get("tracks", []) if not is_restricted_lalanne_track(track)]

        source_assets: list[str] = []
        for uri_container, uri in walk_uris(config):
            if "://" in uri or uri.startswith("data:"):
                raise ValueError(f"{source_id}: remote/data URI is not allowed in the portable package: {uri}")
            source_asset = (config_path.parent / uri).resolve()
            try:
                source_asset.relative_to(viewer_root.resolve())
            except ValueError as exc:
                raise ValueError(f"{source_id}: asset escapes viewer root: {uri}") from exc
            if not source_asset.is_file():
                raise FileNotFoundError(f"{source_id}: missing configured asset: {source_asset}")
            destination_name = f"{source_id}__{source_asset.name}"
            if destination_name not in seen_destination_names:
                shutil.copy2(source_asset, package_root / "assets" / destination_name)
                seen_destination_names.add(destination_name)
            uri_container["uri"] = f"assets/{destination_name}"
            source_assets.append(f"assets/{destination_name}")

        if not config.get("assemblies"):
            raise ValueError(f"{source_id}: config has no assembly")
        source_assembly_name = str(config["assemblies"][0]["name"])
        source_fai = reference_files(config, package_root)[1]
        config["defaultSession"] = default_linear_session(
            source_id,
            source_assembly_name,
            config.get("tracks", []),
            package_root,
            source_fai,
        )

        config_output = package_root / f"{source_id}.config.json"
        config_output.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        config_text = config_output.read_text(encoding="utf-8").lower()
        if source_id in LALANNE_SOURCES and ("literature_curated" in config_text or "curated terminator" in config_text):
            raise ValueError(f"{source_id}: restricted Lalanne literature overlay remains in public config")
        catalog["sources"][source_id] = {
            "config": config_output.name,
            "asset_count": len(set(source_assets)),
            "assets": sorted(set(source_assets)),
            "track_count": len(config.get("tracks", [])),
        }

    (package_root / "assemblies").mkdir()
    for assembly_accession, source_ids in ASSEMBLY_GROUPS.items():
        source_configs = [
            json.loads((package_root / f"{source_id}.config.json").read_text(encoding="utf-8"))
            for source_id in source_ids
        ]
        reference_pairs = [reference_files(config, package_root) for config in source_configs]
        fasta_hashes = {sha256(pair[0]) for pair in reference_pairs}
        fai_hashes = {sha256(pair[1]) for pair in reference_pairs}
        if len(fasta_hashes) != 1 or len(fai_hashes) != 1:
            raise ValueError(
                f"{assembly_accession}: sources cannot share one view because FASTA/FAI content differs"
            )

        combined = copy.deepcopy(source_configs[0])
        assembly_name = f"BTED_{assembly_accession.replace('.', '_')}"
        combined_assembly = combined["assemblies"][0]
        combined_assembly["name"] = assembly_name
        combined_assembly["displayName"] = f"BTED {assembly_accession} · {len(source_ids)} source tracks"
        combined_assembly["sequence"]["trackId"] = f"{assembly_name}_refseq"

        combined_tracks: list[dict[str, Any]] = []
        reference_tracks = [track for track in source_configs[0].get("tracks", []) if is_reference_annotation(track)]
        if len(reference_tracks) != 1:
            raise ValueError(f"{assembly_accession}: expected one reference annotation track")
        reference_track = copy.deepcopy(reference_tracks[0])
        reference_track["assemblyNames"] = [assembly_name]
        combined_tracks.append(reference_track)

        endpoint_track_ids: list[str] = []
        for source_id, config in zip(source_ids, source_configs):
            endpoint_tracks = [track for track in config.get("tracks", []) if not is_reference_annotation(track)]
            if not endpoint_tracks:
                raise ValueError(f"{source_id}: no source endpoint track found for assembly view")
            for track in endpoint_tracks:
                track = copy.deepcopy(track)
                track["assemblyNames"] = [assembly_name]
                track["name"] = f"{source_id} · {track.get('name', 'endpoint track')}"
                track["category"] = ["BTED source tracks", source_id]
                combined_tracks.append(track)
                endpoint_track_ids.append(str(track.get("trackId")))

        combined["tracks"] = combined_tracks
        combined["defaultSession"] = default_linear_session(
            assembly_accession,
            assembly_name,
            combined_tracks,
            package_root,
            reference_pairs[0][1],
        )
        # The combined config lives one directory below the source configs.
        # Keep all resources portable by resolving them through ../assets/.
        for uri_container, uri in walk_uris(combined):
            if uri.startswith("assets/"):
                uri_container["uri"] = f"../{uri}"
        combined_path = package_root / "assemblies" / f"{assembly_accession}.config.json"
        combined_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        catalog["assemblies"][assembly_accession] = {
            "config": str(combined_path.relative_to(package_root)),
            "source_ids": source_ids,
            "reference_source_id": source_ids[0],
            "endpoint_track_ids": endpoint_track_ids,
            "reference_fasta_sha256": next(iter(fasta_hashes)),
            "reference_fai_sha256": next(iter(fai_hashes)),
        }

    (package_root / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    package_files = sorted(path for path in package_root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    (package_root / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256(path)}  {path.relative_to(package_root)}\n" for path in package_files),
        encoding="utf-8",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(package_root, arcname=package_name)
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    checksum_path.write_text(f"{sha256(archive_path)}  {archive_path.name}\n", encoding="utf-8")

    total_bytes = sum(path.stat().st_size for path in package_root.rglob("*") if path.is_file())
    print(
        f"PASS  {archive_path.name}: {len(SOURCE_CONFIGS)} source configs, "
        f"{len(ASSEMBLY_GROUPS)} multi-track assembly configs, "
        f"{len(seen_destination_names)} referenced assets, {total_bytes / 1024 / 1024:.1f} MiB unpacked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
