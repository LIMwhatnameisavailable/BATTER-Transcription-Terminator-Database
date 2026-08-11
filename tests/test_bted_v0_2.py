"""Regression tests for the BTED v0.2.0 public-demo data contract."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_ROOT = REPO_ROOT / "data/public/v0.2.0"
RELEASE = json.loads((RELEASE_ROOT / "release_manifest.json").read_text(encoding="utf-8"))
CORE_HEADER = [
    "end_id", "source_id", "sample_id", "assay", "evidence_class",
    "author_endpoint_id", "published_reference_accession",
    "reference_assembly", "reference_name", "replicon_label",
    "biological_coordinate_1based", "bed_start_0based", "bed_end_0based",
    "strand", "signal_or_score", "author_category",
    "associated_gene_or_locus", "pmid", "doi", "source_table_or_file",
    "coordinate_interpretation", "original_row_reference", "qc_status", "note",
]


def tsv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class TestBtedV020Release(unittest.TestCase):
    def test_release_scope_is_frozen(self) -> None:
        summary = RELEASE["summary"]
        self.assertEqual(summary["source_count"], 22)
        self.assertEqual(summary["published_standardized_sources"], 21)
        self.assertEqual(summary["audit_only_sources"], 1)
        self.assertEqual(summary["published_record_count"], 28_399)
        self.assertEqual(summary["jbrowse_sources"], 21)

    def test_core_schema_and_bed_coordinate_contract(self) -> None:
        for source_id, entry in RELEASE["sources"].items():
            if entry["release_status"] == "audit_only":
                continue
            root = REPO_ROOT / entry["record_root"]
            rows = tsv_rows(root / "endpoints.tsv")
            with (root / "endpoints.tsv").open(encoding="utf-8", newline="") as handle:
                header = next(csv.reader(handle, delimiter="\t"))
            self.assertEqual(header, CORE_HEADER, source_id)
            beds = (root / "endpoints.bed").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), len(beds), source_id)
            for row, bed in zip(rows, beds):
                chrom, start, end, end_id, _score, strand = bed.split("\t")
                position = int(row["biological_coordinate_1based"])
                self.assertEqual(chrom, row["reference_name"], source_id)
                self.assertEqual(int(start), position - 1, source_id)
                self.assertEqual(int(end), position, source_id)
                self.assertEqual(end_id, row["end_id"], source_id)
                self.assertEqual(strand, row["strand"], source_id)

    def test_source_specific_fields_are_mapped_or_explicitly_withheld(self) -> None:
        for source_id, entry in RELEASE["sources"].items():
            fields = json.loads(
                (REPO_ROOT / entry["record_root"] / "fields.json").read_text(encoding="utf-8")
            )
            source_fields = fields.get("source_annotations", {}).get("fields", [])
            if entry["release_status"] == "audit_only":
                self.assertEqual(source_fields, [], source_id)
                continue
            self.assertTrue(source_fields, source_id)
            for field in source_fields:
                self.assertIn(
                    field["publication_status"],
                    {"published", "withheld_external_link_only"},
                    source_id,
                )
                self.assertIn(
                    field["evidence_role"],
                    {
                        "experimental_measurement",
                        "author_called_endpoint",
                        "author_annotation",
                        "prediction_annotation",
                        "curation_metadata",
                    },
                    source_id,
                )

    def test_companion_tables_keep_valid_end_id_foreign_keys(self) -> None:
        for source_id, entry in RELEASE["sources"].items():
            if entry["release_status"] == "audit_only":
                continue
            root = REPO_ROOT / entry["record_root"]
            end_ids = {row["end_id"] for row in tsv_rows(root / "endpoints.tsv")}
            for filename in ("source_annotations.tsv", "gene_associations.tsv", "condition_observations.tsv"):
                path = root / filename
                if not path.is_file():
                    continue
                for row in tsv_rows(path):
                    if row["end_id"]:
                        self.assertIn(row["end_id"], end_ids, f"{source_id}/{filename}")
                    else:
                        self.assertTrue(
                            row.get("link_status", "").startswith("unlinked"),
                            f"{source_id}/{filename}: blank end_id lacks an explicit unlinked status",
                        )

    def test_known_boundaries_are_enforced(self) -> None:
        s1_002 = RELEASE_ROOT / "records/BATTER_S1_002"
        self.assertFalse((s1_002 / "endpoints.tsv").exists())
        self.assertFalse((s1_002 / "endpoints.bed").exists())
        self.assertFalse(RELEASE["sources"]["BATTER_S1_002"]["has_jbrowse"])

        vnat = tsv_rows(RELEASE_ROOT / "records/BATTER_S1_005/endpoints.tsv")
        self.assertEqual({row["reference_name"] for row in vnat}, {"CP009977.1", "CP009978.1"})

        s1_020 = tsv_rows(RELEASE_ROOT / "records/BATTER_S1_020/endpoints.tsv")
        self.assertEqual({row["evidence_class"] for row in s1_020}, {"author_called_endpoint"})
        self.assertTrue(all("S2D" in row["source_table_or_file"] for row in s1_020))

    def test_static_catalog_groups_22_sources_into_20_assemblies(self) -> None:
        catalog = json.loads((REPO_ROOT / "site/data/catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["sources"]), 22)
        self.assertEqual(len(catalog["assemblies"]), 20)
        self.assertEqual(sum(bool(row["has_jbrowse"]) for row in catalog["sources"]), 21)
        self.assertEqual(len(list((REPO_ROOT / "site/records").glob("BATTER_S1_*.html"))), 22)
        self.assertEqual(len(list((REPO_ROOT / "site/assemblies").glob("GCF_*.html"))), 20)
        assemblies = {row["assembly"]: row for row in catalog["assemblies"]}
        self.assertEqual(
            assemblies["GCF_000739105.1"]["source_ids"],
            ["BATTER_S1_007", "BATTER_S1_013"],
        )
        self.assertEqual(assemblies["GCF_000739105.1"]["record_count"], 2_848)
        self.assertEqual(
            assemblies["GCF_005519465.1"]["source_ids"],
            ["BATTER_S1_015", "BATTER_S1_017"],
        )
        self.assertEqual(assemblies["GCF_005519465.1"]["record_count"], 2_567)
        self.assertEqual(
            sum("Open source track" in path.read_text(encoding="utf-8") for path in (REPO_ROOT / "site/records").glob("*.html")),
            21,
        )
        s1_005_page = (REPO_ROOT / "site/records/BATTER_S1_005.html").read_text(encoding="utf-8")
        self.assertIn("../downloads/records/BATTER_S1_005/endpoints.bed", s1_005_page)
        self.assertNotIn("Coordinate convention", s1_005_page)
        self.assertNotIn("fields.json", s1_005_page)
        self.assertNotIn("raw.githubusercontent.com", s1_005_page)
        s1_002_page = (REPO_ROOT / "site/records/BATTER_S1_002.html").read_text(encoding="utf-8")
        self.assertIn("audit_only", s1_002_page)
        self.assertNotIn("BATTER_S1_002/endpoints.bed", s1_002_page)

    def test_assembly_download_packages_preserve_source_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "assemblies"
            result = subprocess.run(
                [sys.executable, "scripts/build_assembly_downloads.py", "--output-dir", str(output)],
                cwd=REPO_ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            catalog = json.loads((output / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["assembly_count"], 20)
            self.assertEqual(len(list(output.glob("GCF_*/metadata.json"))), 20)
            self.assertEqual(len(list(output.glob("GCF_*/endpoints.bed"))), 19)
            self.assertEqual(
                sum(entry["record_count"] for entry in catalog["assemblies"].values()),
                28_399,
            )
            for assembly, expected_sources, expected_records in (
                ("GCF_000739105.1", ["BATTER_S1_007", "BATTER_S1_013"], 2_848),
                ("GCF_005519465.1", ["BATTER_S1_015", "BATTER_S1_017"], 2_567),
            ):
                metadata = json.loads((output / assembly / "metadata.json").read_text(encoding="utf-8"))
                self.assertEqual([row["source_id"] for row in metadata["sources"]], expected_sources)
                self.assertEqual(metadata["record_count"], expected_records)
                bed_rows = (output / assembly / "endpoints.bed").read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(bed_rows), expected_records)
                for source_id in expected_sources:
                    self.assertTrue(any(source_id in row.split("\t")[3] for row in bed_rows))

    def test_tracked_jbrowse_overlays_cover_sources_and_shared_assemblies(self) -> None:
        root = RELEASE_ROOT / "jbrowse-config-overlays"
        catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["sources"]), 21)
        self.assertEqual(
            set(catalog["assemblies"]),
            {"GCF_000739105.1", "GCF_005519465.1"},
        )
        for source_id, entry in catalog["sources"].items():
            config = json.loads((root / entry["config"]).read_text(encoding="utf-8"))
            views = config.get("defaultSession", {}).get("views", [])
            self.assertEqual(len(views), 1, source_id)
            self.assertEqual(views[0]["type"], "LinearGenomeView", source_id)
        for assembly, entry in catalog["assemblies"].items():
            config = json.loads((root / entry["config"]).read_text(encoding="utf-8"))
            self.assertEqual(len(config["defaultSession"]["views"][0]["tracks"]), 3, assembly)

    def test_release_and_site_validators_pass(self) -> None:
        for command in (
            [sys.executable, "scripts/validate_bted_v0_2.py"],
            [sys.executable, "scripts/validate-site.py", "site"],
        ):
            result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
