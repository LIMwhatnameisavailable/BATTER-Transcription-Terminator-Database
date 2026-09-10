#!/usr/bin/env python3
"""Generate Cloudflare D1 schema/import batches from a verified BTED bundle.

The generated SQL is a local/preview artifact and is intentionally written to
an explicit output directory outside Git.  The script only reads the
materialized verified bundle; it does not reinterpret endpoints, copy source
annotations, upload assets, or contact Cloudflare/Hugging Face.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "prototype" / "accession-range" / "schema.sql"


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sql_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


def json_value(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def insert_sql(table: str, columns: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    statements: list[str] = []
    column_sql = ", ".join(columns)
    for row in rows:
        values = ", ".join(sql_value(value) for value in row)
        statements.append(f"INSERT INTO {table} ({column_sql}) VALUES ({values});")
    if not statements:
        return ""
    # Wrangler's local D1 executor rejects explicit BEGIN/COMMIT statements;
    # let D1 apply the file using its own statement batching/atomicity.
    return "\n".join(statements) + "\n"


def write_batch(output: Path, name: str, table: str, columns: Sequence[str], rows: Iterable[Sequence[Any]]) -> int:
    materialized = list(rows)
    (output / name).write_text(insert_sql(table, columns, materialized), encoding="utf-8")
    return len(materialized)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")

    bundle = args.bundle_dir.expanduser().resolve()
    output = args.output_dir.expanduser().resolve()
    if not bundle.is_dir():
        parser.error(f"bundle directory does not exist: {bundle}")
    if output.exists() and any(output.iterdir()):
        parser.error(f"output directory must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("asset_origin", {}).get("asset_origin_status") != "verified":
        parser.error("the D1 preview requires a verified asset-origin bundle")
    release_version = str(manifest["release_version"])
    release = jsonl(bundle / "release_versions.jsonl")[0]
    # This is a preview projection, not a PostgreSQL promotion.  Keep the
    # canonical release version/checksum but make the D1 catalogue selectable.
    release_row = (
        release_version,
        "preview",
        1,
        release.get("release_date"),
        release.get("canonical_manifest_path"),
        release.get("canonical_manifest_sha256"),
        manifest["asset_origin"]["asset_origin_status"],
        manifest.get("materializer_version"),
    )

    publications = jsonl(bundle / "publications.jsonl")
    assemblies = jsonl(bundle / "assemblies.jsonl")
    contigs = jsonl(bundle / "contigs.jsonl")
    sources = jsonl(bundle / "sources.jsonl")
    accessions = jsonl(bundle / "source_accessions.jsonl")
    endpoints = jsonl(bundle / "endpoints.jsonl")
    assets = jsonl(bundle / "assets.jsonl")

    publication_by_pmid = {str(row["pmid"]): row for row in publications}
    bed_by_source: dict[str, dict[str, Any]] = {}
    for asset in assets:
        source_id = asset.get("source_id_ref")
        if source_id and asset.get("asset_kind") == "bed":
            bed_by_source[str(source_id)] = asset

    files: dict[str, int] = {}
    files["00_release.sql"] = write_batch(
        output,
        "00_release.sql",
        "release_versions",
        (
            "release_version", "status", "is_current", "release_date",
            "canonical_manifest_path", "canonical_manifest_sha256", "asset_origin_status",
            "materializer_version",
        ),
        [release_row],
    )
    files["01_publications.sql"] = write_batch(
        output,
        "01_publications.sql",
        "publications",
        ("pmid", "doi", "pmc", "published_year", "journal", "paper_title", "citation_json"),
        (
            (
                str(row["pmid"]), row.get("doi"), row.get("pmc"), row.get("published_year"),
                row.get("journal"), row.get("paper_title"), json_value(row.get("citation_json")),
            )
            for row in publications
        ),
    )
    files["02_assemblies.sql"] = write_batch(
        output,
        "02_assemblies.sql",
        "assemblies",
        (
            "release_version", "accession", "assembly_name", "organism_name", "strain",
            "taxon_id", "reference_url",
        ),
        (
            (
                release_version, row["assembly_accession"], row.get("assembly_name"),
                row.get("organism_name"), row.get("strain"), row.get("taxon_id"),
                row.get("reference_url"),
            )
            for row in assemblies
        ),
    )
    files["03_contigs.sql"] = write_batch(
        output,
        "03_contigs.sql",
        "contigs",
        (
            "release_version", "assembly_accession", "contig_accession", "contig_name",
            "length_bp", "sequence_sha256", "provenance_json",
        ),
        (
            (
                release_version, row["assembly_accession"], row["contig_accession"],
                row.get("contig_name"), row.get("length_bp"), row.get("sequence_sha256"),
                json_value(row.get("provenance_json")),
            )
            for row in contigs
        ),
    )
    files["04_sources.sql"] = write_batch(
        output,
        "04_sources.sql",
        "sources",
        (
            "release_version", "source_id", "assembly_accession", "publication_pmid",
            "species", "phylum", "assay_family", "evidence_class", "release_status",
            "record_count", "used_for_batter_augmentation", "has_jbrowse", "accessibility_status",
            "coordinate_status", "processing_status", "redistribution_status", "manifest_path",
            "manifest_sha256", "record_root", "source_note", "decision_note", "known_limitations",
        ),
        (
            (
                release_version, row["source_id"], row.get("assembly_id_ref"),
                str(row["publication_id_ref"]) if row.get("publication_id_ref") is not None else None,
                row.get("species"), row.get("phylum"), row.get("assay_family"), row.get("evidence_class"),
                row.get("release_status"), row.get("record_count", 0), row.get("used_for_batter_augmentation", False),
                row.get("has_jbrowse", False), row.get("accessibility_status"), row.get("coordinate_status"),
                row.get("processing_status"), row.get("redistribution_status"), row.get("manifest_path"),
                row.get("manifest_sha256"), row.get("record_root"), row.get("source_note"),
                row.get("decision_note"), row.get("known_limitations"),
            )
            for row in sources
        ),
    )
    files["05_accessions.sql"] = write_batch(
        output,
        "05_accessions.sql",
        "source_accessions",
        (
            "release_version", "source_id", "accession_namespace", "accession", "raw_value",
            "accession_type", "ordinal", "external_url",
        ),
        (
            (
                release_version, row["source_id_ref"], row.get("accession_namespace"), row.get("accession"),
                row.get("raw_value"), row.get("accession_type"), row.get("ordinal"), row.get("external_url"),
            )
            for row in accessions
        ),
    )

    track_rows = []
    for order, source in enumerate(sources, 1):
        source_id = source["source_id"]
        publication = publication_by_pmid.get(str(source["publication_id_ref"]))
        raw = [a for a in accessions if a.get("source_id_ref") == source_id]
        bed = bed_by_source.get(source_id)
        track_rows.append(
            (
                f"{source_id}--track", release_version, source_id, source.get("assembly_id_ref"),
                publication.get("published_year") if publication else None,
                str(publication.get("pmid")) if publication else None,
                publication.get("doi") if publication else None,
                publication.get("paper_title") if publication else None,
                publication.get("journal") if publication else None,
                json_value(raw), source.get("assay_family"), source.get("evidence_class"),
                source.get("record_count", 0), bed.get("asset_id") if bed else None,
                1 if bed and bed.get("is_public") else 0, order,
                json_value({"source_note": source.get("source_note"), "decision_note": source.get("decision_note"), "known_limitations": source.get("known_limitations")}),
            )
        )
    files["07_tracks.sql"] = write_batch(
        output, "07_tracks.sql", "tracks",
        (
            "track_id", "release_version", "source_id", "assembly_accession", "publication_year",
            "pmid", "doi", "paper_title", "journal", "raw_accessions_json", "assay",
            "evidence_class", "record_count", "asset_key", "is_public", "display_order", "metadata_json",
        ),
        track_rows,
    )
    files["06_assets.sql"] = write_batch(
        output,
        "06_assets.sql",
        "assets",
        (
            "asset_key", "release_version", "assembly_accession", "source_id", "asset_kind",
            "logical_path", "origin_url", "origin_host", "content_type", "byte_size", "sha256",
            "supports_range", "redistribution_status", "is_public", "active",
        ),
        (
            (
                row["asset_id"], release_version, row.get("assembly_id_ref"), row.get("source_id_ref"),
                row.get("asset_kind"), row.get("logical_path"), row.get("origin_url"), row.get("origin_host"),
                row.get("mime_type"), row.get("byte_size"), row.get("sha256"), row.get("supports_range", False),
                row.get("redistribution_status"), row.get("is_public", False), 1,
            )
            for row in assets
        ),
    )

    endpoint_columns = (
        "end_id", "release_version", "source_id", "sample_id", "assay", "evidence_class",
        "author_endpoint_id", "published_reference_accession", "reference_assembly", "reference_name",
        "replicon_label", "biological_coordinate_1based", "bed_start_0based", "bed_end_0based",
        "strand", "signal_or_score", "author_category", "associated_gene_or_locus", "pmid", "doi",
        "source_table_or_file", "coordinate_interpretation", "original_row_reference", "qc_status", "note",
    )
    for start in range(0, len(endpoints), args.batch_size):
        batch = endpoints[start:start + args.batch_size]
        name = f"08_endpoints_{start // args.batch_size:04d}.sql"
        files[name] = write_batch(
            output,
            name,
            "endpoints",
            endpoint_columns,
            (
                tuple(row.get(column) for column in endpoint_columns[:-1]) + (row.get("note"),)
                for row in batch
            ),
        )

    summary = {
        "release_version": release_version,
        "preview_status": "preview",
        "verified_asset_origin": manifest["asset_origin"]["base"],
        "counts": {
            "publications": len(publications), "assemblies": len(assemblies), "contigs": len(contigs),
            "sources": len(sources), "source_accessions": len(accessions), "tracks": len(track_rows),
            "assets": len(assets), "public_assets": sum(1 for row in assets if row.get("is_public")),
            "endpoints": len(endpoints),
        },
        "files": files,
        "source_annotation_policy": "source_annotations remain in verified HF/metadata assets; no D1 annotation table",
        "gene_policy": "genes omitted because the catalogue Worker does not query gene records",
    }
    (output / "IMPORT_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(SCHEMA_PATH, output / "schema.sql")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
