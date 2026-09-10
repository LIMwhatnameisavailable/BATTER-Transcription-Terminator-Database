"""Focused checks for the tracked v0.3 JBrowse asset inventory."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import unittest
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE = REPO_ROOT.parent / "bted-v0.2" / "dist" / "BTED-v0.2.0-jbrowse"
TSV = REPO_ROOT / "data/registry/jbrowse_assets.v0.2.0.tsv"
PROVENANCE = REPO_ROOT / "data/registry/jbrowse_assets.v0.2.0.json"


def _load_builder():
    path = REPO_ROOT / "scripts/build_v03_jbrowse_asset_inventory.py"
    spec = importlib.util.spec_from_file_location("bted_v03_jbrowse_inventory", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@unittest.skipUnless(BUNDLE.is_dir(), "the frozen v0.2 JBrowse bundle is not available")
class TestJBrowseAssetInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = _load_builder()
        cls.rows, cls.provenance = cls.builder.build_inventory(bundle=BUNDLE)

    def test_fixed_105_row_split(self) -> None:
        self.assertEqual(len(self.rows), 105)
        kinds = Counter(row["asset_kind"] for row in self.rows)
        self.assertEqual(kinds["fasta"], 19)
        self.assertEqual(kinds["fai"], 19)
        self.assertEqual(kinds["gff3"], 19)
        self.assertEqual(kinds["tbi"], 19)
        self.assertEqual(kinds["bed"], 21)
        self.assertEqual(kinds["bigwig"], 8)

    def test_tracked_output_and_required_columns(self) -> None:
        with TSV.open(encoding="utf-8", newline="") as handle:
            tracked = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(tracked), 105)
        self.assertEqual(set(tracked[0]), set(self.builder.TSV_COLUMNS))
        self.assertEqual(tracked, sorted(tracked, key=lambda row: row["asset_id"]))
        metadata = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        self.assertEqual(metadata["row_count"], 105)
        self.assertEqual(metadata["counts"]["assembly_assets"], 76)
        self.assertEqual(metadata["counts"]["canonical_endpoint_assets"], 21)
        self.assertEqual(metadata["counts"]["raw_bigwig_assets"], 8)

    def test_every_object_has_declared_size_and_checksum(self) -> None:
        for row in self.rows:
            if row["bundle_path"]:
                path = BUNDLE / row["bundle_path"]
            else:
                path = REPO_ROOT / "data/public/v0.2.0" / row["canonical_path"]
            self.assertTrue(path.is_file(), row["object_path"])
            self.assertEqual(int(row["byte_size"]), path.stat().st_size)
            self.assertEqual(row["sha256"], _sha256(path))
            self.assertEqual(row["supports_range"], "false")
            self.assertEqual(
                row["is_public"],
                "true" if row["redistribution_status"] == "verified_redistributable" else "false",
            )

    def test_shared_reference_is_deduplicated_and_excluded_assets_stay_out(self) -> None:
        assembly_rows = [row for row in self.rows if row["asset_kind"] in {"fasta", "fai", "gff3", "tbi"}]
        for accession, representative in (
            ("GCF_000739105.1", "BATTER_S1_007"),
            ("GCF_005519465.1", "BATTER_S1_015"),
        ):
            shared = [row for row in assembly_rows if row["assembly_accession"] == accession]
            self.assertEqual(len(shared), 4)
            self.assertEqual({row["source_id"] for row in shared}, {representative})
        self.assertIn("BATTER_S1_013", {row["source_id"] for row in self.rows})
        self.assertIn("BATTER_S1_017", {row["source_id"] for row in self.rows})
        all_paths = "\n".join(row["bundle_path"] + row["canonical_path"] for row in self.rows)
        self.assertNotIn("BATTER_S1_002", all_paths)
        self.assertNotIn("candidate", all_paths.lower())
        self.assertNotIn("signed-log", all_paths.lower())
        self.assertNotIn("normalized", all_paths.lower())
        self.assertNotIn(".config.json", all_paths.lower())
        self.assertTrue(self.provenance["deduplicated_shared_references"])

    def test_rebuilding_is_deterministic(self) -> None:
        rows_again, provenance_again = self.builder.build_inventory(bundle=BUNDLE)
        self.assertEqual(rows_again, self.rows)
        self.assertEqual(provenance_again, self.provenance)


if __name__ == "__main__":
    unittest.main()
