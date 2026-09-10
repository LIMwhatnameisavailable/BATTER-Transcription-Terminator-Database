"""Focused tests for merging the tracked JBrowse asset inventory."""

from __future__ import annotations

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from backend.importer.materialize import materialize_release
from backend.importer.postgres import verify_bundle


REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_ROOT = REPO_ROOT / "data/public/v0.2.0"
INVENTORY = REPO_ROOT / "data/registry/jbrowse_assets.v0.2.0.tsv"


class TestJBrowseInventoryMaterialization(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "bundle"
        cls.result = materialize_release(
            RELEASE_ROOT,
            repo_root=REPO_ROOT,
            output_dir=cls.output,
            asset_origin_base="https://example.test/assets",
            generated_at_utc="2026-08-21T00:00:00Z",
            jbrowse_asset_inventory=INVENTORY,
        )
        with (cls.output / "assets.jsonl").open(encoding="utf-8") as handle:
            cls.assets = [json.loads(line) for line in handle if line.strip()]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_inventory_merges_to_211_assets_with_expected_scopes(self) -> None:
        self.assertEqual(self.result.table_counts["assets"], 211)
        self.assertEqual(
            Counter(row["asset_kind"] for row in self.assets),
            Counter(
                {
                    "metadata": 84,
                    "checksum": 22,
                    "bed": 21,
                    "fasta": 19,
                    "fai": 19,
                    "gff3": 19,
                    "tbi": 19,
                    "bigwig": 8,
                }
            ),
        )
        assembly_assets = [row for row in self.assets if row["assembly_id_ref"]]
        self.assertEqual(len(assembly_assets), 76)
        self.assertTrue(all(row["source_id_ref"] is None for row in assembly_assets))
        self.assertEqual(len({row["assembly_id_ref"] for row in assembly_assets}), 19)

    def test_canonical_beds_are_replaced_and_audit_source_has_no_browser_asset(self) -> None:
        beds = [row for row in self.assets if row["asset_kind"] == "bed"]
        self.assertEqual(len(beds), 21)
        self.assertTrue(
            all(row["asset_id"].startswith("v0.2.0--source-BATTER_S1_") for row in beds)
        )
        self.assertEqual(
            {row["logical_path"] for row in beds},
            {f"records/BATTER_S1_{number:03d}/endpoints.bed" for number in range(1, 23) if number != 2},
        )
        audit_assets = [row for row in self.assets if row["source_id_ref"] == "BATTER_S1_002"]
        self.assertTrue(audit_assets)
        self.assertTrue(
            {row["asset_kind"] for row in audit_assets} <= {"metadata", "checksum"}
        )

    def test_inventory_paths_origin_and_public_state(self) -> None:
        inventory_assets = [
            row
            for row in self.assets
            if row["asset_id"].startswith("v0.2.0--assembly-")
            or row["asset_id"].startswith("v0.2.0--source-")
        ]
        self.assertEqual(len(inventory_assets), 105)
        for row in self.assets:
            self.assertEqual(
                row["origin_url"],
                f"https://example.test/assets/{row['logical_path']}",
            )
            self.assertFalse(row["supports_range"])
            if row["redistribution_status"] == "external_link_only":
                self.assertFalse(row["is_public"])
        self.assertEqual(
            {row["source_id_ref"] for row in inventory_assets if row["asset_kind"] == "bigwig"},
            {"BATTER_S1_001", "BATTER_S1_003", "BATTER_S1_004", "BATTER_S1_005"},
        )

    def test_manifest_inventory_provenance_and_bundle_verification(self) -> None:
        provenance = self.result.manifest["jbrowse_asset_inventory"]
        self.assertEqual(provenance["path"], "data/registry/jbrowse_assets.v0.2.0.tsv")
        self.assertEqual(provenance["row_count"], 105)
        self.assertEqual(provenance["canonical_bed_replacements"], 21)
        self.assertEqual(provenance["reference_asset_count"], 76)
        self.assertEqual(provenance["raw_signal_asset_count"], 8)
        verification = verify_bundle(self.output)
        self.assertEqual(verification.table_counts["assets"], 211)


if __name__ == "__main__":
    unittest.main()
