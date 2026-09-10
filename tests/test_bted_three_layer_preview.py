import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = REPO_ROOT / "site"
PILOT_BED = SITE_ROOT / "data/pilots/BATTER_S1_003_batter_tpe_regional_pilot.bed"
PILOT_PROVENANCE = SITE_ROOT / "data/pilots/BATTER_S1_003_batter_tpe_regional_pilot.provenance.json"
WORKER = REPO_ROOT / "prototype/accession-range/src/worker.js"


class ThreeLayerPreviewTests(unittest.TestCase):
    def test_preview_page_uses_natural_names_and_keeps_evidence_boundaries(self):
        page = (SITE_ROOT / "evidence-layers-preview.html").read_text(encoding="utf-8")
        self.assertIn("Explore the evidence behind this genome", page)
        self.assertIn("Measured 3′-end signal", page)
        self.assertIn("Curated endpoint records", page)
        self.assertIn("Training augmentation examples", page)
        self.assertIn("Model-predicted regions", page)
        self.assertIn("Experimental evidence", page)
        self.assertIn("Model context", page)
        self.assertIn("Computational output", page)
        self.assertEqual(page.count('<article class="evidence-card '), 4)
        self.assertEqual(page.count('class="technical-details"'), 4)
        self.assertIn("Unavailable", page)
        self.assertIn("no coordinate-level instances", page)
        self.assertIn("non-experimental", page)
        self.assertIn("regional compatibility pilot", page)
        self.assertIn("experimental=false", page)
        self.assertIn("Compare, don’t conflate", page)
        self.assertIn("<svg", page)
        for legacy_copy in ("A / B / D", "A/B/D", "A → B", "D stays separate", "C is not included", "Letters describe provenance"):
            self.assertNotIn(legacy_copy, page)
        self.assertNotRegex(page, r">[ABCD]</(?:div|span)")
        self.assertIn("browser.html?config=", page)
        self.assertIn("pilot%3Dthree-layer", page)
        self.assertIn("BATTER_S1_003_batter_tpe_regional_pilot.bed", page)
        self.assertIn("BATTER_S1_003_batter_tpe_regional_pilot.provenance.json", page)
        self.assertIn("Explore in genome browser", page)
        self.assertIn("not validation probabilities", page)

    def test_model_pilot_bed_is_realistic_and_genome_scoped(self):
        rows = [line.split("\t") for line in PILOT_BED.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(rows), 11)
        self.assertEqual(sum(row[5] == "+" for row in rows), 7)
        self.assertEqual(sum(row[5] == "-" for row in rows), 4)
        for row in rows:
            self.assertEqual(len(row), 7)
            self.assertEqual(row[0], "NC_000964.3")
            start, end = int(row[1]), int(row[2])
            self.assertLess(start, end)
            self.assertGreaterEqual(start, 0)
            self.assertLessEqual(end, 4215606)
            self.assertTrue(row[3].startswith("BTED_S1_003_BATTER_TPE_REGIONAL_"))
            self.assertIn(row[5], {"+", "-"})
            float(row[4])
            float(row[6])

    def test_provenance_separates_prediction_from_experiment(self):
        provenance = json.loads(PILOT_PROVENANCE.read_text(encoding="utf-8"))
        self.assertEqual(provenance["dataset_id"], "BATTER_S1_003")
        self.assertEqual(provenance["evidence_class"], "model_prediction")
        self.assertFalse(provenance["experimental"])
        self.assertEqual(provenance["prediction_count"], 11)
        self.assertEqual(provenance["official_commit"], "9133d2d36b60c238a1e36760a296eff9f001fb72")
        self.assertIn("compatibility", provenance["compatibility_sanity_check"]["interpretation"])
        self.assertIn("not be merged into the experimental endpoint table", " ".join(provenance["limitations"]))

    def test_worker_adds_pilot_after_experimental_tracks(self):
        worker = WORKER.read_text(encoding="utf-8")
        self.assertIn('evidence_class: "model_prediction"', worker)
        self.assertIn("BATTER_S1_003_batter_tpe_regional_pilot.bed", worker)
        self.assertIn('searchParams.get("pilot") === "three-layer"', worker)
        self.assertIn('accession === "GCF_000009045.1"', worker)
        self.assertLess(worker.index("configTracks.push(...tracksConfig)"), worker.index("const pilotPath"))
        self.assertIn("showLabels: false", worker)
        self.assertNotIn("prediction_only", worker)

    def test_s1_002_remains_without_browser_or_preview_link(self):
        page = (SITE_ROOT / "records/BATTER_S1_002.html").read_text(encoding="utf-8")
        self.assertNotIn("browser.html?config=", page)
        self.assertNotIn("evidence-layers-preview.html", page)


if __name__ == "__main__":
    unittest.main()
