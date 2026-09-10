"""Offline-verifiable PostgreSQL writer for a BTED v0.3 staging bundle.

This module is the first write-capable layer in the v0.3 pipeline.  It has no
database dependency at import time: psycopg3 is imported by the CLI only after
the caller has explicitly confirmed a write.  A bundle is fully verified and
its natural-key closure is checked before a transaction is opened.  The
writer never updates an existing release, uses one SERIALIZABLE transaction,
and keeps all values parameterized.

The functions in this module are intentionally usable with a small fake
connection in offline tests.  They do not download assets, infer biological
annotations, or alter the canonical release.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence
from urllib.parse import quote, urlparse

from .canonical import V02_ENDPOINT_COLUMNS, sha256_file
from .materialize import (
    MATERIALIZATION_SCHEMA_VERSION,
    MATERIALIZER_VERSION,
)


RELEASE_VERSION_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_TABLES = (
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
PUBLIC_ENDPOINT_EVIDENCE = {
    "observed_signal",
    "called_endpoint",
    "author_called_endpoint",
    "curated_record",
}
ANNOTATION_KINDS = {
    "experimental_measurement",
    "author_annotation",
    "prediction_annotation",
    "curation_metadata",
}
ASSET_KINDS = {
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
    "release_manifest",
    "other",
}
RELEASE_STATUSES = {"staged", "validated"}
SOURCE_STATUSES = {"published_standardized", "audit_only", "to_review", "blocked"}
REDISTRIBUTION_STATUSES = {
    "verified_redistributable",
    "external_link_only",
    "audit_only",
    "to_review",
}

# These are the physical columns from backend/database/schema.sql.  Identity
# columns and PostgreSQL defaults are deliberately absent from the B1 rows.
# The helper columns below are consumed by the writer and never passed to SQL.
TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "release_versions": (
        "release_version",
        "release_date",
        "canonical_manifest_path",
        "canonical_manifest_sha256",
        "status",
        "is_current",
        "created_at",
    ),
    "import_runs": (
        "release_version",
        "importer_name",
        "importer_version",
        "input_manifest_path",
        "input_manifest_sha256",
        "staging_location",
        "run_status",
        "started_at",
        "finished_at",
        "validation_summary",
        "error_summary",
        "committed_at",
    ),
    "publications": (
        "pmid",
        "doi",
        "pmc",
        "published_year",
        "journal",
        "paper_title",
        "citation_json",
    ),
    "assemblies": (
        "assembly_accession",
        "assembly_name",
        "organism_name",
        "strain",
        "taxon_id",
        "reference_url",
    ),
    "contigs": (
        "assembly_id",
        "contig_accession",
        "contig_name",
        "length_bp",
        "sequence_sha256",
    ),
    "sources": (
        "release_version",
        "source_id",
        "publication_id",
        "assembly_id",
        "species",
        "phylum",
        "assay_family",
        "release_status",
        "evidence_class",
        "redistribution_status",
        "accessibility_status",
        "coordinate_status",
        "processing_status",
        "used_for_batter_augmentation",
        "record_count",
        "has_jbrowse",
        "manifest_path",
        "manifest_sha256",
        "record_root",
        "source_note",
        "decision_note",
        "known_limitations",
    ),
    "source_accessions": (
        "source_pk",
        "accession_namespace",
        "accession",
        "raw_value",
        "accession_type",
        "ordinal",
        "external_url",
    ),
    "samples": (
        "source_pk",
        "sample_id",
        "sample_label",
        "biological_condition",
        "replicate_label",
        "sample_accession",
        "metadata_json",
    ),
    "endpoints": (
        "release_version",
        "source_pk",
        "contig_id",
        "sample_pk",
        *V02_ENDPOINT_COLUMNS,
    ),
    "source_annotations": (
        "release_version",
        "source_pk",
        "end_id",
        "annotation_kind",
        "source_record_id",
        "ordinal",
        "annotation_json",
        "provenance_json",
    ),
    "genes": (
        "release_version",
        "assembly_id",
        "contig_id",
        "gene_id",
        "locus_tag",
        "gene_name",
        "feature_type",
        "start_1based",
        "end_1based",
        "strand",
        "annotation_asset_id",
        "annotation_sha256",
        "attributes_json",
    ),
    "endpoint_gene_context": (
        "release_version",
        "endpoint_pk",
        "gene_pk",
        "relation_type",
        "distance_nt",
        "method",
        "algorithm_version",
        "context_json",
    ),
    "assets": (
        "asset_id",
        "release_version",
        "source_pk",
        "assembly_id",
        "asset_kind",
        "logical_path",
        "origin_url",
        "origin_host",
        "byte_size",
        "sha256",
        "mime_type",
        "supports_range",
        "redistribution_status",
        "is_public",
    ),
}

TABLE_HELPERS: dict[str, frozenset[str]] = {
    "release_versions": frozenset(),
    "import_runs": frozenset(),
    "publications": frozenset(),
    "assemblies": frozenset({"source_ids"}),
    "contigs": frozenset({"assembly_id_ref", "assembly_accession", "provenance_json"}),
    "sources": frozenset({"publication_id_ref", "assembly_id_ref"}),
    "source_accessions": frozenset({"source_id_ref"}),
    "samples": frozenset({"source_id_ref"}),
    "endpoints": frozenset({"source_id_ref", "source_pk_ref", "contig_id_ref", "sample_id_ref"}),
    "source_annotations": frozenset({"source_id_ref"}),
    "genes": frozenset({"assembly_id_ref", "contig_id_ref"}),
    "endpoint_gene_context": frozenset(),
    "assets": frozenset({"source_id_ref", "assembly_id_ref"}),
}

# B1 materialization emits all non-identity physical values except the
# database-generated foreign keys and import_run committed_at.  This explicit
# contract makes a missing/renamed field a hard error instead of a silent NULL.
TABLE_REQUIRED: dict[str, frozenset[str]] = {
    table: frozenset(columns) for table, columns in TABLE_COLUMNS.items()
}
TABLE_REQUIRED["import_runs"] = frozenset(TABLE_COLUMNS["import_runs"]) - {"committed_at"}
TABLE_REQUIRED["contigs"] = frozenset(TABLE_COLUMNS["contigs"]) - {"assembly_id"}
TABLE_REQUIRED["sources"] = frozenset(TABLE_COLUMNS["sources"]) - {"publication_id", "assembly_id"}
TABLE_REQUIRED["source_accessions"] = frozenset(TABLE_COLUMNS["source_accessions"]) - {"source_pk"}
TABLE_REQUIRED["samples"] = frozenset(TABLE_COLUMNS["samples"]) - {"source_pk"}
TABLE_REQUIRED["endpoints"] = frozenset(TABLE_COLUMNS["endpoints"]) - {
    "source_pk",
    "contig_id",
    "sample_pk",
}
TABLE_REQUIRED["source_annotations"] = frozenset(TABLE_COLUMNS["source_annotations"]) - {"source_pk"}
TABLE_REQUIRED["genes"] = frozenset(TABLE_COLUMNS["genes"]) - {"assembly_id", "contig_id"}
TABLE_REQUIRED["assets"] = frozenset(TABLE_COLUMNS["assets"]) - {"source_pk", "assembly_id"}

ADVISORY_LOCK_KEY = int.from_bytes(hashlib.sha256(b"BTED:v0.3:postgres-writer").digest()[:8], "big", signed=True)


class PostgresWriterError(RuntimeError):
    """A bundle or database precondition prevented a safe write."""


@dataclass(frozen=True)
class BundleVerification:
    bundle_dir: Path
    manifest: dict[str, Any]
    table_files: dict[str, Path]
    table_metadata: dict[str, dict[str, Any]]

    @property
    def release_version(self) -> str:
        return str(self.manifest["release_version"])

    @property
    def table_counts(self) -> dict[str, int]:
        return {
            table: int(meta["row_count"])
            for table, meta in self.table_metadata.items()
        }


@dataclass
class PreflightState:
    """Small natural-key index built without retaining large JSONL rows."""

    release_version: str
    release_row: dict[str, Any]
    import_run_row: dict[str, Any]
    publications: dict[str, dict[str, Any]]
    assemblies: dict[str, dict[str, Any]]
    contigs: dict[tuple[str, str], dict[str, Any]]
    sources: dict[str, dict[str, Any]]
    accessions: list[dict[str, Any]]
    samples: dict[tuple[str, str], dict[str, Any]]
    endpoint_keys: set[tuple[str, str]]
    endpoint_counts: Counter[str]
    annotation_keys: set[tuple[str, str, str, str, int]]
    annotation_counts: Counter[str]
    genes: dict[tuple[str, str, str], dict[str, Any]]
    assets: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class LoadResult:
    release_version: str
    run_id: int
    status: str
    counts: dict[str, int]


def _json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise PostgresWriterError(f"cannot parse bundle metadata: {path.name}") from exc
    if not isinstance(value, dict):
        raise PostgresWriterError(f"bundle metadata must be an object: {path.name}")
    return value


def _sha256_and_size(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        raise PostgresWriterError(f"cannot open bundle table: {path.name}") from exc
    with handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                raise PostgresWriterError(f"blank JSONL line: {path.name}:{number}")
            try:
                value = json.loads(line, parse_constant=_reject_nonfinite)
            except (json.JSONDecodeError, ValueError) as exc:
                raise PostgresWriterError(f"invalid JSONL: {path.name}:{number}") from exc
            if not isinstance(value, dict):
                raise PostgresWriterError(f"JSONL row must be object: {path.name}:{number}")
            yield value


def _checksum_entries(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise PostgresWriterError("cannot read bundle SHA256SUMS.txt") from exc
    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or not SHA256_RE.fullmatch(parts[0]):
            raise PostgresWriterError(f"invalid SHA256SUMS.txt line {number}")
        name = parts[1].lstrip("*")
        if not name or Path(name).name != name or name in entries:
            raise PostgresWriterError(f"invalid or duplicate checksum path: {name!r}")
        entries[name] = parts[0]
    return entries


def verify_bundle(bundle_dir: str | Path) -> BundleVerification:
    """Verify a B1 bundle without opening a database or retaining JSONL rows."""

    root = Path(bundle_dir).expanduser().resolve()
    if not root.is_dir():
        raise PostgresWriterError(f"bundle directory does not exist: {root}")
    manifest_path = root / "manifest.json"
    sums_path = root / "SHA256SUMS.txt"
    if not manifest_path.is_file() or not sums_path.is_file():
        raise PostgresWriterError("bundle must contain manifest.json and SHA256SUMS.txt")
    manifest = _json_object(manifest_path)
    release_version = str(manifest.get("release_version", ""))
    if not RELEASE_VERSION_RE.fullmatch(release_version):
        raise PostgresWriterError("bundle release_version is not semver vMAJOR.MINOR.PATCH")
    if manifest.get("materialization_schema_version") != MATERIALIZATION_SCHEMA_VERSION:
        raise PostgresWriterError("unsupported materialization schema version")
    if not str(manifest.get("materializer_version", "")).startswith("bted-materializer-"):
        raise PostgresWriterError("bundle materializer version is missing or invalid")
    if manifest.get("canonical_validation_status") != "validated":
        raise PostgresWriterError("bundle canonical_validation_status is not validated")
    if manifest.get("postgresql_ready") is not True:
        raise PostgresWriterError("bundle is not marked postgresql_ready")
    if manifest.get("write_mode") != "not_written":
        raise PostgresWriterError("bundle write_mode must be not_written")
    if manifest.get("unresolved") not in ([], None):
        raise PostgresWriterError("bundle contains unresolved items")
    origin = manifest.get("asset_origin")
    if not isinstance(origin, Mapping) or origin.get("asset_origin_status") not in {
        "planned_not_verified",
        "verified",
    }:
        raise PostgresWriterError("bundle asset_origin_status is missing or invalid")
    origin_base = str(origin.get("base", "")).rstrip("/")
    parsed_base = urlparse(origin_base)
    if parsed_base.scheme != "https" or not parsed_base.hostname:
        raise PostgresWriterError("bundle asset origin base must be HTTPS")
    if str(origin.get("host", "")) != parsed_base.hostname:
        raise PostgresWriterError("bundle asset origin host does not match base")
    tables = manifest.get("tables")
    if not isinstance(tables, Mapping) or set(tables) != set(EXPECTED_TABLES):
        raise PostgresWriterError("bundle table set does not match the PostgreSQL contract")

    table_files: dict[str, Path] = {}
    table_metadata: dict[str, dict[str, Any]] = {}
    expected_names = {"manifest.json", "SHA256SUMS.txt"}
    for table in EXPECTED_TABLES:
        meta = tables.get(table)
        if not isinstance(meta, Mapping):
            raise PostgresWriterError(f"table metadata is not an object: {table}")
        file_name = str(meta.get("file", ""))
        if not file_name or Path(file_name).name != file_name or not file_name.endswith(".jsonl"):
            raise PostgresWriterError(f"invalid table file name: {table}")
        if not isinstance(meta.get("row_count"), int) or int(meta["row_count"]) < 0:
            raise PostgresWriterError(f"invalid row_count: {table}")
        if (
            not isinstance(meta.get("byte_size"), int)
            or isinstance(meta.get("byte_size"), bool)
            or int(meta["byte_size"]) < 0
        ):
            raise PostgresWriterError(f"invalid byte_size: {table}")
        if not SHA256_RE.fullmatch(str(meta.get("sha256", ""))):
            raise PostgresWriterError(f"invalid table SHA-256: {table}")
        path = root / file_name
        if not path.is_file():
            raise PostgresWriterError(f"missing table file: {file_name}")
        if file_name in expected_names:
            raise PostgresWriterError(f"duplicate bundle file: {file_name}")
        expected_names.add(file_name)
        table_files[table] = path
        table_metadata[table] = dict(meta)

    entries = list(root.iterdir())
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise PostgresWriterError("bundle root contains a directory or symbolic link")
    actual_names = {path.name for path in entries}
    if actual_names != expected_names:
        extra = sorted(actual_names - expected_names)
        missing = sorted(expected_names - actual_names)
        raise PostgresWriterError(f"bundle file set mismatch; extra={extra}, missing={missing}")
    sums = _checksum_entries(sums_path)
    expected_checksum_names = expected_names - {"SHA256SUMS.txt"}
    if set(sums) != expected_checksum_names:
        extra = sorted(set(sums) - expected_checksum_names)
        missing = sorted(expected_checksum_names - set(sums))
        raise PostgresWriterError(f"bundle checksum file set mismatch; extra={extra}, missing={missing}")
    for name in sorted(expected_checksum_names):
        actual, byte_size = _sha256_and_size(root / name)
        if actual != sums[name]:
            raise PostgresWriterError(f"bundle checksum mismatch: {name}")
        if name == "manifest.json":
            continue
        table = next(table for table, path in table_files.items() if path.name == name)
        meta = table_metadata[table]
        if actual != str(meta["sha256"]) or byte_size != int(meta["byte_size"]):
            raise PostgresWriterError(f"table checksum/byte_size metadata mismatch: {table}")
        count = 0
        for _ in _iter_jsonl(root / name):
            count += 1
        if count != int(meta["row_count"]):
            raise PostgresWriterError(
                f"table row_count mismatch: {table} ({count} != {meta['row_count']})"
            )
    # Release-level counters are part of the B1 manifest and must agree with
    # the table metadata before any SQL is attempted.
    source_count = manifest.get("source_count")
    annotation_count = manifest.get("source_annotation_materialized_row_count")
    if (
        isinstance(source_count, bool)
        or not isinstance(source_count, int)
        or source_count != int(table_metadata["sources"]["row_count"])
    ):
        raise PostgresWriterError("manifest source_count does not match sources table")
    if (
        isinstance(annotation_count, bool)
        or not isinstance(annotation_count, int)
        or annotation_count != int(table_metadata["source_annotations"]["row_count"])
    ):
        raise PostgresWriterError("manifest source annotation count does not match table")
    gene_count = manifest.get("gene_count", 0)
    context_count = manifest.get("endpoint_gene_context_count", 0)
    contig_count = manifest.get("contig_count", int(table_metadata["contigs"]["row_count"]))
    if (
        isinstance(contig_count, bool)
        or not isinstance(contig_count, int)
        or contig_count != int(table_metadata["contigs"]["row_count"])
    ):
        raise PostgresWriterError("manifest contig count does not match contigs table")
    if (
        isinstance(gene_count, bool)
        or not isinstance(gene_count, int)
        or gene_count != int(table_metadata["genes"]["row_count"])
    ):
        raise PostgresWriterError("manifest gene count does not match genes table")
    if (
        isinstance(context_count, bool)
        or not isinstance(context_count, int)
        or context_count != int(table_metadata["endpoint_gene_context"]["row_count"])
    ):
        raise PostgresWriterError("manifest endpoint_gene_context count does not match table")
    return BundleVerification(root, manifest, table_files, table_metadata)


def _require_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PostgresWriterError(f"{context} must be an object")
    return value


def _validate_row_shape(table: str, row: Mapping[str, Any], number: int) -> None:
    allowed = set(TABLE_COLUMNS[table]) | set(TABLE_HELPERS[table])
    unknown = sorted(set(row) - allowed)
    if unknown:
        raise PostgresWriterError(f"{table}:{number} has unknown fields: {unknown}")
    missing = sorted(TABLE_REQUIRED[table] - set(row))
    if missing:
        raise PostgresWriterError(f"{table}:{number} is missing fields: {missing}")


def _bool(value: Any, context: str) -> bool:
    if isinstance(value, bool):
        return value
    raise PostgresWriterError(f"{context} must be boolean")


def _int(value: Any, context: str) -> int:
    if isinstance(value, bool):
        raise PostgresWriterError(f"{context} must be integer")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise PostgresWriterError(f"{context} must be integer") from exc


def _json_value(value: Any, context: str) -> str:
    if not isinstance(value, (dict, list)):
        raise PostgresWriterError(f"{context} must be JSON object/array")
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PostgresWriterError(f"{context} is not JSON serializable") from exc


def _iter_table(verification: BundleVerification, table: str) -> Iterator[dict[str, Any]]:
    for number, row in enumerate(_iter_jsonl(verification.table_files[table]), start=1):
        _validate_row_shape(table, row, number)
        yield row


def _preflight(verification: BundleVerification) -> PreflightState:
    release_version = verification.release_version
    release_rows = list(_iter_table(verification, "release_versions"))
    import_rows = list(_iter_table(verification, "import_runs"))
    if len(release_rows) != 1 or len(import_rows) != 1:
        raise PostgresWriterError("bundle must contain exactly one release_versions and import_runs row")
    release_row = release_rows[0]
    import_row = import_rows[0]
    if release_row["release_version"] != release_version or import_row["release_version"] != release_version:
        raise PostgresWriterError("release/version mismatch in release_versions or import_runs")
    if release_row["status"] not in RELEASE_STATUSES or _bool(release_row["is_current"], "release_versions.is_current"):
        raise PostgresWriterError("load bundle must be staged/validated and not current")
    if import_row["run_status"] not in {"validated", "staging"}:
        raise PostgresWriterError("load bundle import_run must be validated/staging")
    if not isinstance(import_row["validation_summary"], Mapping):
        raise PostgresWriterError("import_run validation_summary must be an object")

    publications: dict[str, dict[str, Any]] = {}
    for number, row in enumerate(_iter_table(verification, "publications"), start=1):
        pmid = str(row["pmid"])
        if pmid in publications:
            raise PostgresWriterError(f"duplicate publication PMID: {pmid}")
        publications[pmid] = row

    assemblies: dict[str, dict[str, Any]] = {}
    for number, row in enumerate(_iter_table(verification, "assemblies"), start=1):
        accession = str(row["assembly_accession"])
        if accession in assemblies:
            raise PostgresWriterError(f"duplicate assembly accession: {accession}")
        source_ids = row.get("source_ids")
        if not isinstance(source_ids, list) or source_ids != sorted(set(source_ids)):
            raise PostgresWriterError(f"assemblies:{number} source_ids must be sorted and unique")
        assemblies[accession] = row

    contigs: dict[tuple[str, str], dict[str, Any]] = {}
    for number, row in enumerate(_iter_table(verification, "contigs"), start=1):
        assembly = str(row["assembly_accession"])
        contig = str(row["contig_accession"])
        if row["assembly_id_ref"] != assembly:
            raise PostgresWriterError(f"contigs:{number} assembly_id_ref mismatch")
        if assembly not in assemblies:
            raise PostgresWriterError(f"contigs:{number} references unknown assembly: {assembly}")
        _require_mapping(row["provenance_json"], f"contigs:{number}.provenance_json")
        key = (assembly, contig)
        if key in contigs:
            raise PostgresWriterError(f"duplicate contig: {assembly}/{contig}")
        if _int(row["length_bp"], f"contigs:{number}.length_bp") <= 0:
            raise PostgresWriterError(f"contigs:{number} length_bp must be positive")
        contigs[key] = row

    sources: dict[str, dict[str, Any]] = {}
    for number, row in enumerate(_iter_table(verification, "sources"), start=1):
        source_id = str(row["source_id"])
        if source_id in sources:
            raise PostgresWriterError(f"duplicate source_id: {source_id}")
        if row["release_version"] != release_version:
            raise PostgresWriterError(f"sources:{number} release_version mismatch")
        if str(row["publication_id_ref"]) not in publications:
            raise PostgresWriterError(f"sources:{number} unknown publication PMID")
        if str(row["assembly_id_ref"]) not in assemblies:
            raise PostgresWriterError(f"sources:{number} unknown assembly accession")
        if row["release_status"] not in SOURCE_STATUSES:
            raise PostgresWriterError(f"sources:{number} invalid release_status")
        if row["evidence_class"] not in {
            "observed_signal",
            "called_endpoint",
            "author_called_endpoint",
            "curated_record",
            "author_integrated_mixed_evidence",
            "prediction_only",
            "NA",
        }:
            raise PostgresWriterError(f"sources:{number} invalid evidence_class")
        if row["redistribution_status"] not in REDISTRIBUTION_STATUSES:
            raise PostgresWriterError(f"sources:{number} invalid redistribution_status")
        record_count = _int(row["record_count"], f"sources:{number}.record_count")
        if record_count < 0:
            raise PostgresWriterError(f"sources:{number} record_count must be non-negative")
        _bool(row["used_for_batter_augmentation"], f"sources:{number}.used_for_batter_augmentation")
        has_jbrowse = _bool(row["has_jbrowse"], f"sources:{number}.has_jbrowse")
        evidence_class = str(row["evidence_class"])
        release_status = str(row["release_status"])
        if release_status == "published_standardized":
            if record_count <= 0 or evidence_class not in PUBLIC_ENDPOINT_EVIDENCE:
                raise PostgresWriterError(
                    f"sources:{number} published_standardized public-state combination is invalid"
                )
        elif release_status == "audit_only":
            if record_count != 0 or has_jbrowse or evidence_class != "NA":
                raise PostgresWriterError(
                    f"sources:{number} audit_only public-state combination is invalid"
                )
        elif release_status in {"to_review", "blocked"}:
            if record_count != 0 or has_jbrowse:
                raise PostgresWriterError(
                    f"sources:{number} {release_status} public-state combination is invalid"
                )
        sources[source_id] = row

    accessions: list[dict[str, Any]] = []
    accession_keys: set[tuple[str, str, str]] = set()
    for number, row in enumerate(_iter_table(verification, "source_accessions"), start=1):
        source_id = str(row["source_id_ref"])
        if source_id not in sources:
            raise PostgresWriterError(f"source_accessions:{number} unknown source")
        if row["ordinal"] is not None:
            ordinal = _int(row["ordinal"], f"source_accessions:{number}.ordinal")
            if ordinal <= 0:
                raise PostgresWriterError(f"source_accessions:{number} ordinal must be positive")
        key = (source_id, str(row["accession_namespace"]), str(row["accession"]))
        if key in accession_keys:
            raise PostgresWriterError(f"duplicate source accession: {key}")
        accession_keys.add(key)
        accessions.append(row)

    samples: dict[tuple[str, str], dict[str, Any]] = {}
    for number, row in enumerate(_iter_table(verification, "samples"), start=1):
        source_id = str(row["source_id_ref"])
        sample_id = str(row["sample_id"])
        if source_id not in sources:
            raise PostgresWriterError(f"samples:{number} unknown source")
        key = (source_id, sample_id)
        if key in samples:
            raise PostgresWriterError(f"duplicate sample: {key}")
        _require_mapping(row["metadata_json"], f"samples:{number}.metadata_json")
        samples[key] = row

    endpoint_keys: set[tuple[str, str]] = set()
    endpoint_counts: Counter[str] = Counter()
    endpoint_contigs: set[tuple[str, str]] = set()
    endpoint_samples: set[tuple[str, str]] = set()
    for number, row in enumerate(_iter_table(verification, "endpoints"), start=1):
        source_id = str(row["source_id"])
        if row["source_id_ref"] != source_id or row["source_pk_ref"] != source_id:
            raise PostgresWriterError(f"endpoints:{number} source helper mismatch")
        if source_id not in sources:
            raise PostgresWriterError(f"endpoints:{number} unknown source")
        if sources[source_id]["release_status"] != "published_standardized":
            raise PostgresWriterError(
                f"endpoints:{number} non-published source cannot have endpoint rows"
            )
        if row["release_version"] != release_version:
            raise PostgresWriterError(f"endpoints:{number} release_version mismatch")
        if row["evidence_class"] not in PUBLIC_ENDPOINT_EVIDENCE:
            raise PostgresWriterError(f"endpoints:{number} invalid public evidence_class")
        contig_ref = _require_mapping(row["contig_id_ref"], f"endpoints:{number}.contig_id_ref")
        if set(contig_ref) != {"assembly_accession", "contig_accession"}:
            raise PostgresWriterError(f"endpoints:{number} contig_id_ref keys mismatch")
        contig_key = (str(contig_ref["assembly_accession"]), str(contig_ref["contig_accession"]))
        if contig_key not in contigs:
            raise PostgresWriterError(f"endpoints:{number} unknown contig")
        if contig_key[0] != str(sources[source_id]["assembly_id_ref"]):
            raise PostgresWriterError(f"endpoints:{number} contig assembly/source assembly mismatch")
        if row["reference_assembly"] != contig_key[0] or row["reference_name"] != contig_key[1]:
            raise PostgresWriterError(f"endpoints:{number} contig/reference mismatch")
        sample_ref = _require_mapping(row["sample_id_ref"], f"endpoints:{number}.sample_id_ref")
        if set(sample_ref) != {"source_id", "sample_id"}:
            raise PostgresWriterError(f"endpoints:{number} sample_id_ref keys mismatch")
        sample_key = (str(sample_ref["source_id"]), str(sample_ref["sample_id"]))
        if sample_key not in samples or sample_key[0] != source_id or row["sample_id"] != sample_key[1]:
            raise PostgresWriterError(f"endpoints:{number} sample helper mismatch")
        endpoint_key = (source_id, str(row["end_id"]))
        if endpoint_key in endpoint_keys:
            raise PostgresWriterError(f"duplicate endpoint natural key: {endpoint_key}")
        endpoint_keys.add(endpoint_key)
        endpoint_counts[source_id] += 1
        endpoint_contigs.add(contig_key)
        endpoint_samples.add(sample_key)
        position = _int(row["biological_coordinate_1based"], f"endpoints:{number}.position")
        if position < 1:
            raise PostgresWriterError(f"endpoints:{number} biological coordinate must be >= 1")
        contig_length = _int(contigs[contig_key]["length_bp"], f"contig {contig_key}.length_bp")
        if position > contig_length:
            raise PostgresWriterError(
                f"endpoints:{number} position exceeds contig length ({position} > {contig_length})"
            )
        if _int(row["bed_start_0based"], f"endpoints:{number}.bed_start") != position - 1:
            raise PostgresWriterError(f"endpoints:{number} BED start mismatch")
        if _int(row["bed_end_0based"], f"endpoints:{number}.bed_end") != position:
            raise PostgresWriterError(f"endpoints:{number} BED end mismatch")
        if row["strand"] not in {"+", "-"}:
            raise PostgresWriterError(f"endpoints:{number} invalid strand")

    annotation_keys: set[tuple[str, str, str, str, int]] = set()
    annotation_counts: Counter[str] = Counter()
    for number, row in enumerate(_iter_table(verification, "source_annotations"), start=1):
        source_id = str(row["source_id_ref"])
        endpoint_key = (source_id, str(row["end_id"]))
        if source_id not in sources or endpoint_key not in endpoint_keys:
            raise PostgresWriterError(f"source_annotations:{number} endpoint foreign key missing")
        if row["release_version"] != release_version or row["annotation_kind"] not in ANNOTATION_KINDS:
            raise PostgresWriterError(f"source_annotations:{number} release/evidence value invalid")
        _require_mapping(row["annotation_json"], f"source_annotations:{number}.annotation_json")
        _require_mapping(row["provenance_json"], f"source_annotations:{number}.provenance_json")
        key = (
            source_id,
            str(row["end_id"]),
            str(row["annotation_kind"]),
            str(row["source_record_id"]),
            _int(row["ordinal"], f"source_annotations:{number}.ordinal"),
        )
        if key[-1] <= 0:
            raise PostgresWriterError(f"source_annotations:{number} ordinal must be positive")
        if key in annotation_keys:
            raise PostgresWriterError(f"duplicate annotation natural key: {key}")
        annotation_keys.add(key)
        annotation_counts[source_id] += 1

    assets: dict[str, dict[str, Any]] = {}
    for number, row in enumerate(_iter_table(verification, "assets"), start=1):
        asset_id = str(row["asset_id"])
        if asset_id in assets:
            raise PostgresWriterError(f"duplicate asset_id: {asset_id}")
        if row["release_version"] != release_version or row["asset_kind"] not in ASSET_KINDS:
            raise PostgresWriterError(f"assets:{number} release/asset_kind invalid")
        source_id = row.get("source_id_ref")
        if source_id is not None and source_id != "" and str(source_id) not in sources:
            raise PostgresWriterError(f"assets:{number} unknown source")
        assembly_id = row.get("assembly_id_ref")
        if assembly_id is not None and assembly_id != "" and str(assembly_id) not in assemblies:
            raise PostgresWriterError(f"assets:{number} unknown assembly")
        if not SHA256_RE.fullmatch(str(row["sha256"])):
            raise PostgresWriterError(f"assets:{number} invalid sha256")
        byte_size = _int(row["byte_size"], f"assets:{number}.byte_size")
        if byte_size < 0:
            raise PostgresWriterError(f"assets:{number} byte_size must be non-negative")
        supports_range = _bool(row["supports_range"], f"assets:{number}.supports_range")
        _bool(row["is_public"], f"assets:{number}.is_public")
        if row["redistribution_status"] not in REDISTRIBUTION_STATUSES:
            raise PostgresWriterError(f"assets:{number} invalid redistribution_status")
        parsed_origin = urlparse(str(row["origin_url"]))
        if parsed_origin.scheme != "https" or not parsed_origin.hostname:
            raise PostgresWriterError(f"assets:{number} origin_url must be HTTPS")
        if str(row["origin_host"]) != parsed_origin.hostname:
            raise PostgresWriterError(f"assets:{number} origin_host does not match origin_url")
        expected_origin = (
            f"{str(verification.manifest['asset_origin']['base']).rstrip('/')}"
            f"/{quote(str(row['logical_path']), safe='/-._~')}"
        )
        if str(row["origin_url"]) != expected_origin:
            raise PostgresWriterError(
                f"assets:{number} origin_url does not match logical_path"
            )
        if verification.manifest["asset_origin"]["asset_origin_status"] == "planned_not_verified" and supports_range:
            raise PostgresWriterError(
                f"assets:{number} cannot claim supports_range before remote HTTP 206 audit"
            )
        assets[asset_id] = row

    genes: dict[tuple[str, str, str], dict[str, Any]] = {}
    gene_contigs: set[tuple[str, str]] = set()
    seen_gene_ids: set[str] = set()
    for number, row in enumerate(_iter_table(verification, "genes"), start=1):
        if row["release_version"] != release_version:
            raise PostgresWriterError(f"genes:{number} release_version mismatch")
        assembly = str(row["assembly_id_ref"])
        if assembly not in assemblies:
            raise PostgresWriterError(f"genes:{number} unknown assembly")
        contig_ref = _require_mapping(row["contig_id_ref"], f"genes:{number}.contig_id_ref")
        if set(contig_ref) != {"assembly_accession", "contig_accession"}:
            raise PostgresWriterError(f"genes:{number} contig_id_ref keys mismatch")
        contig_key = (
            str(contig_ref["assembly_accession"]),
            str(contig_ref["contig_accession"]),
        )
        if contig_key not in contigs:
            raise PostgresWriterError(f"genes:{number} unknown contig")
        if contig_key[0] != assembly:
            raise PostgresWriterError(f"genes:{number} assembly/contig mismatch")
        attributes = _require_mapping(row["attributes_json"], f"genes:{number}.attributes_json")
        original_id = str(attributes.get("ID", "")).strip()
        gene_id = str(row["gene_id"])
        if not original_id or gene_id != f"{assembly}:{original_id}":
            raise PostgresWriterError(f"genes:{number} gene_id is not stable assembly:original-ID")
        if gene_id in seen_gene_ids:
            raise PostgresWriterError(f"duplicate global gene_id: {gene_id}")
        seen_gene_ids.add(gene_id)
        if str(row["feature_type"]) != "gene":
            raise PostgresWriterError(f"genes:{number} feature_type must be gene")
        start = _int(row["start_1based"], f"genes:{number}.start_1based")
        end = _int(row["end_1based"], f"genes:{number}.end_1based")
        if start < 1 or end < start:
            raise PostgresWriterError(f"genes:{number} coordinates are outside contig")
        if row["strand"] not in {"+", "-"}:
            raise PostgresWriterError(f"genes:{number} invalid strand")
        annotation_asset_id = str(row["annotation_asset_id"])
        annotation_asset = assets.get(annotation_asset_id)
        if annotation_asset is None:
            raise PostgresWriterError(f"genes:{number} annotation asset is not registered")
        if annotation_asset["asset_kind"] != "gff3":
            raise PostgresWriterError(f"genes:{number} annotation asset must be gff3")
        annotation_sha = str(row["annotation_sha256"])
        if not SHA256_RE.fullmatch(annotation_sha):
            raise PostgresWriterError(f"genes:{number} invalid annotation_sha256")
        if annotation_sha != str(annotation_asset["sha256"]):
            raise PostgresWriterError(f"genes:{number} annotation checksum mismatch")
        key = (assembly, contig_key[1], gene_id)
        if key in genes:
            raise PostgresWriterError(f"duplicate gene natural key: {key}")
        genes[key] = row
        gene_contigs.add(contig_key)

    for source_id, source in sources.items():
        if source["release_status"] != "published_standardized" and endpoint_counts[source_id]:
            raise PostgresWriterError(f"non-published source has endpoint rows: {source_id}")
        if endpoint_counts[source_id] != _int(source["record_count"], f"source {source_id}.record_count"):
            raise PostgresWriterError(f"endpoint count does not match source record_count: {source_id}")
        expected_assembly_sources = sorted(
            sid for sid, row in sources.items() if str(row["assembly_id_ref"]) == str(source["assembly_id_ref"])
        )
        assembly_sources = assemblies[str(source["assembly_id_ref"])]["source_ids"]
        if assembly_sources != expected_assembly_sources:
            raise PostgresWriterError(f"assembly source_ids closure failed: {source['assembly_id_ref']}")
    if not endpoint_contigs.issubset(set(contigs)):
        raise PostgresWriterError("endpoint contig references contain unknown contigs")
    if set(contigs) != endpoint_contigs | gene_contigs:
        raise PostgresWriterError("contig natural-key closure does not match endpoint/gene references")
    if endpoint_samples != set(samples):
        raise PostgresWriterError("sample natural-key closure does not match endpoint references")
    for source_id, sample_id in samples:
        if sources[source_id]["release_status"] != "published_standardized":
            raise PostgresWriterError(f"non-published source has sample rows: {source_id}/{sample_id}")
    if "BATTER_S1_002" in sources:
        if endpoint_counts["BATTER_S1_002"] or annotation_counts["BATTER_S1_002"]:
            raise PostgresWriterError("BATTER_S1_002 audit_only row boundary violated")
    if any(_iter_table(verification, "endpoint_gene_context")):
        raise PostgresWriterError("endpoint_gene_context must be empty for this B1 release")
    return PreflightState(
        release_version,
        release_row,
        import_row,
        publications,
        assemblies,
        contigs,
        sources,
        accessions,
        samples,
        endpoint_keys,
        endpoint_counts,
        annotation_keys,
        annotation_counts,
        genes,
        assets,
    )


@contextmanager
def _cursor(connection: Any) -> Iterator[Any]:
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        close = getattr(cursor, "close", None)
        if callable(close):
            close()


@contextmanager
def _transaction(connection: Any) -> Iterator[None]:
    transaction_factory = getattr(connection, "transaction", None)
    if not callable(transaction_factory):
        raise PostgresWriterError("connection does not provide a transaction() context")
    transaction = transaction_factory()
    try:
        with transaction:
            yield
    except Exception:
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            rollback()
        raise


def _begin_guards(cursor: Any) -> None:
    cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
    cursor.execute("SELECT pg_advisory_xact_lock(%s)", (ADVISORY_LOCK_KEY,))


def _one(cursor: Any, sql: str, params: Sequence[Any]) -> Any:
    cursor.execute(sql, tuple(params))
    row = cursor.fetchone()
    return row


def _rows(cursor: Any, sql: str, params: Sequence[Any]) -> list[Any]:
    cursor.execute(sql, tuple(params))
    return list(cursor.fetchall())


def _row_value(row: Any, index: int, key: str | None = None) -> Any:
    if row is None:
        return None
    if key is not None and isinstance(row, Mapping):
        return row[key]
    return row[index]


def _insert_returning(cursor: Any, sql: str, params: Sequence[Any], context: str) -> int:
    row = _one(cursor, sql, params)
    if row is None:
        raise PostgresWriterError(f"database did not return identity for {context}")
    return int(_row_value(row, 0))


def _compare_existing(table: str, incoming: Mapping[str, Any], existing: Mapping[str, Any], fields: Sequence[str]) -> None:
    for field in fields:
        if existing.get(field) != incoming.get(field):
            raise PostgresWriterError(f"existing {table} natural key is incompatible: {field}")


def _load_publications(cursor: Any, state: PreflightState) -> dict[str, int]:
    ids: dict[str, int] = {}
    fields = ("pmid", "doi", "pmc", "published_year", "journal", "paper_title", "citation_json")
    for pmid, row in sorted(state.publications.items()):
        existing = _one(
            cursor,
            "SELECT publication_id, pmid, doi, pmc, published_year, journal, paper_title, citation_json FROM publications WHERE pmid = %s",
            (pmid,),
        )
        incoming = dict(row)
        if existing is not None:
            existing_map = {
                field: _row_value(existing, index)
                for index, field in enumerate(("publication_id", *fields))
            }
            _compare_existing("publications", incoming, existing_map, fields)
            ids[pmid] = int(existing_map["publication_id"])
            continue
        params = [incoming[field] for field in fields[:-1]] + [_json_value(incoming[fields[-1]], f"publication {pmid}.citation_json")]
        ids[pmid] = _insert_returning(
            cursor,
            "INSERT INTO publications (pmid, doi, pmc, published_year, journal, paper_title, citation_json) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb) RETURNING publication_id",
            params,
            f"publication {pmid}",
        )
    return ids


def _load_assemblies(cursor: Any, state: PreflightState) -> dict[str, int]:
    ids: dict[str, int] = {}
    fields = ("assembly_accession", "assembly_name", "organism_name", "strain", "taxon_id", "reference_url")
    for accession, row in sorted(state.assemblies.items()):
        existing = _one(
            cursor,
            "SELECT assembly_id, assembly_accession, assembly_name, organism_name, strain, taxon_id, reference_url FROM assemblies WHERE assembly_accession = %s",
            (accession,),
        )
        if existing is not None:
            existing_map = {
                field: _row_value(existing, index)
                for index, field in enumerate(("assembly_id", *fields))
            }
            _compare_existing("assemblies", row, existing_map, fields)
            ids[accession] = int(existing_map["assembly_id"])
            continue
        ids[accession] = _insert_returning(
            cursor,
            "INSERT INTO assemblies (assembly_accession, assembly_name, organism_name, strain, taxon_id, reference_url) VALUES (%s, %s, %s, %s, %s, %s) RETURNING assembly_id",
            [row[field] for field in fields],
            f"assembly {accession}",
        )
    return ids


def _load_contigs(cursor: Any, state: PreflightState, assembly_ids: Mapping[str, int]) -> dict[tuple[str, str], int]:
    ids: dict[tuple[str, str], int] = {}
    for (assembly, accession), row in sorted(state.contigs.items()):
        assembly_id = assembly_ids[assembly]
        existing = _one(
            cursor,
            "SELECT contig_id, assembly_id, contig_accession, contig_name, length_bp, sequence_sha256 FROM contigs WHERE assembly_id = %s AND contig_accession = %s",
            (assembly_id, accession),
        )
        fields = ("assembly_id", "contig_accession", "contig_name", "length_bp", "sequence_sha256")
        incoming = {
            "assembly_id": assembly_id,
            "contig_accession": row["contig_accession"],
            "contig_name": row["contig_name"],
            "length_bp": _int(row["length_bp"], f"contig {assembly}/{accession}.length_bp"),
            "sequence_sha256": row["sequence_sha256"],
        }
        if existing is not None:
            existing_map = {
                field: _row_value(existing, index)
                for index, field in enumerate(("contig_id", *fields))
            }
            _compare_existing("contigs", incoming, existing_map, fields)
            ids[(assembly, accession)] = int(existing_map["contig_id"])
            continue
        ids[(assembly, accession)] = _insert_returning(
            cursor,
            "INSERT INTO contigs (assembly_id, contig_accession, contig_name, length_bp, sequence_sha256) VALUES (%s, %s, %s, %s, %s) RETURNING contig_id",
            [incoming[field] for field in fields],
            f"contig {assembly}/{accession}",
        )
    return ids


def _load_sources(cursor: Any, state: PreflightState, publication_ids: Mapping[str, int], assembly_ids: Mapping[str, int]) -> dict[str, int]:
    ids: dict[str, int] = {}
    fields = [
        "release_version", "source_id", "publication_id", "assembly_id", "species", "phylum",
        "assay_family", "release_status", "evidence_class", "redistribution_status",
        "accessibility_status", "coordinate_status", "processing_status",
        "used_for_batter_augmentation", "record_count", "has_jbrowse", "manifest_path",
        "manifest_sha256", "record_root", "source_note", "decision_note", "known_limitations",
    ]
    for source_id, row in sorted(state.sources.items()):
        params = [
            row[field] if field not in {"publication_id", "assembly_id"}
            else publication_ids[str(row["publication_id_ref"])] if field == "publication_id"
            else assembly_ids[str(row["assembly_id_ref"])]
            for field in fields
        ]
        ids[source_id] = _insert_returning(
            cursor,
            "INSERT INTO sources (release_version, source_id, publication_id, assembly_id, species, phylum, assay_family, release_status, evidence_class, redistribution_status, accessibility_status, coordinate_status, processing_status, used_for_batter_augmentation, record_count, has_jbrowse, manifest_path, manifest_sha256, record_root, source_note, decision_note, known_limitations) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING source_pk",
            params,
            f"source {source_id}",
        )
    return ids


def _load_accessions(cursor: Any, state: PreflightState, source_ids: Mapping[str, int], batch_size: int) -> None:
    rows = []
    for row in state.accessions:
        rows.append(
            (
                source_ids[str(row["source_id_ref"])],
                row["accession_namespace"], row["accession"], row["raw_value"],
                row["accession_type"], row["ordinal"], row["external_url"],
            )
        )
    sql = "INSERT INTO source_accessions (source_pk, accession_namespace, accession, raw_value, accession_type, ordinal, external_url) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    for offset in range(0, len(rows), batch_size):
        cursor.executemany(sql, rows[offset : offset + batch_size])


def _load_samples(cursor: Any, state: PreflightState, source_ids: Mapping[str, int]) -> dict[tuple[str, str], int]:
    ids: dict[tuple[str, str], int] = {}
    fields = ("source_pk", "sample_id", "sample_label", "biological_condition", "replicate_label", "sample_accession", "metadata_json")
    for key, row in sorted(state.samples.items()):
        source_id, sample_id = key
        params = [source_ids[source_id], row["sample_id"], row["sample_label"], row["biological_condition"], row["replicate_label"], row["sample_accession"], _json_value(row["metadata_json"], f"sample {source_id}/{sample_id}.metadata_json")]
        ids[key] = _insert_returning(
            cursor,
            "INSERT INTO samples (source_pk, sample_id, sample_label, biological_condition, replicate_label, sample_accession, metadata_json) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb) RETURNING sample_pk",
            params,
            f"sample {source_id}/{sample_id}",
        )
    return ids


def _endpoint_params(row: Mapping[str, Any], source_ids: Mapping[str, int], contig_ids: Mapping[tuple[str, str], int], sample_ids: Mapping[tuple[str, str], int]) -> tuple[Any, ...]:
    source_id = str(row["source_id_ref"])
    contig = row["contig_id_ref"]
    sample = row["sample_id_ref"]
    contig_key = (str(contig["assembly_accession"]), str(contig["contig_accession"]))
    sample_key = (str(sample["source_id"]), str(sample["sample_id"]))
    return (
        row["release_version"], source_ids[source_id], contig_ids[contig_key], sample_ids[sample_key],
        *[row[column] for column in V02_ENDPOINT_COLUMNS],
    )


def _load_endpoints(cursor: Any, verification: BundleVerification, source_ids: Mapping[str, int], contig_ids: Mapping[tuple[str, str], int], sample_ids: Mapping[tuple[str, str], int], batch_size: int) -> None:
    sql = "INSERT INTO endpoints (release_version, source_pk, contig_id, sample_pk, end_id, source_id, sample_id, assay, evidence_class, author_endpoint_id, published_reference_accession, reference_assembly, reference_name, replicon_label, biological_coordinate_1based, bed_start_0based, bed_end_0based, strand, signal_or_score, author_category, associated_gene_or_locus, pmid, doi, source_table_or_file, coordinate_interpretation, original_row_reference, qc_status, note) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    batch: list[tuple[Any, ...]] = []
    for row in _iter_table(verification, "endpoints"):
        batch.append(_endpoint_params(row, source_ids, contig_ids, sample_ids))
        if len(batch) >= batch_size:
            cursor.executemany(sql, batch)
            batch = []
    if batch:
        cursor.executemany(sql, batch)


def _load_annotations(cursor: Any, verification: BundleVerification, source_ids: Mapping[str, int], batch_size: int) -> None:
    sql = "INSERT INTO source_annotations (release_version, source_pk, end_id, annotation_kind, source_record_id, ordinal, annotation_json, provenance_json) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)"
    batch: list[tuple[Any, ...]] = []
    for row in _iter_table(verification, "source_annotations"):
        batch.append((
            row["release_version"], source_ids[str(row["source_id_ref"])], row["end_id"],
            row["annotation_kind"], row["source_record_id"], row["ordinal"],
            _json_value(row["annotation_json"], "annotation_json"),
            _json_value(row["provenance_json"], "provenance_json"),
        ))
        if len(batch) >= batch_size:
            cursor.executemany(sql, batch)
            batch = []
    if batch:
        cursor.executemany(sql, batch)


def _load_assets(cursor: Any, verification: BundleVerification, source_ids: Mapping[str, int], assembly_ids: Mapping[str, int], batch_size: int) -> None:
    sql = "INSERT INTO assets (asset_id, release_version, source_pk, assembly_id, asset_kind, logical_path, origin_url, origin_host, byte_size, sha256, mime_type, supports_range, redistribution_status, is_public) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    batch: list[tuple[Any, ...]] = []
    for row in _iter_table(verification, "assets"):
        source_ref = row.get("source_id_ref")
        assembly_ref = row.get("assembly_id_ref")
        batch.append((
            row["asset_id"], row["release_version"],
            source_ids[str(source_ref)] if source_ref not in (None, "") else None,
            assembly_ids[str(assembly_ref)] if assembly_ref not in (None, "") else None,
            row["asset_kind"], row["logical_path"], row["origin_url"], row["origin_host"],
            row["byte_size"], row["sha256"], row["mime_type"], row["supports_range"],
            row["redistribution_status"], row["is_public"],
        ))
        if len(batch) >= batch_size:
            cursor.executemany(sql, batch)
            batch = []
    if batch:
        cursor.executemany(sql, batch)


def _load_genes(
    cursor: Any,
    verification: BundleVerification,
    assembly_ids: Mapping[str, int],
    contig_ids: Mapping[tuple[str, str], int],
    batch_size: int,
) -> None:
    sql = (
        "INSERT INTO genes (release_version, assembly_id, contig_id, gene_id, "
        "locus_tag, gene_name, feature_type, start_1based, end_1based, strand, "
        "annotation_asset_id, annotation_sha256, attributes_json) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)"
    )
    batch: list[tuple[Any, ...]] = []
    for row in _iter_table(verification, "genes"):
        contig_ref = row["contig_id_ref"]
        assembly = str(row["assembly_id_ref"])
        contig_key = (
            str(contig_ref["assembly_accession"]),
            str(contig_ref["contig_accession"]),
        )
        batch.append(
            (
                row["release_version"],
                assembly_ids[assembly],
                contig_ids[contig_key],
                row["gene_id"],
                row["locus_tag"],
                row["gene_name"],
                row["feature_type"],
                row["start_1based"],
                row["end_1based"],
                row["strand"],
                row["annotation_asset_id"],
                row["annotation_sha256"],
                _json_value(row["attributes_json"], "gene attributes_json"),
            )
        )
        if len(batch) >= batch_size:
            cursor.executemany(sql, batch)
            batch = []
    if batch:
        cursor.executemany(sql, batch)


def _load_run_and_release(
    cursor: Any,
    state: PreflightState,
    asset_origin_status: str,
) -> int:
    existing = _one(cursor, "SELECT release_version FROM release_versions WHERE release_version = %s", (state.release_version,))
    if existing is not None:
        raise PostgresWriterError("release_version already exists; release-specific rows are not overwritten")
    release = state.release_row
    _insert_returning(
        cursor,
        "INSERT INTO release_versions (release_version, release_date, canonical_manifest_path, canonical_manifest_sha256, status, is_current, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING release_id",
        [release[field] for field in ("release_version", "release_date", "canonical_manifest_path", "canonical_manifest_sha256", "status", "is_current", "created_at")],
        f"release {state.release_version}",
    )
    run = state.import_run_row
    summary = dict(_require_mapping(run["validation_summary"], "import_run.validation_summary"))
    if asset_origin_status not in {"planned_not_verified", "verified"}:
        raise PostgresWriterError("invalid asset_origin_status in verified bundle")
    summary["asset_origin_status"] = asset_origin_status
    summary["canonical_validation_status"] = "validated"
    summary["postgresql_ready"] = True
    run_id = _insert_returning(
        cursor,
        "INSERT INTO import_runs (release_version, importer_name, importer_version, input_manifest_path, input_manifest_sha256, staging_location, run_status, started_at, finished_at, validation_summary, error_summary) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s) RETURNING import_run_id",
        [
            run["release_version"], run["importer_name"], run["importer_version"],
            run["input_manifest_path"], run["input_manifest_sha256"], run["staging_location"],
            "staging", run["started_at"], None, _json_value(summary, "import_run.validation_summary"),
            run["error_summary"],
        ],
        f"import run {state.release_version}",
    )
    return run_id


def _audit_counts(cursor: Any, state: PreflightState, release_version: str) -> dict[str, int]:
    expected = {
        "sources": len(state.sources),
        "endpoints": len(state.endpoint_keys),
        "source_annotations": len(state.annotation_keys),
        "assets": len(state.assets),
    }
    # Keep the legacy result shape for the canonical no-gene bundle.  Once
    # GFF-derived genes are present, audit both the gene count and the
    # intentionally empty context table.
    if state.genes:
        expected["genes"] = len(state.genes)
        expected["endpoint_gene_context"] = 0
    actual: dict[str, int] = {}
    for table in expected:
        row = _one(cursor, f"SELECT COUNT(*) FROM {table} WHERE release_version = %s", (release_version,))
        if row is None:
            raise PostgresWriterError(f"count audit returned no row: {table}")
        actual[table] = int(_row_value(row, 0))
    if actual != expected:
        raise PostgresWriterError(f"database count audit failed: expected={expected}, actual={actual}")
    endpoint_rows = _rows(
        cursor,
        "SELECT s.source_id, s.record_count, COUNT(e.endpoint_pk) FROM sources AS s LEFT JOIN endpoints AS e ON e.release_version = s.release_version AND e.source_pk = s.source_pk WHERE s.release_version = %s GROUP BY s.source_id, s.record_count",
        (release_version,),
    )
    endpoint_by_source = {
        str(_row_value(row, 0)): (
            int(_row_value(row, 1)),
            int(_row_value(row, 2)),
        )
        for row in endpoint_rows
    }
    if set(endpoint_by_source) != set(state.sources):
        raise PostgresWriterError("database per-source endpoint audit source set mismatch")
    for source_id, source in state.sources.items():
        db_record_count, db_endpoint_count = endpoint_by_source[source_id]
        expected_record_count = _int(source["record_count"], f"source {source_id}.record_count")
        if db_record_count != expected_record_count or db_endpoint_count != expected_record_count:
            raise PostgresWriterError(
                f"database per-source endpoint count audit failed: {source_id} "
                f"record_count={db_record_count}, endpoints={db_endpoint_count}, expected={expected_record_count}"
            )
    annotation_rows = _rows(
        cursor,
        "SELECT s.source_id, COUNT(a.annotation_id) FROM sources AS s LEFT JOIN source_annotations AS a ON a.release_version = s.release_version AND a.source_pk = s.source_pk WHERE s.release_version = %s GROUP BY s.source_id",
        (release_version,),
    )
    annotation_by_source = {
        str(_row_value(row, 0)): int(_row_value(row, 1))
        for row in annotation_rows
    }
    if set(annotation_by_source) != set(state.sources):
        raise PostgresWriterError("database per-source annotation audit source set mismatch")
    for source_id in state.sources:
        if annotation_by_source.get(source_id, 0) != state.annotation_counts.get(source_id, 0):
            raise PostgresWriterError(
                f"database per-source annotation count audit failed: {source_id}"
            )
    return actual


def load_bundle(
    bundle_dir: str | Path,
    connection: Any,
    *,
    batch_size: int = 1000,
) -> LoadResult:
    """Load a verified bundle in one transaction using a psycopg3 connection."""

    if batch_size <= 0:
        raise PostgresWriterError("batch_size must be positive")
    verification = verify_bundle(bundle_dir)
    state = _preflight(verification)
    # No connection method is called until both structural and natural-key
    # validation has completed.
    with _transaction(connection):
        with _cursor(connection) as cursor:
            _begin_guards(cursor)
            run_id = _load_run_and_release(
                cursor,
                state,
                str(verification.manifest["asset_origin"]["asset_origin_status"]),
            )
            publication_ids = _load_publications(cursor, state)
            assembly_ids = _load_assemblies(cursor, state)
            contig_ids = _load_contigs(cursor, state, assembly_ids)
            source_ids = _load_sources(cursor, state, publication_ids, assembly_ids)
            _load_accessions(cursor, state, source_ids, batch_size)
            sample_ids = _load_samples(cursor, state, source_ids)
            _load_endpoints(cursor, verification, source_ids, contig_ids, sample_ids, batch_size)
            _load_annotations(cursor, verification, source_ids, batch_size)
            _load_assets(cursor, verification, source_ids, assembly_ids, batch_size)
            _load_genes(cursor, verification, assembly_ids, contig_ids, batch_size)
            counts = _audit_counts(cursor, state, verification.release_version)
            updated = cursor.execute(
                "UPDATE import_runs SET run_status = %s, finished_at = CURRENT_TIMESTAMP, committed_at = CURRENT_TIMESTAMP WHERE import_run_id = %s AND run_status = %s",
                ("committed", run_id, "staging"),
            )
            if getattr(updated, "rowcount", 1) != 1:
                raise PostgresWriterError("import_run commit audit failed")
    return LoadResult(verification.release_version, run_id, "committed", counts)


def _promote_preconditions(verification: BundleVerification) -> PreflightState:
    status = verification.manifest["asset_origin"]["asset_origin_status"]
    if status != "verified":
        raise PostgresWriterError(
            "promotion requires asset_origin_status=verified after remote asset/Range audit"
        )
    return _preflight(verification)


def promote_bundle(bundle_dir: str | Path, connection: Any) -> dict[str, Any]:
    """Promote a committed, remotely verified release in one transaction."""

    verification = verify_bundle(bundle_dir)
    state = _promote_preconditions(verification)
    with _transaction(connection):
        with _cursor(connection) as cursor:
            _begin_guards(cursor)
            latest = _one(
                cursor,
                "SELECT import_run_id, validation_summary FROM import_runs WHERE release_version = %s AND run_status = %s ORDER BY committed_at DESC, import_run_id DESC LIMIT 1",
                (verification.release_version, "committed"),
            )
            if latest is None:
                raise PostgresWriterError("no committed import_run is available for promotion")
            summary = _row_value(latest, 1)
            if isinstance(summary, str):
                try:
                    summary = json.loads(summary, parse_constant=_reject_nonfinite)
                except (json.JSONDecodeError, ValueError) as exc:
                    raise PostgresWriterError("committed import_run validation_summary is invalid") from exc
            if not isinstance(summary, Mapping) or summary.get("asset_origin_status") != "verified":
                raise PostgresWriterError("committed import_run is not asset-verified")
            counts = _audit_counts(cursor, state, verification.release_version)
            current = _one(
                cursor,
                "SELECT release_version FROM release_versions WHERE is_current = TRUE",
                (),
            )
            if current is not None and str(_row_value(current, 0)) != verification.release_version:
                cursor.execute(
                    "UPDATE release_versions SET is_current = FALSE, status = %s WHERE is_current = TRUE",
                    ("retired",),
                )
            updated = cursor.execute(
                "UPDATE release_versions SET status = %s, is_current = TRUE WHERE release_version = %s AND status IN (%s, %s) AND is_current = FALSE",
                ("published", verification.release_version, "staged", "validated"),
            )
            if getattr(updated, "rowcount", 1) != 1:
                raise PostgresWriterError("target release could not be promoted")
    return {
        "release_version": verification.release_version,
        "run_id": int(_row_value(latest, 0)),
        "status": "published",
        "counts": counts,
    }


def database_url_from_env(name: str = "BTED_DATABASE_URL") -> str:
    value = os.environ.get(name)
    if not value:
        raise PostgresWriterError(f"database URL environment variable is not set: {name}")
    return value


def connect_psycopg_from_env(name: str = "BTED_DATABASE_URL") -> Any:
    """Lazy-connect psycopg3 without exposing the URL in an exception."""

    url = database_url_from_env(name)
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise PostgresWriterError(
            "psycopg3 is not installed; install requirements-v03.txt before a real DB write"
        ) from exc
    try:
        return psycopg.connect(url)
    except Exception as exc:  # pragma: no cover - requires a real driver/server
        raise PostgresWriterError("database connection failed") from exc


def verify_summary(verification: BundleVerification) -> dict[str, Any]:
    return {
        "release_version": verification.release_version,
        "status": "verified",
        "counts": verification.table_counts,
        "asset_origin_status": verification.manifest["asset_origin"]["asset_origin_status"],
    }
