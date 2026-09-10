"""Static contract checks for the BTED v0.3 database skeleton.

These tests deliberately do not require PostgreSQL.  They check that the SQL
and v0.3 documents cannot silently narrow the v0.2 release boundary before a
real importer/database migration exists.
"""

from __future__ import annotations

import csv
import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "backend/database/schema.sql"
ARCHITECTURE_PATH = REPO_ROOT / "docs/v0.3/architecture.md"
DATABASE_DOC_PATH = REPO_ROOT / "docs/v0.3/database-schema.md"
API_DOC_PATH = REPO_ROOT / "docs/v0.3/api-contract.md"
BROWSER_UI_PATH = REPO_ROOT / "docs/v0.3/browser-ui-contract.md"
RELEASE_PATH = REPO_ROOT / "data/public/v0.2.0/release_manifest.json"
REGISTRY_PATH = REPO_ROOT / "data/registry/batter_s1_source_registry.tsv"
S1_007_ENDPOINTS = REPO_ROOT / "data/public/v0.2.0/records/BATTER_S1_007/endpoints.tsv"
S1_002_MANIFEST = REPO_ROOT / "data/public/v0.2.0/records/BATTER_S1_002/manifest.json"


V02_ENDPOINT_COLUMNS = [
    "end_id",
    "source_id",
    "sample_id",
    "assay",
    "evidence_class",
    "author_endpoint_id",
    "published_reference_accession",
    "reference_assembly",
    "reference_name",
    "replicon_label",
    "biological_coordinate_1based",
    "bed_start_0based",
    "bed_end_0based",
    "strand",
    "signal_or_score",
    "author_category",
    "associated_gene_or_locus",
    "pmid",
    "doi",
    "source_table_or_file",
    "coordinate_interpretation",
    "original_row_reference",
    "qc_status",
    "note",
]


