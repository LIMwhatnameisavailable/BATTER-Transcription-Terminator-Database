#!/usr/bin/env python3
"""Prepare the public objects declared by a materialized BTED bundle.

The materialized ``assets.jsonl`` is the complete release object list.  The
tracked browser inventory is used to cross-check browser identities and to
resolve local JBrowse files; canonical ``records/`` paths resolve from the
release root.  This command never uploads anything and never overwrites a
non-empty output directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INVENTORY = REPO_ROOT / "data/registry/jbrowse_assets.v0.2.0.tsv"
DEFAULT_RELEASE = REPO_ROOT / "data/public/v0.2.0"
DEFAULT_BUNDLE = REPO_ROOT.parent / "bted-v0.2/dist/BTED-v0.2.0-jbrowse"
MANIFEST_NAME = "ASSET_OBJECTS.json"
CHECKSUM_NAME = "SHA256SUMS.txt"
GENERATOR_VERSION = "bted-public-asset-objects-0.2.0"


class AssetPreparationError(ValueError):
    """Raised when a materialized asset or source file cannot be prepared."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_relative(value: str, *, field: str) -> Path:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise AssetPreparationError(f"unsafe {field}: {value!r}")
    return path


def _validate_output_dir(output_dir: Path) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise AssetPreparationError(f"output path is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            raise AssetPreparationError(f"output directory must be empty: {output_dir}")


def _load_inventory(inventory_path: Path) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    try:
        with inventory_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
    except (OSError, csv.Error) as error:
        raise AssetPreparationError(f"cannot read browser inventory: {inventory_path}") from error
    by_object_path: dict[str, dict[str, str]] = {}
    for row in rows:
        object_path = row.get("object_path", "")
        if not object_path or object_path in by_object_path:
            raise AssetPreparationError(f"duplicate or missing browser object_path: {object_path!r}")
        by_object_path[object_path] = row
    return rows, by_object_path


def _load_materialized_bundle(materialized_bundle: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest_path = materialized_bundle / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AssetPreparationError(f"cannot read materialized manifest: {manifest_path}") from error
    if not isinstance(manifest, dict):
        raise AssetPreparationError("materialized manifest must be a JSON object")
    table = manifest.get("tables", {}).get("assets", {})
    if not isinstance(table, dict) or not isinstance(table.get("file"), str):
        raise AssetPreparationError("materialized manifest has no assets table")
    assets_relative = _safe_relative(table["file"], field="assets table file")
    assets_path = materialized_bundle / assets_relative
    try:
        actual_sha = sha256(assets_path)
        rows = [json.loads(line) for line in assets_path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as error:
        raise AssetPreparationError(f"cannot read materialized assets: {assets_path}") from error
    if actual_sha != table.get("sha256") or len(rows) != table.get("row_count"):
        raise AssetPreparationError("materialized assets checksum or row count mismatch")
    if not all(isinstance(row, dict) for row in rows):
        raise AssetPreparationError("materialized assets rows must be JSON objects")
    return manifest, rows


def _source_for_asset(
    asset: dict[str, Any],
    *,
    inventory_by_object_path: dict[str, dict[str, str]],
    bundle: Path,
    release_root: Path,
) -> tuple[str, Path, str, dict[str, str] | None]:
    logical_path = _safe_relative(str(asset.get("logical_path", "")), field="logical_path")
    object_path = logical_path.as_posix()
    inventory_row = inventory_by_object_path.get(object_path)
    if inventory_row is not None:
        bundle_path = inventory_row.get("bundle_path", "").strip()
        canonical_path = inventory_row.get("canonical_path", "").strip()
        if bool(bundle_path) == bool(canonical_path):
            raise AssetPreparationError(f"{asset.get('asset_id', '<unknown>')}: invalid inventory source path")
        if bundle_path:
            relative = _safe_relative(bundle_path, field="bundle_path")
            return "jbrowse_bundle", bundle / relative, relative.as_posix(), inventory_row
        relative = _safe_relative(canonical_path, field="canonical_path")
        return "canonical_release", release_root / relative, relative.as_posix(), inventory_row

    if logical_path.parts[0] != "records":
        raise AssetPreparationError(f"{asset.get('asset_id', '<unknown>')}: no local source mapping for {object_path}")
    return "canonical_release", release_root / logical_path, object_path, None


def _validate_inventory_identity(asset: dict[str, Any], inventory_row: dict[str, str] | None) -> None:
    if inventory_row is None:
        return
    asset_id = str(asset.get("asset_id"))
    if asset_id != inventory_row.get("asset_id"):
        raise AssetPreparationError(f"{asset_id}: materialized/inventory asset_id mismatch")
    if int(asset.get("byte_size", -1)) != int(inventory_row.get("byte_size", -2)):
        raise AssetPreparationError(f"{asset_id}: materialized/inventory byte_size mismatch")
    if str(asset.get("sha256")) != inventory_row.get("sha256"):
        raise AssetPreparationError(f"{asset_id}: materialized/inventory sha256 mismatch")


def prepare_public_asset_objects(
    *,
    materialized_bundle: Path,
    inventory_path: Path = DEFAULT_INVENTORY,
    bundle: Path = DEFAULT_BUNDLE,
    release_root: Path = DEFAULT_RELEASE,
    output_dir: Path,
    manifest_only: bool = False,
) -> dict[str, Any]:
    """Validate selected materialized assets and write an upload-ready layout."""

    _validate_output_dir(output_dir)
    inventory_rows, inventory_by_object_path = _load_inventory(inventory_path)
    materialized_manifest, assets = _load_materialized_bundle(materialized_bundle)
    release_versions = sorted({str(asset.get("release_version", "")) for asset in assets})
    if len(release_versions) != 1 or not release_versions[0]:
        raise AssetPreparationError(f"expected one materialized release version, found {release_versions}")
    if materialized_manifest.get("release_version") != release_versions[0]:
        raise AssetPreparationError("materialized manifest release_version mismatch")

    asset_ids: set[str] = set()
    object_paths: set[str] = set()
    selected = [
        asset
        for asset in assets
        if asset.get("is_public") is True
        and asset.get("redistribution_status") == "verified_redistributable"
    ]
    selected.sort(key=lambda asset: (str(asset.get("logical_path")), str(asset.get("asset_id"))))
    objects: list[dict[str, Any]] = []
    sources: list[tuple[Path, Path]] = []

    for asset in selected:
        asset_id = str(asset.get("asset_id", ""))
        if not asset_id or asset_id in asset_ids:
            raise AssetPreparationError(f"duplicate or missing materialized asset_id: {asset_id!r}")
        asset_ids.add(asset_id)
        object_path = _safe_relative(str(asset.get("logical_path", "")), field="logical_path").as_posix()
        if object_path in object_paths:
            raise AssetPreparationError(f"duplicate materialized logical_path: {object_path}")
        object_paths.add(object_path)
        source_kind, source_path, source_relative, inventory_row = _source_for_asset(
            asset,
            inventory_by_object_path=inventory_by_object_path,
            bundle=bundle,
            release_root=release_root,
        )
        _validate_inventory_identity(asset, inventory_row)
        if not source_path.is_file():
            raise AssetPreparationError(f"{asset_id}: missing source file: {source_relative}")
        actual_size = source_path.stat().st_size
        actual_sha = sha256(source_path)
        if actual_size != int(asset["byte_size"]):
            raise AssetPreparationError(f"{asset_id}: byte_size mismatch")
        if actual_sha != asset["sha256"]:
            raise AssetPreparationError(f"{asset_id}: sha256 mismatch")

        item = {
            "asset_id": asset_id,
            "release_version": release_versions[0],
            "source_id": asset.get("source_id_ref"),
            "assembly_accession": asset.get("assembly_id_ref"),
            "asset_kind": asset.get("asset_kind"),
            "object_path": object_path,
            "byte_size": actual_size,
            "sha256": actual_sha,
            "mime_type": asset.get("mime_type"),
            "supports_range": bool(asset.get("supports_range", False)),
            "redistribution_status": asset["redistribution_status"],
            "is_public": True,
            "source": {"kind": source_kind, "path": source_relative},
        }
        if inventory_row is not None:
            item["asset_role"] = inventory_row.get("asset_role")
        objects.append(item)
        sources.append((source_path, _safe_relative(object_path, field="object_path")))

    browser_inventory_public = {
        row["asset_id"]
        for row in inventory_rows
        if row.get("is_public") == "true"
        and row.get("redistribution_status") == "verified_redistributable"
    }
    selected_browser = {
        str(asset.get("asset_id"))
        for asset in selected
        if str(asset.get("logical_path")) in inventory_by_object_path
    }
    if selected_browser != browser_inventory_public:
        raise AssetPreparationError("materialized browser public set does not match tracked inventory")

    materialized_manifest_path = materialized_bundle / "manifest.json"
    manifest = {
        "schema_version": "1.0",
        "generator": "scripts/prepare_v03_public_asset_objects.py",
        "generator_version": GENERATOR_VERSION,
        "release_version": release_versions[0],
        "mode": "manifest_only" if manifest_only else "copy",
        "materialized_bundle": {
            "path": "manifest.json",
            "sha256": sha256(materialized_manifest_path),
            "asset_row_count": len(assets),
        },
        "inventory": {
            "path": "data/registry/jbrowse_assets.v0.2.0.tsv",
            "sha256": sha256(inventory_path),
            "row_count": len(inventory_rows),
            "public_browser_count": len(browser_inventory_public),
        },
        "selection": {
            "policy": "materialized assets where is_public=true AND redistribution_status=verified_redistributable",
            "selected_count": len(objects),
            "excluded_count": len(assets) - len(objects),
            "materialized_asset_count": len(assets),
            "public_browser_crosscheck_count": len(selected_browser),
        },
        "objects": objects,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    if not manifest_only:
        for source_path, object_relative in sources:
            destination = output_dir / object_relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, destination)
            if destination.stat().st_size != source_path.stat().st_size or sha256(destination) != sha256(source_path):
                raise AssetPreparationError(f"copied object verification failed: {object_relative}")

    manifest_path = output_dir / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checksum_rows = [(sha256(manifest_path), MANIFEST_NAME)]
    if not manifest_only:
        checksum_rows.extend((item["sha256"], item["object_path"]) for item in objects)
    (output_dir / CHECKSUM_NAME).write_text(
        "".join(f"{digest}  {path}\n" for digest, path in sorted(checksum_rows, key=lambda item: item[1])),
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialized-bundle", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--jbrowse-bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest-only", action="store_true")
    args = parser.parse_args()
    manifest = prepare_public_asset_objects(
        materialized_bundle=args.materialized_bundle,
        inventory_path=args.inventory,
        bundle=args.jbrowse_bundle,
        release_root=args.release_root,
        output_dir=args.output_dir,
        manifest_only=args.manifest_only,
    )
    print(
        f"PASS {manifest['selection']['selected_count']} public objects "
        f"({manifest['mode']}) -> {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
