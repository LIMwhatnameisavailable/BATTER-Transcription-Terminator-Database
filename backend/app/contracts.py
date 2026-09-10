"""Small, dependency-free contracts shared by the BTED read API.

The query layer deliberately keeps these objects as dataclasses/plain mappings.
FastAPI/Pydantic is an optional transport dependency; repository and service
tests can therefore run without installing a web framework or a database
driver.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Mapping, Protocol, Sequence


class RepositoryNotFound(LookupError):
    """A release or resource is not public in the requested release."""


class RepositoryUnavailable(RuntimeError):
    """The read repository could not reach its backing database."""


@dataclass(frozen=True)
class ReleaseContext:
    release_version: str
    status: str
    canonical_manifest_sha256: str
    import_run_id: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "release_version": self.release_version,
            "status": self.status,
            "canonical_manifest_sha256": self.canonical_manifest_sha256,
            "import_run_id": self.import_run_id,
        }


@dataclass(frozen=True)
class Page:
    page: int
    page_size: int
    returned: int
    total: int

    @property
    def has_next(self) -> bool:
        return self.page * self.page_size < self.total

    def as_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "returned": self.returned,
            "total": self.total,
            "has_next": self.has_next,
        }


class ReadRepository(Protocol):
    """Repository surface consumed by :class:`ReadService`.

    A fake implementation can satisfy this protocol with in-memory mappings.
    The PostgreSQL implementation keeps SQL details below this boundary.
    """

    def resolve_release(self, release_version: str | None = None) -> ReleaseContext: ...

    def health(self) -> Mapping[str, Any]: ...

    def stats(self, release: ReleaseContext) -> Mapping[str, Any]: ...

    def list_sources(self, release: ReleaseContext, filters: Mapping[str, Any], *, offset: int, limit: int, sort: str, descending: bool) -> tuple[list[Mapping[str, Any]], int]: ...

    def get_source(self, release: ReleaseContext, source_id: str) -> Mapping[str, Any] | None: ...

    def list_assemblies(self, release: ReleaseContext, filters: Mapping[str, Any], *, offset: int, limit: int, sort: str, descending: bool) -> tuple[list[Mapping[str, Any]], int]: ...

    def get_assembly(self, release: ReleaseContext, assembly_accession: str) -> Mapping[str, Any] | None: ...

    def get_jbrowse_bundle(self, release: ReleaseContext, assembly_accession: str) -> Mapping[str, Any] | None: ...

    def list_endpoints(self, release: ReleaseContext, filters: Mapping[str, Any], *, offset: int, limit: int, sort: str, descending: bool) -> tuple[list[Mapping[str, Any]], int]: ...

    def get_endpoint(self, release: ReleaseContext, end_id: str) -> Mapping[str, Any] | None: ...

    def list_genes(self, release: ReleaseContext, filters: Mapping[str, Any], *, offset: int, limit: int, sort: str, descending: bool) -> tuple[list[Mapping[str, Any]], int]: ...

    def get_gene(self, release: ReleaseContext, gene_id: str) -> Mapping[str, Any] | None: ...

    def get_public_asset(self, release: ReleaseContext, asset_id: str) -> Mapping[str, Any] | None: ...

    def list_augmentation(self, release: ReleaseContext, *, offset: int, limit: int) -> tuple[list[Mapping[str, Any]], int]: ...

    def validate_source_ids(self, release: ReleaseContext, source_ids: Sequence[str], *, published_only: bool = False) -> None: ...

    def validate_assembly(self, release: ReleaseContext, assembly_accession: str) -> None: ...

    def validate_contig(self, release: ReleaseContext, assembly_accession: str, contig_accession: str) -> None: ...

    def iter_endpoint_rows(self, release: ReleaseContext, filters: Mapping[str, Any]) -> Iterator[Mapping[str, Any]]: ...
