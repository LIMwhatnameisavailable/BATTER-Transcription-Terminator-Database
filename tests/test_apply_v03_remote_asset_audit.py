"""Focused offline tests for applying a remote asset audit report."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = REPO_ROOT / "scripts/apply_v03_remote_asset_audit.py"
    spec = importlib.util.spec_from_file_location("apply_v03_remote_asset_audit", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestApplyRemoteAssetAudit(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_module()
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.inventory = self.root / "inventory.tsv"
        fields = [
            "asset_id", "release_version", "source_id", "assembly_accession", "asset_role",
            "asset_kind", "bundle_path", "canonical_path", "object_path", "byte_size", "sha256",
            "mime_type", "supports_range", "redistribution_status", "is_public",
        ]
        rows = [
            {
                "asset_id": "browser-public", "release_version": "v0.2.0", "source_id": "S1",
                "assembly_accession": "GCF_TEST.1", "asset_role": "reference_fasta", "asset_kind": "fasta",
                "bundle_path": "reference.fna", "canonical_path": "",
                "object_path": "assemblies/GCF_TEST.1/reference/reference.fna", "byte_size": "4",
                "sha256": "a" * 64, "mime_type": "text/plain", "supports_range": "false",
                "redistribution_status": "verified_redistributable", "is_public": "true",
            },
            {
                "asset_id": "browser-private", "release_version": "v0.2.0", "source_id": "S2",
                "assembly_accession": "GCF_PRIVATE.1", "asset_role": "reference_fasta", "asset_kind": "fasta",
                "bundle_path": "private.fna", "canonical_path": "",
                "object_path": "assemblies/GCF_PRIVATE.1/reference/reference.fna", "byte_size": "5",
                "sha256": "b" * 64, "mime_type": "text/plain", "supports_range": "false",
                "redistribution_status": "external_link_only", "is_public": "false",
            },
        ]
        with self.inventory.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        self.assets = [
            {
                "asset_id": "browser-public", "release_version": "v0.2.0", "source_id_ref": None,
                "assembly_id_ref": "GCF_TEST.1", "asset_kind": "fasta",
                "logical_path": "assemblies/GCF_TEST.1/reference/reference.fna",
                "origin_url": "https://cdn.example/assets/assemblies/GCF_TEST.1/reference/reference.fna",
                "origin_host": "cdn.example", "byte_size": 4, "sha256": "a" * 64,
                "mime_type": "text/plain", "supports_range": False,
                "redistribution_status": "verified_redistributable", "is_public": True,
            },
            {
                "asset_id": "browser-private", "release_version": "v0.2.0", "source_id_ref": None,
                "assembly_id_ref": "GCF_PRIVATE.1", "asset_kind": "fasta",
                "logical_path": "assemblies/GCF_PRIVATE.1/reference/reference.fna",
                "origin_url": "https://cdn.example/assets/assemblies/GCF_PRIVATE.1/reference/reference.fna",
                "origin_host": "cdn.example", "byte_size": 5, "sha256": "b" * 64,
                "mime_type": "text/plain", "supports_range": False,
                "redistribution_status": "external_link_only", "is_public": False,
            },
            {
                "asset_id": "canonical-metadata", "release_version": "v0.2.0", "source_id_ref": "S1",
                "assembly_id_ref": None, "asset_kind": "metadata", "logical_path": "records/S1/manifest.json",
                "origin_url": "https://cdn.example/assets/records/S1/manifest.json", "origin_host": "cdn.example",
                "byte_size": 6, "sha256": "c" * 64, "mime_type": "application/json",
                "supports_range": False, "redistribution_status": "verified_redistributable", "is_public": True,
            },
        ]
        assets_path = self.bundle / "assets.jsonl"
        assets_path.write_text(
            "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in self.assets),
            encoding="utf-8",
        )
        manifest = {
            "materialization_schema_version": "bted-postgresql-staging-0.3.0",
            "materializer_version": "bted-materializer-0.3.0-b1",
            "release_version": "v0.2.0", "canonical_validation_status": "validated",
            "postgresql_ready": True, "write_mode": "not_written", "unresolved": [],
            "asset_origin": {"base": "https://cdn.example/assets", "host": "cdn.example", "asset_origin_status": "planned_not_verified"},
            "jbrowse_asset_inventory": {"path": "inventory.tsv", "sha256": _sha(self.inventory), "asset_origin_status": "planned_not_verified"},
            "tables": {"assets": {"file": "assets.jsonl", "row_count": 3, "sha256": _sha(assets_path), "byte_size": assets_path.stat().st_size}},
        }
        (self.bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (self.bundle / "SHA256SUMS.txt").write_text("fixture\n", encoding="utf-8")
        self.audit = self.root / "REMOTE_ASSET_AUDIT.json"
        self.audit_row = {
            "asset_id": "browser-public",
            "object_path": "assemblies/GCF_TEST.1/reference/reference.fna",
            "url": "https://cdn.example/assets/assemblies/GCF_TEST.1/reference/reference.fna",
            "byte_size": 4, "sha256": "a" * 64, "head_status": 200, "range_status": 206,
            "supports_range": True, "ok": True,
        }
        self.metadata_audit_row = {
            "asset_id": "canonical-metadata", "object_path": "records/S1/manifest.json",
            "url": "https://cdn.example/assets/records/S1/manifest.json",
            "byte_size": 6, "sha256": "c" * 64, "head_status": 200, "range_status": 206,
            "supports_range": True, "ok": True,
        }
        self._write_audit(self.audit_row, self.metadata_audit_row)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_audit(self, *rows: dict) -> None:
        self.audit.write_text(
            json.dumps({"schema_version": "1.1", "release_version": "v0.2.0", "objects": list(rows)}),
            encoding="utf-8",
        )

    def test_all_passed_required_public_assets_become_range_capable(self) -> None:
        output = self.root / "verified"
        with mock.patch.object(self.module, "verify_bundle") as verify:
            manifest = self.module.apply_remote_asset_audit(
                bundle_dir=self.bundle, audit_path=self.audit, output_dir=output,
                inventory_path=self.inventory,
            )
        self.assertEqual(verify.call_count, 2)
        self.assertEqual(manifest["asset_origin"]["asset_origin_status"], "verified")
        rows = [json.loads(line) for line in (output / "assets.jsonl").read_text(encoding="utf-8").splitlines()]
        state = {row["asset_id"]: row["supports_range"] for row in rows}
        self.assertEqual(state, {"browser-public": True, "browser-private": False, "canonical-metadata": True})
        self.assertEqual(manifest["remote_asset_audit"]["required_public_asset_count"], 2)
        self.assertEqual(manifest["remote_asset_audit"]["required_public_browser_asset_count"], 1)
        self.assertEqual(manifest["remote_asset_audit"]["passed_count"], 2)
        self.assertIn("manifest.json", (output / "SHA256SUMS.txt").read_text(encoding="utf-8"))

    def test_identity_mismatch_or_failed_range_does_not_create_verified_bundle(self) -> None:
        for suffix, change in (
            ("identity", {"sha256": "d" * 64}),
            ("range", {"range_status": 200, "supports_range": False, "ok": False}),
        ):
            row = dict(self.audit_row)
            row.update(change)
            self._write_audit(row, self.metadata_audit_row)
            output = self.root / f"failed-{suffix}"
            with mock.patch.object(self.module, "verify_bundle"):
                with self.assertRaises(self.module.RemoteAuditApplicationError):
                    self.module.apply_remote_asset_audit(
                        bundle_dir=self.bundle, audit_path=self.audit, output_dir=output,
                        inventory_path=self.inventory,
                    )
            self.assertFalse(output.exists())

    def test_missing_public_canonical_asset_audit_is_rejected(self) -> None:
        self._write_audit(self.audit_row)
        with mock.patch.object(self.module, "verify_bundle"):
            with self.assertRaisesRegex(
                self.module.RemoteAuditApplicationError,
                "all required public assets",
            ):
                self.module.apply_remote_asset_audit(
                    bundle_dir=self.bundle,
                    audit_path=self.audit,
                    output_dir=self.root / "missing-canonical",
                    inventory_path=self.inventory,
                )

    def test_cli_entrypoint_imports_from_repository_root(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/apply_v03_remote_asset_audit.py", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--remote-audit", result.stdout)


if __name__ == "__main__":
    unittest.main()
