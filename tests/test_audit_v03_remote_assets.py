"""Offline tests for the v0.3 remote public asset audit."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = REPO_ROOT / "scripts/audit_v03_remote_assets.py"
    spec = importlib.util.spec_from_file_location("audit_v03_remote_assets", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "release_version": "v0.2.0",
                "objects": [
                    {
                        "asset_id": "zeta",
                        "object_path": "records/S1/endpoints.bed",
                        "byte_size": 7,
                        "sha256": "z" * 64,
                        "url": "https://evil.example/not-used",
                    },
                    {
                        "asset_id": "alpha",
                        "object_path": "assemblies/GCF_TEST/reference/reference.fna",
                        "byte_size": 4,
                        "sha256": "a" * 64,
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


class FakeTransport:
    def __init__(self, module: Any, *, mode: str = "success") -> None:
        self.module = module
        self.mode = mode
        self.calls: list[tuple[str, str, Mapping[str, str]]] = []

    def request(self, method: str, url: str, headers: Mapping[str, str]):
        self.calls.append((method, url, dict(headers)))
        if self.mode == "404":
            return self.module.TransportResponse(404, {}, b"")
        if method == "HEAD":
            size = "999" if self.mode == "wrong-length" else ("4" if "reference.fna" in url else "7")
            return self.module.TransportResponse(200, {"Content-Length": size}, b"")
        if self.mode == "no-206":
            return self.module.TransportResponse(200, {"Content-Length": "4"}, b"whole")
        size = 4 if "reference.fna" in url else 7
        return self.module.TransportResponse(206, {"Content-Range": f"bytes 0-0/{size}"}, b"x")


class TestRemoteAssetAudit(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_module()

    def test_success_is_deterministic_and_uses_only_registered_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "ASSET_OBJECTS.json"
            _manifest(manifest)
            first_output = root / "first" / "REMOTE_ASSET_AUDIT.json"
            second_output = root / "second" / "REMOTE_ASSET_AUDIT.json"
            first_transport = FakeTransport(self.module)
            second_transport = FakeTransport(self.module)
            first = self.module.audit_remote_assets(
                manifest, "https://cdn.example/assets/", output_path=first_output, transport=first_transport
            )
            self.module.audit_remote_assets(
                manifest, "https://cdn.example/assets", output_path=second_output, transport=second_transport
            )
            self.assertEqual(first_output.read_bytes(), second_output.read_bytes())
            self.assertEqual(first["summary"], {"total": 2, "ok": 2, "failed": 0})
            self.assertEqual([item["asset_id"] for item in first["objects"]], ["alpha", "zeta"])
            self.assertEqual(first["objects"][0]["object_path"], "assemblies/GCF_TEST/reference/reference.fna")
            self.assertEqual(first["objects"][0]["byte_size"], 4)
            self.assertTrue(all(item["supports_range"] and item["ok"] for item in first["objects"]))
            self.assertEqual(
                [url for _, url, _ in first_transport.calls],
                [
                    "https://cdn.example/assets/assemblies/GCF_TEST/reference/reference.fna",
                    "https://cdn.example/assets/assemblies/GCF_TEST/reference/reference.fna",
                    "https://cdn.example/assets/records/S1/endpoints.bed",
                    "https://cdn.example/assets/records/S1/endpoints.bed",
                ],
            )
            self.assertEqual(first["objects"][0]["sha256"], "a" * 64)
            self.assertNotIn("evil.example", first_output.read_text(encoding="utf-8"))

    def test_404_is_recorded_as_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "ASSET_OBJECTS.json"
            _manifest(manifest)
            audit = self.module.audit_remote_assets(manifest, "https://cdn.example", transport=FakeTransport(self.module, mode="404"))
            self.assertEqual(audit["summary"], {"total": 2, "ok": 0, "failed": 2})
            self.assertEqual(audit["objects"][0]["head_status"], 404)
            self.assertFalse(audit["objects"][0]["supports_range"])

    def test_wrong_head_length_fails_but_valid_range_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "ASSET_OBJECTS.json"
            _manifest(manifest)
            audit = self.module.audit_remote_assets(manifest, "https://cdn.example", transport=FakeTransport(self.module, mode="wrong-length"))
            self.assertEqual(audit["summary"], {"total": 2, "ok": 0, "failed": 2})
            self.assertTrue(audit["objects"][0]["supports_range"])
            self.assertFalse(audit["objects"][0]["ok"])

    def test_non_206_range_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "ASSET_OBJECTS.json"
            _manifest(manifest)
            audit = self.module.audit_remote_assets(manifest, "https://cdn.example", transport=FakeTransport(self.module, mode="no-206"))
            self.assertEqual(audit["summary"], {"total": 2, "ok": 0, "failed": 2})
            self.assertFalse(audit["objects"][0]["supports_range"])
            self.assertEqual(audit["objects"][0]["range_status"], 200)

    def test_rejects_non_https_and_unsafe_manifest_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "ASSET_OBJECTS.json"
            _manifest(manifest)
            with self.assertRaises(self.module.RemoteAssetAuditError):
                self.module.audit_remote_assets(manifest, "http://cdn.example", transport=FakeTransport(self.module))
            manifest.write_text(
                json.dumps({"objects": [{"asset_id": "bad", "object_path": "../secret", "byte_size": 1, "sha256": "a"}]}),
                encoding="utf-8",
            )
            with self.assertRaises(self.module.RemoteAssetAuditError):
                self.module.audit_remote_assets(manifest, "https://cdn.example", transport=FakeTransport(self.module))


if __name__ == "__main__":
    unittest.main()
