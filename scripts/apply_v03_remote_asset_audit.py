#!/usr/bin/env python3
"""Apply a deterministic remote-asset audit to a materialized BTED bundle.

This is an offline, report-driven step.  It neither uploads nor requests any
remote object.  A verified output is produced only when every public,
redistributable materialized asset is present in the report, matches the materialized
identity, and passed both HEAD and single-byte Range checks.  The tracked
browser inventory is an additional provenance check for its browser subset;
the complete required set comes from the materialized asset table.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.importer.postgres import verify_bundle  # noqa: E402


DEFAULT_INVENTORY = REPO_ROOT / "data/registry/jbrowse_assets.v0.2.0.tsv"
GENERATOR_VERSION = "bted-apply-remote-asset-audit-0.1.0"


class RemoteAuditApplicationError(ValueError):
    """Raised when a remote audit cannot safely verify a materialized bundle."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RemoteAuditApplicationError(f"cannot read JSON: {path}") from error
    if not isinstance(value, dict):
        raise RemoteAuditApplicationError(f"JSON root must be an object: {path}")
    return value


def _load_assets(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise RemoteAuditApplicationError(f"assets.jsonl:{number} is not an object")
                rows.append(value)
    except (OSError, json.JSONDecodeError) as error:
        raise RemoteAuditApplicationError(f"cannot read assets table: {path}") from error
    return rows


def _required_browser_assets(inventory_path: Path) -> dict[str, dict[str, str]]:
    try:
        with inventory_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
    except (OSError, csv.Error) as error:
        raise RemoteAuditApplicationError(f"cannot read browser inventory: {inventory_path}") from error
    selected = {
        row["asset_id"]: row
        for row in rows
        if row.get("is_public") == "true"
        and row.get("redistribution_status") == "verified_redistributable"
    }
    if len(selected) != sum(
        row.get("is_public") == "true"
        and row.get("redistribution_status") == "verified_redistributable"
        for row in rows
    ):
        raise RemoteAuditApplicationError("browser inventory contains duplicate public asset_id")
    return selected


def _apply_report(
    manifest: dict[str, Any],
    assets: list[dict[str, Any]],
    audit: Mapping[str, Any],
    browser_inventory: Mapping[str, Mapping[str, str]],
) -> list[dict[str, Any]]:
    release_version = str(manifest.get("release_version", ""))
    if audit.get("release_version") != release_version:
        raise RemoteAuditApplicationError("remote audit release_version mismatch")
    audit_objects = audit.get("objects")
    if not isinstance(audit_objects, list):
        raise RemoteAuditApplicationError("remote audit must contain an objects list")
    audit_by_id = {
        str(row.get("asset_id")): row
        for row in audit_objects
        if isinstance(row, Mapping) and row.get("asset_id")
    }
    assets_by_id = {str(row.get("asset_id")): row for row in assets}
    required = {
        asset_id: row
        for asset_id, row in assets_by_id.items()
        if row.get("is_public") is True
        and row.get("redistribution_status") == "verified_redistributable"
    }
    if set(audit_by_id) != set(required):
        raise RemoteAuditApplicationError("remote audit asset set does not match all required public assets")
    if not set(browser_inventory) <= set(required):
        raise RemoteAuditApplicationError("browser inventory public assets are missing from required bundle assets")

    for asset_id, asset in required.items():
        report = audit_by_id[asset_id]
        identity = (
            str(asset.get("logical_path")),
            int(asset.get("byte_size", -1)),
            str(asset.get("sha256")),
        )
        audited = (
            str(report.get("object_path")),
            int(report.get("byte_size", -1)),
            str(report.get("sha256")),
        )
        if audited != identity:
            raise RemoteAuditApplicationError(f"{asset_id}: asset identity mismatch")
        inventory_row = browser_inventory.get(asset_id)
        if inventory_row is not None:
            browser_identity = (
                str(inventory_row.get("object_path")),
                int(str(inventory_row.get("byte_size", -1))),
                str(inventory_row.get("sha256")),
            )
            if browser_identity != identity:
                raise RemoteAuditApplicationError(f"{asset_id}: browser inventory identity mismatch")
        if report.get("url") != asset.get("origin_url"):
            raise RemoteAuditApplicationError(f"{asset_id}: audited URL does not match materialized origin")
        if not (
            report.get("ok") is True
            and report.get("supports_range") is True
            and report.get("head_status") == 200
            and report.get("range_status") == 206
        ):
            raise RemoteAuditApplicationError(f"{asset_id}: HEAD/Range audit did not pass")
        if asset.get("is_public") is not True or asset.get("redistribution_status") != "verified_redistributable":
            raise RemoteAuditApplicationError(f"{asset_id}: materialized public/redistribution state mismatch")

    updated: list[dict[str, Any]] = []
    for row in assets:
        item = dict(row)
        if str(item.get("asset_id")) in required:
            item["supports_range"] = True
        elif item.get("is_public") is not True or item.get("redistribution_status") != "verified_redistributable":
            item["supports_range"] = False
        updated.append(item)
    return updated


def _write_verified_bundle(
    source_dir: Path,
    output_dir: Path,
    manifest: dict[str, Any],
    assets: list[dict[str, Any]],
) -> None:
    if output_dir.exists():
        if not output_dir.is_dir() or any(output_dir.iterdir()):
            raise RemoteAuditApplicationError(f"output directory must be empty: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.tmp-", dir=output_dir.parent))
    try:
        for path in source_dir.iterdir():
            if path.name not in {"manifest.json", "SHA256SUMS.txt", "assets.jsonl"}:
                shutil.copyfile(path, temp_dir / path.name)
        assets_path = temp_dir / "assets.jsonl"
        with assets_path.open("w", encoding="utf-8", newline="") as handle:
            for row in assets:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        manifest["tables"]["assets"] = {
            **manifest["tables"]["assets"],
            "row_count": len(assets),
            "sha256": sha256(assets_path),
            "byte_size": assets_path.stat().st_size,
        }
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        checksum_lines = [
            f"{sha256(path)}  {path.name}"
            for path in sorted(temp_dir.iterdir(), key=lambda item: item.name)
        ]
        (temp_dir / "SHA256SUMS.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
        if output_dir.exists():
            output_dir.rmdir()
        os.replace(temp_dir, output_dir)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def apply_remote_asset_audit(
    *,
    bundle_dir: Path,
    audit_path: Path,
    output_dir: Path,
    inventory_path: Path = DEFAULT_INVENTORY,
) -> dict[str, Any]:
    """Create a checksum-complete verified bundle from a passed audit report."""

    bundle_dir = bundle_dir.resolve()
    verify_bundle(bundle_dir)
    manifest = _load_json(bundle_dir / "manifest.json")
    if manifest.get("asset_origin", {}).get("asset_origin_status") != "planned_not_verified":
        raise RemoteAuditApplicationError("input bundle must be planned_not_verified")
    inventory_meta = manifest.get("jbrowse_asset_inventory")
    if not isinstance(inventory_meta, Mapping) or inventory_meta.get("sha256") != sha256(inventory_path):
        raise RemoteAuditApplicationError("tracked browser inventory does not match bundle provenance")
    browser_inventory = _required_browser_assets(inventory_path)
    audit = _load_json(audit_path)
    assets = _load_assets(bundle_dir / manifest["tables"]["assets"]["file"])
    required_public_count = sum(
        row.get("is_public") is True
        and row.get("redistribution_status") == "verified_redistributable"
        for row in assets
    )
    updated_assets = _apply_report(manifest, assets, audit, browser_inventory)

    output_manifest = dict(manifest)
    output_manifest["asset_origin"] = dict(manifest["asset_origin"])
    output_manifest["asset_origin"]["asset_origin_status"] = "verified"
    output_manifest["jbrowse_asset_inventory"] = dict(inventory_meta)
    output_manifest["jbrowse_asset_inventory"]["asset_origin_status"] = "verified"
    output_manifest["remote_asset_audit"] = {
        "path": audit_path.name,
        "sha256": sha256(audit_path),
        "required_public_asset_count": required_public_count,
        "required_public_browser_asset_count": len(browser_inventory),
        "passed_count": required_public_count,
        "application_generator_version": GENERATOR_VERSION,
    }
    _write_verified_bundle(bundle_dir, output_dir.resolve(), output_manifest, updated_assets)
    verify_bundle(output_dir)
    return output_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--remote-audit", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--jbrowse-asset-inventory", type=Path, default=DEFAULT_INVENTORY)
    args = parser.parse_args()
    manifest = apply_remote_asset_audit(
        bundle_dir=args.bundle_dir,
        audit_path=args.remote_audit,
        output_dir=args.output_dir,
        inventory_path=args.jbrowse_asset_inventory,
    )
    count = manifest["remote_asset_audit"]["passed_count"]
    print(f"PASS verified {count} public assets -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
