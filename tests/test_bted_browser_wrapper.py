"""Static contract checks for the BTED user-facing JBrowse wrapper."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = REPO_ROOT / "site"


class TestBtedBrowserWrapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wrapper = (SITE_ROOT / "browser.html").read_text(encoding="utf-8")
        cls.script = (SITE_ROOT / "assets/browser-wrapper.js").read_text(encoding="utf-8")
        cls.assemblies = json.loads((SITE_ROOT / "data/assemblies.json").read_text(encoding="utf-8"))

    def test_wrapper_is_outside_unmodified_jbrowse_bundle(self) -> None:
        self.assertIn('data-browser-frame', self.wrapper)
        self.assertIn('src="assets/browser-wrapper.js', self.wrapper)
        self.assertIn('title="BTED interactive genome browser"', self.wrapper)
        self.assertIn('jbrowse/index.html?', self.script)
        self.assertIn('data-browser-studies', self.wrapper)
        self.assertIn('config', self.script)
        self.assertIn('loc', self.script)
        self.assertIn('session', self.script)

    def test_wrapper_exposes_source_links_and_source_switch(self) -> None:
        for token in (
            "Publication",
            "PubMed",
            "DOI",
            "Raw data",
            "Download BED",
            "Dataset details",
            "Source track",
            "All source tracks",
        ):
            self.assertIn(token, self.wrapper + self.script)
        self.assertIn("source_id", self.script)
        self.assertIn("Sources sharing an assembly remain independent", self.script)
        self.assertIn("renderStudyLinks", self.script)
        self.assertIn("window.location.origin", self.script)
        self.assertIn(r"\/api\/assemblies\/", self.script)
        self.assertIn("jbrowse-config", self.script)

    def test_static_metadata_has_links_for_single_and_shared_assemblies(self) -> None:
        assemblies = self.assemblies["assemblies"]
        checks = {
            "GCF_000005845.1": {"BATTER_S1_001"},
            "GCF_000739105.1": {"BATTER_S1_007", "BATTER_S1_013"},
        }
        for accession, source_ids in checks.items():
            tracks = {track["source_id"]: track for track in assemblies[accession]["tracks"]}
            self.assertEqual(set(tracks), source_ids)
            for source_id in source_ids:
                track = tracks[source_id]
                self.assertRegex(track["publication_url"], r"pubmed\.ncbi\.nlm\.nih\.gov/\d+")
                self.assertRegex(track["doi_url"], r"https://doi\.org/.+")
                self.assertTrue(track["raw_data_accession"])
                self.assertTrue(track["raw_data_url"])
                self.assertIn(source_id, track["bed_url"])
                self.assertEqual(track["record_url"], f"records/{source_id}.html")

    def test_generated_public_links_use_wrapper_and_audit_source_stays_out(self) -> None:
        html_pages = list((SITE_ROOT / "records").glob("BATTER_S1_*.html")) + list((SITE_ROOT / "assemblies").glob("GCF_*.html"))
        wrapper_links = sum("browser.html?config=" in page.read_text(encoding="utf-8") for page in html_pages)
        self.assertEqual(wrapper_links, 40)  # 21 source pages + 19 published assembly pages
        audit_page = (SITE_ROOT / "records/BATTER_S1_002.html").read_text(encoding="utf-8")
        self.assertNotIn("browser.html?config=", audit_page)
        self.assertNotIn("BATTER_S1_002--endpoints-bed", self.script)

    def test_accession_search_uses_wrapper(self) -> None:
        script = (SITE_ROOT / "assets/accession-range-demo.js").read_text(encoding="utf-8")
        self.assertIn("browser.html?config=", script)
        self.assertNotIn("/jbrowse/index.html?config=", script)


if __name__ == "__main__":
    unittest.main()
