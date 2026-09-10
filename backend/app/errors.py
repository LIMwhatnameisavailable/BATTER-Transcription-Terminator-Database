"""Stable JSON error contract for the BTED API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    field: str | None = None
    release_version: str | None = None
    headers: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def as_dict(self) -> dict[str, Any]:
        error: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.field is not None:
            error["field"] = self.field
        if self.release_version is not None:
            error["release_version"] = self.release_version
        return {"error": error}


def not_found(code: str, message: str, *, field: str | None = None, release_version: str | None = None) -> ApiError:
    return ApiError(404, code, message, field, release_version)


def invalid(code: str, message: str, *, field: str | None = None, release_version: str | None = None) -> ApiError:
    return ApiError(422, code, message, field, release_version)
