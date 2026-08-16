"""Tests for the accession lookup and same-origin Range delivery prototype."""

from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path

from scripts.run_accession_range_demo import (
    build_assembly_payload,
    build_jbrowse_config,
    parse_byte_range,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOTYPE_ROOT = REPO_ROOT / "prototype/accession-range"
REGISTRY = json.loads((PROTOTYPE_ROOT / "registry.json").read_text(encoding="utf-8"))


class TestAccessionRangePrototype(unittest.TestCase):
    def test_d1_schema_and_seed_are_consistent(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.executescript((PROTOTYPE_ROOT / "schema.sql").read_text(encoding="utf-8"))
        connection.executescript((PROTOTYPE_ROOT / "seed.sql").read_text(encoding="utf-8"))
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM assemblies").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0], 6)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM tracks").fetchone()[0], 2)
        self.assertEqual(
            connection.execute("SELECT SUM(record_count) FROM tracks").fetchone()[0],
            2_848,
        )
        connection.close()

    def test_registry_uses_one_reference_and_two_independent_tracks(self) -> None:
        assembly = REGISTRY["assemblies"]["GCF_000739105.1"]
        self.assertEqual(assembly["source_ids"], ["BATTER_S1_007", "BATTER_S1_013"])
        self.assertEqual(assembly["record_count"], 2_848)
        self.assertEqual(len(assembly["reference_assets"]), 4)
        self.assertEqual(len(assembly["tracks"]), 2)
        self.assertEqual(
            [track["publication_year"] for track in assembly["tracks"]],
            [2019, 2020],
        )
        self.assertTrue(all(track["record_url"].startswith("records/") for track in assembly["tracks"]))
        self.assertEqual(
            [track["raw_data_accession"] for track in assembly["tracks"]],
            ["PRJEB31507", "PRJEB31507"],
        )
        self.assertTrue(all(track["publication_url"].startswith("https://pubmed.ncbi.nlm.nih.gov/") for track in assembly["tracks"]))
        self.assertTrue(all(track["interpretation_note"] and track["interpretation_note_zh"] for track in assembly["tracks"]))
        self.assertTrue(all(
            len(REGISTRY["assets"][asset_key].get("equivalent_source_assets", [])) == 2
            for asset_key in assembly["reference_assets"].values()
        ))
        self.assertEqual(
            {track["evidence_class"] for track in assembly["tracks"]},
            {"author_called_endpoint"},
        )
        self.assertTrue(all(len(asset["sha256"]) == 64 for asset in REGISTRY["assets"].values()))

    def test_payload_and_jbrowse_config_use_only_same_origin_asset_keys(self) -> None:
        base = "http://127.0.0.1:8016"
        payload = build_assembly_payload(REGISTRY, "GCF_000739105.1", base)
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["record_count"], 2_848)
        self.assertEqual(len(payload["assets"]), 6)
        self.assertTrue(all(asset["range_url"].startswith(f"{base}/api/remote-data/") for asset in payload["assets"]))
        config = build_jbrowse_config(payload, base)
        self.assertEqual(len(config["assemblies"]), 1)
        self.assertEqual(len(config["tracks"]), 3)
        self.assertEqual(
            [track["metadata"].get("source_id") for track in config["tracks"][1:]],
            ["BATTER_S1_007", "BATTER_S1_013"],
        )
        serialized = json.dumps(config)
        self.assertNotIn("huggingface.co", serialized)
        self.assertNotIn("../assets/", serialized)

    def test_byte_range_parser(self) -> None:
        self.assertIsNone(parse_byte_range(None, 1_000))
        self.assertEqual(parse_byte_range("bytes=0-127", 1_000), (0, 127))
        self.assertEqual(parse_byte_range("bytes=900-", 1_000), (900, 999))
        self.assertEqual(parse_byte_range("bytes=-100", 1_000), (900, 999))
        self.assertEqual(parse_byte_range("bytes=950-2000", 1_000), (950, 999))
        for invalid in ("bytes=", "items=0-10", "bytes=1000-1001", "bytes=20-10"):
            with self.assertRaises(ValueError, msg=invalid):
                parse_byte_range(invalid, 1_000)

    def test_site_exposes_a_user_facing_bilingual_search(self) -> None:
        page = (REPO_ROOT / "site/accession-range-demo.html").read_text(encoding="utf-8")
        assembly = (REPO_ROOT / "site/assemblies/GCF_000739105.1.html").read_text(encoding="utf-8")
        genomes = (REPO_ROOT / "site/sources.html").read_text(encoding="utf-8")
        self.assertIn("Find transcript 3′-end data", page)
        self.assertIn("查找转录本 3′ 端数据", page)
        self.assertIn('data-language-choice="en"', page)
        self.assertIn('data-language-choice="zh"', page)
        self.assertIn("What does one record mean?", page)
        self.assertIn("一条记录代表什么？", page)
        self.assertIn("Studies available for this genome", page)
        self.assertIn("What do these records represent?", page)
        self.assertNotIn("D1-compatible registry", page)
        self.assertNotIn("Test 128-byte Range", page)
        self.assertIn("accession-range-demo.js", page)
        self.assertIn("Find this genome by accession", assembly)
        self.assertIn("Quick search", genomes)
        self.assertNotIn("Architecture prototype", assembly)
        self.assertNotIn("API pilot", genomes)
        self.assertNotIn("functionally validated terminator", page.lower())


if __name__ == "__main__":
    unittest.main()
