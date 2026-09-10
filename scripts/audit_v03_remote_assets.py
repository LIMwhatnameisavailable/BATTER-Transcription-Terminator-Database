#!/usr/bin/env python3
"""Audit remote BTED public assets with HEAD and one byte-range request.

The input is the deterministic ``ASSET_OBJECTS.json`` produced by
``prepare_v03_public_asset_objects.py``.  URLs are derived only from each
registered ``object_path`` and the explicit HTTPS origin base; the manifest is
never treated as an arbitrary URL list.  This command performs no uploads,
retries, caching, or multi-range requests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen


MANIFEST_NAME = "ASSET_OBJECTS.json"
OUTPUT_NAME = "REMOTE_ASSET_AUDIT.json"
GENERATOR_VERSION = "bted-remote-asset-audit-0.2.0"


class RemoteAssetAuditError(ValueError):
    """Raised when the manifest or origin cannot be audited safely."""


class TransportResponse:
    """Small response shape used by the default and injected transports."""

    def __init__(self, status: int | None, headers: Mapping[str, str], body: bytes = b"") -> None:
        self.status = status
        self.headers = headers
        self.body = body


class Transport(Protocol):
    def request(self, method: str, url: str, headers: Mapping[str, str]) -> Any:
        """Return a response-like object for one HTTP request."""


class UrllibTransport:
    """Dependency-free HTTP transport used by the command-line entry point."""

    def request(self, method: str, url: str, headers: Mapping[str, str]) -> TransportResponse:
        request = Request(url, headers=dict(headers), method=method)
        try:
            with urlopen(request) as response:  # noqa: S310 - URL is derived locally below.
                return TransportResponse(
                    status=response.status,
                    headers=dict(response.headers.items()),
                    body=response.read(),
                )
        except HTTPError as error:
            return TransportResponse(
                status=error.code,
                headers=dict(error.headers.items()) if error.headers else {},
                body=error.read(),
            )
        except URLError:
            return TransportResponse(status=None, headers={})


def _normalize_origin_base(origin_base: str) -> str:
    parsed = urlsplit(origin_base)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RemoteAssetAuditError("--origin-base must be an explicit https:// URL")
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise RemoteAssetAuditError("--origin-base must not contain credentials, query, or fragment")
    path = parsed.path.rstrip("/")
    return urlunsplit(("https", parsed.netloc, path, "", ""))


def _safe_object_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise RemoteAssetAuditError("each object must have a non-empty object_path")
    if "\\" in value or "?" in value or "#" in value:
        raise RemoteAssetAuditError(f"unsafe object_path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise RemoteAssetAuditError(f"unsafe object_path: {value!r}")
    normalized = path.as_posix()
    if normalized != value or normalized.startswith("/"):
        raise RemoteAssetAuditError(f"unsafe object_path: {value!r}")
    return normalized


def _load_objects(manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RemoteAssetAuditError(f"cannot read asset manifest: {manifest_path}") from error
    if not isinstance(manifest, dict) or not isinstance(manifest.get("objects"), list):
        raise RemoteAssetAuditError("asset manifest must contain an objects list")

    objects: list[dict[str, Any]] = []
    seen_asset_ids: set[str] = set()
    seen_paths: set[str] = set()
    for raw in manifest["objects"]:
        if not isinstance(raw, dict):
            raise RemoteAssetAuditError("each asset manifest object must be an object")
        asset_id = raw.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            raise RemoteAssetAuditError("each object must have a non-empty asset_id")
        if asset_id in seen_asset_ids:
            raise RemoteAssetAuditError(f"duplicate asset_id: {asset_id}")
        seen_asset_ids.add(asset_id)
        object_path = _safe_object_path(raw.get("object_path"))
        if object_path in seen_paths:
            raise RemoteAssetAuditError(f"duplicate object_path: {object_path}")
        seen_paths.add(object_path)
        size = raw.get("byte_size")
        if isinstance(size, bool) or not isinstance(size, int) or size < 1:
            raise RemoteAssetAuditError(f"{asset_id}: byte_size must be a positive integer")
        sha256 = raw.get("sha256")
        if not isinstance(sha256, str) or not sha256:
            raise RemoteAssetAuditError(f"{asset_id}: sha256 must be a non-empty registered value")
        objects.append({
            "asset_id": asset_id,
            "object_path": object_path,
            "byte_size": size,
            "sha256": sha256,
        })
    return manifest, sorted(objects, key=lambda item: (item["object_path"], item["asset_id"]))


def _object_url(origin_base: str, object_path: str) -> str:
    encoded_path = quote(object_path, safe="/._-")
    return f"{origin_base}/{encoded_path}" if origin_base else encoded_path


def _header(headers: Mapping[str, Any], name: str) -> str | None:
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            return str(value)
    return None


def _response_parts(response: Any) -> TransportResponse:
    if isinstance(response, TransportResponse):
        return response
    if isinstance(response, tuple) and len(response) >= 2:
        status, headers = response[:2]
        body = response[2] if len(response) > 2 else b""
        return TransportResponse(status=int(status) if status is not None else None, headers=headers or {}, body=body or b"")
    status = getattr(response, "status", getattr(response, "status_code", None))
    headers = getattr(response, "headers", {}) or {}
    body = getattr(response, "body", getattr(response, "content", b"")) or b""
    return TransportResponse(status=int(status) if status is not None else None, headers=headers, body=body)


def _request(transport: Transport | Any, method: str, url: str, headers: Mapping[str, str]) -> TransportResponse:
    try:
        if hasattr(transport, "request"):
            response = transport.request(method, url, headers=headers)
        else:
            response = transport(method, url, headers)
        return _response_parts(response)
    except Exception:  # A failed remote request is recorded as a failed audit row.
        return TransportResponse(status=None, headers={})


def audit_remote_assets(
    manifest_path: Path,
    origin_base: str,
    *,
    output_path: Path | None = None,
    transport: Transport | Any | None = None,
) -> dict[str, Any]:
    """Audit every registered object and optionally write the deterministic report."""

    origin = _normalize_origin_base(origin_base)
    manifest, objects = _load_objects(manifest_path)
    active_transport = transport or UrllibTransport()
    records: list[dict[str, Any]] = []
    for item in objects:
        url = _object_url(origin, item["object_path"])
        head = _request(active_transport, "HEAD", url, {})
        ranged = _request(active_transport, "GET", url, {"Range": "bytes=0-0"})
        expected_range = f"bytes 0-0/{item['byte_size']}"
        head_ok = head.status == 200 and _header(head.headers, "Content-Length") == str(item["byte_size"])
        range_ok = (
            ranged.status == 206
            and _header(ranged.headers, "Content-Range") == expected_range
            and len(ranged.body) == 1
        )
        records.append({
            "asset_id": item["asset_id"],
            "object_path": item["object_path"],
            "url": url,
            "byte_size": item["byte_size"],
            "sha256": item["sha256"],
            "head_status": head.status,
            "range_status": ranged.status,
            "supports_range": range_ok,
            "ok": head_ok and range_ok,
        })

    audit: dict[str, Any] = {
        "schema_version": "1.1",
        "generator": "scripts/audit_v03_remote_assets.py",
        "generator_version": GENERATOR_VERSION,
        "release_version": manifest.get("release_version"),
        "manifest": manifest_path.name,
        "origin_base": origin,
        "objects": records,
        "summary": {
            "total": len(records),
            "ok": sum(1 for record in records if record["ok"]),
            "failed": sum(1 for record in records if not record["ok"]),
        },
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset_objects", nargs="?", type=Path, help="path to ASSET_OBJECTS.json")
    parser.add_argument("--asset-objects", "--manifest", dest="asset_objects_option", type=Path)
    parser.add_argument("--origin-base", required=True, help="explicit HTTPS origin base for registered object paths")
    parser.add_argument("--output", type=Path, help=f"audit output path (default: {OUTPUT_NAME} beside the manifest)")
    args = parser.parse_args()
    manifest_path = args.asset_objects_option or args.asset_objects
    if manifest_path is None:
        parser.error("an ASSET_OBJECTS.json path is required")
    output_path = args.output or manifest_path.parent / OUTPUT_NAME
    audit = audit_remote_assets(manifest_path, args.origin_base, output_path=output_path)
    print(f"{'PASS' if audit['summary']['failed'] == 0 else 'FAIL'} {audit['summary']['ok']}/{audit['summary']['total']} remote assets -> {output_path}")
    return 0 if audit["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
