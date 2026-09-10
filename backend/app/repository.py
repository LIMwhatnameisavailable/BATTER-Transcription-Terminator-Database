"""Read-only PostgreSQL repository for the BTED v0.3 API.

SQL values are always parameters.  The small set of interpolated fragments are
selected from fixed allowlists in this module, never from a request string.
The repository opens and closes a connection for each operation; the API layer
does not retain a connection between requests.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Mapping, Sequence
from urllib.parse import quote

from backend.importer.canonical import V02_ENDPOINT_COLUMNS

from .contracts import ReleaseContext, RepositoryNotFound, RepositoryUnavailable


ConnectionFactory = Callable[[], Any]


def _json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return default
    return default


def _accession_url(namespace: str, accession: str) -> str | None:
    namespace_upper = namespace.upper()
    if namespace_upper == "GEO":
        return f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={quote(accession)}"
    if namespace_upper == "SRA":
        return f"https://www.ncbi.nlm.nih.gov/sra/{quote(accession)}"
    if namespace_upper == "ENA":
        return f"https://www.ebi.ac.uk/ena/browser/view/{quote(accession)}"
    if namespace_upper in {"BIOSTUDIES", "ARRAYEXPRESS"}:
        return f"https://www.ebi.ac.uk/biostudies/arrayexpress/studies/{quote(accession)}"
    return None


def _in_clause(values: Sequence[Any]) -> str:
    """Return placeholders only; callers still pass values separately."""

    return ", ".join(["%s"] * len(values))


def _row_as_dict(row: Sequence[Any], columns: Sequence[str]) -> dict[str, Any]:
    return {column: row[index] for index, column in enumerate(columns)}


class PostgresReadRepository:
    """Parameterised, read-only repository used by the service layer."""

    SOURCE_SORTS = {
        "source_id": "s.source_id",
        "record_count": "s.record_count",
        "species": "s.species",
        "publication_year": "p.published_year",
    }
    ASSEMBLY_SORTS = {
        "assembly_accession": "a.assembly_accession",
        "species": "a.organism_name",
        "endpoint_count": "endpoint_count",
    }
    ENDPOINT_SORTS = {
        "end_id": "e.end_id",
        "position": "e.biological_coordinate_1based",
        "source_id": "e.source_id",
        "contig_accession": "c.contig_accession",
    }
    GENE_SORTS = {
        "contig_accession": "c.contig_accession",
        "start_1based": "g.start_1based",
        "gene_id": "g.gene_id",
    }

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self.connection_factory = connection_factory

    @classmethod
    def from_env(cls, env_name: str = "BTED_DATABASE_URL") -> "PostgresReadRepository":
        value = os.environ.get(env_name)
        if not value:
            raise RepositoryUnavailable(f"database URL environment variable is not set: {env_name}")
        try:
            import psycopg  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RepositoryUnavailable(
                "psycopg3 is not installed; install requirements-v03.txt before using the API"
            ) from exc

        def connect() -> Any:
            try:
                return psycopg.connect(value)
            except Exception as exc:  # pragma: no cover - requires real driver/server
                raise RepositoryUnavailable("database connection failed") from exc

        return cls(connect)

    @contextmanager
    def _cursor(self) -> Iterator[Any]:
        try:
            connection = self.connection_factory()
        except (RepositoryUnavailable, RepositoryNotFound):
            raise
        except Exception as exc:
            raise RepositoryUnavailable("database connection failed") from exc
        cursor = None
        try:
            cursor = connection.cursor()
            yield cursor
        except (RepositoryUnavailable, RepositoryNotFound):
            raise
        except Exception as exc:
            raise RepositoryUnavailable("database read failed") from exc
        finally:
            if cursor is not None:
                close_cursor = getattr(cursor, "close", None)
                if callable(close_cursor):
                    close_cursor()
            close_connection = getattr(connection, "close", None)
            if callable(close_connection):
                close_connection()

    @staticmethod
    def _release_from_row(row: Sequence[Any] | None) -> ReleaseContext:
        if row is None:
            raise RepositoryNotFound("published release not found")
        return ReleaseContext(
            release_version=str(row[0]),
            status=str(row[1]),
            canonical_manifest_sha256=str(row[2]),
            import_run_id=int(row[3]) if row[3] is not None else None,
        )

    def resolve_release(self, release_version: str | None = None) -> ReleaseContext:
        base = (
            "SELECT r.release_version, r.status, r.canonical_manifest_sha256, "
            "ir.import_run_id "
            "FROM release_versions AS r "
            "LEFT JOIN LATERAL ("
            " SELECT import_run_id FROM import_runs "
            " WHERE release_version = r.release_version AND run_status = 'committed' "
            " ORDER BY committed_at DESC NULLS LAST, import_run_id DESC LIMIT 1"
            ") AS ir ON TRUE "
        )
        if release_version is None:
            sql = base + "WHERE r.is_current = TRUE AND r.status = 'published'"
            params: tuple[Any, ...] = ()
        else:
            sql = base + "WHERE r.release_version = %s AND r.status = 'published'"
            params = (release_version,)
        with self._cursor() as cursor:
            cursor.execute(sql, params)
            return self._release_from_row(cursor.fetchone())

    def health(self) -> Mapping[str, Any]:
        with self._cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
        return {"status": "ok", "database": "ok", "probe": int(row[0]) if row else 1}

    def stats(self, release: ReleaseContext) -> Mapping[str, Any]:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT release_status, COUNT(*) FROM sources "
                "WHERE release_version = %s GROUP BY release_status ORDER BY release_status",
                (release.release_version,),
            )
            source_counts = {str(row[0]): int(row[1]) for row in cursor.fetchall()}
            cursor.execute(
                "SELECT e.evidence_class, COUNT(*) "
                "FROM endpoints AS e JOIN sources AS s ON s.release_version = e.release_version "
                "AND s.source_pk = e.source_pk "
                "WHERE e.release_version = %s AND s.release_status = 'published_standardized' "
                "GROUP BY e.evidence_class ORDER BY e.evidence_class",
                (release.release_version,),
            )
            evidence_counts = {str(row[0]): int(row[1]) for row in cursor.fetchall()}
            cursor.execute(
                "SELECT COUNT(DISTINCT assembly_id) FROM sources WHERE release_version = %s",
                (release.release_version,),
            )
            assembly_count = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM sources WHERE release_version = %s "
                "AND used_for_batter_augmentation = TRUE",
                (release.release_version,),
            )
            augmentation_count = int(cursor.fetchone()[0])
        return {
            "sources": {
                "total": sum(source_counts.values()),
                "published_standardized": source_counts.get("published_standardized", 0),
                "audit_only": source_counts.get("audit_only", 0),
            },
            "endpoints": {
                "total": sum(evidence_counts.values()),
                "by_evidence_class": evidence_counts,
            },
            "assemblies": {"total": assembly_count},
            "augmentation": {"eligible_sources": augmentation_count, "scope": "source"},
        }

    @staticmethod
    def _source_columns() -> str:
        return (
            "s.source_pk, s.source_id, s.release_status, s.species, s.phylum, s.assay_family, "
            "s.evidence_class, s.redistribution_status, s.accessibility_status, s.coordinate_status, "
            "s.processing_status, s.used_for_batter_augmentation, s.record_count, s.has_jbrowse, "
            "s.manifest_path, s.manifest_sha256, s.record_root, s.source_note, s.decision_note, "
            "s.known_limitations, p.pmid, p.doi, p.pmc, p.published_year, p.journal, p.paper_title, "
            "p.citation_json, a.assembly_accession, a.assembly_name, a.organism_name, a.strain, "
            "a.taxon_id, a.reference_url, "
            "COALESCE((SELECT json_agg(json_build_object("
            "'namespace', sa.accession_namespace, 'accession', sa.accession, "
            "'raw_value', sa.raw_value, 'type', sa.accession_type, 'ordinal', sa.ordinal, "
            "'url', COALESCE(sa.external_url, '')"
            ") ORDER BY sa.ordinal NULLS LAST, sa.source_accession_id) "
            "FROM source_accessions AS sa WHERE sa.source_pk = s.source_pk), '[]'::json), "
            "COALESCE((SELECT json_agg(json_build_object("
            "'asset_id', aa.asset_id, 'asset_kind', aa.asset_kind, 'logical_path', aa.logical_path, "
            "'sha256', aa.sha256, 'byte_size', aa.byte_size, 'mime_type', aa.mime_type, "
            "'supports_range', aa.supports_range"
            ") ORDER BY aa.asset_id) FROM assets AS aa "
            "WHERE aa.release_version = s.release_version AND aa.source_pk = s.source_pk "
            "AND aa.is_public = TRUE), '[]'::json)"
        )

    @staticmethod
    def _source_from_row(row: Sequence[Any]) -> dict[str, Any]:
        accessions = _json_value(row[33], [])
        assets = _json_value(row[34], [])
        normalized_accessions: list[dict[str, Any]] = []
        for item in accessions if isinstance(accessions, list) else []:
            if not isinstance(item, Mapping):
                continue
            namespace = str(item.get("namespace", ""))
            accession = str(item.get("accession", ""))
            url = item.get("url") or _accession_url(namespace, accession)
            normalized_accessions.append({
                "namespace": namespace,
                "accession": accession,
                "raw_value": item.get("raw_value"),
                "type": item.get("type"),
                "ordinal": item.get("ordinal"),
                "url": url,
            })
        return {
            "source_pk": int(row[0]),
            "source_id": row[1],
            "release_status": row[2],
            "species": row[3],
            "phylum": row[4],
            "assay_family": row[5],
            "evidence_class": row[6],
            "redistribution_status": row[7],
            "accessibility_status": row[8],
            "coordinate_status": row[9],
            "processing_status": row[10],
            "used_for_batter_augmentation": bool(row[11]),
            "record_count": int(row[12]),
            "has_jbrowse": bool(row[13]),
            "manifest_path": row[14],
            "manifest_sha256": row[15],
            "record_root": row[16],
            "source_note": row[17],
            "decision_note": row[18],
            "known_limitations": row[19],
            "publication": {
                "pmid": row[20], "doi": row[21], "pmc": row[22], "year": row[23],
                "journal": row[24], "title": row[25], "citation": _json_value(row[26], {}),
            },
            "assembly": {
                "accession": row[27], "name": row[28], "organism_name": row[29],
                "strain": row[30], "taxon_id": row[31], "reference_url": row[32],
            },
            "accessions": normalized_accessions,
            "assets": assets if isinstance(assets, list) else [],
        }

    def _source_where(self, filters: Mapping[str, Any]) -> tuple[list[str], list[Any]]:
        clauses = ["s.release_version = %s"]
        params: list[Any] = []
        if filters.get("source_id"):
            clauses.append("s.source_id = %s")
            params.append(filters["source_id"])
        if filters.get("species"):
            clauses.append("s.species = %s")
            params.append(filters["species"])
        if filters.get("assay_family"):
            clauses.append("s.assay_family = %s")
            params.append(filters["assay_family"])
        if filters.get("release_status"):
            clauses.append("s.release_status = %s")
            params.append(filters["release_status"])
        if filters.get("evidence_class"):
            clauses.append("s.evidence_class = %s")
            params.append(filters["evidence_class"])
        if filters.get("assembly_accession"):
            clauses.append("a.assembly_accession = %s")
            params.append(filters["assembly_accession"])
        if filters.get("augmentation_eligible") is not None:
            clauses.append("s.used_for_batter_augmentation = %s")
            params.append(bool(filters["augmentation_eligible"]))
        if filters.get("q"):
            pattern = f"%{filters['q']}%"
            clauses.append(
                "(s.source_id ILIKE %s OR s.species ILIKE %s OR COALESCE(a.strain, '') ILIKE %s "
                "OR COALESCE(p.pmid, '') ILIKE %s OR EXISTS ("
                "SELECT 1 FROM source_accessions AS sq WHERE sq.source_pk = s.source_pk "
                "AND (sq.accession ILIKE %s OR sq.raw_value ILIKE %s)))"
            )
            params.extend([pattern] * 6)
        return clauses, params

    def list_sources(self, release: ReleaseContext, filters: Mapping[str, Any], *, offset: int, limit: int, sort: str, descending: bool) -> tuple[list[Mapping[str, Any]], int]:
        clauses, filter_params = self._source_where(filters)
        params = [release.release_version, *filter_params]
        # _source_where includes the release placeholder so the first value is
        # always the selected release.
        where = " AND ".join(clauses)
        order = self.SOURCE_SORTS.get(sort, self.SOURCE_SORTS["source_id"])
        direction = "DESC" if descending else "ASC"
        select = self._source_columns()
        with self._cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM sources AS s JOIN publications AS p ON p.publication_id = s.publication_id JOIN assemblies AS a ON a.assembly_id = s.assembly_id WHERE {where}", tuple(params))
            total = int(cursor.fetchone()[0])
            cursor.execute(
                f"SELECT {select} FROM sources AS s "
                f"JOIN publications AS p ON p.publication_id = s.publication_id "
                f"JOIN assemblies AS a ON a.assembly_id = s.assembly_id "
                f"WHERE {where} ORDER BY {order} {direction}, s.source_id ASC LIMIT %s OFFSET %s",
                tuple([*params, limit, offset]),
            )
            rows = [self._source_from_row(row) for row in cursor.fetchall()]
        return rows, total

    def get_source(self, release: ReleaseContext, source_id: str) -> Mapping[str, Any] | None:
        rows, _ = self.list_sources(
            release,
            {"source_id": source_id},
            offset=0,
            limit=1,
            sort="source_id",
            descending=False,
        )
        return rows[0] if rows else None

    def list_augmentation(self, release: ReleaseContext, *, offset: int, limit: int) -> tuple[list[Mapping[str, Any]], int]:
        return self.list_sources(
            release,
            {"augmentation_eligible": True},
            offset=offset,
            limit=limit,
            sort="source_id",
            descending=False,
        )

    def list_assemblies(self, release: ReleaseContext, filters: Mapping[str, Any], *, offset: int, limit: int, sort: str, descending: bool) -> tuple[list[Mapping[str, Any]], int]:
        clauses = [
            "EXISTS (SELECT 1 FROM sources AS sx WHERE sx.release_version = %s AND sx.assembly_id = a.assembly_id)"
        ]
        params: list[Any] = [release.release_version]
        if filters.get("assembly_accession"):
            clauses.append("a.assembly_accession = %s")
            params.append(filters["assembly_accession"])
        if filters.get("species"):
            clauses.append("a.organism_name = %s")
            params.append(filters["species"])
        if filters.get("contig_accession"):
            clauses.append(
                "EXISTS (SELECT 1 FROM contigs AS fc WHERE fc.assembly_id = a.assembly_id AND fc.contig_accession = %s)"
            )
            params.append(filters["contig_accession"])
        if filters.get("q"):
            pattern = f"%{filters['q']}%"
            clauses.append(
                "(a.assembly_accession ILIKE %s OR COALESCE(a.assembly_name, '') ILIKE %s "
                "OR COALESCE(a.organism_name, '') ILIKE %s OR COALESCE(a.strain, '') ILIKE %s)"
            )
            params.extend([pattern] * 4)
        where = " AND ".join(clauses)
        order = self.ASSEMBLY_SORTS.get(sort, self.ASSEMBLY_SORTS["assembly_accession"])
        direction = "DESC" if descending else "ASC"
        select = (
            "a.assembly_id, a.assembly_accession, a.assembly_name, a.organism_name, a.strain, "
            "a.taxon_id, a.reference_url, "
            "COALESCE((SELECT json_agg(json_build_object('accession', c.contig_accession, "
            "'name', c.contig_name, 'length_bp', c.length_bp, 'sequence_sha256', c.sequence_sha256) "
            "ORDER BY c.contig_accession) FROM contigs AS c WHERE c.assembly_id = a.assembly_id), '[]'::json), "
            "COALESCE((SELECT json_agg(json_build_object('asset_id', aa.asset_id, 'asset_kind', aa.asset_kind, "
            "'logical_path', aa.logical_path, 'sha256', aa.sha256, 'byte_size', aa.byte_size, "
            "'mime_type', aa.mime_type, 'supports_range', aa.supports_range) ORDER BY aa.asset_id) "
            "FROM assets AS aa WHERE aa.release_version = %s AND aa.assembly_id = a.assembly_id "
            "AND aa.is_public = TRUE), '[]'::json), "
            "COALESCE((SELECT json_agg(json_build_object('source_id', ss.source_id, "
            "'record_count', ss.record_count, 'evidence_class', ss.evidence_class, "
            "'release_status', ss.release_status, 'has_jbrowse', ss.has_jbrowse, "
            "'assets', COALESCE((SELECT json_agg(json_build_object('asset_id', sa.asset_id, "
            "'asset_kind', sa.asset_kind, 'logical_path', sa.logical_path, 'sha256', sa.sha256, "
            "'byte_size', sa.byte_size, 'mime_type', sa.mime_type, 'supports_range', sa.supports_range) "
            "ORDER BY sa.asset_id) FROM assets AS sa WHERE sa.release_version = ss.release_version "
            "AND sa.source_pk = ss.source_pk AND sa.is_public = TRUE), '[]'::json)) ORDER BY ss.source_id) "
            "FROM sources AS ss WHERE ss.release_version = %s AND ss.assembly_id = a.assembly_id), '[]'::json), "
            "(SELECT COUNT(*) FROM endpoints AS ee JOIN sources AS es ON es.release_version = ee.release_version "
            "AND es.source_pk = ee.source_pk WHERE ee.release_version = %s AND es.assembly_id = a.assembly_id), "
            "(SELECT COUNT(*) FROM genes AS gg WHERE gg.release_version = %s AND gg.assembly_id = a.assembly_id)"
        )
        count_params = list(params)
        # The four release placeholders occur in the SELECT subqueries before
        # the filter placeholders in WHERE.
        query_params = [
            release.release_version,
            release.release_version,
            release.release_version,
            release.release_version,
            *params,
            limit,
            offset,
        ]
        with self._cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM assemblies AS a WHERE {where}", tuple(count_params))
            total = int(cursor.fetchone()[0])
            cursor.execute(
                f"SELECT {select} FROM assemblies AS a WHERE {where} ORDER BY {order} {direction}, a.assembly_accession ASC LIMIT %s OFFSET %s",
                tuple(query_params),
            )
            raw_rows = cursor.fetchall()
        rows = []
        for row in raw_rows:
            rows.append({
                "assembly_id": int(row[0]),
                "assembly_accession": row[1],
                "assembly_name": row[2],
                "organism_name": row[3],
                "strain": row[4],
                "taxon_id": row[5],
                "reference_url": row[6],
                "contigs": _json_value(row[7], []),
                "assets": _json_value(row[8], []),
                "source_tracks": _json_value(row[9], []),
                "endpoint_count": int(row[10]),
                "gene_count": int(row[11]),
            })
        return rows, total

    def get_assembly(self, release: ReleaseContext, assembly_accession: str) -> Mapping[str, Any] | None:
        rows, _ = self.list_assemblies(
            release,
            {"assembly_accession": assembly_accession},
            offset=0,
            limit=1,
            sort="assembly_accession",
            descending=False,
        )
        return rows[0] if rows else None

    def get_jbrowse_bundle(self, release: ReleaseContext, assembly_accession: str) -> Mapping[str, Any] | None:
        """Return one assembly plus its public source rows for config building."""

        assembly = self.get_assembly(release, assembly_accession)
        if assembly is None:
            return None
        sources: list[Mapping[str, Any]] = []
        for track in assembly.get("source_tracks", []):
            if not isinstance(track, Mapping) or not track.get("source_id"):
                continue
            source = self.get_source(release, str(track["source_id"]))
            if source is not None:
                sources.append(source)
        return {"assembly": assembly, "sources": sources}

    @staticmethod
    def _endpoint_select(*, include_annotation_summary: bool = False) -> str:
        columns = ", ".join(f"e.{column}" for column in V02_ENDPOINT_COLUMNS)
        select = (
            f"{columns}, s.manifest_sha256, s.release_status, s.redistribution_status, "
            "a.assembly_accession AS source_assembly_accession, "
            "COALESCE((SELECT json_agg(json_build_object('namespace', sa.accession_namespace, "
            "'accession', sa.accession, 'type', sa.accession_type, 'url', COALESCE(sa.external_url, '')) "
            "ORDER BY sa.ordinal NULLS LAST, sa.source_accession_id) FROM source_accessions AS sa "
            "WHERE sa.source_pk = s.source_pk), '[]'::json)"
        )
        if include_annotation_summary:
            select += (
                ", COALESCE((SELECT json_build_object("
                "'row_count', COUNT(*),"
                "'annotation_kinds', COALESCE(array_agg(DISTINCT an.annotation_kind ORDER BY an.annotation_kind), ARRAY[]::text[])"
                ") FROM source_annotations AS an WHERE an.release_version = e.release_version "
                "AND an.source_pk = e.source_pk AND an.end_id = e.end_id), "
                "json_build_object('row_count', 0, 'annotation_kinds', ARRAY[]::text[]))"
            )
        return select

    @staticmethod
    def _endpoint_from_row(row: Sequence[Any], *, release_version: str, include_annotation_summary: bool = False) -> dict[str, Any]:
        data = _row_as_dict(row, V02_ENDPOINT_COLUMNS)
        data["raw_accessions"] = _json_value(row[28], [])
        data["provenance"] = {
            "release_version": release_version,
            "source_manifest_sha256": row[24],
            "source_release_status": row[25],
            "redistribution_status": row[26],
            "assembly_accession": row[27],
            "contig_accession": data["reference_name"],
            "source_table_or_file": data["source_table_or_file"],
            "original_row_reference": data["original_row_reference"],
        }
        if include_annotation_summary:
            data["source_annotations_summary"] = _json_value(row[29], {"row_count": 0, "annotation_kinds": []})
        return data

    def _endpoint_where(self, release: ReleaseContext, filters: Mapping[str, Any]) -> tuple[list[str], list[Any]]:
        clauses = [
            "e.release_version = %s",
            "s.release_version = %s",
            "s.release_status = 'published_standardized'",
        ]
        params: list[Any] = [release.release_version, release.release_version]
        source_ids = filters.get("source_ids") or []
        if source_ids:
            clauses.append(f"s.source_id IN ({_in_clause(source_ids)})")
            params.extend(source_ids)
        for key, expression in (
            ("assembly_accession", "a.assembly_accession"),
            ("contig_accession", "c.contig_accession"),
            ("sample_id", "e.sample_id"),
            ("strand", "e.strand"),
            ("evidence_class", "e.evidence_class"),
            ("author_category", "e.author_category"),
            ("gene_or_locus", "e.associated_gene_or_locus"),
        ):
            if filters.get(key) not in (None, ""):
                clauses.append(f"{expression} = %s")
                params.append(filters[key])
        if filters.get("position_min") is not None:
            clauses.append("e.biological_coordinate_1based >= %s")
            params.append(filters["position_min"])
        if filters.get("position_max") is not None:
            clauses.append("e.biological_coordinate_1based <= %s")
            params.append(filters["position_max"])
        if filters.get("q"):
            pattern = f"%{filters['q']}%"
            clauses.append(
                "(e.end_id ILIKE %s OR e.author_endpoint_id ILIKE %s OR e.original_row_reference ILIKE %s)"
            )
            params.extend([pattern] * 3)
        return clauses, params

    def _endpoint_from_cursor(self, cursor: Any, sql: str, params: Sequence[Any], *, release_version: str, limit: int | None = None, offset: int = 0) -> tuple[list[Mapping[str, Any]], int | None]:
        cursor.execute(sql, tuple(params))
        rows = [self._endpoint_from_row(row, release_version=release_version) for row in cursor.fetchall()]
        return rows, None

    def list_endpoints(self, release: ReleaseContext, filters: Mapping[str, Any], *, offset: int, limit: int, sort: str, descending: bool) -> tuple[list[Mapping[str, Any]], int]:
        clauses, params = self._endpoint_where(release, filters)
        where = " AND ".join(clauses)
        order = self.ENDPOINT_SORTS.get(sort, self.ENDPOINT_SORTS["end_id"])
        direction = "DESC" if descending else "ASC"
        from_sql = "FROM endpoints AS e JOIN sources AS s ON s.release_version = e.release_version AND s.source_pk = e.source_pk JOIN contigs AS c ON c.contig_id = e.contig_id JOIN assemblies AS a ON a.assembly_id = c.assembly_id"
        with self._cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) {from_sql} WHERE {where}", tuple(params))
            total = int(cursor.fetchone()[0])
            cursor.execute(
                f"SELECT {self._endpoint_select()} {from_sql} WHERE {where} ORDER BY {order} {direction}, e.end_id ASC LIMIT %s OFFSET %s",
                tuple([*params, limit, offset]),
            )
            rows = [self._endpoint_from_row(row, release_version=release.release_version) for row in cursor.fetchall()]
        return rows, total

    def get_endpoint(self, release: ReleaseContext, end_id: str) -> Mapping[str, Any] | None:
        clauses, params = self._endpoint_where(release, {})
        clauses.append("e.end_id = %s")
        params.append(end_id)
        from_sql = "FROM endpoints AS e JOIN sources AS s ON s.release_version = e.release_version AND s.source_pk = e.source_pk JOIN contigs AS c ON c.contig_id = e.contig_id JOIN assemblies AS a ON a.assembly_id = c.assembly_id"
        with self._cursor() as cursor:
            cursor.execute(
                f"SELECT {self._endpoint_select(include_annotation_summary=True)} {from_sql} WHERE {' AND '.join(clauses)} LIMIT 1",
                tuple(params),
            )
            row = cursor.fetchone()
        return self._endpoint_from_row(row, release_version=release.release_version, include_annotation_summary=True) if row is not None else None

    def list_genes(self, release: ReleaseContext, filters: Mapping[str, Any], *, offset: int, limit: int, sort: str, descending: bool) -> tuple[list[Mapping[str, Any]], int]:
        clauses = ["g.release_version = %s"]
        params: list[Any] = [release.release_version]
        for key, expression in (
            ("assembly_accession", "a.assembly_accession"),
            ("contig_accession", "c.contig_accession"),
            ("gene_id", "g.gene_id"),
            ("locus_tag", "g.locus_tag"),
            ("feature_type", "g.feature_type"),
        ):
            if filters.get(key) not in (None, ""):
                clauses.append(f"{expression} = %s")
                params.append(filters[key])
        for key, expression in (("start_min", "g.start_1based"), ("start_max", "g.start_1based")):
            if filters.get(key) is not None:
                clauses.append(f"{expression} {'>=' if key == 'start_min' else '<='} %s")
                params.append(filters[key])
        where = " AND ".join(clauses)
        from_sql = (
            "FROM genes AS g JOIN contigs AS c ON c.contig_id = g.contig_id "
            "JOIN assemblies AS a ON a.assembly_id = g.assembly_id"
        )
        select = (
            "g.gene_pk, g.release_version, g.gene_id, g.locus_tag, g.gene_name, g.feature_type, "
            "g.start_1based, g.end_1based, g.strand, g.annotation_asset_id, g.annotation_sha256, "
            "g.attributes_json, a.assembly_accession, c.contig_accession, c.contig_name, "
            "a.organism_name, a.strain"
        )
        order = self.GENE_SORTS.get(sort, self.GENE_SORTS["contig_accession"])
        direction = "DESC" if descending else "ASC"
        with self._cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) {from_sql} WHERE {where}", tuple(params))
            total = int(cursor.fetchone()[0])
            cursor.execute(
                f"SELECT {select} {from_sql} WHERE {where} ORDER BY {order} {direction}, g.gene_id ASC LIMIT %s OFFSET %s",
                tuple([*params, limit, offset]),
            )
            raw_rows = cursor.fetchall()
        return [self._gene_from_row(row) for row in raw_rows], total

    @staticmethod
    def _gene_from_row(row: Sequence[Any]) -> dict[str, Any]:
        return {
            "gene_pk": int(row[0]), "release_version": row[1], "gene_id": row[2],
            "locus_tag": row[3], "gene_name": row[4], "feature_type": row[5],
            "start_1based": int(row[6]), "end_1based": int(row[7]), "strand": row[8],
            "annotation_asset_id": row[9], "annotation_sha256": row[10],
            "attributes": _json_value(row[11], {}), "assembly_accession": row[12],
            "contig_accession": row[13], "contig_name": row[14], "organism_name": row[15],
            "strain": row[16],
        }

    def get_gene(self, release: ReleaseContext, gene_id: str) -> Mapping[str, Any] | None:
        rows, _ = self.list_genes(
            release,
            {"gene_id": gene_id},
            offset=0,
            limit=2,
            sort="contig_accession",
            descending=False,
        )
        return rows[0] if rows else None

    def get_public_asset(self, release: ReleaseContext, asset_id: str) -> Mapping[str, Any] | None:
        """Return one public asset registered in the selected published release."""

        with self._cursor() as cursor:
            cursor.execute(
                "SELECT a.asset_id, a.release_version, a.asset_kind, a.logical_path, "
                "a.origin_url, a.origin_host, a.byte_size, a.sha256, a.mime_type, "
                "a.supports_range, a.redistribution_status, a.is_public "
                "FROM assets AS a JOIN release_versions AS r "
                "ON r.release_version = a.release_version "
                "WHERE a.asset_id = %s AND a.release_version = %s "
                "AND r.status = 'published' AND a.is_public = TRUE",
                (asset_id, release.release_version),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "asset_id": row[0],
            "release_version": row[1],
            "asset_kind": row[2],
            "logical_path": row[3],
            "origin_url": row[4],
            "origin_host": row[5],
            "byte_size": int(row[6]),
            "sha256": row[7],
            "mime_type": row[8],
            "supports_range": bool(row[9]),
            "redistribution_status": row[10],
            "is_public": bool(row[11]),
        }

    def validate_source_ids(self, release: ReleaseContext, source_ids: Sequence[str], *, published_only: bool = False) -> None:
        if not source_ids:
            return
        status_clause = " AND release_status = 'published_standardized'" if published_only else ""
        with self._cursor() as cursor:
            cursor.execute(
                f"SELECT source_id FROM sources WHERE release_version = %s{status_clause} AND source_id IN ({_in_clause(source_ids)})",
                tuple([release.release_version, *source_ids]),
            )
            found = {str(row[0]) for row in cursor.fetchall()}
        missing = [source_id for source_id in source_ids if source_id not in found]
        if missing:
            raise RepositoryNotFound(f"source not found in release: {missing[0]}")

    def validate_assembly(self, release: ReleaseContext, assembly_accession: str) -> None:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM assemblies AS a WHERE a.assembly_accession = %s AND EXISTS ("
                "SELECT 1 FROM sources AS s WHERE s.release_version = %s AND s.assembly_id = a.assembly_id)",
                (assembly_accession, release.release_version),
            )
            if cursor.fetchone() is None:
                raise RepositoryNotFound(f"assembly not found in release: {assembly_accession}")

    def validate_contig(self, release: ReleaseContext, assembly_accession: str, contig_accession: str) -> None:
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM contigs AS c JOIN assemblies AS a ON a.assembly_id = c.assembly_id "
                "WHERE a.assembly_accession = %s AND c.contig_accession = %s AND EXISTS ("
                "SELECT 1 FROM sources AS s WHERE s.release_version = %s AND s.assembly_id = a.assembly_id)",
                (assembly_accession, contig_accession, release.release_version),
            )
            if cursor.fetchone() is None:
                raise RepositoryNotFound(
                    f"contig not found in assembly: {assembly_accession}/{contig_accession}"
                )

    def iter_endpoint_rows(self, release: ReleaseContext, filters: Mapping[str, Any]) -> Iterator[Mapping[str, Any]]:
        clauses, params = self._endpoint_where(release, filters)
        where = " AND ".join(clauses)
        from_sql = "FROM endpoints AS e JOIN sources AS s ON s.release_version = e.release_version AND s.source_pk = e.source_pk JOIN contigs AS c ON c.contig_id = e.contig_id JOIN assemblies AS a ON a.assembly_id = c.assembly_id"
        sql = f"SELECT {self._endpoint_select()} {from_sql} WHERE {where} ORDER BY e.end_id ASC"
        try:
            connection = self.connection_factory()
        except Exception as exc:
            raise RepositoryUnavailable("database connection failed") from exc
        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(sql, tuple(params))
            while True:
                fetchmany = getattr(cursor, "fetchmany", None)
                if callable(fetchmany):
                    batch = fetchmany(1000)
                else:  # pragma: no cover - defensive fallback for a tiny DB adapter
                    row = cursor.fetchone()
                    batch = [] if row is None else [row]
                if not batch:
                    break
                for row in batch:
                    yield self._endpoint_from_row(row, release_version=release.release_version)
        except RepositoryUnavailable:
            raise
        except Exception as exc:
            raise RepositoryUnavailable("database download query failed") from exc
        finally:
            if cursor is not None:
                close_cursor = getattr(cursor, "close", None)
                if callable(close_cursor):
                    close_cursor()
            close_connection = getattr(connection, "close", None)
            if callable(close_connection):
                close_connection()
