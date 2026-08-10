"""Regression tests for the BTED v0.1 local-snapshot ingestion release.

Run from repository root:
    python -m unittest -v tests/test_bted_ingestion.py
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_PATH = REPO_ROOT / "data/public/release_manifest.v0.1-local-snapshot.json"
STATUS_PATH = REPO_ROOT / "data/registry/batter_s1_publication_status.tsv"


class TestBtedIngestionRelease(unittest.TestCase):
    def setUp(self) -> None:
        self.release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))
        with STATUS_PATH.open(encoding="utf-8", newline="") as handle:
            self.status_rows = list(csv.DictReader(handle, delimiter="\t"))

    def test_release_has_all_batter_s1_sources(self) -> None:
        expected = [f"BATTER_S1_{number:03d}" for number in range(1, 23)]
        self.assertEqual(list(self.release["sources"]), expected)
        self.assertEqual([row["source_id"] for row in self.status_rows], expected)

    def test_release_summary_and_status_counts(self) -> None:
        summary = self.release["summary"]
        self.assertEqual(summary["source_count"], 22)
        self.assertEqual(summary["published_standardized_sources"], 21)
        self.assertEqual(summary["audit_only_sources"], 1)
        self.assertEqual(summary["published_record_count"], 28_399)
        self.assertEqual(
            {row["source_id"] for row in self.status_rows if row["release_status"] == "audit_only"},
            {"BATTER_S1_002"},
        )

    def test_public_files_obey_evidence_boundary(self) -> None:
        forbidden = {"author_integrated_mixed_evidence", "prediction_only"}
        for source_id, entry in self.release["sources"].items():
            if entry["release_status"] != "published_standardized":
                self.assertFalse(entry["public_asset"], source_id)
                continue
            path = REPO_ROOT / entry["public_asset"]
            self.assertTrue(path.is_file(), path)
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(rows), entry["record_count"], source_id)
            self.assertTrue(all(row["evidence_class"] not in forbidden for row in rows), source_id)

    def test_release_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_bted_release.py"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
