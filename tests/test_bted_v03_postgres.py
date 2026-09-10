"""Offline tests for the BTED v0.3 PostgreSQL writer.

The fake connection records SQL and transaction state but never executes SQL.
The real release is materialized once so batching and natural-key closure are
tested against the 28,399/81,477-row bundle without printing those rows.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from backend.importer.materialize import materialize_release
from backend.importer.postgres import (
    BundleVerification,
    PostgresWriterError,
    _preflight,
    _iter_jsonl,
    load_bundle,
    promote_bundle,
    verify_bundle,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_ROOT = REPO_ROOT / "data/public/v0.2.0"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_minimal_bundle(
    root: Path,
    *,
    publication_rows: list[dict[str, Any]] | None = None,
    asset_rows: list[dict[str, Any]] | None = None,
) -> Path:
    """Create a tiny structurally valid bundle for local failure tests."""

    root.mkdir(parents=True, exist_ok=True)
    rows: dict[str, list[dict[str, Any]]] = {
        table: []
        for table in (
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
        )
    }
    rows["release_versions"] = [{
        "release_version": "v0.2.0",
        "release_date": "2026-08-10",
        "canonical_manifest_path": "release_manifest.json",
        "canonical_manifest_sha256": "a" * 64,
        "status": "validated",
        "is_current": False,
        "created_at": "2026-08-21T00:00:00Z",
    }]
    rows["import_runs"] = [{
        "release_version": "v0.2.0",
        "importer_name": "bted-materialize",
        "importer_version": "bted-materializer-0.3.0-b1",
        "input_manifest_path": "release_manifest.json",
        "input_manifest_sha256": "a" * 64,
        "staging_location": "test",
        "run_status": "validated",
        "started_at": "2026-08-21T00:00:00Z",
        "finished_at": "2026-08-21T00:00:00Z",
        "validation_summary": {
            "canonical_validation_status": "validated",
            "postgresql_ready": True,
            "write_mode": "not_written",
        },
        "error_summary": None,
    }]
    if publication_rows is not None:
        rows["publications"] = publication_rows
    if asset_rows is not None:
        rows["assets"] = asset_rows
    table_meta: dict[str, dict[str, Any]] = {}
    for table, table_rows in rows.items():
        path = root / f"{table}.jsonl"
        payload = b"".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            + b"\n"
            for row in table_rows
        )
        path.write_bytes(payload)
        table_meta[table] = {
            "file": path.name,
            "row_count": len(table_rows),
            "sha256": _sha256(path),
            "byte_size": len(payload),
        }
    manifest = {
        "materialization_schema_version": "bted-postgresql-staging-0.3.0",
        "materializer_version": "bted-materializer-0.3.0-b1",
        "release_version": "v0.2.0",
        "generated_at_utc": "2026-08-21T00:00:00Z",
        "canonical_validation_status": "validated",
        "postgresql_ready": True,
        "write_mode": "not_written",
        "canonical_manifest": {"path": "release_manifest.json", "sha256": "a" * 64},
        "contig_registry": {"path": "data/registry/reference_contigs.v0.2.0.tsv", "sha256": "b" * 64},
        "asset_origin": {"base": "https://example.test/assets", "host": "example.test", "asset_origin_status": "planned_not_verified"},
        "foreign_key_mode": "natural_key_refs",
        "unresolved": [],
        "source_count": 0,
        "source_annotation_input_row_count": 0,
        "source_annotation_materialized_row_count": 0,
        "annotation_field_provenance": [],
        "published_source_count": 0,
        "audit_only_source_ids": [],
        "tables": table_meta,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksum_lines = [
        f"{_sha256(root / name)}  {name}\n"
        for name in sorted(["manifest.json", *[f"{table}.jsonl" for table in rows]])
    ]
    (root / "SHA256SUMS.txt").write_text("".join(checksum_lines), encoding="utf-8")
    return root


def _tiny_preflight_verification(root: Path, mutate: Any = None) -> BundleVerification:
    """Build a small, checksum-free verification object for preflight CHECK tests."""

    assembly = "GCF_000000001.1"
    contig = "NC_000001.1"
    rows: dict[str, list[dict[str, Any]]] = {
        table: []
        for table in (
            "release_versions", "import_runs", "publications", "assemblies", "contigs",
            "sources", "source_accessions", "samples", "endpoints", "source_annotations",
            "genes", "endpoint_gene_context", "assets",
        )
    }
    rows["release_versions"] = [{
        "release_version": "v0.2.0", "release_date": "2026-08-21",
        "canonical_manifest_path": "release_manifest.json", "canonical_manifest_sha256": "a" * 64,
        "status": "validated", "is_current": False, "created_at": "2026-08-21T00:00:00Z",
    }]
    rows["import_runs"] = [{
        "release_version": "v0.2.0", "importer_name": "test", "importer_version": "test",
        "input_manifest_path": "release_manifest.json", "input_manifest_sha256": "a" * 64,
        "staging_location": "test", "run_status": "validated",
        "started_at": "2026-08-21T00:00:00Z", "finished_at": "2026-08-21T00:00:00Z",
        "validation_summary": {}, "error_summary": None,
    }]
    rows["publications"] = [{
        "pmid": "1", "doi": "10.1000/test", "pmc": None, "published_year": 2020,
        "journal": "Test", "paper_title": "Test paper", "citation_json": {},
    }]
    rows["assemblies"] = [{
        "assembly_accession": assembly, "assembly_name": "test", "organism_name": "Test bacterium",
        "strain": "test", "taxon_id": None, "reference_url": "https://example.test/assembly",
        "source_ids": ["S"],
    }]
    rows["contigs"] = [{
        "assembly_id_ref": assembly, "assembly_accession": assembly, "contig_accession": contig,
        "contig_name": contig, "length_bp": 100, "sequence_sha256": None, "provenance_json": {},
    }]
    rows["sources"] = [{
        "release_version": "v0.2.0", "source_id": "S", "publication_id_ref": "1",
        "assembly_id_ref": assembly, "species": "Test bacterium", "phylum": "Test",
        "assay_family": "Term-seq", "release_status": "published_standardized",
        "evidence_class": "author_called_endpoint", "redistribution_status": "external_link_only",
        "accessibility_status": "public", "coordinate_status": "verified",
        "processing_status": "standardized", "used_for_batter_augmentation": False,
        "record_count": 1, "has_jbrowse": True, "manifest_path": "manifest.json",
        "manifest_sha256": "a" * 64, "record_root": "records/S", "source_note": "",
        "decision_note": "", "known_limitations": "",
    }]
    rows["source_accessions"] = [{
        "source_id_ref": "S", "accession_namespace": "GEO", "accession": "GSE1",
        "raw_value": "GSE1", "accession_type": "study", "ordinal": 1,
        "external_url": "https://example.test/GSE1",
    }]
    rows["samples"] = [{
        "source_id_ref": "S", "sample_id": "sample-1", "sample_label": "sample",
        "biological_condition": "condition", "replicate_label": "rep1", "sample_accession": "S1",
        "metadata_json": {},
    }]
    rows["endpoints"] = [{
        "release_version": "v0.2.0", "source_id_ref": "S", "source_pk_ref": "S",
        "contig_id_ref": {"assembly_accession": assembly, "contig_accession": contig},
        "sample_id_ref": {"source_id": "S", "sample_id": "sample-1"},
        "end_id": "S--sample-1--NC_000001.1--+--1", "source_id": "S", "sample_id": "sample-1",
        "assay": "Term-seq", "evidence_class": "author_called_endpoint", "author_endpoint_id": "E1",
        "published_reference_accession": contig, "reference_assembly": assembly,
        "reference_name": contig, "replicon_label": "chromosome", "biological_coordinate_1based": 1,
        "bed_start_0based": 0, "bed_end_0based": 1, "strand": "+", "signal_or_score": "1",
        "author_category": "endpoint", "associated_gene_or_locus": "NA", "pmid": "1",
        "doi": "10.1000/test", "source_table_or_file": "test.tsv",
        "coordinate_interpretation": "1-based", "original_row_reference": "test:1",
        "qc_status": "pass", "note": "",
    }]
    rows["source_annotations"] = [{
        "release_version": "v0.2.0", "source_id_ref": "S",
        "end_id": rows["endpoints"][0]["end_id"], "annotation_kind": "author_annotation",
        "source_record_id": "E1", "ordinal": 1, "annotation_json": {"category": "endpoint"},
        "provenance_json": {},
    }]
    rows["assets"] = [{
        "asset_id": "release--manifest", "release_version": "v0.2.0", "asset_kind": "release_manifest",
        "logical_path": "release_manifest.json", "origin_url": "https://example.test/assets/release_manifest.json",
        "origin_host": "example.test", "byte_size": 1, "sha256": "a" * 64,
        "mime_type": "application/json", "supports_range": False,
        "redistribution_status": "external_link_only", "is_public": False,
    }]
    if mutate is not None:
        mutate(rows)
    root.mkdir(parents=True, exist_ok=True)
    table_files: dict[str, Path] = {}
    for table, table_rows in rows.items():
        path = root / f"{table}.jsonl"
        path.write_text(
            "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n" for row in table_rows),
            encoding="utf-8",
        )
        table_files[table] = path
    manifest = {
        "release_version": "v0.2.0",
        "asset_origin": {
            "base": "https://example.test/assets",
            "host": "example.test",
            "asset_origin_status": "planned_not_verified",
        },
    }
    return BundleVerification(root, manifest, table_files, {})


class FakeResult:
    def __init__(self, rowcount: int = 1) -> None:
        self.rowcount = rowcount


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection
        self.fetchone_value: Any = None
        self.fetchall_value: list[Any] = []

    @staticmethod
    def _normal(sql: str) -> str:
        return " ".join(sql.split())

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> FakeResult | "FakeCursor":
        normalized = self._normal(sql)
        self.connection.calls.append(("execute", normalized, tuple(params)))
        self.fetchone_value = None
        self.fetchall_value = []
        if normalized.startswith("SELECT release_version FROM release_versions WHERE release_version"):
            if self.connection.release_exists:
                self.fetchone_value = ("v0.2.0",)
        elif normalized.startswith("SELECT publication_id, pmid,"):
            self.fetchone_value = self.connection.existing_publications.get(str(params[0]))
        elif normalized.startswith("SELECT assembly_id, assembly_accession,"):
            self.fetchone_value = self.connection.existing_assemblies.get(str(params[0]))
        elif normalized.startswith("SELECT contig_id, assembly_id,"):
            self.fetchone_value = self.connection.existing_contigs.get((int(params[0]), str(params[1])))
        elif normalized.startswith("SELECT COUNT(*) FROM "):
            table = normalized.split("SELECT COUNT(*) FROM ", 1)[1].split()[0]
            self.fetchone_value = (self.connection.counts[table],)
        elif normalized.startswith("SELECT s.source_id, s.record_count,"):
            self.fetchall_value = list(self.connection.endpoint_group_counts)
        elif normalized.startswith("SELECT s.source_id, COUNT(a.annotation_id)"):
            self.fetchall_value = list(self.connection.annotation_group_counts)
        elif normalized.startswith("SELECT import_run_id, validation_summary"):
            self.fetchone_value = self.connection.latest_committed
        elif normalized.startswith("SELECT release_version FROM release_versions WHERE is_current"):
            self.fetchone_value = self.connection.current_release
        elif normalized.startswith("INSERT INTO ") and " RETURNING " in normalized:
            self.fetchone_value = (self.connection.next_id,)
            self.connection.next_id += 1
        elif normalized.startswith("UPDATE import_runs"):
            return FakeResult(1)
        elif normalized.startswith("UPDATE release_versions"):
            return FakeResult(1)
        elif normalized.startswith("SET TRANSACTION") or normalized.startswith("SELECT pg_advisory_xact_lock"):
            pass
        else:
            raise AssertionError(f"unhandled fake SQL: {normalized}")
        return self

    def executemany(self, sql: str, params: list[tuple[Any, ...]]) -> FakeResult:
        normalized = self._normal(sql)
        self.connection.calls.append(("executemany", normalized, len(params)))
        for table in ("source_accessions", "endpoints", "source_annotations", "assets"):
            if f"INSERT INTO {table} " in normalized:
                self.connection.batch_calls.setdefault(table, []).append(len(params))
                if self.connection.fail_table == table:
                    raise PostgresWriterError(f"fake failure in {table}")
                break
        return FakeResult(len(params))

    def fetchone(self) -> Any:
        return self.fetchone_value

    def fetchall(self) -> list[Any]:
        return self.fetchall_value

    def close(self) -> None:
        return None


class FakeTransaction:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection

    def __enter__(self) -> "FakeTransaction":
        self.connection.transaction_started = True
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> bool:
        if exc_type is None:
            self.connection.committed = True
        else:
            self.connection.transaction_rolled_back = True
        return False


class FakeConnection:
    def __init__(self, *, source_counts: dict[str, int], annotation_counts: dict[str, int]) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.batch_calls: dict[str, list[int]] = {}
        self.counts = {"sources": 22, "endpoints": 28399, "source_annotations": 81477, "assets": 127}
        self.endpoint_group_counts = [(source_id, count, count) for source_id, count in sorted(source_counts.items())]
        self.annotation_group_counts = [(source_id, annotation_counts.get(source_id, 0)) for source_id in sorted(source_counts)]
        self.existing_publications: dict[str, tuple[Any, ...]] = {}
        self.existing_assemblies: dict[str, tuple[Any, ...]] = {}
        self.existing_contigs: dict[tuple[int, str], tuple[Any, ...]] = {}
        self.release_exists = False
        self.current_release = None
        self.latest_committed = None
        self.next_id = 1
        self.fail_table: str | None = None
        self.transaction_started = False
        self.transaction_rolled_back = False
        self.committed = False

    def transaction(self) -> FakeTransaction:
        return FakeTransaction(self)

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def rollback(self) -> None:
        self.transaction_rolled_back = True

    def close(self) -> None:
        return None


class TestBtedV03Postgres(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.bundle = Path(cls.temp.name) / "bundle"
        cls.result = materialize_release(
            RELEASE_ROOT,
            repo_root=REPO_ROOT,
            output_dir=cls.bundle,
            asset_origin_base="https://example.test/assets",
            generated_at_utc="2026-08-21T00:00:00Z",
        )
        cls.verification = verify_bundle(cls.bundle)
        cls.state = _preflight(cls.verification)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def _fake(self) -> FakeConnection:
        return FakeConnection(
            # SQL's LEFT JOIN audit returns zero rows for audit-only sources;
            # include those source IDs in the fake result as the real database
            # would, rather than iterating only over Counter keys with values.
            source_counts={
                source_id: self.state.endpoint_counts.get(source_id, 0)
                for source_id in self.state.sources
            },
            annotation_counts={
                source_id: self.state.annotation_counts.get(source_id, 0)
                for source_id in self.state.sources
            },
        )

    def test_verify_bundle_real_counts_and_planned_origin(self) -> None:
        self.assertEqual(self.verification.table_counts["endpoints"], 28399)
        self.assertEqual(self.verification.table_counts["source_annotations"], 81477)
        self.assertEqual(self.verification.table_counts["assets"], 127)
        self.assertEqual(self.verification.manifest["asset_origin"]["asset_origin_status"], "planned_not_verified")

    def test_fake_load_order_batching_count_audit_and_commit(self) -> None:
        connection = self._fake()
        result = load_bundle(self.bundle, connection, batch_size=1000)
        self.assertEqual(result.run_id, 2)
        self.assertEqual(result.status, "committed")
        self.assertEqual(result.counts, {"sources": 22, "endpoints": 28399, "source_annotations": 81477, "assets": 127})
        self.assertTrue(connection.transaction_started)
        self.assertTrue(connection.committed)
        self.assertFalse(connection.transaction_rolled_back)
        self.assertEqual(connection.batch_calls["endpoints"], [1000] * 28 + [399])
        self.assertEqual(connection.batch_calls["source_annotations"], [1000] * 81 + [477])
        labels = [call[1].split()[2] for call in connection.calls if call[0] == "execute" and call[1].startswith("INSERT INTO")]
        self.assertEqual(labels[:4], ["release_versions", "import_runs", "publications", "publications"])
        joined_sql = "\n".join(call[1] for call in connection.calls)
        self.assertNotRegex(joined_sql, r"\b(DROP|TRUNCATE|DELETE)\b")

    def test_mid_transaction_failure_rolls_back(self) -> None:
        connection = self._fake()
        connection.fail_table = "source_annotations"
        with self.assertRaises(PostgresWriterError):
            load_bundle(self.bundle, connection)
        self.assertTrue(connection.transaction_started)
        self.assertTrue(connection.transaction_rolled_back)
        self.assertFalse(connection.committed)

    def test_preflight_error_does_not_begin_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = _write_minimal_bundle(Path(directory) / "bundle", publication_rows=[{"pmid": "1"}])
            connection = self._fake()
            with self.assertRaises(PostgresWriterError):
                load_bundle(bundle, connection)
            self.assertFalse(connection.transaction_started)

    def test_bundle_tamper_extra_file_and_root_symlink_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = _write_minimal_bundle(Path(directory) / "bundle")
            (bundle / "extra.txt").write_text("extra", encoding="utf-8")
            with self.assertRaises(PostgresWriterError):
                verify_bundle(bundle)
            (bundle / "extra.txt").unlink()
            (bundle / "nested").mkdir()
            with self.assertRaises(PostgresWriterError):
                verify_bundle(bundle)
            (bundle / "nested").rmdir()
            try:
                os.symlink(bundle / "manifest.json", bundle / "manifest-link.json")
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available on this platform")
            with self.assertRaises(PostgresWriterError):
                verify_bundle(bundle)

    def test_bundle_checksum_and_row_count_tamper_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = _write_minimal_bundle(Path(directory) / "bundle")
            (bundle / "assets.jsonl").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(PostgresWriterError):
                verify_bundle(bundle)

    def test_bundle_rejects_nonfinite_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = _write_minimal_bundle(Path(directory) / "bundle")
            (bundle / "assets.jsonl").write_text('{"value":NaN}\n', encoding="utf-8")
            with self.assertRaises(PostgresWriterError) as error:
                verify_bundle(bundle)
            self.assertIn("checksum mismatch", str(error.exception))
            with self.assertRaises(PostgresWriterError):
                list(_iter_jsonl(bundle / "assets.jsonl"))

    def test_preflight_checks_asset_origin_and_planned_range(self) -> None:
        asset = {
            "asset_id": "release--manifest",
            "release_version": "v0.2.0",
            "asset_kind": "release_manifest",
            "logical_path": "release_manifest.json",
            "origin_url": "https://example.test/assets/release_manifest.json",
            "origin_host": "wrong.example.test",
            "byte_size": 1,
            "sha256": "a" * 64,
            "mime_type": "application/json",
            "supports_range": True,
            "redistribution_status": "external_link_only",
            "is_public": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            bundle = _write_minimal_bundle(Path(directory) / "bundle", asset_rows=[asset])
            verification = verify_bundle(bundle)
            with self.assertRaises(PostgresWriterError) as error:
                _preflight(verification)
            self.assertIn("origin_host", str(error.exception))

        asset["origin_host"] = "example.test"
        with tempfile.TemporaryDirectory() as directory:
            bundle = _write_minimal_bundle(Path(directory) / "bundle", asset_rows=[asset])
            with self.assertRaises(PostgresWriterError) as error:
                _preflight(verify_bundle(bundle))
            self.assertIn("supports_range", str(error.exception))

        asset["supports_range"] = False
        asset["origin_url"] = "https://example.test/assets/release--manifest"
        with tempfile.TemporaryDirectory() as directory:
            bundle = _write_minimal_bundle(Path(directory) / "bundle", asset_rows=[asset])
            with self.assertRaises(PostgresWriterError) as error:
                _preflight(verify_bundle(bundle))
            self.assertIn("logical_path", str(error.exception))

    def test_preflight_rejects_schema_check_violations_before_transaction(self) -> None:
        cases = (
            (
                "endpoint coordinate",
                lambda rows: rows["endpoints"][0].update(
                    biological_coordinate_1based=0, bed_start_0based=-1, bed_end_0based=0
                ),
                "biological coordinate",
            ),
            (
                "negative source count",
                lambda rows: rows["sources"][0].update(record_count=-1),
                "record_count",
            ),
            (
                "published public state",
                lambda rows: rows["sources"][0].update(record_count=0),
                "public-state",
            ),
            (
                "audit-only public state",
                lambda rows: rows["sources"][0].update(
                    release_status="audit_only", evidence_class="NA", record_count=0, has_jbrowse=True
                ),
                "public-state",
            ),
            (
                "to-review public state",
                lambda rows: rows["sources"][0].update(
                    release_status="to_review", evidence_class="NA", record_count=1, has_jbrowse=False
                ),
                "public-state",
            ),
            (
                "annotation ordinal",
                lambda rows: rows["source_annotations"][0].update(ordinal=0),
                "ordinal",
            ),
            (
                "accession ordinal",
                lambda rows: rows["source_accessions"][0].update(ordinal=0),
                "ordinal",
            ),
            (
                "negative asset size",
                lambda rows: rows["assets"][0].update(byte_size=-1),
                "byte_size",
            ),
        )
        for label, mutate, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                verification = _tiny_preflight_verification(Path(directory) / "tiny", mutate)
                with self.assertRaises(PostgresWriterError) as error:
                    _preflight(verification)
                self.assertIn(expected, str(error.exception))

        with tempfile.TemporaryDirectory() as directory:
            verification = _tiny_preflight_verification(Path(directory) / "tiny")
            state = _preflight(verification)
            self.assertEqual(state.endpoint_counts["S"], 1)

    def test_existing_publication_compatible_reuses_identity_and_conflict_fails(self) -> None:
        pmid, row = next(iter(self.state.publications.items()))
        compatible = self._fake()
        compatible.existing_publications[pmid] = (
            9001,
            row["pmid"], row["doi"], row["pmc"], row["published_year"], row["journal"], row["paper_title"], row["citation_json"],
        )
        result = load_bundle(self.bundle, compatible)
        self.assertEqual(result.status, "committed")
        publication_inserts = [
            call for call in compatible.calls
            if call[0] == "execute" and call[1].startswith("INSERT INTO publications")
        ]
        self.assertEqual(len(publication_inserts), len(self.state.publications) - 1)

        conflict = self._fake()
        conflict.existing_publications[pmid] = (
            9001,
            row["pmid"], row["doi"], row["pmc"], row["published_year"], row["journal"], "conflicting title", row["citation_json"],
        )
        with self.assertRaises(PostgresWriterError):
            load_bundle(self.bundle, conflict)
        self.assertTrue(conflict.transaction_rolled_back)

    def test_existing_release_is_rejected_without_release_insert(self) -> None:
        connection = self._fake()
        connection.release_exists = True
        with self.assertRaises(PostgresWriterError):
            load_bundle(self.bundle, connection)
        self.assertFalse(any(call[1].startswith("INSERT INTO release_versions") for call in connection.calls if call[0] == "execute"))

    def test_planned_origin_cannot_be_promoted(self) -> None:
        connection = self._fake()
        with self.assertRaises(PostgresWriterError):
            promote_bundle(self.bundle, connection)
        self.assertFalse(connection.transaction_started)

    def test_cli_verify_and_write_safety(self) -> None:
        verified = subprocess.run(
            [sys.executable, "scripts/import_bted_v03.py", "verify-bundle", "--bundle-dir", str(self.bundle)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertIn('"status": "verified"', verified.stdout)
        no_confirm = subprocess.run(
            [sys.executable, "scripts/import_bted_v03.py", "load-postgres", "--bundle-dir", str(self.bundle)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(no_confirm.returncode, 2)
        no_driver = subprocess.run(
            [sys.executable, "scripts/import_bted_v03.py", "load-postgres", "--bundle-dir", str(self.bundle), "--confirm-write"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            env={key: value for key, value in os.environ.items() if key != "BTED_DATABASE_URL"},
            check=False,
        )
        self.assertEqual(no_driver.returncode, 1)
        self.assertNotIn("postgresql://", no_driver.stderr)


if __name__ == "__main__":
    unittest.main()
