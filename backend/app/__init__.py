"""BTED v0.3 read-only API package.

Importing this package does not require FastAPI, psycopg3, or a running
database.  Use :func:`create_app` in an environment with the optional web
dependencies installed.
"""

from .contracts import Page, ReadRepository, ReleaseContext, RepositoryNotFound, RepositoryUnavailable
from .errors import ApiError
from .main import create_app
from .repository import PostgresReadRepository
from .service import DownloadStream, ReadService

__all__ = [
    "ApiError",
    "DownloadStream",
    "Page",
    "PostgresReadRepository",
    "ReadRepository",
    "ReadService",
    "ReleaseContext",
    "RepositoryNotFound",
    "RepositoryUnavailable",
    "create_app",
]
