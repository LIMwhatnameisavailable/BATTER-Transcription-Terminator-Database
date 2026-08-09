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
        f"{len(seen_destination_names)} referenced assets, {total_bytes / 1024 / 1024:.1f} MiB unpacked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
