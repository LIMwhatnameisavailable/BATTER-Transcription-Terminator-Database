"""Focused tests for the v0.3 GFF-derived gene query layer."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from typing import Any

from backend.importer.materialize import (
    JBROWSE_INVENTORY_COLUMNS,
    _build_gff_gene_tables,
    materialize_release,
)
from backend.importer.postgres import (
    _load_assets,
    _load_genes,
    _preflight,
)

from tests.test_bted_v03_postgres import _tiny_preflight_verification


REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_ROOT = REPO_ROOT / "data/public/v0.2.0"
INVENTORY = REPO_ROOT / "data/registry/jbrowse_assets.v0.2.0.tsv"
DEFAULT_BUNDLE = (
    REPO_ROOT.parent / "bted-v0.2" / "dist" / "BTED-v0.2.0-jbrowse"
)
BUNDLE_ROOT = Path(
    os.environ.get("BTED_V02_JBROWSE_BUNDLE", str(DEFAULT_BUNDLE))
)


class RecordingCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def executemany(self, sql: str, params: list[tuple[Any, ...]]) -> None:
        self.calls.append((sql, len(params)))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bgzf_block(payload: bytes) -> bytes:
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(payload) + compressor.flush()
    header = struct.pack("<BBBBIBBH", 31, 139, 8, 4, 0, 0, 255, 6)
    block_size = len(header) + 8 + len(compressed) + 8
    extra = b"BC" + struct.pack("<HH", 2, block_size - 1)
    trailer = struct.pack("<II", zlib.crc32(payload) & 0xFFFFFFFF, len(payload))
    return header + extra + compressed + trailer


def _write_bgzf(path: Path, text: str) -> None:
    path.write_bytes(_bgzf_block(text.encode("utf-8")) + _bgzf_block(b""))


def _write_synthetic_gene_inventory(root: Path) -> tuple[Path, Path, str]:
    assembly = "GCF_000000001.1"
    bundle_root = root / "bundle"
    asset_root = bundle_root / "assets"
    asset_root.mkdir(parents=True)
    fai_path = asset_root / "reference.fna.fai"
    fai_path.write_text(
        "ctgA\t100\t0\t50\t51\nctgB\t100\t0\t50\t51\n",
        encoding="utf-8",
    )
    gff_path = asset_root / "genes.gff3.gz"
    _write_bgzf(
        gff_path,
        "##gff-version 3\n"
        "ctgA\tRefSeq\tgene\t5\t20\t.\t+\t.\t"
        "ID=gene-1;Name=display%20name;gene=preferred%20name;"
        "locus_tag=LT1;product=alpha%2Cbeta\n"
        "ctgB\tRefSeq\tgene\t80\t125\t.\t-\t.\t"
        "ID=gene-2;Name=second%20name;locus_tag=LT2\n",
    )
    rows: list[dict[str, str]] = []
    common = {
        "release_version": "v0.2.0",
        "source_id": "S",
        "assembly_accession": assembly,
        "canonical_path": "",
        "object_path": "",
        "supports_range": "false",
        "redistribution_status": "verified_redistributable",
        "is_public": "true",
    }
    for role, kind, path, asset_id, mime in (
        (
            "reference_fai",
            "fai",
            "assets/reference.fna.fai",
            "v0.2.0--assembly-GCF_000000001.1--fai",
            "text/plain",
        ),
        (
            "reference_gff3",
            "gff3",
            "assets/genes.gff3.gz",
            "v0.2.0--assembly-GCF_000000001.1--gff3",
            "application/gzip",
        ),
    ):
        source_path = bundle_root / path
        rows.append(
            {
                **common,
                "asset_id": asset_id,
                "asset_role": role,
                "asset_kind": kind,
                "bundle_path": path,
                "byte_size": str(source_path.stat().st_size),
                "sha256": _sha256(source_path),
                "mime_type": mime,
            }
        )
    inventory_path = root / "inventory.tsv"
    with inventory_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=JBROWSE_INVENTORY_COLUMNS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    return inventory_path, bundle_root, assembly


def _gene_rows(rows: dict[str, list[dict[str, Any]]]) -> None:
    rows["assets"].append(
        {
            "asset_id": "v0.2.0--assembly-GCF_000000001.1--gff3",
            "release_version": "v0.2.0",
            "asset_kind": "gff3",
            "logical_path": "assemblies/GCF_000000001.1/reference/genes.gff3.gz",
            "origin_url": "https://example.test/assets/assemblies/GCF_000000001.1/reference/genes.gff3.gz",
            "origin_host": "example.test",
            "byte_size": 10,
            "sha256": "b" * 64,
            "mime_type": "application/gzip",
            "supports_range": False,
            "redistribution_status": "external_link_only",
            "is_public": False,
            "assembly_id_ref": "GCF_000000001.1",
        }
    )
    rows["genes"].append(
        {
            "release_version": "v0.2.0",
            "assembly_id_ref": "GCF_000000001.1",
            "contig_id_ref": {
                "assembly_accession": "GCF_000000001.1",
                "contig_accession": "NC_000001.1",
            },
            "gene_id": "GCF_000000001.1:gene-test",
            "locus_tag": "TEST_0001",
            "gene_name": "test",
            "feature_type": "gene",
            "start_1based": 10,
            "end_1based": 20,
            "strand": "+",
            "annotation_asset_id": "v0.2.0--assembly-GCF_000000001.1--gff3",
            "annotation_sha256": "b" * 64,
            "attributes_json": {
                "ID": "gene-test",
                "Name": "test",
                "locus_tag": "TEST_0001",
            },
        }
    )


class TestBtedV03Genes(unittest.TestCase):
    def test_synthetic_gff_fixture_decodes_and_extends_contigs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory, bundle_root, assembly = _write_synthetic_gene_inventory(
                Path(directory)
            )
            tables: dict[str, list[dict[str, Any]]] = {
                "assemblies": [{"assembly_accession": assembly}],
                "contigs": [
                    {
                        "assembly_id_ref": assembly,
                        "assembly_accession": assembly,
                        "contig_accession": "ctgA",
                        "contig_name": "ctgA",
                        "length_bp": 100,
                        "sequence_sha256": None,
                        "provenance_json": {},
                    }
                ],
                "genes": [],
            }
            summary = _build_gff_gene_tables(
                tables,
                {
                    "release": {"release_version": "v0.2.0"},
                    "repo_root": str(Path(directory)),
                },
                inventory,
                bundle_root,
            )
            self.assertEqual(summary["gene_count"], 2)
            self.assertEqual(summary["canonical_contig_count"], 1)
            self.assertEqual(summary["contig_count"], 2)
            genes = {row["gene_id"]: row for row in tables["genes"]}
            first = genes[f"{assembly}:gene-1"]
            self.assertEqual(first["gene_name"], "preferred name")
            self.assertEqual(first["attributes_json"]["Name"], "display name")
            self.assertEqual(first["attributes_json"]["product"], "alpha,beta")
            self.assertEqual(first["locus_tag"], "LT1")
            second = genes[f"{assembly}:gene-2"]
            self.assertEqual(second["gene_name"], "second name")
            self.assertEqual(second["end_1based"], 125)
            self.assertEqual(
                second["attributes_json"]["_bted_contig_length"],
                "100",
            )
            self.assertIn("_bted_coordinate_note", second["attributes_json"])
            extra = next(
                row
                for row in tables["contigs"]
                if row["contig_accession"] == "ctgB"
            )
            self.assertEqual(
                extra["provenance_json"]["source"],
                "jbrowse_reference_fai",
            )

    def test_fake_preflight_accepts_gene_and_writer_loads_assets_first(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            verification = _tiny_preflight_verification(
                Path(directory) / "bundle",
                mutate=_gene_rows,
            )
            state = _preflight(verification)
            self.assertEqual(len(state.genes), 1)
            cursor = RecordingCursor()
            _load_assets(
                cursor,
                verification,
                {"S": 11},
                {"GCF_000000001.1": 22},
                batch_size=10,
            )
            _load_genes(
                cursor,
                verification,
                {"GCF_000000001.1": 22},
                {("GCF_000000001.1", "NC_000001.1"): 33},
                batch_size=10,
            )
            self.assertEqual(len(cursor.calls), 2)
            self.assertIn("INSERT INTO assets", cursor.calls[0][0])
            self.assertIn("INSERT INTO genes", cursor.calls[1][0])
            self.assertEqual(cursor.calls[1][1], 1)

    @unittest.skipUnless(
        BUNDLE_ROOT.is_dir() and INVENTORY.is_file(),
        "local v0.2 JBrowse bundle is not available on this runner",
    )
    def test_real_gff_import_counts_and_circular_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = materialize_release(
                RELEASE_ROOT,
                repo_root=REPO_ROOT,
                output_dir=Path(directory) / "bundle",
                asset_origin_base="https://example.test/assets",
                generated_at_utc="2026-08-22T00:00:00Z",
                jbrowse_asset_inventory=INVENTORY,
                jbrowse_bundle_root=BUNDLE_ROOT,
            )
            self.assertEqual(result.table_counts["contigs"], 49)
            self.assertEqual(result.table_counts["genes"], 95_437)
            self.assertEqual(result.table_counts["endpoint_gene_context"], 0)
            with (result.output_dir / "genes.jsonl").open(encoding="utf-8") as handle:
                genes = [json.loads(line) for line in handle]
            boundary = [
                row
                for row in genes
                if "_bted_coordinate_note" in row["attributes_json"]
            ]
            self.assertEqual(len(boundary), 5)
            self.assertTrue(
                all(
                    row["end_1based"]
                    > int(row["attributes_json"]["_bted_contig_length"])
                    for row in boundary
                )
            )
            with (result.output_dir / "contigs.jsonl").open(encoding="utf-8") as handle:
                contigs = [json.loads(line) for line in handle]
            extras = {
                (row["assembly_accession"], row["contig_accession"])
                for row in contigs
                if row["provenance_json"].get("source") == "jbrowse_reference_fai"
            }
            self.assertEqual(
                extras,
                {
                    ("GCF_000008685.2", "NC_000957.1"),
                    ("GCF_000008685.2", "NC_001904.1"),
                },
            )
