"""Offline tests for the v0.3 public asset proxy."""

from __future__ import annotations

import importlib.util
import unittest
from typing import Any, Mapping

import httpx

from backend.app.assets import AssetProxyService
from backend.app.contracts import ReleaseContext, RepositoryNotFound
from backend.app.errors import ApiError
from backend.app.repository import PostgresReadRepository
from backend.app.service import ReadService


RELEASE = ReleaseContext("v0.3.0", "published", "a" * 64, 17)
ORIGIN = "https://assets.example.test/records/sample.bin"
PAYLOAD = b"0123456789"


class AssetRepository:
    def __init__(self, *, public: bool = True, supports_range: bool = True) -> None:
        self.asset = {
            "asset_id": "sample--bed",
            "release_version": RELEASE.release_version,
            "asset_kind": "bed",
            "logical_path": "records/sample/endpoints.bed",
            "origin_url": ORIGIN,
            "origin_host": "assets.example.test",
            "byte_size": len(PAYLOAD),
            "sha256": "b" * 64,
            "mime_type": "text/plain",
            "supports_range": supports_range,
            "redistribution_status": "verified_redistributable",
            "is_public": public,
        }

    def resolve_release(self, release_version: str | None = None) -> ReleaseContext:
        if release_version not in (None, RELEASE.release_version):
            raise RepositoryNotFound("release not found")
        return RELEASE

    def get_public_asset(self, release: ReleaseContext, asset_id: str) -> Mapping[str, Any] | None:
        if asset_id != self.asset["asset_id"] or not self.asset["is_public"]:
            return None
        return self.asset


class TestAssetProxy(unittest.TestCase):
    def setUp(self) -> None:
        self.requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            if request.method == "HEAD":
                return httpx.Response(200, headers={"Content-Length": str(len(PAYLOAD))}, request=request)
            range_value = request.headers.get("range")
            if range_value:
                start, end = (int(value) for value in range_value.removeprefix("bytes=").split("-"))
                body = PAYLOAD[start:end + 1]
                return httpx.Response(
                    206,
                    headers={
                        "Content-Range": f"bytes {start}-{end}/{len(PAYLOAD)}",
                        "Content-Length": str(len(body)),
                    },
                    content=body,
                    request=request,
                )
            return httpx.Response(200, headers={"Content-Length": str(len(PAYLOAD))}, content=PAYLOAD, request=request)

        self.client = httpx.Client(transport=httpx.MockTransport(handler))
        self.repository = AssetRepository()
        self.service = ReadService(self.repository, asset_client=self.client)

    def tearDown(self) -> None:
        self.client.close()

    def test_get_forwards_registered_origin_and_headers(self) -> None:
        response = self.service.asset(None, "sample--bed")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.body), PAYLOAD)
        self.assertEqual(response.headers["Content-Length"], "10")
        self.assertEqual(response.headers["Content-Type"], "text/plain")
        self.assertEqual(response.headers["ETag"], f'"sha256:{"b" * 64}"')
        self.assertEqual(response.headers["X-BTED-Release-Version"], "v0.3.0")
        self.assertEqual(str(self.requests[-1].url), ORIGIN)
        self.assertNotIn("url", str(self.requests[-1].url))

    def test_head_has_same_headers_and_no_body(self) -> None:
        response = self.service.asset(None, "sample--bed", method="HEAD")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.body), [])
        self.assertEqual(response.headers["Content-Length"], "10")
        self.assertEqual(self.requests[-1].method, "HEAD")

    def test_single_range_forms_return_206(self) -> None:
        response = self.service.asset(None, "sample--bed", range_header="bytes=2-5")
        self.assertEqual(response.status_code, 206)
        self.assertEqual(b"".join(response.body), b"2345")
        self.assertEqual(response.headers["Content-Range"], "bytes 2-5/10")
        self.assertEqual(response.headers["Content-Length"], "4")

        response = self.service.asset(None, "sample--bed", range_header="bytes=6-")
        self.assertEqual(b"".join(response.body), b"6789")

        response = self.service.asset(None, "sample--bed", range_header="bytes=-3")
        self.assertEqual(b"".join(response.body), b"789")

    def test_invalid_or_multiple_range_returns_416_without_origin_request(self) -> None:
        before = len(self.requests)
        with self.assertRaises(ApiError) as error:
            self.service.asset(None, "sample--bed", range_header="bytes=20-21")
        self.assertEqual(error.exception.status_code, 416)
        self.assertEqual(len(self.requests), before)

        with self.assertRaises(ApiError) as error:
            self.service.asset(None, "sample--bed", range_header="bytes=0-1,4-5")
        self.assertEqual(error.exception.status_code, 416)
        self.assertEqual(len(self.requests), before)

    def test_non_range_asset_rejects_range(self) -> None:
        service = ReadService(AssetRepository(supports_range=False), asset_client=self.client)
        with self.assertRaises(ApiError) as error:
            service.asset(None, "sample--bed", range_header="bytes=0-1")
        self.assertEqual(error.exception.status_code, 416)

    def test_unknown_or_private_asset_is_404(self) -> None:
        with self.assertRaises(ApiError) as error:
            self.service.asset(None, "missing")
        self.assertEqual(error.exception.status_code, 404)
        private = ReadService(AssetRepository(public=False), asset_client=self.client)
        with self.assertRaises(ApiError) as error:
            private.asset(None, "sample--bed")
        self.assertEqual(error.exception.status_code, 404)


