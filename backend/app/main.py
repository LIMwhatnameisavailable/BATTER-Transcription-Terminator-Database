"""FastAPI application factory for the BTED v0.3 read API.

FastAPI is intentionally imported inside :func:`create_app`, so repository and
service contract tests remain runnable in the minimal data-curation
environment where web dependencies are not installed.
"""

from __future__ import annotations

from typing import Any, Callable

from .contracts import ReadRepository, RepositoryUnavailable
from .errors import ApiError
from .service import ReadService


def create_app(
    repository: ReadRepository | Callable[[], ReadRepository] | None = None,
    *,
    jbrowse_base: str = "/jbrowse/",
    asset_client: Any | None = None,
    asset_client_factory: Callable[[], Any] | None = None,
) -> Any:
    """Create the API app with an injectable repository or repository factory.

    Passing a factory is preferred for production: the PostgreSQL repository
    opens and closes a connection for each operation.  Passing a fake object
    is useful for offline API contract tests.
    """

    try:
        from fastapi import Depends, FastAPI, Header, Query, Request
        from fastapi.exceptions import RequestValidationError
        from fastapi.responses import JSONResponse, StreamingResponse
    except ImportError as exc:  # pragma: no cover - exercised when optional deps are absent
        raise RuntimeError(
            "FastAPI is not installed; install requirements-v03.txt to run the API"
        ) from exc

    from .repository import PostgresReadRepository

    app = FastAPI(title="BTED API", version="0.3.0", docs_url="/docs", redoc_url="/redoc")

    def get_repository() -> ReadRepository:
        if repository is None:
            return PostgresReadRepository.from_env()
        if callable(repository):
            return repository()
        return repository

    def get_service() -> ReadService:
        return ReadService(
            get_repository(),
            jbrowse_base=jbrowse_base,
            asset_client=asset_client,
            asset_client_factory=asset_client_factory,
        )

    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.as_dict(), headers=dict(exc.headers or {}))

    @app.exception_handler(RepositoryUnavailable)
    async def repository_error_handler(_: Request, exc: RepositoryUnavailable) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "repository_unavailable", "message": str(exc)}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        location = first.get("loc", [])
        field = str(location[-1]) if location else None
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_parameter",
                    "message": str(first.get("msg", "invalid request parameter")),
                    **({"field": field} if field else {}),
                }
            },
        )

    @app.get("/api/v1/health")
    def health(service: ReadService = Depends(get_service)) -> dict[str, Any]:
        return service.health()

    @app.get("/api/v1/stats")
    def stats(
        release_version: str | None = Query(default=None),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.stats(release_version)

    @app.get("/api/v1/sources")
    def sources(
        release_version: str | None = Query(default=None),
        source_id: str | None = Query(default=None),
        species: str | None = Query(default=None),
        assay_family: str | None = Query(default=None),
        release_status: str | None = Query(default=None),
        evidence_class: str | None = Query(default=None),
        assembly_accession: str | None = Query(default=None),
        augmentation_eligible: bool | None = Query(default=None),
        q: str | None = Query(default=None),
        page: int = Query(default=1),
        page_size: int = Query(default=50),
        sort: str = Query(default="source_id"),
        order: str = Query(default="asc"),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.list_sources(
            release_version,
            filters={
                "source_id": source_id, "species": species, "assay_family": assay_family,
                "release_status": release_status, "evidence_class": evidence_class,
                "assembly_accession": assembly_accession,
                "augmentation_eligible": augmentation_eligible, "q": q,
            },
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
        )

    @app.get("/api/v1/sources/{source_id}")
    def source_detail(
        source_id: str,
        release_version: str | None = Query(default=None),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.source_detail(release_version, source_id)

    @app.get("/api/v1/assemblies")
    def assemblies(
        release_version: str | None = Query(default=None),
        assembly_accession: str | None = Query(default=None),
        species: str | None = Query(default=None),
        contig_accession: str | None = Query(default=None),
        q: str | None = Query(default=None),
        page: int = Query(default=1),
        page_size: int = Query(default=50),
        sort: str = Query(default="assembly_accession"),
        order: str = Query(default="asc"),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.list_assemblies(
            release_version,
            filters={
                "assembly_accession": assembly_accession,
                "species": species,
                "contig_accession": contig_accession,
                "q": q,
            },
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
        )

    @app.get("/api/v1/assemblies/{assembly_id}")
    def assembly_detail(
        assembly_id: str,
        release_version: str | None = Query(default=None),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.assembly_detail(release_version, assembly_id)

    @app.get("/api/v1/assemblies/{assembly_id}/jbrowse-config")
    def assembly_jbrowse_config(
        assembly_id: str,
        source_id: str | None = Query(default=None),
        release_version: str | None = Query(default=None),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.jbrowse_config(release_version, assembly_id, source_id=source_id)

    @app.get("/api/v1/endpoints")
    def endpoints(
        release_version: str | None = Query(default=None),
        source_id: list[str] | None = Query(default=None),
        assembly_accession: str | None = Query(default=None),
        contig_accession: str | None = Query(default=None),
        sample_id: str | None = Query(default=None),
        strand: str | None = Query(default=None),
        evidence_class: str | None = Query(default=None),
        author_category: str | None = Query(default=None),
        gene_or_locus: str | None = Query(default=None),
        position_min: int | None = Query(default=None),
        position_max: int | None = Query(default=None),
        q: str | None = Query(default=None),
        page: int = Query(default=1),
        page_size: int = Query(default=50),
        sort: str = Query(default="end_id"),
        order: str = Query(default="asc"),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.list_endpoints(
            release_version,
            filters={
                "source_ids": source_id or [], "assembly_accession": assembly_accession,
                "contig_accession": contig_accession, "sample_id": sample_id, "strand": strand,
                "evidence_class": evidence_class, "author_category": author_category,
                "gene_or_locus": gene_or_locus, "position_min": position_min,
                "position_max": position_max, "q": q,
            },
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
        )

    @app.get("/api/v1/endpoints/{end_id}")
    def endpoint_detail(
        end_id: str,
        release_version: str | None = Query(default=None),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.endpoint_detail(release_version, end_id)

    @app.get("/api/v1/genes")
    def genes(
        release_version: str | None = Query(default=None),
        assembly_accession: str | None = Query(default=None),
        contig_accession: str | None = Query(default=None),
        gene_id: str | None = Query(default=None),
        locus_tag: str | None = Query(default=None),
        feature_type: str | None = Query(default=None),
        start_min: int | None = Query(default=None),
        start_max: int | None = Query(default=None),
        page: int = Query(default=1),
        page_size: int = Query(default=50),
        sort: str = Query(default="contig_accession"),
        order: str = Query(default="asc"),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.list_genes(
            release_version,
            filters={
                "assembly_accession": assembly_accession, "contig_accession": contig_accession,
                "gene_id": gene_id, "locus_tag": locus_tag, "feature_type": feature_type,
                "start_min": start_min, "start_max": start_max,
            },
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
        )

    @app.get("/api/v1/genes/{gene_id}")
    def gene_detail(
        gene_id: str,
        release_version: str | None = Query(default=None),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.gene_detail(release_version, gene_id)

    @app.get("/api/v1/augmentation")
    def augmentation(
        release_version: str | None = Query(default=None),
        page: int = Query(default=1),
        page_size: int = Query(default=50),
        service: ReadService = Depends(get_service),
    ) -> dict[str, Any]:
        return service.augmentation(release_version, page=page, page_size=page_size)

    @app.get("/api/v1/downloads/endpoints")
    def download_endpoints(
        release_version: str | None = Query(default=None),
        source_id: list[str] | None = Query(default=None),
        assembly_accession: str | None = Query(default=None),
        contig_accession: str | None = Query(default=None),
        evidence_class: str | None = Query(default=None),
        strand: str | None = Query(default=None),
        gene_or_locus: str | None = Query(default=None),
        position_min: int | None = Query(default=None),
        position_max: int | None = Query(default=None),
        format: str = Query(default="tsv"),
        include_annotations: bool = Query(default=False),
        service: ReadService = Depends(get_service),
    ) -> Any:
        stream = service.download_endpoints(
            release_version,
            filters={
                "source_ids": source_id or [], "assembly_accession": assembly_accession,
                "contig_accession": contig_accession, "evidence_class": evidence_class,
                "strand": strand, "gene_or_locus": gene_or_locus,
                "position_min": position_min, "position_max": position_max,
            },
            output_format=format,
            include_annotations=include_annotations,
        )
        return StreamingResponse(stream.body, media_type=stream.media_type, headers=stream.headers)

    def _asset_response(
        asset_id: str,
        *,
        method: str,
        range_header: str | None,
        release_version: str | None,
        service: ReadService,
    ) -> Any:
        proxied = service.asset(
            release_version,
            asset_id,
            method=method,
            range_header=range_header,
        )
        body = proxied.body if method == "GET" else iter(())
        return StreamingResponse(
            body,
            status_code=proxied.status_code,
            media_type=None,
            headers=proxied.headers,
        )

    @app.get("/api/v1/assets/{asset_id}")
    def asset_get(
        asset_id: str,
        range_header: str | None = Header(default=None, alias="Range"),
        release_version: str | None = Query(default=None),
        service: ReadService = Depends(get_service),
    ) -> Any:
        return _asset_response(
            asset_id,
            method="GET",
            range_header=range_header,
            release_version=release_version,
            service=service,
        )

    @app.head("/api/v1/assets/{asset_id}")
    def asset_head(
        asset_id: str,
        range_header: str | None = Header(default=None, alias="Range"),
        release_version: str | None = Query(default=None),
        service: ReadService = Depends(get_service),
    ) -> Any:
        return _asset_response(
            asset_id,
            method="HEAD",
            range_header=range_header,
            release_version=release_version,
            service=service,
        )

    return app
