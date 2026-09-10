"""Focused tests for preparing the complete public v0.3 asset object set."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from backend.importer.materialize import materialize_release


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE = REPO_ROOT.parent / "bted-v0.2/dist/BTED-v0.2.0-jbrowse"
INVENTORY = REPO_ROOT / "data/registry/jbrowse_assets.v0.2.0.tsv"
RELEASE = REPO_ROOT / "data/public/v0.2.0"


def _load_module():
    path = REPO_ROOT / "scripts/prepare_v03_public_asset_objects.py"
    spec = importlib.util.spec_from_file_location("prepare_v03_public_assets", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_materialized_bundle(root: Path, assets: list[dict[str, Any]]) -> Path:
    root.mkdir(parents=True)
    assets_path = root / "assets.jsonl"
    assets_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in assets),
        encoding="utf-8",
    )
    manifest = {
        "release_version": "v0.2.0",
        "asset_origin": {"asset_origin_status": "planned_not_verified"},
        "tables": {
            "assets": {
                "file": "assets.jsonl",
                "row_count": len(assets),
                "sha256": _sha256(assets_path),
            }
        },
    }
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    return root


@unittest.skipUnless(BUNDLE.is_dir() and INVENTORY.is_file(), "the frozen v0.2 JBrowse bundle is not available")
class TestRealPublicAssetPlan(unittest.TestCase):
    def test_real_materialized_bundle_selects_208_and_cross_checks_105_browser_objects(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            staging = materialize_release(
                RELEASE,
                repo_root=REPO_ROOT,
                output_dir=root / "staging",
                asset_origin_base="https://assets.example.test/bted",
                generated_at_utc="2026-08-22T00:00:00Z",
                jbrowse_asset_inventory=INVENTORY,
            ).output_dir
            first = module.prepare_public_asset_objects(
                materialized_bundle=staging,
                inventory_path=INVENTORY,
                bundle=BUNDLE,
                release_root=RELEASE,
                output_dir=root / "first",
                manifest_only=True,
            )
            second = module.prepare_public_asset_objects(
                materialized_bundle=staging,
                inventory_path=INVENTORY,
                bundle=BUNDLE,
                release_root=RELEASE,
                output_dir=root / "second",
                manifest_only=True,
            )
            self.assertEqual(first["selection"], {
                "policy": "materialized assets where is_public=true AND redistribution_status=verified_redistributable",
            "selected_count": 208,
            "excluded_count": 3,
                "materialized_asset_count": 211,
            "public_browser_crosscheck_count": 105,
            })
            self.assertEqual(len(first["objects"]), 208)
            self.assertEqual((root / "first/ASSET_OBJECTS.json").read_bytes(), (root / "second/ASSET_OBJECTS.json").read_bytes())
            self.assertEqual((root / "first/SHA256SUMS.txt").read_bytes(), (root / "second/SHA256SUMS.txt").read_bytes())
            identities = {"asset_id", "object_path", "byte_size", "sha256"}
            self.assertTrue(all(identities <= set(row) for row in first["objects"]))
            paths = {row["object_path"] for row in first["objects"]}
            self.assertIn("records/BATTER_S1_006/source_annotations.tsv", paths)
            self.assertIn("records/BATTER_S1_006/endpoints.bed", paths)
            self.assertIn("assemblies/GCF_000006765.1/reference/reference.fna", paths)
            serialized = json.dumps(first).lower()
            self.assertNotIn("batter_s1_002", serialized)
            self.assertNotIn("external_link_only", serialized)
            for forbidden in ("candidate", "signed-log", "normalized", ".config.json", "jbrowse-ui", "index.html"):
                self.assertNotIn(forbidden, serialized)
            self.assertEqual({path.name for path in (root / "first").iterdir()}, {"ASSET_OBJECTS.json", "SHA256SUMS.txt"})


class TestSmallPublicAssetCopy(unittest.TestCase):
    def test_materialized_identity_resolution_copy_and_nonempty_output_rejection(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = root / "bundle"
            release = root / "release"
            release_file = release / "records/S1/manifest.json"
            release_file.parent.mkdir(parents=True)
            release_file.write_text("{\"source_id\": \"S1\"}\n", encoding="utf-8")
            browser_file = bundle / "reference.fna"
            bundle.mkdir()
            browser_file.write_bytes(b">ctg\nACGT\n")
            inventory = root / "inventory.tsv"
            columns = [
                "asset_id", "release_version", "source_id", "assembly_accession", "asset_role",
                "asset_kind", "bundle_path", "canonical_path", "object_path", "byte_size", "sha256",
                "mime_type", "supports_range", "redistribution_status", "is_public",
            ]
            inventory_row = {
                "asset_id": "public-fasta", "release_version": "v0.2.0", "source_id": "S1",
                "assembly_accession": "GCF_TEST.1", "asset_role": "reference_fasta",
                "asset_kind": "fasta", "bundle_path": "reference.fna", "canonical_path": "",
                "object_path": "assemblies/GCF_TEST.1/reference/reference.fna",
                "byte_size": str(browser_file.stat().st_size), "sha256": _sha256(browser_file),
                "mime_type": "text/plain", "supports_range": "false",
                "redistribution_status": "verified_redistributable", "is_public": "true",
            }
            with inventory.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
                writer.writeheader()
                writer.writerow(inventory_row)
            assets = [
                {
                    "asset_id": "public-manifest", "release_version": "v0.2.0", "asset_kind": "metadata",
                    "logical_path": "records/S1/manifest.json", "byte_size": release_file.stat().st_size,
                    "sha256": _sha256(release_file), "mime_type": "application/json", "supports_range": False,
                    "redistribution_status": "verified_redistributable", "is_public": True,
                    "source_id_ref": "S1", "assembly_id_ref": None,
                },
                {
                    "asset_id": "public-fasta", "release_version": "v0.2.0", "asset_kind": "fasta",
                    "logical_path": inventory_row["object_path"], "byte_size": browser_file.stat().st_size,
                    "sha256": inventory_row["sha256"], "mime_type": "text/plain", "supports_range": False,
                    "redistribution_status": "verified_redistributable", "is_public": True,
                    "source_id_ref": None, "assembly_id_ref": "GCF_TEST.1",
                },
                {
                    "asset_id": "private-checksum", "release_version": "v0.2.0", "asset_kind": "checksum",
                    "logical_path": "records/S1/SHA256SUMS.txt", "byte_size": 1, "sha256": "a" * 64,
                    "mime_type": "text/plain", "supports_range": False,
                    "redistribution_status": "external_link_only", "is_public": False,
                    "source_id_ref": "S1", "assembly_id_ref": None,
                },
            ]
            staging = _write_materialized_bundle(root / "staging", assets)
            output = root / "output"
            manifest = module.prepare_public_asset_objects(
                materialized_bundle=staging,
                inventory_path=inventory,
                bundle=bundle,
                release_root=release,
                output_dir=output,
            )
            self.assertEqual(manifest["selection"]["selected_count"], 2)
            self.assertEqual(manifest["selection"]["excluded_count"], 1)
            self.assertEqual((output / "records/S1/manifest.json").read_bytes(), release_file.read_bytes())
            self.assertEqual((output / "assemblies/GCF_TEST.1/reference/reference.fna").read_bytes(), browser_file.read_bytes())
            self.assertFalse((output / "records/S1/SHA256SUMS.txt").exists())
            with self.assertRaises(module.AssetPreparationError):
                module.prepare_public_asset_objects(
                    materialized_bundle=staging,
                    inventory_path=inventory,
                    bundle=bundle,
                    release_root=release,
                    output_dir=output,
                )


if __name__ == "__main__":
    unittest.main()
