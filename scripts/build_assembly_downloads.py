#!/usr/bin/env python3
"""Build assembly-level BTED download packages.

The public interface exposes only two files per assembly: a BED6 endpoint file
when publishable endpoints exist, and one metadata JSON document.  Source-level
provenance remains intact; records from sources sharing an exact assembly are
concatenated, never deduplicated or reinterpreted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_ROOT = REPO_ROOT / "data/public/v0.2.0"
RELEASE_PATH = RELEASE_ROOT / "release_manifest.json"
REGISTRY_PATH = REPO_ROOT / "data/registry/batter_s1_source_registry.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_inputs() -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))
    with REGISTRY_PATH.open(encoding="utf-8", newline="") as handle:
        registry = {row["source_id"]: row for row in csv.DictReader(handle, delimiter="\t")}
    return release, registry


def build(output_dir: Path) -> dict[str, Any]:
    release, registry = load_inputs()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    grouped: dict[str, list[str]] = defaultdict(list)
    for source_id in release["sources"]:
        grouped[registry[source_id]["reference_genome"]].append(source_id)

    catalog: dict[str, Any] = {
        "release_version": "v0.2.0",
        "assembly_count": len(grouped),
        "assemblies": {},
    }
    summary_rows: list[dict[str, object]] = []

    for assembly, source_ids in grouped.items():
        assembly_dir = output_dir / assembly
        assembly_dir.mkdir()
        bed_path = assembly_dir / "endpoints.bed"
        source_entries: list[dict[str, Any]] = []
        bed_blocks: list[str] = []
        total_records = 0

        for source_id in source_ids:
            release_entry = release["sources"][source_id]
            source = registry[source_id]
            manifest_path = RELEASE_ROOT / "records" / source_id / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            published = release_entry["release_status"] != "audit_only"
            if published:
                source_bed = RELEASE_ROOT / "records" / source_id / "endpoints.bed"
                if not source_bed.is_file():
                    raise FileNotFoundError(f"{source_id}: publishable source is missing endpoints.bed")
                block = source_bed.read_text(encoding="utf-8")
                if block and not block.endswith("\n"):
                    block += "\n"
                bed_blocks.append(block)
                line_count = len([line for line in block.splitlines() if line])
                if line_count != int(release_entry["record_count"]):
                    raise ValueError(f"{source_id}: BED row count differs from release manifest")
                total_records += line_count

            source_entries.append({
                "source_id": source_id,
                "dataset_id": manifest.get("dataset_id", "NA"),
                "species": source["species"],
                "year": int(source["published_year"]),
                "assay": source["assay_family"],
                "evidence_class": "audit_only" if not published else release_entry["evidence_class"],
                "release_status": release_entry["release_status"],
                "record_count": int(release_entry["record_count"]),
                "paper": {
                    "title": source["paper_title"],
                    "pmid": source["pmid"],
                    "pubmed_url": manifest.get("pubmed_url", "NA"),
                    "doi": source["doi"],
                    "doi_url": manifest.get("doi_url", "NA"),
                },
                "raw_data": {
                    "accessions": source["raw_data_accessions"],
                    "url": manifest.get("raw_data_url", "NA"),
                },
                "known_limitations": manifest.get("known_limitations", source["blocker_or_note"]),
            })

        files: dict[str, Any] = {}
        if bed_blocks:
            bed_path.write_text("".join(bed_blocks), encoding="utf-8")
            files["endpoints_bed"] = {
                "path": "endpoints.bed",
                "format": "BED6",
                "record_count": total_records,
                "sha256": sha256(bed_path),
            }

        organisms = sorted({registry[source_id]["species"] for source_id in source_ids})
        metadata = {
            "schema_version": "1.0",
            "release_version": "v0.2.0",
            "assembly_accession": assembly,
            "organisms": organisms,
            "track_count": len(source_ids),
            "published_track_count": sum(
                release["sources"][source_id]["release_status"] != "audit_only" for source_id in source_ids
            ),
            "record_count": total_records,
            "aggregation_policy": (
                "Sources are grouped only when the exact reference assembly accession matches. "
                "BED rows retain source-specific end_id values and are not deduplicated or interpreted as consensus."
            ),
            "coordinate_convention": {
                "biological": "1-based in source core tables",
                "bed": "0-based, half-open BED6; start = biological position - 1; end = biological position",
            },
            "files": files,
            "sources": source_entries,
        }
        metadata_path = assembly_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        catalog["assemblies"][assembly] = {
            "metadata": f"{assembly}/metadata.json",
            "bed": f"{assembly}/endpoints.bed" if bed_blocks else None,
            "source_ids": source_ids,
            "record_count": total_records,
        }
        summary_rows.append({
            "assembly_accession": assembly,
            "organism": "; ".join(organisms),
            "track_count": len(source_ids),
            "published_track_count": metadata["published_track_count"],
            "record_count": total_records,
            "source_ids": ";".join(source_ids),
            "bed_available": "TRUE" if bed_blocks else "FALSE",
        })

    with (output_dir / "assemblies.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(summary_rows)
    (output_dir / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("dist/assembly-downloads"))
    args = parser.parse_args()
    catalog = build(args.output_dir.expanduser())
    published = sum(entry["bed"] is not None for entry in catalog["assemblies"].values())
    print(
        f"PASS  {catalog['assembly_count']} assembly metadata packages; "
        f"{published} BED packages; source provenance retained"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