class TestBtedV03Schema(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = SCHEMA_PATH.read_text(encoding="utf-8")
        cls.database_doc = DATABASE_DOC_PATH.read_text(encoding="utf-8")
        cls.api_doc = API_DOC_PATH.read_text(encoding="utf-8")
        cls.browser_ui = BROWSER_UI_PATH.read_text(encoding="utf-8")
        cls.architecture = ARCHITECTURE_PATH.read_text(encoding="utf-8")

    def test_required_tables_and_jsonb_are_declared(self) -> None:
        required_tables = {
            "release_versions",
            "import_runs",
            "publications",
            "assemblies",
            "contigs",
            "sources",
            "source_accessions",
            "samples",
            "endpoints",
            "source_annotations",
            "genes",
            "endpoint_gene_context",
            "assets",
        }
        for table in required_tables:
            self.assertRegex(
                self.schema,
                rf"CREATE TABLE\s+{table}\s*\(",
                msg=f"missing table {table}",
            )
        self.assertIn("annotation_json JSONB NOT NULL", self.schema)
        self.assertIn("provenance_json JSONB", self.schema)

    def test_current_release_must_be_published(self) -> None:
        self.assertIn("release_versions_current_status_ck", self.schema)
        self.assertIn("CHECK (NOT is_current OR status = 'published')", self.schema)
        self.assertIn("is_current = TRUE", self.database_doc)
        self.assertIn("`is_current = TRUE` 时 `status` 必须为 `published`", self.database_doc)
        self.assertNotIn("S1_001–005", self.database_doc)
        self.assertIn("S1_001、S1_003–S1_005", self.database_doc)

    def test_endpoints_keep_all_v02_columns(self) -> None:
        with S1_007_ENDPOINTS.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle, delimiter="\t"))
        self.assertEqual(header, V02_ENDPOINT_COLUMNS)

        match = re.search(
            r"CREATE TABLE endpoints \((.*?)\n\);\n\nCREATE INDEX",
            self.schema,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match, "could not isolate endpoints table")
        endpoint_ddl = match.group(1)
        for column in V02_ENDPOINT_COLUMNS:
            self.assertRegex(
                endpoint_ddl,
                rf"(?m)^\s+{re.escape(column)}\s+",
                msg=f"24-column endpoint field missing: {column}",
            )
        self.assertIn("endpoints_release_end_uq", endpoint_ddl)
        self.assertIn("source_table_or_file", endpoint_ddl)
        self.assertIn("original_row_reference", endpoint_ddl)
        self.assertIn("coordinate_interpretation", endpoint_ddl)
        self.assertIn("signal_or_score TEXT", endpoint_ddl)

    def test_coordinate_and_contig_semantics_are_explicit(self) -> None:
        with S1_007_ENDPOINTS.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(rows), 1640)
        for row in rows:
            position = int(row["biological_coordinate_1based"])
            self.assertEqual(int(row["bed_start_0based"]), position - 1)
            self.assertEqual(int(row["bed_end_0based"]), position)
            self.assertIn(row["strand"], {"+", "-"})
            self.assertNotIn(
                row["evidence_class"],
                {"author_integrated_mixed_evidence", "prediction_only"},
            )
        for token in ("contig_id", "sample_pk", "release_version"):
            self.assertIn(token, self.schema)
        self.assertIn("bed_start_0based = biological_coordinate_1based - 1", self.schema)
        self.assertIn("bed_end_0based = biological_coordinate_1based", self.schema)

    def test_release_and_audit_only_boundaries_match_v02(self) -> None:
        release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(release["summary"]["source_count"], 22)
        self.assertEqual(release["summary"]["published_standardized_sources"], 21)
        self.assertEqual(release["summary"]["audit_only_sources"], 1)
        self.assertEqual(release["summary"]["published_record_count"], 28_399)
        audit = release["sources"]["BATTER_S1_002"]
        self.assertEqual(audit["release_status"], "audit_only")
        self.assertEqual(audit["record_count"], 0)
        self.assertFalse(audit["has_jbrowse"])
        self.assertNotIn("endpoints.tsv", {file["path"] for file in audit["files"]})

        s1_002 = json.loads(S1_002_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(s1_002["release_status"], "audit_only")
        self.assertEqual(s1_002["used_for_batter_augmentation"], "FALSE")
        self.assertIn("audit_only", self.database_doc)
        self.assertIn("S1_002", self.api_doc)

    def test_augmentation_is_source_level_19_to_3(self) -> None:
        with REGISTRY_PATH.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(rows), 22)
        eligible = [row for row in rows if row["used_for_batter_augmentation"] == "TRUE"]
        ineligible = [row for row in rows if row["used_for_batter_augmentation"] == "FALSE"]
        self.assertEqual(len(eligible), 19)
        self.assertEqual(len(ineligible), 3)
        self.assertIn("used_for_batter_augmentation BOOLEAN NOT NULL", self.schema)
        self.assertNotIn("augmentation_eligible BOOLEAN", self.schema)
        self.assertIn("来源级", self.database_doc)
        self.assertIn("19", self.api_doc)
        self.assertIn("training_claim", self.api_doc)
        self.assertIn("gene clusters", self.api_doc)
        self.assertIn("Rfam", self.api_doc)

    def test_public_endpoint_evidence_check_rejects_prediction_and_mixed(self) -> None:
        evidence_check = re.search(
            r"CONSTRAINT endpoints_evidence_ck\s+CHECK\s*\((.*?)CONSTRAINT endpoints_coordinate_ck",
            self.schema,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(evidence_check, "endpoint evidence CHECK missing")
        allowed_block = evidence_check.group(1)
        for allowed in (
            "observed_signal",
            "called_endpoint",
            "author_called_endpoint",
            "curated_record",
        ):
            self.assertIn(allowed, allowed_block)
        for forbidden in ("author_integrated_mixed_evidence", "prediction_only"):
            self.assertNotIn(forbidden, allowed_block)
            self.assertIn(forbidden, self.schema)
        self.assertIn("prediction_annotation", self.schema)
        self.assertIn("prediction_annotation", self.database_doc)
        self.assertIn("prediction_only", self.api_doc)

    def test_stack_and_same_origin_range_contract_are_documented(self) -> None:
        for component in ("Vercel", "Next.js", "Render", "FastAPI", "Neon", "PostgreSQL", "Hugging Face"):
            self.assertIn(component, self.architecture)
        self.assertIn("/api/v1/assets/{asset_id}", self.architecture)
        self.assertIn("canonical release", self.architecture)
        self.assertIn("206 Partial Content", self.api_doc)
        self.assertIn("Content-Range", self.api_doc)
        self.assertIn("Range", self.api_doc)

    def test_review_fixes_for_details_pagination_and_range(self) -> None:
        self.assertIn("最大 `100`", self.api_doc)
        self.assertNotIn("最大 `1000`", self.api_doc)
        for route in (
            "/api/v1/sources/{source_id}",
            "/api/v1/assemblies/{assembly_id}",
            "/api/v1/endpoints/{end_id}",
            "/api/v1/genes/{gene_id}",
        ):
            self.assertIn(route, self.api_doc)
        for token in ("publication", "raw_accessions", "provenance", "S1_002", "record_count = 0"):
            self.assertIn(token, self.api_doc)
        self.assertIn("完整 SHA-256 只在资产登记/导入阶段", self.api_doc)
        self.assertIn("每次 partial request 不重算整文件 checksum", self.api_doc)

    def test_review_fixes_for_relational_boundaries(self) -> None:
        endpoint = re.search(
            r"CREATE TABLE endpoints \((.*?)\n\);\n\nCREATE INDEX",
            self.schema,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(endpoint)
        endpoint_ddl = endpoint.group(1)
        self.assertIn("sample_pk BIGINT NOT NULL", endpoint_ddl)
        self.assertIn("endpoints_sample_context_fk", endpoint_ddl)
        self.assertIn("REFERENCES samples (source_pk, sample_id, sample_pk)", endpoint_ddl)
        self.assertIn("sources_public_state_ck", self.schema)
        self.assertIn("release_status IN ('to_review', 'blocked')", self.schema)
        self.assertIn("import_runs_input_manifest_idx", self.schema)
        self.assertNotIn("import_runs_unique_input_uq", self.schema)
        self.assertIn("journal TEXT", self.schema)
        self.assertIn("strain TEXT", self.schema)
        self.assertIn("source_record_id TEXT NOT NULL", self.schema)
        self.assertIn("ordinal INTEGER NOT NULL", self.schema)
        self.assertIn(
            "UNIQUE (release_version, end_id, annotation_kind, source_record_id, ordinal)",
            self.schema,
        )

    def test_genes_are_release_and_annotation_asset_isolated(self) -> None:
        genes = re.search(
            r"CREATE TABLE genes \((.*?)\n\);\n\nCREATE INDEX",
            self.schema,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(genes)
        genes_ddl = genes.group(1)
        self.assertIn("release_version TEXT NOT NULL", genes_ddl)
        self.assertIn("annotation_asset_id TEXT NOT NULL", genes_ddl)
        self.assertIn("annotation_sha256 TEXT NOT NULL", genes_ddl)
        self.assertIn("genes_contig_assembly_fk", genes_ddl)
        self.assertIn("genes_release_pk_uq", genes_ddl)
        self.assertIn("genes_annotation_asset_fk", self.schema)
        self.assertIn("endpoint_gene_context_gene_release_fk", self.schema)
        self.assertIn("v_contig_length", self.schema)
        self.assertIn("gene end", self.schema)
        self.assertIn("browser-ui-contract.md", self.architecture)
        for token in (
            "Search by accession",
            "Data augmentation",
            "19 个来源",
            "色块",
            "›",
            "‹",
            "棒棒糖",
            "▲",
            "▼",
            "raw plus/minus BigWig",
            "linear",
            "Original NCBI GFF3",
            "BTED subset GFF3",
        ):
            self.assertIn(token, self.browser_ui)


if __name__ == "__main__":
    unittest.main()
