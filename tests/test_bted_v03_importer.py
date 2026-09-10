"""Tests for the read-only BTED v0.3 canonical-release validator."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from backend.importer.canonical import V02_ENDPOINT_COLUMNS, validate_release
from backend.importer.materialize import MaterializationError, materialize_release
from scripts.build_reference_contig_registry import (
    REFERENCE_CONTIG_COLUMNS,
    RegistryBuildError,
    build_reference_contig_registry,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_ROOT = REPO_ROOT / "data/public/v0.2.0"
REGISTRY = REPO_ROOT / "data/registry/batter_s1_source_registry.tsv"
REGISTRY_MANIFESTS = REPO_ROOT / "data/registry/manifests"
REFERENCE_CONTIG_REGISTRY = REPO_ROOT / "data/registry/reference_contigs.v0.2.0.tsv"
JBROWSE_BUNDLE = REPO_ROOT.parent / "bted-v0.2/dist/BTED-v0.2.0-jbrowse"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def copy_reference_contig_registry(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REFERENCE_CONTIG_REGISTRY, destination)
    return destination


def make_tiny_jbrowse_bundle(
    root: Path,
    release_root: Path,
    source_ids: tuple[str, ...] = ("BATTER_S1_007",),
    lengths: tuple[int, ...] = (100_000,),
    mutate_after_checksum: bool = False,
) -> Path:
    """Create only tiny fake FNA/FAI/config assets for builder tests."""

    bundle = root / "tiny-jbrowse"
    assets = bundle / "assets"
    assets.mkdir(parents=True)
    checksum_paths: list[Path] = []
    for source_id, length in zip(source_ids, lengths):
        endpoint_path = release_root / "records" / source_id / "endpoints.tsv"
        with endpoint_path.open(encoding="utf-8", newline="") as handle:
            endpoint = next(csv.DictReader(handle, delimiter="\t"))
        contig = endpoint["reference_name"]
        fasta_name = f"{source_id}__fake.fna"
        fai_name = f"{source_id}__fake.fna.fai"
        fasta_path = assets / fasta_name
        fai_path = assets / fai_name
        fasta_path.write_text(f">{contig}\nACGT\n", encoding="utf-8")
        fai_path.write_text(f"{contig}\t{length}\t0\t4\t5\n", encoding="utf-8")
        config = {
            "assemblies": [
                {
                    "name": f"{source_id}_assembly",
                    "sequence": {
                        "adapter": {
                            "type": "IndexedFastaAdapter",
                            "fastaLocation": {"uri": f"assets/{fasta_name}"},
                            "faiLocation": {"uri": f"assets/{fai_name}"},
                        }
                    },
                }
            ]
        }
        config_path = bundle / f"{source_id}.config.json"
        config_path.write_text(json.dumps(config) + "\n", encoding="utf-8")
        checksum_paths.extend([config_path, fasta_path, fai_path])
    sums = []
    for path in sorted(checksum_paths, key=lambda item: item.relative_to(bundle).as_posix()):
        sums.append(f"{digest(path)}  {path.relative_to(bundle).as_posix()}\n")
    (bundle / "SHA256SUMS.txt").write_text("".join(sums), encoding="utf-8")
    if mutate_after_checksum:
        first_fasta = assets / f"{source_ids[0]}__fake.fna"
        first_fasta.write_text(first_fasta.read_text(encoding="utf-8") + "A\n", encoding="utf-8")
    return bundle


def _source_row(source_id: str) -> dict[str, str]:
    with REGISTRY.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return next(row for row in rows if row["source_id"] == source_id)


def _refresh_release_file_hashes(release_root: Path, source_id: str) -> None:
    """Refresh one fixture entry and its per-source checksum file."""

    release_path = release_root / "release_manifest.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    entry = release["sources"][source_id]
    record_root = release_root / "records" / source_id
    non_checksum = [
        record_root / str(item["path"])
        for item in entry["files"]
        if item["path"] != "SHA256SUMS.txt"
    ]
    (record_root / "SHA256SUMS.txt").write_text(
        "".join(f"{digest(path)}  {path.name}\n" for path in sorted(non_checksum, key=lambda p: p.name)),
        encoding="utf-8",
    )
    for item in entry["files"]:
        item["sha256"] = digest(record_root / str(item["path"]))
    release_path.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_registry_row(root: Path, row: dict[str, str]) -> None:
    registry_path = root / "data/registry/batter_s1_source_registry.tsv"
    with registry_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    rows.append(row)
    write_tsv(registry_path, fields, rows)


def make_fixture(root: Path, source_id: str = "BATTER_S1_007") -> Path:
    """Create a tiny release fixture; no large release tree is copied."""

    release_root = root / "data/public/v0.2.0"
    record_root = release_root / "records" / source_id
    record_root.mkdir(parents=True)
    registry_row = _source_row(source_id)
    write_tsv(root / "data/registry/batter_s1_source_registry.tsv", list(registry_row), [registry_row])

    source_manifest = json.loads(
        (RELEASE_ROOT / "records" / source_id / "manifest.json").read_text(encoding="utf-8")
    )
    source_manifest["record_count"] = 1
    manifest_path = record_root / "manifest.json"
    manifest_path.write_text(json.dumps(source_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry_manifest_path = root / "data/registry/manifests" / f"{source_id}.json"
    registry_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    registry_manifest_path.write_text(
        (REGISTRY_MANIFESTS / f"{source_id}.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    original_endpoint = RELEASE_ROOT / "records" / source_id / "endpoints.tsv"
    with original_endpoint.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle, delimiter="\t"))
    write_tsv(record_root / "endpoints.tsv", V02_ENDPOINT_COLUMNS, [row])
    (record_root / "endpoints.bed").write_text(
        "\t".join(
            [
                row["reference_name"],
                row["bed_start_0based"],
                row["bed_end_0based"],
                row["end_id"],
                "0",
                row["strand"],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    original_annotation = RELEASE_ROOT / "records" / source_id / "source_annotations.tsv"
    with original_annotation.open(encoding="utf-8", newline="") as handle:
        annotation_reader = csv.DictReader(handle, delimiter="\t")
        annotation_fields = list(annotation_reader.fieldnames or [])
        annotation_row = next(annotation_reader)
    write_tsv(record_root / "source_annotations.tsv", annotation_fields, [annotation_row])
    (record_root / "fields.json").write_text("{}\n", encoding="utf-8")

    entry = {
        "release_status": "published_standardized",
        "record_count": 1,
        "evidence_class": row["evidence_class"],
        "record_root": f"data/public/v0.2.0/records/{source_id}",
        "has_jbrowse": True,
        "redistribution_status": "verified_redistributable",
        "source_annotations_status": "published",
        "files": [],
    }
    declared_paths = (
        record_root / "endpoints.tsv",
        record_root / "endpoints.bed",
        record_root / "fields.json",
        record_root / "manifest.json",
        record_root / "source_annotations.tsv",
    )
    sums = "".join(f"{digest(path)}  {path.name}\n" for path in sorted(declared_paths, key=lambda p: p.name))
    (record_root / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    for path in (*declared_paths, record_root / "SHA256SUMS.txt"):
        entry["files"].append({"path": path.name, "sha256": digest(path)})
    release = {
        "release_version": "v0.2.0",
        "release_date": "2026-08-10",
        "schema": {"core": "24-column BTED endpoint schema"},
        "summary": {
            "source_count": 1,
            "published_standardized_sources": 1,
            "audit_only_sources": 0,
            "published_record_count": 1,
        },
        "sources": {source_id: entry},
    }
    release_path = release_root / "release_manifest.json"
    release_path.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return release_root


def make_same_pmid_conflict_fixture(root: Path) -> Path:
    """Create two tiny sources sharing a PMID but disagreeing on metadata."""

    release_root = make_fixture(root, source_id="BATTER_S1_007")
    source_id = "BATTER_S1_013"
    source1 = release_root / "records/BATTER_S1_007"
    source2 = release_root / "records" / source_id
    source2.mkdir(parents=True)

    # Start with the existing canonical row, then make source 2 a distinct
    # source while deliberately retaining the PMID and changing the DOI/title.
    manifest = json.loads((source1 / "manifest.json").read_text(encoding="utf-8"))
    manifest.update(
        {
            "source_id": source_id,
            "doi": "10.9999/bted-conflict",
            "paper_title": "Conflicting publication metadata",
            "published_year": "2099",
            "record_count": 1,
        }
    )
    (source2 / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    endpoint_path = source1 / "endpoints.tsv"
    with endpoint_path.open(encoding="utf-8", newline="") as handle:
        endpoint = next(csv.DictReader(handle, delimiter="\t"))
    endpoint["source_id"] = source_id
    endpoint["end_id"] = endpoint["end_id"].replace("BATTER_S1_007", source_id)
    endpoint["doi"] = manifest["doi"]
    write_tsv(source2 / "endpoints.tsv", V02_ENDPOINT_COLUMNS, [endpoint])
    (source2 / "endpoints.bed").write_text(
        "\t".join(
            [
                endpoint["reference_name"],
                endpoint["bed_start_0based"],
                endpoint["bed_end_0based"],
                endpoint["end_id"],
                "0",
                endpoint["strand"],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    annotation_path = source1 / "source_annotations.tsv"
    with annotation_path.open(encoding="utf-8", newline="") as handle:
        annotation_reader = csv.DictReader(handle, delimiter="\t")
        annotation_fields = list(annotation_reader.fieldnames or [])
        annotation = next(annotation_reader)
    annotation["end_id"] = annotation["end_id"].replace("BATTER_S1_007", source_id)
    if "source_id" in annotation:
        annotation["source_id"] = source_id
    if "doi" in annotation:
        annotation["doi"] = manifest["doi"]
    write_tsv(source2 / "source_annotations.tsv", annotation_fields, [annotation])
    (source2 / "fields.json").write_text("{}\n", encoding="utf-8")

    # The legacy registry manifest is made consistent with source 2 so this
    # fixture isolates the shared-PMID conflict rather than testing a stale
    # legacy copy at the same time.
    registry_manifest_path = root / "data/registry/manifests" / f"{source_id}.json"
    registry_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    registry_manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    registry_row = _source_row(source_id)
    registry_row.update(
        {
            "pmid": manifest["pmid"],
            "doi": manifest["doi"],
            "paper_title": manifest["paper_title"],
            "published_year": manifest["published_year"],
            "species": manifest["species"],
            "reference_genome": manifest["reference_genome"],
            "raw_data_accessions": "GSE-CONFLICT",
        }
    )
    _append_registry_row(root, registry_row)

    entry = {
        "release_status": "published_standardized",
        "record_count": 1,
        "evidence_class": endpoint["evidence_class"],
        "record_root": f"data/public/v0.2.0/records/{source_id}",
        "has_jbrowse": True,
        "redistribution_status": "verified_redistributable",
        "source_annotations_status": "published",
        "files": [],
    }
    declared_paths = (
        source2 / "endpoints.bed",
        source2 / "endpoints.tsv",
        source2 / "fields.json",
        source2 / "manifest.json",
        source2 / "source_annotations.tsv",
    )
    (source2 / "SHA256SUMS.txt").write_text(
        "".join(f"{digest(path)}  {path.name}\n" for path in sorted(declared_paths, key=lambda p: p.name)),
        encoding="utf-8",
    )
    for path in (*declared_paths, source2 / "SHA256SUMS.txt"):
        entry["files"].append({"path": path.name, "sha256": digest(path)})
    release = json.loads((release_root / "release_manifest.json").read_text(encoding="utf-8"))
    release["summary"].update(
        {
            "source_count": 2,
            "published_standardized_sources": 2,
            "audit_only_sources": 0,
            "published_record_count": 2,
        }
    )
    release["sources"][source_id] = entry
    (release_root / "release_manifest.json").write_text(
        json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return release_root


def make_audit_fixture(root: Path) -> Path:
    """Create an audit-only S1_002 fixture with one forbidden endpoint file."""

    release_root = root / "data/public/v0.2.0"
    record_root = release_root / "records/BATTER_S1_002"
    record_root.mkdir(parents=True)
    row = _source_row("BATTER_S1_002")
    write_tsv(root / "data/registry/batter_s1_source_registry.tsv", list(row), [row])
    source_manifest = json.loads((REGISTRY_MANIFESTS / "BATTER_S1_002.json").read_text(encoding="utf-8"))
    manifest_path = root / "data/registry/manifests/BATTER_S1_002.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(source_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RELEASE_ROOT / "records/BATTER_S1_007/endpoints.tsv").open(encoding="utf-8", newline="") as handle:
        endpoint_row = next(csv.DictReader(handle, delimiter="\t"))
    endpoint_row["source_id"] = "BATTER_S1_002"
    write_tsv(record_root / "endpoints.tsv", V02_ENDPOINT_COLUMNS, [endpoint_row])
    release = {
        "release_version": "v0.2.0",
        "summary": {"source_count": 1, "published_standardized_sources": 0, "audit_only_sources": 1, "published_record_count": 0},
        "sources": {
            "BATTER_S1_002": {
                "release_status": "audit_only",
                "record_count": 0,
                "evidence_class": "NA",
                "record_root": "data/public/v0.2.0/records/BATTER_S1_002",
                "has_jbrowse": False,
                "redistribution_status": "audit_only",
                "files": [],
            }
        },
    }
    (release_root / "release_manifest.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    return release_root


class TestBtedV03Importer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Build one real bundle for the B1 tests.  Keeping it at class scope
        # avoids repeatedly serializing the 28,399 endpoints and 81k grouped
        # annotation rows while still exercising the real v0.2 release.
        cls.materialization_tmp = tempfile.TemporaryDirectory()
        cls.materialization_root = Path(cls.materialization_tmp.name)
        cls.materialization_output = cls.materialization_root / "bundle"
        cls.materialization_result = materialize_release(
            RELEASE_ROOT,
            repo_root=REPO_ROOT,
            output_dir=cls.materialization_output,
            asset_origin_base="https://example.test/assets",
            generated_at_utc="2026-08-21T00:00:00Z",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.materialization_tmp.cleanup()

    def _read_bundle_rows(self, table: str) -> list[dict[str, object]]:
        path = self.materialization_output / f"{table}.jsonl"
        with path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def test_real_materialization_counts_and_audit_only_boundary(self) -> None:
        counts = self.materialization_result.table_counts
        self.assertEqual(counts["release_versions"], 1)
        self.assertEqual(counts["import_runs"], 1)
        self.assertEqual(counts["publications"], 13)
        self.assertEqual(counts["assemblies"], 20)
        self.assertEqual(counts["contigs"], 47)
        self.assertEqual(counts["sources"], 22)
        self.assertEqual(counts["source_accessions"], 32)
        self.assertEqual(counts["samples"], 21)
        self.assertEqual(counts["endpoints"], 28399)
        self.assertEqual(counts["source_annotations"], 81477)
        self.assertEqual(counts["genes"], 0)
        self.assertEqual(counts["endpoint_gene_context"], 0)
        self.assertEqual(counts["assets"], 127)
        self.assertTrue(self.materialization_result.manifest["postgresql_ready"])
        self.assertEqual(self.materialization_result.manifest["asset_origin"]["asset_origin_status"], "planned_not_verified")
        s2_endpoints = [row for row in self._read_bundle_rows("endpoints") if row["source_id_ref"] == "BATTER_S1_002"]
        s2_annotations = [row for row in self._read_bundle_rows("source_annotations") if row["source_id_ref"] == "BATTER_S1_002"]
        s2 = next(row for row in self._read_bundle_rows("sources") if row["source_id"] == "BATTER_S1_002")
        self.assertEqual(s2_endpoints, [])
        self.assertEqual(s2_annotations, [])
        self.assertFalse(s2["has_jbrowse"])

    def test_materialization_preserves_24_columns_and_natural_key_closure(self) -> None:
        endpoints = self._read_bundle_rows("endpoints")
        self.assertTrue(all(set(V02_ENDPOINT_COLUMNS).issubset(row) for row in endpoints))
        sources = self._read_bundle_rows("sources")
        source_ids = {row["source_id"] for row in sources}
        pmids = {row["pmid"] for row in self._read_bundle_rows("publications")}
        assemblies = {row["assembly_accession"] for row in self._read_bundle_rows("assemblies")}
        samples = {(row["source_id_ref"], row["sample_id"]) for row in self._read_bundle_rows("samples")}
        contigs = {
            (row["assembly_accession"], row["contig_accession"])
            for row in self._read_bundle_rows("contigs")
        }
        self.assertTrue({row["source_id_ref"] for row in endpoints} <= source_ids)
        self.assertTrue({row["publication_id_ref"] for row in sources} <= pmids)
        self.assertTrue({row["assembly_id_ref"] for row in sources} <= assemblies)
        self.assertTrue(
            {(row["source_id_ref"], row["sample_id_ref"]["sample_id"]) for row in endpoints}
            <= samples
        )
        self.assertTrue(
            {
                (row["contig_id_ref"]["assembly_accession"], row["contig_id_ref"]["contig_accession"])
                for row in endpoints
            }
            <= contigs
        )
        self.assertTrue(
            all("/" not in row["asset_id"] for row in self._read_bundle_rows("assets"))
        )

    def test_source_annotation_fields_are_lossless_and_prediction_is_separate(self) -> None:
        annotations = self._read_bundle_rows("source_annotations")
        by_source: dict[str, set[str]] = {}
        for row in annotations:
            by_source.setdefault(str(row["source_id_ref"]), set()).update(
                row["annotation_json"].keys()
            )
        for source_id, observed_fields in by_source.items():
            path = RELEASE_ROOT / "records" / source_id / "source_annotations.tsv"
            with path.open(encoding="utf-8", newline="") as handle:
                fields = set(csv.DictReader(handle, delimiter="\t").fieldnames or [])
            self.assertTrue(fields <= observed_fields, source_id)
        prediction = next(row for row in annotations if row["annotation_kind"] == "prediction_annotation")
        self.assertNotIn(prediction["annotation_kind"], {"observed_signal", "called_endpoint", "author_called_endpoint"})
        self.assertIn("endpoint_evidence_class", prediction["provenance_json"])
        self.assertNotIn("original_row", prediction["provenance_json"])
        self.assertNotIn("field_definitions", prediction["provenance_json"])
        self.assertNotIn("field_roles", prediction["provenance_json"])
        author = next(
            row for row in annotations
            if row["annotation_kind"] == "author_annotation"
            and "original_evidence_roles" in row["provenance_json"]
        )
        self.assertEqual(
            set(author["provenance_json"]["original_evidence_roles"]),
            {"author_called_endpoint"},
        )

        field_provenance = self.materialization_result.manifest["annotation_field_provenance"]
        self.assertEqual(len(field_provenance), 22)
        self.assertEqual(
            {item["source_id"] for item in field_provenance},
            {row["source_id"] for row in self._read_bundle_rows("sources")},
        )
        for item in field_provenance:
            self.assertTrue(item["fields_json_path"].startswith("records/"))
            self.assertNotIn("/Users/", item["fields_json_path"])
            self.assertRegex(item["fields_json_sha256"], r"^[0-9a-f]{64}$")
            self.assertGreaterEqual(item["source_annotations_row_count"], 0)
            if item["source_annotations_path"]:
                self.assertTrue(item["source_annotations_path"].startswith("records/"))
                self.assertRegex(item["source_annotations_sha256"], r"^[0-9a-f]{64}$")

    def test_source_annotation_bundle_size_is_bounded(self) -> None:
        annotation_path = self.materialization_output / "source_annotations.jsonl"
        total_size = sum(path.stat().st_size for path in self.materialization_output.iterdir())
        # A repeated field dictionary previously made this one file roughly
        # 248 MiB.  Keep the staging representation comfortably below 100 MiB
        # for the current release while retaining all annotation values.
        self.assertLess(annotation_path.stat().st_size, 100 * 1024 * 1024)
        self.assertLess(total_size, 150 * 1024 * 1024)

    def test_asset_kinds_and_natural_key_helper_fields_are_explicit(self) -> None:
        allowed = {
            "fasta", "fai", "gff3", "tbi", "bigwig", "bed", "config", "metadata",
            "checksum", "archive", "release_manifest", "other",
        }
        assets = self._read_bundle_rows("assets")
        self.assertTrue({row["asset_kind"] for row in assets} <= allowed)
        self.assertTrue(all("origin_status" not in row for row in assets))
        self.assertTrue(all(row["supports_range"] is False for row in assets))
        self.assertTrue(all(
            row["origin_url"] == f"https://example.test/assets/{row['logical_path']}"
            for row in assets
        ))
        accession_rows = self._read_bundle_rows("source_accessions")
        self.assertTrue(all("metadata_json" not in row for row in accession_rows))
        self.assertTrue(all("source_id_ref" in row for row in accession_rows))

    def test_materialization_fixed_timestamp_is_byte_reproducible(self) -> None:
        output = self.materialization_root / "bundle-second"
        result = materialize_release(
            RELEASE_ROOT,
            repo_root=REPO_ROOT,
            output_dir=output,
            asset_origin_base="https://example.test/assets",
            generated_at_utc="2026-08-21T00:00:00Z",
        )
        first = (self.materialization_output / "SHA256SUMS.txt").read_text(encoding="utf-8")
        second = (output / "SHA256SUMS.txt").read_text(encoding="utf-8")
        self.assertEqual(first, second)
        self.assertEqual(result.manifest["tables"], self.materialization_result.manifest["tables"])

    def test_materialization_rejects_invalid_origin_and_nonempty_directory(self) -> None:
        with self.assertRaises(MaterializationError):
            materialize_release(
                RELEASE_ROOT,
                repo_root=REPO_ROOT,
                output_dir=self.materialization_root / "invalid-origin",
                asset_origin_base="http://example.test/assets",
                generated_at_utc="2026-08-21T00:00:00Z",
            )
        nonempty = self.materialization_root / "nonempty"
        nonempty.mkdir()
        (nonempty / "keep.txt").write_text("do not overwrite", encoding="utf-8")
        with self.assertRaises(MaterializationError):
            materialize_release(
                RELEASE_ROOT,
                repo_root=REPO_ROOT,
                output_dir=nonempty,
                asset_origin_base="https://example.test/assets",
                generated_at_utc="2026-08-21T00:00:00Z",
            )
        self.assertEqual((nonempty / "keep.txt").read_text(encoding="utf-8"), "do not overwrite")

    def test_failed_validation_does_not_materialize(self) -> None:
        output = self.materialization_root / "failed"
        with self.assertRaises(MaterializationError):
            materialize_release(
                RELEASE_ROOT,
                repo_root=REPO_ROOT,
                contig_registry=self.materialization_root / "missing-contigs.tsv",
                output_dir=output,
                asset_origin_base="https://example.test/assets",
                generated_at_utc="2026-08-21T00:00:00Z",
            )
        self.assertFalse(output.exists())
    def test_real_v02_release_is_happy_path_and_plan_is_deterministic(self) -> None:
        first = validate_release(RELEASE_ROOT)
        second = validate_release(RELEASE_ROOT)
        self.assertTrue(first.ok, [issue.as_dict() for issue in first.issues[:5]])
        self.assertEqual(first.plan, second.plan)
        self.assertEqual(first.summary["source_count"], 22)
        self.assertEqual(first.summary["published_standardized_sources"], 21)
        self.assertEqual(first.summary["audit_only_sources"], 1)
        self.assertEqual(first.summary["published_record_count"], 28_399)
        self.assertEqual(first.summary["augmentation_true"], 19)
        self.assertEqual(first.summary["augmentation_false"], 3)
        self.assertEqual(first.summary["publication_count"], 13)
        self.assertEqual(first.summary["assembly_count"], 20)
        self.assertEqual(first.summary["contig_count"], 47)
        self.assertEqual(first.summary["sample_count"], 21)
        self.assertEqual(first.summary["source_accession_count"], 32)
        self.assertEqual(first.summary["source_annotation_table_count"], 17)
        self.assertEqual(first.summary["source_annotation_record_count"], 24_887)
        self.assertEqual(first.plan["write_mode"], "not_written")
        self.assertEqual(first.plan["canonical_validation_status"], "validated")
        self.assertTrue(first.plan["postgresql_ready"])
        self.assertEqual(first.plan["unresolved"], [])
        self.assertEqual(len(first.plan["tables"]["contigs"]["rows"]), 47)
        self.assertTrue(
            all(
                row["length_bp"] > row["max_endpoint_position_1based"] > 0
                for row in first.plan["tables"]["contigs"]["rows"]
            )
        )
        self.assertEqual(first.plan["tables"]["import_runs"]["row_count"], 1)
        self.assertEqual(first.plan["tables"]["assets"]["row_count"], 127)
        self.assertTrue(
            all(
                {"asset_id", "logical_path", "source_id", "asset_kind", "sha256", "byte_size", "is_public"}
                <= set(asset)
                for asset in first.plan["tables"]["assets"]["keys"]
            )
        )
        self.assertTrue(
            all("/" not in asset["asset_id"] for asset in first.plan["tables"]["assets"]["keys"])
        )
        self.assertTrue(
            {
                asset["asset_kind"] for asset in first.plan["tables"]["assets"]["keys"]
            }
            <= {
                "fasta",
                "fai",
                "gff3",
                "tbi",
                "bigwig",
                "bed",
                "config",
                "metadata",
                "checksum",
                "archive",
            }
        )
        self.assertTrue(
            all(
                {"accession_namespace", "accession", "raw_value"} <= set(accession)
                for accession in first.plan["tables"]["source_accessions"]["keys"]
            )
        )
        self.assertTrue(
            all(
                accession["accession_namespace"] in {"GEO", "SRA", "ENA", "BioStudies"}
                for accession in first.plan["tables"]["source_accessions"]["keys"]
            )
        )
        self.assertEqual(first.plan["tables"]["genes"]["row_count"], 0)
        self.assertEqual(first.plan["tables"]["endpoint_gene_context"]["row_count"], 0)
        self.assertFalse(first.summary["unresolved"])

    def test_missing_reference_contig_registry_keeps_canonical_valid_but_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = validate_release(make_fixture(root), repo_root=root)
            self.assertTrue(report.ok)
            self.assertEqual(report.plan["canonical_validation_status"], "validated")
            self.assertFalse(report.plan["postgresql_ready"])
            self.assertTrue(any("reference contig registry missing" in item for item in report.plan["unresolved"]))
            self.assertIsNone(report.plan["tables"]["contigs"]["rows"][0]["length_bp"])

    def test_reference_contig_registry_length_equal_endpoint_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry_path = copy_reference_contig_registry(root / "reference_contigs.tsv")
            with registry_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            target = next(row for row in rows if row["assembly_accession"] == "GCF_000005845.1")
            target["length_bp"] = str(int(target["max_endpoint_position_1based"]))
            write_tsv(registry_path, REFERENCE_CONTIG_COLUMNS, rows)
            report = validate_release(RELEASE_ROOT, contig_registry=registry_path)
            self.assertTrue(report.ok, [issue.as_dict() for issue in report.issues[:3]])
            self.assertTrue(report.plan["postgresql_ready"])

    def test_reference_contig_registry_length_below_endpoint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry_path = copy_reference_contig_registry(root / "reference_contigs.tsv")
            with registry_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            target = next(row for row in rows if row["assembly_accession"] == "GCF_000005845.1")
            target["length_bp"] = str(int(target["max_endpoint_position_1based"]) - 1)
            write_tsv(registry_path, REFERENCE_CONTIG_COLUMNS, rows)
            report = validate_release(RELEASE_ROOT, contig_registry=registry_path)
            self.assertFalse(report.ok)
            self.assertTrue(
                any("length_bp" in issue.message and "endpoint" in issue.message for issue in report.issues)
            )

    def test_reference_contig_registry_requires_exact_endpoint_contig_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing_path = copy_reference_contig_registry(root / "missing.tsv")
            with missing_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            rows = [row for row in rows if not (row["assembly_accession"] == "GCF_000005845.1" and row["contig_accession"] == "NC_000913.2")]
            write_tsv(missing_path, REFERENCE_CONTIG_COLUMNS, rows)
            missing_report = validate_release(RELEASE_ROOT, contig_registry=missing_path)
            self.assertFalse(missing_report.ok)
            self.assertTrue(any("missing endpoint contig" in issue.message for issue in missing_report.issues))

            extra_path = copy_reference_contig_registry(root / "extra.tsv")
            with extra_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            extra = dict(rows[0])
            extra.update(
                {
                    "assembly_accession": "GCF_999999999.1",
                    "contig_accession": "NC_FAKE.1",
                    "length_bp": "2",
                    "max_endpoint_position_1based": "1",
                }
            )
            rows.append(extra)
            write_tsv(extra_path, REFERENCE_CONTIG_COLUMNS, rows)
            extra_report = validate_release(RELEASE_ROOT, contig_registry=extra_path)
            self.assertFalse(extra_report.ok)
            self.assertTrue(any("extra contig" in issue.message for issue in extra_report.issues))

    @unittest.skipUnless(JBROWSE_BUNDLE.is_dir(), "local v0.2 JBrowse bundle is not checked out")
    def test_reference_contig_builder_real_bundle_has_47_rows(self) -> None:
        provenance = build_reference_contig_registry(
            RELEASE_ROOT,
            JBROWSE_BUNDLE,
            generated_at_utc="2026-08-21T00:00:00Z",
        )
        self.assertEqual(provenance["source_count"], 21)
        self.assertEqual(provenance["contig_count"], 47)
        self.assertEqual(len(provenance["rows"]), 47)
        self.assertIn("BATTER_S1_007;BATTER_S1_013", {
            row["supporting_source_ids"] for row in provenance["rows"]
        })

    def test_reference_contig_builder_tiny_bundle_and_checksum_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            bundle = make_tiny_jbrowse_bundle(root, release_root)
            provenance = build_reference_contig_registry(
                release_root,
                bundle,
                generated_at_utc="2026-08-21T00:00:00Z",
            )
            self.assertEqual(provenance["contig_count"], 1)
            self.assertEqual(provenance["rows"][0]["length_bp"], "100000")

            short_bundle = make_tiny_jbrowse_bundle(
                root / "short",
                release_root,
                lengths=(1,),
            )
            with self.assertRaisesRegex(RegistryBuildError, "shorter than the maximum endpoint"):
                build_reference_contig_registry(release_root, short_bundle)

            bad_bundle = make_tiny_jbrowse_bundle(root / "bad", release_root, mutate_after_checksum=True)
            with self.assertRaises(RegistryBuildError):
                build_reference_contig_registry(release_root, bad_bundle)

    def test_reference_contig_builder_rejects_invalid_generated_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            bundle = make_tiny_jbrowse_bundle(root, release_root)
            for timestamp in (
                "2026-08-21T00:00:00",
                "2026-08-21T00:00:00+08:00",
                "not-a-timestamp",
            ):
                with self.subTest(timestamp=timestamp):
                    with self.assertRaisesRegex(RegistryBuildError, "generated_at_utc"):
                        build_reference_contig_registry(
                            release_root,
                            bundle,
                            generated_at_utc=timestamp,
                        )

    def test_reference_contig_builder_cli_accepts_fixed_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            bundle = make_tiny_jbrowse_bundle(root, release_root)
            output_tsv = root / "out/reference_contigs.tsv"
            output_json = root / "out/reference_contigs.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts/build_reference_contig_registry.py"),
                    "--release-root",
                    str(release_root),
                    "--jbrowse-bundle",
                    str(bundle),
                    "--output-tsv",
                    str(output_tsv),
                    "--output-json",
                    str(output_json),
                    "--generated-at-utc",
                    "2026-08-21T00:00:00Z",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(output_json.read_text(encoding="utf-8"))["generated_at_utc"], "2026-08-21T00:00:00Z")

    def test_reference_contig_builder_rejects_shared_contig_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_same_pmid_conflict_fixture(root)
            bundle = make_tiny_jbrowse_bundle(
                root,
                release_root,
                source_ids=("BATTER_S1_007", "BATTER_S1_013"),
                lengths=(100_000, 99_999),
            )
            with self.assertRaisesRegex(RegistryBuildError, "shared contig conflict"):
                build_reference_contig_registry(release_root, bundle)

    def test_coordinate_error_has_source_file_and_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            endpoint_path = release_root / "records/BATTER_S1_007/endpoints.tsv"
            lines = endpoint_path.read_text(encoding="utf-8").splitlines()
            fields = lines[0].split("\t")
            values = lines[1].split("\t")
            values[fields.index("bed_start_0based")] = str(int(values[fields.index("bed_start_0based")]) - 1)
            endpoint_path.write_text("\n".join([lines[0], "\t".join(values)]) + "\n", encoding="utf-8")
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(
                any(
                    issue.source_id == "BATTER_S1_007"
                    and issue.line == 2
                    and "坐标转换" in issue.message
                    for issue in report.issues
                )
            )

    def test_annotation_orphan_has_source_file_and_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            annotation_path = release_root / "records/BATTER_S1_007/source_annotations.tsv"
            lines = annotation_path.read_text(encoding="utf-8").splitlines()
            fields = lines[0].split("\t")
            values = lines[1].split("\t")
            values[fields.index("end_id")] = "BTED_BATTER_S1_007_ORPHAN"
            annotation_path.write_text("\n".join([lines[0], "\t".join(values)]) + "\n", encoding="utf-8")
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(any(issue.line == 2 and "annotation end_id" in issue.message for issue in report.issues))

    def test_audit_only_cannot_have_endpoint_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = validate_release(make_audit_fixture(root), repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(any(issue.source_id == "BATTER_S1_002" and "audit_only" in issue.message for issue in report.issues))

    def test_manifest_row_count_mismatch_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            release_path = release_root / "release_manifest.json"
            release = json.loads(release_path.read_text(encoding="utf-8"))
            release["summary"]["published_record_count"] = 2
            release["sources"]["BATTER_S1_007"]["record_count"] = 2
            release_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(any("record_count" in issue.message for issue in report.issues))

    def test_canonical_record_manifest_is_the_import_truth(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            manifest_path = release_root / "records/BATTER_S1_007/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["paper_title"] = "Tampered canonical title"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _refresh_release_file_hashes(release_root, "BATTER_S1_007")
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(
                any(
                    issue.source_id == "BATTER_S1_007"
                    and "来源 manifest paper_title 与 registry" in issue.message
                    and issue.file.endswith("records/BATTER_S1_007/manifest.json")
                    for issue in report.issues
                )
            )

    def test_required_file_must_be_declared(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            release_path = release_root / "release_manifest.json"
            release = json.loads(release_path.read_text(encoding="utf-8"))
            entry = release["sources"]["BATTER_S1_007"]
            entry["files"] = [item for item in entry["files"] if item["path"] != "fields.json"]
            release_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(any("未声明必要文件: fields.json" in issue.message for issue in report.issues))

    def test_required_file_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            (release_root / "records/BATTER_S1_007/fields.json").unlink()
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(any("声明的文件不存在: fields.json" in issue.message for issue in report.issues))

    def test_sha256sums_entry_must_match_actual_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            sums_path = release_root / "records/BATTER_S1_007/SHA256SUMS.txt"
            lines = sums_path.read_text(encoding="utf-8").splitlines()
            lines[0] = ("0" * 64) + lines[0][64:]
            sums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            _refresh_release_file_hashes(release_root, "BATTER_S1_007")
            # Refreshing would repair the mutation, so apply it after the
            # release entry has been refreshed and update only the checksum
            # file's release hash.
            lines = sums_path.read_text(encoding="utf-8").splitlines()
            lines[0] = ("0" * 64) + lines[0][64:]
            sums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            release_path = release_root / "release_manifest.json"
            release = json.loads(release_path.read_text(encoding="utf-8"))
            for item in release["sources"]["BATTER_S1_007"]["files"]:
                if item["path"] == "SHA256SUMS.txt":
                    item["sha256"] = digest(sums_path)
            release_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(any("SHA256SUMS 与实际文件不一致" in issue.message for issue in report.issues))

    def test_sha256sums_undeclared_entry_is_structured_issue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            sums_path = release_root / "records/BATTER_S1_007/SHA256SUMS.txt"
            with sums_path.open("a", encoding="utf-8") as handle:
                handle.write("" + ("0" * 64) + "  not-declared.tsv\n")
            release_path = release_root / "release_manifest.json"
            release = json.loads(release_path.read_text(encoding="utf-8"))
            for item in release["sources"]["BATTER_S1_007"]["files"]:
                if item["path"] == "SHA256SUMS.txt":
                    item["sha256"] = digest(sums_path)
            release_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(
                any(
                    issue.source_id == "BATTER_S1_007"
                    and issue.line == 1
                    and "条目未在 release manifest 声明" in issue.message
                    for issue in report.issues
                )
            )

    def test_release_version_must_be_semver(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            release_path = release_root / "release_manifest.json"
            release = json.loads(release_path.read_text(encoding="utf-8"))
            release["release_version"] = "v0.2"
            release_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(any("vMAJOR.MINOR.PATCH" in issue.message for issue in report.issues))

    def test_canonical_manifest_release_version_must_match_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            manifest_path = release_root / "records/BATTER_S1_007/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["release_version"] = "v9.9.9"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _refresh_release_file_hashes(release_root, "BATTER_S1_007")
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(any("release_version 与根 release 不一致" in issue.message for issue in report.issues))

    def test_registry_extra_source_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            extra = _source_row("BATTER_S1_013")
            _append_registry_row(root, extra)
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(any("registry source 未出现在 release manifest" in issue.message for issue in report.issues))

    def test_same_pmid_metadata_conflict_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_same_pmid_conflict_fixture(root)
            report = validate_release(release_root, repo_root=root)
            self.assertFalse(report.ok)
            self.assertTrue(any("相同 PMID" in issue.message for issue in report.issues))

    def test_cli_writes_plan_and_reports_asset_sections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = make_fixture(root)
            plan_path = root / "plan.json"
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts/import_bted_v03.py"),
                "validate",
                "--repo-root",
                str(root),
                "--release-root",
                str(release_root),
                "--plan-json",
                str(plan_path),
            ]
            completed = subprocess.run(command, check=False, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = json.loads(completed.stdout)
            saved_plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertTrue(output["ok"])
            self.assertEqual(saved_plan["tables"]["import_runs"]["row_count"], 1)
            self.assertGreater(saved_plan["tables"]["assets"]["row_count"], 0)


if __name__ == "__main__":
    unittest.main()