class _AssetCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchone(self) -> tuple[Any, ...]:
        return (
            "sample--bed", RELEASE.release_version, "bed", "records/sample/endpoints.bed",
            ORIGIN, "assets.example.test", len(PAYLOAD), "b" * 64, "text/plain", True,
            "verified_redistributable", True,
        )

    def close(self) -> None:
        self.closed = True


class _AssetConnection:
    def __init__(self) -> None:
        self.cursor_instance = _AssetCursor()
        self.closed = False

    def cursor(self) -> _AssetCursor:
        return self.cursor_instance

    def close(self) -> None:
        self.closed = True


class TestPublicAssetRepository(unittest.TestCase):
    def test_public_asset_query_is_parameterized_and_release_scoped(self) -> None:
        connection = _AssetConnection()
        repository = PostgresReadRepository(lambda: connection)
        asset = repository.get_public_asset(RELEASE, "sample--bed")
        self.assertEqual(asset["asset_id"], "sample--bed")
        sql, params = connection.cursor_instance.calls[0]
        self.assertIn("a.is_public = TRUE", sql)
        self.assertIn("r.status = 'published'", sql)
        self.assertIn("%s", sql)
        self.assertEqual(params, ("sample--bed", "v0.3.0"))
        self.assertTrue(connection.cursor_instance.closed)
        self.assertTrue(connection.closed)


@unittest.skipUnless(importlib.util.find_spec("fastapi"), "FastAPI optional dependency is not installed")
class TestAssetHttpRoute(unittest.TestCase):
    def setUp(self) -> None:
        from backend.app.main import create_app
        from fastapi.testclient import TestClient

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "HEAD":
                return httpx.Response(200, request=request)
            if request.headers.get("range") == "bytes=0-2":
                return httpx.Response(
                    206,
                    headers={"Content-Range": "bytes 0-2/10", "Content-Length": "3"},
                    content=PAYLOAD[:3],
                    request=request,
                )
            return httpx.Response(200, content=PAYLOAD, request=request)

        self.upstream = httpx.Client(transport=httpx.MockTransport(handler))
        self.client = TestClient(create_app(AssetRepository(), asset_client=self.upstream))

    def tearDown(self) -> None:
        self.upstream.close()

    def test_get_head_range_404_416_and_no_arbitrary_url(self) -> None:
        response = self.client.get("/api/v1/assets/sample--bed?url=https://evil.example/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, PAYLOAD)
        self.assertEqual(response.headers["x-bted-release-version"], "v0.3.0")
        self.assertEqual(self.client.head("/api/v1/assets/sample--bed").status_code, 200)
        ranged = self.client.get("/api/v1/assets/sample--bed", headers={"Range": "bytes=0-2"})
        self.assertEqual(ranged.status_code, 206)
        self.assertEqual(ranged.content, PAYLOAD[:3])
        invalid = self.client.get("/api/v1/assets/sample--bed", headers={"Range": "bytes=8-20"})
        self.assertEqual(invalid.status_code, 416)
        self.assertEqual(invalid.headers["content-range"], "bytes */10")
        missing = self.client.get("/api/v1/assets/missing")
        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
