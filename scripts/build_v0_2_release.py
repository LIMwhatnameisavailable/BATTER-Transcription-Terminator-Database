#!/usr/bin/env python3
"""Build the BTED v0.2.0 portable data release from the local BGIRNA snapshot.

The v0.1 release reduced every source to a stable 24-column cross-source table.
This builder keeps that table compatible and adds a lossless, source-specific
annotation layer.  Every input column is either copied to
``source_annotations.tsv`` or explicitly recorded as withheld in
``fields.json``.  Prediction annotations may be retained as annotations, but
they never change the endpoint evidence class.

The four Lalanne 2018 source tables are not openly licensed in Europe PMC.
Their compact, factual v0.1 core records remain available, but the larger
author-specific annotation layer is not copied into the public v0.2 release.
The field manifest records every withheld column and the reason.

Usage:
    python3 scripts/build_v0_2_release.py --input-root /path/to/BGIRNA
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import build_local_snapshot_release as v01


REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_VERSION = "v0.2.0"
RELEASE_DATE = "2026-08-10"
OUTPUT_ROOT = REPO_ROOT / "data/public/v0.2.0"
RECORD_ROOT = OUTPUT_ROOT / "records"

LALANNE_SOURCES = {
    "BATTER_S1_001", "BATTER_S1_003", "BATTER_S1_004", "BATTER_S1_005",
}

LICENSE_BY_PMID = {
    "29606352": {
        "article_license": "not_open_access_author_manuscript",
        "redistribution_status": "external_link_only",
        "license_source": "https://europepmc.org/article/MED/29606352",
        "note": "Europe PMC reports isOpenAccess=N and no reusable article license. Author-specific supplementary fields are not recopied in v0.2.0.",
    },
    "30517198": {"article_license": "CC BY", "redistribution_status": "verified_redistributable"},
    "31555254": {"article_license": "CC BY", "redistribution_status": "verified_redistributable"},
    "31594819": {"article_license": "CC BY", "redistribution_status": "verified_redistributable"},
    "32694125": {"article_license": "CC BY", "redistribution_status": "verified_redistributable"},
    "33319794": {"article_license": "CC BY; endpoint workbook CC0", "redistribution_status": "verified_redistributable"},
    "33947798": {"article_license": "CC BY", "redistribution_status": "verified_redistributable"},
    "34054774": {"article_license": "CC BY", "redistribution_status": "verified_redistributable"},
    "34874777": {"article_license": "CC BY", "redistribution_status": "verified_redistributable"},
    "35491820": {"article_license": "CC BY", "redistribution_status": "verified_redistributable"},
    "37096044": {"article_license": "CC BY", "redistribution_status": "verified_redistributable"},
    "37402717": {"article_license": "CC BY", "redistribution_status": "verified_redistributable"},
    "38030608": {"article_license": "CC BY", "redistribution_status": "audit_only"},
}

COMPANION_TABLES = {
    "BATTER_S1_008": [{
        "input": "data/paeruginosa/processed/BATTER_S1_008/gene_associated_tts.tsv",
        "asset": "gene_associations.tsv",
        "evidence_role": "author_annotation",
        "link_method": "coordinate",
        "note": "Author gene-associated TTS interpretation table; not promoted to a second endpoint set.",
    }],
    "BATTER_S1_021": [{
        "input": "data/bburgdorferi/processed/BATTER_S1_021/published_3prime_end_observations.tsv",
        "asset": "condition_observations.tsv",
        "evidence_role": "experimental_measurement",
        "link_method": "author_id",
        "note": "Condition-level observations linked to the unique endpoint table.",
    }],
}

PREDICTION_TOKENS = (
    "predicted", "prediction", "structure", "fold", "mfe", "kinefold",
    "terminator_score", "hairpin", "u_tract", "a_tract", "transterm",
    "webgester", "rnie", "rhoterm",
)
MEASUREMENT_TOKENS = (
    "coverage", "enrichment", "intensity", "abundance", "read_count",
    "signal", "pvalue", "padj", "fold_change", "readthrough", "z_score",
    "base_mean", "condition_", "conditions_detected", "observed_",
)
CURATION_TOKENS = (
    "source_id", "species", "sample_id", "assay", "evidence_class", "pmid",
    "doi", "source_table", "coordinate_interpretation", "qc_status", "note",
    "match_status", "nearest_candidate", "distance_to_candidate",
)
ENDPOINT_TOKENS = (
    "end_id", "site_id", "record_id", "author_tts_id", "author_tep_id",
    "literature_end_id", "reference", "assembly", "chrom", "replicon",
    "coordinate", "position", "strand", "bed_start", "bed_end",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            raise ValueError(f"Missing TSV header: {path}")
        return list(reader.fieldnames), list(reader)


def write_tsv(path: Path, columns: list[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def infer_type(values: Iterable[str]) -> str:
    nonempty = [value.strip() for value in values if value.strip() and value.strip().upper() != "NA"]
    if not nonempty:
        return "string"
    lowered = {value.lower() for value in nonempty}
    if lowered <= {"true", "false", "yes", "no"}:
        return "boolean"
    try:
        for value in nonempty:
            int(value)
        return "integer"
    except ValueError:
        pass
    try:
        for value in nonempty:
            float(value)
        return "number"
    except ValueError:
        return "string"


def evidence_role(name: str) -> str:
    lower = name.lower()
    if any(token in lower for token in PREDICTION_TOKENS):
        return "prediction_annotation"
    if any(token in lower for token in MEASUREMENT_TOKENS):
        return "experimental_measurement"
    if any(token in lower for token in CURATION_TOKENS):
        return "curation_metadata"
    if any(token in lower for token in ENDPOINT_TOKENS):
        return "author_called_endpoint"
    return "author_annotation"


def units_for(name: str) -> str:
    lower = name.lower()
    if "kcal_mol" in lower or lower == "mfe":
        return "kcal/mol"
    if "fraction" in lower or lower in {"pvalue", "padj"}:
        return "fraction"
    if any(token in lower for token in ("coordinate", "position", "start", "end", "length")):
        return "nt"
    if any(token in lower for token in ("coverage", "count", "intensity", "abundance", "signal")):
        return "source-defined count or score"
    return "NA"


def output_name(original_name: str, used: set[str]) -> str:
    candidate = "source_end_id" if original_name == "end_id" else original_name
    if candidate in {"canonical_end_id", "source_record_id", "link_status"}:
        candidate = f"source_{candidate}"
    base = candidate
    suffix = 2
    while candidate in used:
        candidate = f"{base}_{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def field_manifest(
    original_columns: list[str],
    rows: list[dict[str, str]],
    published: bool,
) -> tuple[list[dict[str, object]], dict[str, str]]:
    used = {"end_id", "source_record_id", "link_status"}
    mapping: dict[str, str] = {}
    fields: list[dict[str, object]] = []
    for original in original_columns:
        out = output_name(original, used)
        mapping[original] = out
        values = [row.get(original, "") for row in rows]
        fields.append({
            "name": out,
            "original_name": original,
            "data_type": infer_type(values),
            "required": all(value.strip() and value.strip().upper() != "NA" for value in values),
            "evidence_role": evidence_role(original),
            "units": units_for(original),
            "publication_status": "published" if published else "withheld_external_link_only",
            "description": f"Source-specific field retained from the standardized local input column '{original}'.",
        })
    return fields, mapping


def canonical_and_annotations(
    source_id: str,
    input_root: Path,
    registry_row: dict[str, str],
    config: dict[str, str],
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, object]]:
    source_input = input_root / config["input"]
    original_columns, input_rows = read_tsv(source_input)
    publish_annotations = source_id not in LALANNE_SOURCES
    fields, mapping = field_manifest(original_columns, input_rows, publish_annotations)

    canonical_rows: list[dict[str, str]] = []
    annotation_rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for row_number, input_row in enumerate(input_rows, start=2):
        canonical = v01.canonical_row(source_id, input_row, row_number, config, registry_row, config["input"])
        v01.validate_input_row(source_id, canonical)
        if canonical["end_id"] in seen_ids:
            raise ValueError(f"{source_id}: duplicate canonical end_id {canonical['end_id']}")
        seen_ids.add(canonical["end_id"])
        canonical_rows.append(canonical)
        source_record_id = v01.first_value(
            input_row,
            ["author_endpoint_id", "author_tts_id", "author_tep_id", "genomic_site_id", "literature_end_id", "site_id", "end_id", "record_id"],
            f"row_{row_number}",
        )
        annotation = {"end_id": canonical["end_id"], "source_record_id": source_record_id}
        annotation.update({mapping[name]: input_row.get(name, "") for name in original_columns})
        annotation_rows.append(annotation)

    manifest = {
        "table": "source_annotations.tsv",
        "publication_status": "published" if publish_annotations else "withheld_external_link_only",
        "source_input": config["input"],
        "source_input_sha256": sha256(source_input),
        "source_input_columns": original_columns,
        "field_count": len(original_columns),
        "fields": fields,
        "withheld_reason": "NA" if publish_annotations else "The article/supplement is not openly licensed in Europe PMC; retrieve author-specific fields from the original supplement.",
    }
    return canonical_rows, annotation_rows, manifest


def link_companion_rows(
    companion_rows: list[dict[str, str]],
    canonical_rows: list[dict[str, str]],
    method: str,
) -> list[dict[str, str]]:
    by_author = {row["author_endpoint_id"]: row["end_id"] for row in canonical_rows}
    by_coordinate: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in canonical_rows:
        by_coordinate[(row["reference_name"], row["biological_coordinate_1based"], row["strand"])].append(row["end_id"])

    linked: list[dict[str, str]] = []
    for row in companion_rows:
        end_id = ""
        if method == "author_id":
            end_id = by_author.get(v01.first_value(row, ["site_id", "end_id", "record_id"], ""), "")
        elif method == "coordinate":
            key = (
                v01.first_value(row, ["reference_name", "chrom"], ""),
                v01.first_value(row, ["biological_coordinate_1based", "published_coordinate_1based"], ""),
                v01.first_value(row, ["strand"], ""),
            )
            matches = by_coordinate.get(key, [])
            end_id = matches[0] if len(matches) == 1 else ""
        linked.append({"end_id": end_id, "link_status": "linked" if end_id else "unlinked_author_annotation", **row})
    return linked


def write_checksums(directory: Path) -> list[dict[str, str]]:
    checksum_path = directory / "SHA256SUMS.txt"
    files = sorted(path for path in directory.iterdir() if path.is_file() and path.name != checksum_path.name)
    records = [{"path": path.name, "sha256": sha256(path)} for path in files]
    checksum_path.write_text("".join(f"{item['sha256']}  {item['path']}\n" for item in records), encoding="utf-8")
    return records + [{"path": checksum_path.name, "sha256": sha256(checksum_path)}]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    args = parser.parse_args()
    input_root = args.input_root.expanduser().resolve()
    if not (input_root / "data/source_registry/manifests").is_dir():
        parser.error("--input-root does not contain the BTED source manifests")

    registry = v01.read_registry()
    source_ids = [f"BATTER_S1_{number:03d}" for number in range(1, 23)]
    if sorted(registry) != source_ids:
        raise RuntimeError("Registry must contain exactly BATTER_S1_001 through BATTER_S1_022")

    RECORD_ROOT.mkdir(parents=True, exist_ok=True)
    release_sources: dict[str, dict[str, object]] = {}
    license_rows: list[dict[str, str]] = []

    for source_id in source_ids:
        # Release metadata is governed by the reviewed, Git-tracked registry.
        # The external BGIRNA snapshot supplies processed data inputs only.
        source_manifest_path = REPO_ROOT / "data/registry/manifests" / f"{source_id}.json"
        source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
        source_manifest.pop("repository_release", None)
        pmid = str(source_manifest.get("pmid", ""))
        license_info = {
            "article_license": "to_review",
            "redistribution_status": "to_review",
            "license_source": f"https://europepmc.org/article/MED/{pmid}" if pmid else "NA",
            "note": "License metadata requires review.",
            **LICENSE_BY_PMID.get(pmid, {}),
        }
        if pmid in LICENSE_BY_PMID and license_info["note"] == "License metadata requires review.":
            license_info["note"] = (
                "Europe PMC license metadata checked on 2026-08-10; this status governs "
                "the v0.2.0 source-specific table. Original repository terms still apply."
            )
        license_rows.append({
            "source_id": source_id,
            "pmid": pmid or "NA",
            "article_license": license_info["article_license"],
            "redistribution_status": license_info["redistribution_status"],
            "license_source": license_info["license_source"],
            "note": license_info["note"],
        })

        destination = RECORD_ROOT / source_id
        destination.mkdir(parents=True, exist_ok=True)

        if source_id == "BATTER_S1_002":
            fields_payload = {
                "schema_version": "1.0",
                "source_id": source_id,
                "release_version": RELEASE_VERSION,
                "core_table": {"publication_status": "not_emitted_audit_only"},
                "source_annotations": {"publication_status": "not_emitted_audit_only"},
            }
            (destination / "fields.json").write_text(json.dumps(fields_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            record_manifest = {
                **source_manifest,
                "release_version": RELEASE_VERSION,
                "release_status": "audit_only",
                "record_count": 0,
                "evidence_class": "NA",
                "has_jbrowse": False,
                "redistribution": license_info,
                "decision_note": "No public endpoint table or JBrowse configuration is emitted because per-record experimental provenance is not separable from the integrated summary.",
                "known_limitations": "The author summary integrates multiple experimental systems. Per-record experimental provenance cannot yet be separated reliably, so v0.2.0 publishes source metadata only and provides neither endpoint rows nor JBrowse.",
            }
            (destination / "manifest.json").write_text(json.dumps(record_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            files = write_checksums(destination)
            release_sources[source_id] = {
                "release_status": "audit_only", "record_count": 0, "evidence_class": "NA",
                "record_root": str(destination.relative_to(REPO_ROOT)), "has_jbrowse": False,
                "redistribution_status": license_info["redistribution_status"], "files": files,
            }
            continue

        config = v01.PUBLIC_TABLES[source_id]
        canonical_rows, annotation_rows, source_fields = canonical_and_annotations(
            source_id, input_root, registry[source_id], config
        )
        write_tsv(destination / "endpoints.tsv", v01.ENDPOINT_COLUMNS, canonical_rows)
        v01.write_bed(destination / "endpoints.bed", canonical_rows)
        if source_fields["publication_status"] == "published":
            annotation_columns = ["end_id", "source_record_id"] + [field["name"] for field in source_fields["fields"]]
            write_tsv(destination / "source_annotations.tsv", annotation_columns, annotation_rows)

        companion_manifests: list[dict[str, object]] = []
        for companion in COMPANION_TABLES.get(source_id, []):
            companion_path = input_root / companion["input"]
            columns, rows = read_tsv(companion_path)
            linked_rows = link_companion_rows(rows, canonical_rows, companion["link_method"])
            output = destination / companion["asset"]
            write_tsv(output, ["end_id", "link_status"] + columns, linked_rows)
            companion_manifests.append({
                **companion,
                "row_count": len(rows),
                "linked_rows": sum(bool(row["end_id"]) for row in linked_rows),
                "source_input_sha256": sha256(companion_path),
                "fields": [
                    {
                        "name": name,
                        "data_type": infer_type(row.get(name, "") for row in rows),
                        "evidence_role": evidence_role(name),
                        "units": units_for(name),
                    }
                    for name in columns
                ],
            })

        fields_payload = {
            "schema_version": "1.0",
            "source_id": source_id,
            "release_version": RELEASE_VERSION,
            "core_table": {
                "table": "endpoints.tsv", "row_count": len(canonical_rows),
                "columns": v01.ENDPOINT_COLUMNS,
                "coordinate_convention": "1-based biological coordinate; BED is 0-based half-open",
            },
            "source_annotations": source_fields,
            "companion_tables": companion_manifests,
            "allowed_evidence_roles": [
                "experimental_measurement", "author_called_endpoint", "author_annotation",
                "prediction_annotation", "curation_metadata",
            ],
        }
        (destination / "fields.json").write_text(json.dumps(fields_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        record_manifest = {
            **source_manifest,
            "release_version": RELEASE_VERSION,
            "release_status": "published_standardized",
            "record_count": len(canonical_rows),
            "evidence_class": config["evidence"],
            "has_jbrowse": True,
            "jbrowse_config": f"{source_id}.config.json",
            "redistribution": license_info,
            "source_annotations_status": source_fields["publication_status"],
            "decision_note": config["note"],
            "known_limitations": source_manifest.get("blocker_or_note", "NA"),
        }
        (destination / "manifest.json").write_text(json.dumps(record_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        files = write_checksums(destination)
        release_sources[source_id] = {
            "release_status": "published_standardized",
            "record_count": len(canonical_rows),
            "evidence_class": config["evidence"],
            "record_root": str(destination.relative_to(REPO_ROOT)),
            "has_jbrowse": True,
            "redistribution_status": license_info["redistribution_status"],
            "source_annotations_status": source_fields["publication_status"],
            "files": files,
        }

    license_path = REPO_ROOT / "data/registry/batter_s1_license_status.v0.2.0.tsv"
    write_tsv(
        license_path,
        ["source_id", "pmid", "article_license", "redistribution_status", "license_source", "note"],
        license_rows,
    )

    release_manifest = {
        "release_version": RELEASE_VERSION,
        "release_date": RELEASE_DATE,
        "schema": {
            "core": "24-column BTED endpoint schema",
            "source_annotations": "lossless source-specific fields keyed by end_id",
        },
        "summary": {
            "source_count": 22,
            "published_standardized_sources": 21,
            "audit_only_sources": 1,
            "published_record_count": sum(int(entry["record_count"]) for entry in release_sources.values()),
            "jbrowse_sources": sum(bool(entry["has_jbrowse"]) for entry in release_sources.values()),
            "source_annotation_tables": sum(entry.get("source_annotations_status") == "published" for entry in release_sources.values()),
            "external_link_only_annotation_sources": len(LALANNE_SOURCES),
        },
        "evidence_policy": "Prediction-only and inseparable mixed-evidence records are excluded. Prediction fields retained in source annotations do not change endpoint evidence.",
        "sources": release_sources,
    }
    release_path = OUTPUT_ROOT / "release_manifest.json"
    release_path.write_text(json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUTPUT_ROOT / "SHA256SUMS.txt").write_text(
        f"{sha256(release_path)}  release_manifest.json\n",
        encoding="utf-8",
    )

    status_path = REPO_ROOT / "data/registry/batter_s1_publication_status.v0.2.0.tsv"
    status_rows = []
    for source_id in source_ids:
        entry = release_sources[source_id]
        status_rows.append({
            "source_id": source_id,
            "release_status": entry["release_status"],
            "record_count": str(entry["record_count"]),
            "evidence_class": entry["evidence_class"],
            "has_jbrowse": str(entry["has_jbrowse"]).lower(),
            "source_annotations_status": entry.get("source_annotations_status", "not_emitted_audit_only"),
            "redistribution_status": entry["redistribution_status"],
            "record_root": entry["record_root"],
        })
    write_tsv(
        status_path,
        ["source_id", "release_status", "record_count", "evidence_class", "has_jbrowse", "source_annotations_status", "redistribution_status", "record_root"],
        status_rows,
    )

    print(
        "PASS  BTED v0.2.0: "
        f"{release_manifest['summary']['published_standardized_sources']} public sources, "
        f"{release_manifest['summary']['published_record_count']} records, "
        f"{release_manifest['summary']['source_annotation_tables']} published source-annotation tables"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
