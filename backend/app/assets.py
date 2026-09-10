"""Read-only proxy for public BTED release assets.

The database row is the allowlist.  The proxy never accepts an origin URL from
the request and only forwards to the HTTPS URL registered for that asset.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Mapping
from urllib.parse import urlsplit

from .contracts import ReadRepository, ReleaseContext, RepositoryNotFound
from .errors import ApiError


@dataclass(frozen=True)
class AssetProxyResponse:
    status_code: int
    headers: dict[str, str]
    body: Iterator[bytes]


@dataclass(frozen=True)
class _ByteRange:
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start + 1


_RANGE_RE = re.compile(r"^bytes=([^,]+)$", re.IGNORECASE)


def _parse_range(value: str | None, size: int) -> _ByteRange | None:
    if value is None:
        return None
    match = _RANGE_RE.fullmatch(value.strip())
    if match is None or size <= 0:
        raise ValueError("only one bytes range is supported")
    spec = match.group(1).strip()
    if "-" not in spec:
        raise ValueError("invalid bytes range")
    start_text, end_text = (part.strip() for part in spec.split("-", 1))
    try:
        if start_text:
            start = int(start_text)
            if start < 0 or start >= size:
                raise ValueError("range start is outside the asset")
            if end_text:
                end = int(end_text)
                if end < start or end >= size:
                    raise ValueError("range end is outside the asset")
            else:
                end = size - 1
            return _ByteRange(start, end)
        if not end_text:
            raise ValueError("range suffix is empty")
        suffix = int(end_text)
        if suffix <= 0 or suffix > size:
            raise ValueError("range suffix is outside the asset")
        return _ByteRange(size - suffix, size - 1)
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("range "):
            raise
        raise ValueError("invalid bytes range") from exc


class AssetProxyService:
    """Resolve a public asset and stream it from its registered HTTPS origin."""

    def __init__(
        self,
        repository: ReadRepository,
        *,
        http_client: Any | None = None,
        http_client_factory: Callable[[], Any] | None = None,
    ) -> None:
        if http_client is not None and http_client_factory is not None:
            raise ValueError("provide either http_client or http_client_factory, not both")
        self.repository = repository
        self.http_client = http_client
        self.http_client_factory = http_client_factory

    @staticmethod
    def _range_error(release: ReleaseContext, size: int, message: str) -> ApiError:
        return ApiError(
            416,
            "range_not_satisfiable",
            message,
            field="range",
            release_version=release.release_version,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Range": f"bytes */{size}",
                "X-BTED-Release-Version": release.release_version,
            },
        )

    @staticmethod
    def _base_headers(asset: Mapping[str, Any], release: ReleaseContext) -> dict[str, str]:
        size = int(asset["byte_size"])
        sha256 = str(asset["sha256"])
        return {
            "Accept-Ranges": "bytes" if bool(asset.get("supports_range")) else "none",
            "Content-Length": str(size),
            "Content-Type": str(asset.get("mime_type") or "application/octet-stream"),
            "ETag": f'"sha256:{sha256}"',
            "X-BTED-Release-Version": release.release_version,
        }

    @staticmethod
    def _validate_origin(asset: Mapping[str, Any]) -> str:
        origin_url = str(asset.get("origin_url") or "")
        origin_host = str(asset.get("origin_host") or "").lower()
        parsed = urlsplit(origin_url)
        if parsed.scheme.lower() != "https" or not parsed.hostname or not origin_host:
            raise ApiError(502, "invalid_asset_origin", "registered asset origin is not a valid HTTPS URL")
        if parsed.hostname.lower() != origin_host:
            raise ApiError(502, "invalid_asset_origin", "registered asset origin host does not match its allowlist")
        return origin_url

    def _client(self) -> tuple[Any, bool]:
        if self.http_client is not None:
            return self.http_client, False
        if self.http_client_factory is not None:
            return self.http_client_factory(), False
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - optional runtime dependency
            raise ApiError(503, "asset_proxy_unavailable", "httpx is not installed") from exc
        return httpx.Client(follow_redirects=False, timeout=60.0), True

    @staticmethod
    def _close_client(client: Any, owned: bool) -> None:
        if owned:
            close = getattr(client, "close", None)
            if callable(close):
                close()

    def fetch(
        self,
        release: ReleaseContext,
        asset_id: str,
        *,
        method: str = "GET",
        range_header: str | None = None,
    ) -> AssetProxyResponse:
        asset = self.repository.get_public_asset(release, asset_id)
        if asset is None:
            raise RepositoryNotFound(f"public asset not found: {asset_id}")

        size = int(asset["byte_size"])
        response_headers = self._base_headers(asset, release)
        try:
            byte_range = _parse_range(range_header, size)
        except ValueError as exc:
            raise self._range_error(release, size, str(exc)) from exc
        if byte_range is not None and not bool(asset.get("supports_range")):
            raise self._range_error(release, size, "this asset does not support byte ranges")

        origin_url = self._validate_origin(asset)
        request_method = method.upper()
        if request_method not in {"GET", "HEAD"}:
            raise ApiError(405, "method_not_allowed", "asset endpoint supports GET and HEAD")
        request_headers = {"Accept-Encoding": "identity"}
        if byte_range is not None:
            request_headers["Range"] = f"bytes={byte_range.start}-{byte_range.end}"

        client, owned = self._client()
        try:
            request = client.build_request(request_method, origin_url, headers=request_headers)
            upstream = client.send(request, stream=True)
        except ApiError:
            self._close_client(client, owned)
            raise
        except Exception as exc:
            self._close_client(client, owned)
            raise ApiError(502, "asset_origin_unavailable", "registered asset origin is unavailable") from exc

        expected_status = 206 if byte_range is not None else 200
        if upstream.status_code != expected_status:
            upstream.close()
            self._close_client(client, owned)
            raise ApiError(502, "asset_origin_invalid_response", "registered asset origin returned an unexpected status")

        if byte_range is not None:
            expected_content_range = f"bytes {byte_range.start}-{byte_range.end}/{size}"
            actual_content_range = upstream.headers.get("Content-Range", "")
            upstream_length = upstream.headers.get("Content-Length")
            if actual_content_range != expected_content_range or upstream_length not in {None, str(byte_range.length)}:
                upstream.close()
                self._close_client(client, owned)
                raise ApiError(502, "asset_origin_invalid_response", "registered asset origin returned an invalid byte range")
            response_headers["Content-Range"] = expected_content_range
            response_headers["Content-Length"] = str(byte_range.length)

        if request_method == "HEAD":
            upstream.close()
            self._close_client(client, owned)
            return AssetProxyResponse(206 if byte_range is not None else 200, response_headers, iter(()))

        def body() -> Iterator[bytes]:
            try:
                yield from upstream.iter_bytes()
            finally:
                upstream.close()
                self._close_client(client, owned)

        return AssetProxyResponse(206 if byte_range is not None else 200, response_headers, body())
