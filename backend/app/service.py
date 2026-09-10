"""Release-aware business rules for the BTED read API.

This layer is deliberately independent of FastAPI.  It is the place where
release selection, public evidence boundaries, pagination and stable response
shapes are enforced, which makes the rules testable with an in-memory fake
repository.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlencode

from backend.importer.canonical import V02_ENDPOINT_COLUMNS

from .assets import AssetProxyResponse, AssetProxyService
from .browser import BrowserConfigUnavailable, build_jbrowse_config, has_public_endpoint_bed, is_public_asset
from .contracts import Page, ReadRepository, ReleaseContext, RepositoryNotFound, RepositoryUnavailable
from .errors import ApiError, invalid, not_found


PUBLIC_EVIDENCE = frozenset(
    {"observed_signal", "called_endpoint", "author_called_endpoint", "curated_record"}
)
SOURCE_STATUSES = frozenset({"published_standardized", "audit_only", "to_review", "blocked"})
STRANDS = frozenset({"+", "-"})
SORTS = {
    "sources": frozenset({"source_id", "record_count", "species", "publication_year"}),
    "assemblies": frozenset({"assembly_accession", "species", "endpoint_count"}),
    "endpoints": frozenset({"end_id", "position", "source_id", "contig_accession"}),
    "genes": frozenset({"contig_accession", "start_1based", "gene_id"}),
}


def _external_accession_url(namespace: str, accession: str) -> str | None:
    namespace = namespace.upper()
    if namespace == "GEO":
        return f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={quote(accession)}"
    if namespace == "SRA":
        return f"https://www.ncbi.nlm.nih.gov/sra/{quote(accession)}"
    if namespace == "ENA":
        return f"https://www.ebi.ac.uk/ena/browser/view/{quote(accession)}"
    if namespace in {"BIOSTUDIES", "ARRAYEXPRESS"}:
        return f"https://www.ebi.ac.uk/biostudies/arrayexpress/studies/{quote(accession)}"
    return None


def _json_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


@dataclass(frozen=True)
class DownloadStream:
    body: Iterator[str]
    media_type: str
    filename: str
    headers: dict[str, str]


class ReadService:
    def __init__(
        self,
        repository: ReadRepository,
        *,
        jbrowse_base: str = "/jbrowse/",
        asset_client: Any | None = None,
        asset_client_factory: Any | None = None,
    ) -> None:
        self.repository = repository
        self.jbrowse_base = jbrowse_base.rstrip("/") + "/"
        self.asset_proxy = AssetProxyService(
            repository,
            http_client=asset_client,
            http_client_factory=asset_client_factory,
        )

    def _release(self, release_version: str | None) -> ReleaseContext:
        try:
            return self.repository.resolve_release(release_version)
        except RepositoryNotFound as exc:
            requested = release_version or "current"
            raise not_found(
                "release_not_found",
                f"published release not found: {requested}",
                field="release_version" if release_version else None,
                release_version=release_version,
            ) from exc
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable") from exc

    @staticmethod
    def _page(page: int, page_size: int) -> tuple[int, int, int]:
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            raise invalid("invalid_pagination", "page must be an integer >= 1", field="page")
        if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= 100:
            raise invalid("invalid_pagination", "page_size must be an integer between 1 and 100", field="page_size")
        return page, page_size, (page - 1) * page_size

    @staticmethod
    def _sort(resource: str, sort: str, order: str) -> tuple[str, bool]:
        if sort not in SORTS[resource]:
            raise invalid("invalid_sort", f"unsupported sort for {resource}: {sort}", field="sort")
        if order not in {"asc", "desc"}:
            raise invalid("invalid_sort", "order must be asc or desc", field="order")
        return sort, order == "desc"

    def _page_response(self, release: ReleaseContext, rows: Iterable[Mapping[str, Any]], total: int, page: int, page_size: int) -> dict[str, Any]:
        data = list(rows)
        return {
            "release": release.as_dict(),
            "data": data,
            "pagination": Page(page, page_size, len(data), total).as_dict(),
        }

    def health(self) -> dict[str, Any]:
        try:
            result = dict(self.repository.health())
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable") from exc
        result.setdefault("status", "ok")
        result.setdefault("service", "bted-api")
        return result

    def stats(self, release_version: str | None) -> dict[str, Any]:
        release = self._release(release_version)
        try:
            stats = dict(self.repository.stats(release))
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        return {"release": release.as_dict(), **stats}

    @staticmethod
    def _publication(row: Mapping[str, Any]) -> dict[str, Any]:
        publication = row.get("publication")
        if isinstance(publication, Mapping):
            result = dict(publication)
        else:
            result = {
                "pmid": row.get("pmid"),
                "doi": row.get("doi"),
                "pmc": row.get("pmc"),
                "year": row.get("published_year", row.get("year")),
                "journal": row.get("journal"),
                "title": row.get("paper_title", row.get("title")),
            }
        links: dict[str, str] = {}
        if result.get("pmid"):
            links["pubmed"] = f"https://pubmed.ncbi.nlm.nih.gov/{quote(str(result['pmid']))}/"
        if result.get("doi"):
            links["doi"] = f"https://doi.org/{quote(str(result['doi']))}"
        if result.get("pmc"):
            pmc = str(result["pmc"])
            links["pmc"] = pmc if pmc.startswith("http") else f"https://pmc.ncbi.nlm.nih.gov/articles/{quote(pmc)}/"
        if links:
            result["links"] = links
        return result

    @staticmethod
    def _accessions(row: Mapping[str, Any]) -> list[dict[str, Any]]:
        raw = row.get("accessions", row.get("raw_accessions", []))
        result: list[dict[str, Any]] = []
        if not isinstance(raw, list):
            return result
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            namespace = str(item.get("namespace", ""))
            accession = str(item.get("accession", ""))
            value = dict(item)
            value.setdefault("url", _external_accession_url(namespace, accession))
            value.setdefault("type", value.get("accession_type"))
            result.append(value)
        return result

    def _source_item(self, release: ReleaseContext, row: Mapping[str, Any]) -> dict[str, Any]:
        source_id = str(row["source_id"])
        assembly = row.get("assembly")
        if not isinstance(assembly, Mapping):
            assembly = {"accession": row.get("assembly_accession")}
        publication = self._publication(row)
        accessions = self._accessions(row)
        assets = row.get("assets", [])
        if not isinstance(assets, list):
            assets = []
        browser_available = (
            row.get("release_status") == "published_standardized"
            and int(row.get("record_count", 0) or 0) > 0
            and has_public_endpoint_bed(row)
        )
        manifest_asset = next(
            (asset for asset in assets if isinstance(asset, Mapping) and str(asset.get("logical_path", "")).endswith("manifest.json")),
            None,
        )
        links: dict[str, Any] = {"bted_record": f"/sources/{quote(source_id)}"}
        if manifest_asset and manifest_asset.get("asset_id"):
            links["manifest"] = f"/api/v1/assets/{quote(str(manifest_asset['asset_id']))}"
        if row.get("release_status") == "published_standardized" and int(row.get("record_count", 0)) > 0:
            links["endpoints_download"] = (
                f"/api/v1/downloads/endpoints?release_version={quote(release.release_version)}"
                f"&source_id={quote(source_id)}"
            )
            if browser_available:
                assembly_accession = assembly.get("accession")
                if assembly_accession:
                    config_url = f"/api/v1/assemblies/{quote(str(assembly_accession), safe='')}/jbrowse-config"
                    config_url = f"{config_url}?source_id={quote(source_id, safe='')}"
                    query: dict[str, str] = {
                        "config": config_url,
                        "assembly": str(assembly_accession),
                    }
                    links["jbrowse_config"] = config_url
                    links["jbrowse"] = self.jbrowse_base + "?" + urlencode(query)
        result = {
            "source_id": source_id,
            "release_status": row.get("release_status"),
            "species": row.get("species"),
            "phylum": row.get("phylum"),
            "assay_family": row.get("assay_family"),
            "evidence_class": row.get("evidence_class"),
            "record_count": int(row.get("record_count", 0)),
            "has_jbrowse": browser_available,
            "used_for_batter_augmentation": bool(row.get("used_for_batter_augmentation", False)),
            "augmentation_eligible": bool(row.get("used_for_batter_augmentation", False)),
            "publication": publication,
            "assembly": dict(assembly),
            "accessions": accessions,
            "raw_accessions": accessions,
            "assets": [dict(asset) for asset in assets if isinstance(asset, Mapping)],
            "links": links,
            "provenance": {
                "release_version": release.release_version,
                "source_manifest_sha256": row.get("manifest_sha256"),
                "manifest_path": row.get("manifest_path"),
            },
        }
        for optional in ("redistribution_status", "accessibility_status", "coordinate_status", "processing_status", "source_note", "decision_note", "known_limitations"):
            if row.get(optional) is not None:
                result[optional] = row[optional]
        return result

    def list_sources(self, release_version: str | None, *, filters: Mapping[str, Any], page: int, page_size: int, sort: str, order: str) -> dict[str, Any]:
        release = self._release(release_version)
        page, page_size, offset = self._page(page, page_size)
        sort, descending = self._sort("sources", sort, order)
        normalized = dict(filters)
        status = normalized.get("release_status")
        if status is not None and status not in SOURCE_STATUSES:
            raise invalid("invalid_filter", f"unsupported release_status: {status}", field="release_status", release_version=release.release_version)
        try:
            rows, total = self.repository.list_sources(release, normalized, offset=offset, limit=page_size, sort=sort, descending=descending)
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        return self._page_response(release, (self._source_item(release, row) for row in rows), total, page, page_size)

    def source_detail(self, release_version: str | None, source_id: str) -> dict[str, Any]:
        release = self._release(release_version)
        try:
            row = self.repository.get_source(release, source_id)
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        if row is None:
            raise not_found("source_not_found", f"source not found: {source_id}", field="source_id", release_version=release.release_version)
        return {"release": release.as_dict(), **self._source_item(release, row)}

    def list_assemblies(self, release_version: str | None, *, filters: Mapping[str, Any], page: int, page_size: int, sort: str, order: str) -> dict[str, Any]:
        release = self._release(release_version)
        page, page_size, offset = self._page(page, page_size)
        sort, descending = self._sort("assemblies", sort, order)
        try:
            rows, total = self.repository.list_assemblies(release, filters, offset=offset, limit=page_size, sort=sort, descending=descending)
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        return self._page_response(release, (self._assembly_item(release, row) for row in rows), total, page, page_size)

    def _assembly_item(self, release: ReleaseContext, row: Mapping[str, Any]) -> dict[str, Any]:
        accession = row.get("assembly_accession")
        contigs = row.get("contigs", [])
        raw_tracks = row.get("source_tracks", [])
        tracks: list[dict[str, Any]] = []
        if isinstance(raw_tracks, list):
            for raw_track in raw_tracks:
                if not isinstance(raw_track, Mapping):
                    continue
                track = dict(raw_track)
                if track.get("source_id"):
                    track["links"] = {"source": f"/api/v1/sources/{quote(str(track['source_id']))}"}
                track["has_jbrowse"] = (
                    track.get("release_status") == "published_standardized"
                    and int(track.get("record_count", 0) or 0) > 0
                    and has_public_endpoint_bed(track)
                )
                track["provenance"] = {"release_version": release.release_version, "assembly_accession": accession}
                tracks.append(track)
        result = {
            "assembly_accession": accession,
            "assembly_name": row.get("assembly_name"),
            "organism_name": row.get("organism_name"),
            "strain": row.get("strain"),
            "taxon_id": row.get("taxon_id"),
            "reference_url": row.get("reference_url"),
            "contigs": contigs if isinstance(contigs, list) else [],
            "assets": row.get("assets", []) if isinstance(row.get("assets", []), list) else [],
            "source_count": len(tracks),
            "endpoint_count": int(row.get("endpoint_count", 0)),
            "gene_count": int(row.get("gene_count", 0) or 0),
            "source_tracks": tracks,
            "provenance": {
                "release_version": release.release_version,
                "assembly_accession": accession,
            },
        }
        if accession and any(
            isinstance(track, Mapping)
            and track.get("release_status") == "published_standardized"
            and bool(track.get("has_jbrowse", False))
            for track in tracks
        ) and any(
            isinstance(asset, Mapping)
            and str(asset.get("asset_kind", "")) == "fasta"
            and is_public_asset(asset)
            for asset in result["assets"]
        ) and any(
            isinstance(asset, Mapping)
            and str(asset.get("asset_kind", "")) == "fai"
            and is_public_asset(asset)
            for asset in result["assets"]
        ):
            config_url = f"/api/v1/assemblies/{quote(str(accession), safe='')}/jbrowse-config"
            result["links"] = {
                "jbrowse_config": config_url,
                "jbrowse": self.jbrowse_base + "?" + urlencode({"config": config_url, "assembly": str(accession)}),
            }
        return result

    def jbrowse_config(
        self,
        release_version: str | None,
        assembly_accession: str,
        *,
        source_id: str | None = None,
    ) -> dict[str, Any]:
        release = self._release(release_version)
        try:
            getter = getattr(self.repository, "get_jbrowse_bundle", None)
            if callable(getter):
                bundle = getter(release, assembly_accession)
            else:
                assembly = self.repository.get_assembly(release, assembly_accession)
                bundle = None if assembly is None else {"assembly": assembly, "sources": []}
        except RepositoryNotFound as exc:
            raise not_found("assembly_not_found", str(exc), field="assembly_accession", release_version=release.release_version) from exc
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        if not bundle:
            raise not_found("assembly_not_found", f"assembly not found: {assembly_accession}", field="assembly_accession", release_version=release.release_version)
        assembly = bundle.get("assembly") if isinstance(bundle, Mapping) else None
        sources = bundle.get("sources", []) if isinstance(bundle, Mapping) else []
        if not isinstance(assembly, Mapping) or not isinstance(sources, Sequence):
            raise not_found("jbrowse_not_available", "assembly browser metadata is unavailable", field="assembly_accession", release_version=release.release_version)
        try:
            return build_jbrowse_config(
                assembly,
                [self._source_item(release, source) for source in sources if isinstance(source, Mapping)],
                release,
                default_source_id=source_id,
            )
        except BrowserConfigUnavailable as exc:
            raise not_found("jbrowse_not_available", str(exc), field="assembly_accession", release_version=release.release_version) from exc

    def assembly_detail(self, release_version: str | None, assembly_accession: str) -> dict[str, Any]:
        release = self._release(release_version)
        try:
            row = self.repository.get_assembly(release, assembly_accession)
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        if row is None:
            raise not_found("assembly_not_found", f"assembly not found: {assembly_accession}", field="assembly_accession", release_version=release.release_version)
        return {"release": release.as_dict(), **self._assembly_item(release, row)}

    @staticmethod
    def _validate_endpoint_filters(filters: Mapping[str, Any], release_version: str) -> dict[str, Any]:
        normalized = dict(filters)
        evidence = normalized.get("evidence_class")
        if evidence is not None and evidence not in PUBLIC_EVIDENCE:
            raise invalid("invalid_filter", f"{evidence} is not a public endpoint evidence class", field="evidence_class", release_version=release_version)
        strand = normalized.get("strand")
        if strand is not None and strand not in STRANDS:
            raise invalid("invalid_filter", "strand must be '+' or '-'", field="strand", release_version=release_version)
        for field in ("position_min", "position_max"):
            if normalized.get(field) is not None:
                value = normalized[field]
                if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                    raise invalid("invalid_filter", f"{field} must be an integer >= 1", field=field, release_version=release_version)
        if normalized.get("position_min") is not None and normalized.get("position_max") is not None and normalized["position_min"] > normalized["position_max"]:
            raise invalid("invalid_filter", "position_min must not exceed position_max", field="position_min", release_version=release_version)
        if normalized.get("contig_accession") and not normalized.get("assembly_accession"):
            raise invalid("invalid_filter", "contig_accession requires assembly_accession", field="contig_accession", release_version=release_version)
        return normalized

    @staticmethod
    def _endpoint_item(release: ReleaseContext, row: Mapping[str, Any], *, detail: bool = False) -> dict[str, Any]:
        result = {column: row.get(column) for column in V02_ENDPOINT_COLUMNS}
        provenance = dict(row.get("provenance", {})) if isinstance(row.get("provenance"), Mapping) else {}
        provenance.setdefault("release_version", release.release_version)
        provenance.setdefault("contig_accession", row.get("reference_name"))
        result["provenance"] = provenance
        if detail:
            result["raw_accessions"] = row.get("raw_accessions", [])
            result["source"] = {"source_id": row.get("source_id"), "release_status": provenance.get("source_release_status")}
            result["publication"] = self._publication(row)
            result["source_annotations"] = row.get(
                "source_annotations_summary",
                {
                    "status": "not_loaded_in_c1",
                    "note": "annotation summary is pending the C1 annotation query extension",
                },
            )
            result["links"] = {
                "source": f"/api/v1/sources/{quote(str(row.get('source_id')))}",
                "download": f"/api/v1/downloads/endpoints?release_version={quote(release.release_version)}&source_id={quote(str(row.get('source_id')))}",
            }
            if row.get("source_id") == "BATTER_S1_002":
                result.pop("links", None)
        return result

    def list_endpoints(self, release_version: str | None, *, filters: Mapping[str, Any], page: int, page_size: int, sort: str, order: str) -> dict[str, Any]:
        release = self._release(release_version)
        page, page_size, offset = self._page(page, page_size)
        sort, descending = self._sort("endpoints", sort, order)
        normalized = self._validate_endpoint_filters(filters, release.release_version)
        assembly = normalized.get("assembly_accession")
        contig = normalized.get("contig_accession")
        source_ids = normalized.get("source_ids") or []
        try:
            if source_ids:
                self.repository.validate_source_ids(release, source_ids, published_only=True)
            if assembly:
                self.repository.validate_assembly(release, assembly)
            if assembly and contig:
                self.repository.validate_contig(release, assembly, contig)
            rows, total = self.repository.list_endpoints(release, normalized, offset=offset, limit=page_size, sort=sort, descending=descending)
        except RepositoryNotFound as exc:
            raise not_found("resource_not_found", str(exc), release_version=release.release_version) from exc
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        return self._page_response(release, (self._endpoint_item(release, row) for row in rows), total, page, page_size)

    def endpoint_detail(self, release_version: str | None, end_id: str) -> dict[str, Any]:
        release = self._release(release_version)
        try:
            row = self.repository.get_endpoint(release, end_id)
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        if row is None:
            raise not_found("endpoint_not_found", f"endpoint not found: {end_id}", field="end_id", release_version=release.release_version)
        return {"release": release.as_dict(), **self._endpoint_item(release, row, detail=True)}

    @staticmethod
    def _gene_item(release: ReleaseContext, row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "gene_id": row.get("gene_id"),
            "locus_tag": row.get("locus_tag"),
            "gene_name": row.get("gene_name"),
            "feature_type": row.get("feature_type"),
            "start_1based": row.get("start_1based"),
            "end_1based": row.get("end_1based"),
            "strand": row.get("strand"),
            "assembly_accession": row.get("assembly_accession"),
            "contig_accession": row.get("contig_accession"),
            "contig_name": row.get("contig_name"),
            "annotation_asset_id": row.get("annotation_asset_id"),
            "annotation_sha256": row.get("annotation_sha256"),
            "attributes": row.get("attributes", {}),
            "provenance": {
                "release_version": release.release_version,
                "assembly_accession": row.get("assembly_accession"),
                "contig_accession": row.get("contig_accession"),
                "annotation_asset_id": row.get("annotation_asset_id"),
                "annotation_sha256": row.get("annotation_sha256"),
            },
        }

    def list_genes(self, release_version: str | None, *, filters: Mapping[str, Any], page: int, page_size: int, sort: str, order: str) -> dict[str, Any]:
        release = self._release(release_version)
        page, page_size, offset = self._page(page, page_size)
        sort, descending = self._sort("genes", sort, order)
        normalized = dict(filters)
        for field in ("start_min", "start_max"):
            if normalized.get(field) is not None and (isinstance(normalized[field], bool) or not isinstance(normalized[field], int) or normalized[field] < 1):
                raise invalid("invalid_filter", f"{field} must be an integer >= 1", field=field, release_version=release.release_version)
        try:
            rows, total = self.repository.list_genes(release, normalized, offset=offset, limit=page_size, sort=sort, descending=descending)
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        return self._page_response(release, (self._gene_item(release, row) for row in rows), total, page, page_size)

    def gene_detail(self, release_version: str | None, gene_id: str) -> dict[str, Any]:
        release = self._release(release_version)
        try:
            row = self.repository.get_gene(release, gene_id)
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        if row is None:
            raise not_found("gene_not_found", f"gene not found: {gene_id}", field="gene_id", release_version=release.release_version)
        return {"release": release.as_dict(), **self._gene_item(release, row)}

    def asset(
        self,
        release_version: str | None,
        asset_id: str,
        *,
        method: str = "GET",
        range_header: str | None = None,
    ) -> AssetProxyResponse:
        release = self._release(release_version)
        try:
            return self.asset_proxy.fetch(
                release,
                asset_id,
                method=method,
                range_header=range_header,
            )
        except RepositoryNotFound as exc:
            raise not_found(
                "asset_not_found",
                f"public asset not found: {asset_id}",
                field="asset_id",
                release_version=release.release_version,
            ) from exc
        except RepositoryUnavailable as exc:
            raise ApiError(
                503,
                "repository_unavailable",
                "query repository is unavailable",
                release_version=release.release_version,
            ) from exc

    def augmentation(self, release_version: str | None, *, page: int, page_size: int) -> dict[str, Any]:
        release = self._release(release_version)
        page, page_size, offset = self._page(page, page_size)
        try:
            rows, total = self.repository.list_augmentation(release, offset=offset, limit=page_size)
        except RepositoryUnavailable as exc:
            raise ApiError(503, "repository_unavailable", "query repository is unavailable", release_version=release.release_version) from exc
        data = []
        for row in rows:
            source = self._source_item(release, row)
            data.append({
                "source_id": source["source_id"],
                "record_count": source["record_count"],
                "evidence_class": source["evidence_class"],
                "publication": source["publication"],
                "assembly_accession": source["assembly"].get("accession"),
                "provenance": source["provenance"],
            })
        return {
            "release": release.as_dict(),
            "scope": "source",
            "selection_rule": "BATTER Table S1 used_for_batter_augmentation = TRUE",
            "eligible_source_count": total,
            "training_claim": "none; source-level eligibility only",
            "data": data,
            "pagination": Page(page, page_size, len(data), total).as_dict(),
        }

    def _validate_download_filters(self, release: ReleaseContext, filters: Mapping[str, Any]) -> dict[str, Any]:
        normalized = self._validate_endpoint_filters(filters, release.release_version)
        source_ids = normalized.get("source_ids") or []
        assembly = normalized.get("assembly_accession")
        contig = normalized.get("contig_accession")
        try:
            if source_ids:
                self.repository.validate_source_ids(release, source_ids, published_only=True)
            if assembly:
                self.repository.validate_assembly(release, assembly)
            if assembly and contig:
                self.repository.validate_contig(release, assembly, contig)
        except RepositoryNotFound as exc:
            raise not_found("resource_not_found", str(exc), release_version=release.release_version) from exc
        return normalized

    def download_endpoints(self, release_version: str | None, *, filters: Mapping[str, Any], output_format: str = "tsv", include_annotations: bool = False) -> DownloadStream:
        release = self._release(release_version)
        if output_format not in {"tsv", "bed6"}:
            raise invalid("invalid_format", "format must be tsv or bed6", field="format", release_version=release.release_version)
        if include_annotations:
            raise invalid(
                "unsupported_annotation_download",
                "include_annotations is not available in the C1 read-only endpoint export",
                field="include_annotations",
                release_version=release.release_version,
            )
        normalized = self._validate_download_filters(release, filters)
        rows = self.repository.iter_endpoint_rows(release, normalized)

        def body() -> Iterator[str]:
            if output_format == "tsv":
                yield "\t".join(V02_ENDPOINT_COLUMNS) + "\n"
                for row in rows:
                    yield "\t".join(_json_text(row.get(column)) for column in V02_ENDPOINT_COLUMNS) + "\n"
            else:
                yield "chrom\tstart\tend\tname\tscore\tstrand\n"
                for row in rows:
                    # BED6 score is a display field; the original signal_or_score
                    # remains lossless in TSV and endpoint JSON.
                    yield "\t".join(
                        (
                            _json_text(row.get("reference_name")),
                            _json_text(row.get("bed_start_0based")),
                            _json_text(row.get("bed_end_0based")),
                            _json_text(row.get("end_id")),
                            "0",
                            _json_text(row.get("strand")),
                        )
                    ) + "\n"

        extension = "bed" if output_format == "bed6" else "tsv"
        return DownloadStream(
            body=body(),
            media_type="text/tab-separated-values; charset=utf-8",
            filename=f"BTED-{release.release_version}-endpoints.{extension}",
            headers={
                "X-BTED-Release-Version": release.release_version,
                "X-BTED-Manifest-SHA256": release.canonical_manifest_sha256,
                "Content-Disposition": f'attachment; filename="BTED-{release.release_version}-endpoints.{extension}"',
            },
        )
