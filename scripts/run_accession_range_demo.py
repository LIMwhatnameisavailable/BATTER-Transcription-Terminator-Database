#!/usr/bin/env python3
"""Serve the BTED accession/Range prototype with a local object backend.

The routes mirror the proposed production contract:

* ``/api/assemblies/{accession}`` returns assembly and track metadata;
* ``/api/assemblies/{accession}/jbrowse-config`` builds JBrowse config at request time;
* ``/api/remote-data/{asset_key}`` is an allowlisted, byte-Range-aware object proxy.

Local files stand in for future checksum-verified Hugging Face objects.  The
browser-facing API is intentionally the same so the UI can be tested before an
external upload or Cloudflare account is required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = REPO_ROOT / "prototype/accession-range/registry.json"
RANGE_PATTERN = re.compile(r"^bytes=(\d*)-(\d*)$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_and_validate_registry(registry_path: Path, asset_dir: Path) -> dict[str, Any]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for asset_key, asset in registry["assets"].items():
        source_assets = asset.get("equivalent_source_assets", [asset["source_asset"]])
        for filename in source_assets:
            path = asset_dir / filename
            if not path.is_file():
                raise FileNotFoundError(f"{asset_key}: missing local object {path}")
            if path.stat().st_size != int(asset["byte_size"]):
                raise ValueError(f"{asset_key}: byte size differs for {filename}")
            if sha256(path) != asset["sha256"]:
                raise ValueError(f"{asset_key}: SHA-256 differs for {filename}")
    return registry


def asset_url(base_url: str, asset_key: str) -> str:
    return f"{base_url}/api/remote-data/{quote(asset_key, safe='')}"


def build_assembly_payload(registry: dict[str, Any], accession: str, base_url: str) -> dict[str, Any] | None:
    assembly = registry["assemblies"].get(accession)
    if assembly is None:
        return None
    asset_keys = set(assembly["reference_assets"].values())
    asset_keys.update(track["asset_key"] for track in assembly["tracks"])
    assets = []
    for key in sorted(asset_keys):
        entry = registry["assets"][key]
        assets.append({
            "asset_key": key,
            "role": entry["role"],
            "format": entry["format"],
            "byte_size": entry["byte_size"],
            "sha256": entry["sha256"],
            "object_path": entry["object_path"],
            "range_url": asset_url(base_url, key),
        })
    tracks = []
    for track in assembly["tracks"]:
        tracks.append({**track, "range_url": asset_url(base_url, track["asset_key"])})
    return {
        "schema_version": registry["schema_version"],
        "delivery_mode": "accession_lookup_same_origin_range_proxy",
        "origin_backend": registry["prototype_status"],
        "production_origin": registry["production_origin"],
        "assembly": {
            "accession": accession,
            "display_name": assembly["display_name"],
            "reference_name": assembly["reference_name"],
            "reference_length": assembly["reference_length"],
        },
        "record_count": assembly["record_count"],
        "source_ids": assembly["source_ids"],
        "duplicate_reference_bytes_avoided": assembly["duplicate_reference_bytes_avoided"],
        "assets": assets,
        "tracks": tracks,
        "jbrowse_config_url": f"{base_url}/api/assemblies/{quote(accession, safe='')}/jbrowse-config",
    }


def build_jbrowse_config(payload: dict[str, Any], base_url: str) -> dict[str, Any]:
    by_role = {asset["role"]: asset for asset in payload["assets"]}
    accession = payload["assembly"]["accession"]
    assembly_name = f"BTED_EDGE_{accession.replace('.', '_')}"
    gene_track_id = f"{assembly_name}_genes"
    track_configs = []
    for track in payload["tracks"]:
        track_configs.append({
            "type": "FeatureTrack",
            "trackId": track["track_id"],
            "name": f"{track['source_id']} · {track['name']}",
            "adapter": {
                "type": "BedAdapter",
                "bedLocation": {"uri": track["range_url"], "locationType": "UriLocation"},
            },
            "displays": [{
                "type": "LinearBasicDisplay",
                "displayId": f"{track['track_id']}_display",
                "showLabels": False,
                "height": 38,
            }],
            "category": ["BTED source tracks", track["source_id"]],
            "assemblyNames": [assembly_name],
            "metadata": {
                "source_id": track["source_id"],
                "assay": track["assay"],
                "evidence_class": track["evidence_class"],
                "record_count": track["record_count"],
                "delivery": "same-origin Range proxy",
            },
        })
    track_ids = [gene_track_id, *(track["track_id"] for track in payload["tracks"])]
    return {
        "assemblies": [{
            "name": assembly_name,
            "displayName": f"{payload['assembly']['display_name']} ({accession}) · edge prototype",
            "sequence": {
                "type": "ReferenceSequenceTrack",
                "trackId": f"{assembly_name}_refseq",
                "adapter": {
                    "type": "IndexedFastaAdapter",
                    "fastaLocation": {"uri": by_role["reference_sequence"]["range_url"], "locationType": "UriLocation"},
                    "faiLocation": {"uri": by_role["reference_index"]["range_url"], "locationType": "UriLocation"},
                },
            },
        }],
        "configuration": {},
        "connections": [],
        "tracks": [{
            "type": "FeatureTrack",
            "trackId": gene_track_id,
            "name": "NCBI gene annotation · one shared assembly object",
            "adapter": {
                "type": "Gff3TabixAdapter",
                "gffGzLocation": {"uri": by_role["gene_annotation"]["range_url"], "locationType": "UriLocation"},
                "index": {
                    "location": {"uri": by_role["gene_annotation_index"]["range_url"], "locationType": "UriLocation"},
                    "indexType": "TBI",
                },
            },
            "category": ["Reference annotation"],
            "assemblyNames": [assembly_name],
            "metadata": {"delivery": "same-origin Range proxy"},
        }, *track_configs],
        "defaultSession": {
            "name": f"{accession} · accession-driven remote tracks",
            "views": [{
                "id": "bted_edge_linear_genome_view",
                "type": "LinearGenomeView",
                "offsetPx": 0,
                "bpPerPx": 10.001,
                "displayedRegions": [{
                    "refName": payload["assembly"]["reference_name"],
                    "start": 62367,
                    "end": 72368,
                    "reversed": False,
                    "assemblyName": assembly_name,
                }],
                "tracks": [{
                    "id": f"bted_edge_track_{index + 1}",
                    "type": "FeatureTrack",
                    "configuration": track_id,
                    "minimized": False,
                    "displays": [{
                        "id": f"bted_edge_display_{index + 1}",
                        "type": "LinearBasicDisplay",
                        "configuration": (
                            f"{track_id}-LinearBasicDisplay" if index == 0 else f"{track_id}_display"
                        ),
                    }],
                } for index, track_id in enumerate(track_ids)],
            }],
        },
    }


def parse_byte_range(value: str | None, size: int) -> tuple[int, int] | None:
    if not value:
        return None
    match = RANGE_PATTERN.fullmatch(value.strip())
    if not match or (not match.group(1) and not match.group(2)):
        raise ValueError("unsupported Range header")
    start_text, end_text = match.groups()
    if not start_text:
        suffix = int(end_text)
        if suffix <= 0:
            raise ValueError("invalid suffix range")
        start = max(0, size - suffix)
        end = size - 1
    else:
        start = int(start_text)
        end = int(end_text) if end_text else size - 1
    if start >= size or start < 0 or end < start:
        raise ValueError("range outside object")
    return start, min(end, size - 1)


class DemoHandler(SimpleHTTPRequestHandler):
    registry: dict[str, Any]
    asset_dir: Path

    def _base_url(self) -> str:
        return f"http://{self.headers.get('Host', '127.0.0.1')}"

    def _json(self, payload: dict[str, Any], status: int = 200, head_only: bool = False) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _serve_api(self, head_only: bool) -> bool:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json({
                "status": "ok",
                "backend": "local checksum-verified objects",
                "production_target": "Cloudflare D1 + Hugging Face Range proxy",
            }, head_only=head_only)
            return True
        prefix = "/api/remote-data/"
        if path.startswith(prefix):
            asset_key = unquote(path[len(prefix):])
            self._serve_object(asset_key, head_only)
            return True
        match = re.fullmatch(r"/api/assemblies/([^/]+)(/jbrowse-config)?", path)
        if not match:
            return False
        accession = unquote(match.group(1))
        payload = build_assembly_payload(self.registry, accession, self._base_url())
        if payload is None:
            self._json({"error": "assembly_not_found", "accession": accession}, 404, head_only)
        elif match.group(2):
            self._json(build_jbrowse_config(payload, self._base_url()), head_only=head_only)
        else:
            self._json(payload, head_only=head_only)
        return True

    def _serve_object(self, asset_key: str, head_only: bool) -> None:
        asset = self.registry["assets"].get(asset_key)
        if asset is None:
            self._json({"error": "unknown_asset", "asset_key": asset_key}, 404, head_only)
            return
        path = self.asset_dir / asset["source_asset"]
        size = path.stat().st_size
        try:
            selected = parse_byte_range(self.headers.get("Range"), size)
        except ValueError:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return
        start, end = selected if selected is not None else (0, size - 1)
        length = end - start + 1
        self.send_response(HTTPStatus.PARTIAL_CONTENT if selected is not None else HTTPStatus.OK)
        self.send_header("Content-Type", asset["content_type"])
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        self.send_header("ETag", f'"sha256-{asset["sha256"]}"')
        self.send_header("X-BTED-Asset-Key", asset_key)
        self.send_header("X-BTED-SHA256", asset["sha256"])
        if selected is not None:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if head_only:
            return
        with path.open("rb") as handle:
            handle.seek(start)
            remaining = length
            while remaining:
                chunk = handle.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def do_GET(self) -> None:  # noqa: N802
        if not self._serve_api(False):
            super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if not self._serve_api(True):
            super().do_HEAD()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=Path(".pages-preview"))
    parser.add_argument("--asset-dir", type=Path, default=Path("dist/BTED-v0.2.0-jbrowse/assets"))
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8016)
    args = parser.parse_args()

    site_dir = args.site_dir.expanduser().resolve()
    asset_dir = args.asset_dir.expanduser().resolve()
    registry_path = args.registry.expanduser().resolve()
    if not site_dir.is_dir():
        parser.error(f"site directory does not exist: {site_dir}")
    if not asset_dir.is_dir():
        parser.error(f"asset directory does not exist: {asset_dir}")
    registry = load_and_validate_registry(registry_path, asset_dir)

    handler = lambda *handler_args, **kwargs: DemoHandler(  # noqa: E731
        *handler_args, directory=str(site_dir), **kwargs
    )
    DemoHandler.registry = registry
    DemoHandler.asset_dir = asset_dir
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"PASS  Registry and {len(registry['assets'])} objects verified")
    print(f"Open  http://{args.host}:{args.port}/accession-range-demo.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
