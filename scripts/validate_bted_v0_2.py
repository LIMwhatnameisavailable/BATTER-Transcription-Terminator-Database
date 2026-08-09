#!/usr/bin/env python3
"""Validate the BTED v0.2.0 two-layer data release."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import build_local_snapshot_release as v01


REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_ROOT = REPO_ROOT / "data/public/v0.2.0"
RELEASE_PATH = RELEASE_ROOT / "release_manifest.json"
LICENSE_PATH = REPO_ROOT / "data/registry/batter_s1_license_status.v0.2.0.tsv"
STATUS_PATH = REPO_ROOT / "data/registry/batter_s1_publication_status.v0.2.0.tsv"
EXPECTED_SOURCES = [f"BATTER_S1_{number:03d}" for number in range(1, 23)]
ALLOWED_ROLES = {
    "experimental_measurement", "author_called_endpoint", "author_annotation",
    "prediction_annotation", "curation_metadata",
}
FORBIDDEN_CORE_EVIDENCE = {"author_integrated_mixed_evidence", "prediction_only"}
REQUIRED_URL_FIELDS = ("pubmed_url", "doi_url", "raw_data_url")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def check_checksums(source_id: str, directory: Path, problems: list[str]) -> None:
    checksum_path = directory / "SHA256SUMS.txt"
    if not checksum_path.is_file():
        problems.append(f"{source_id}: missing SHA256SUMS.txt")
        return
    seen: set[str] = set()
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2:
            problems.append(f"{source_id}: malformed checksum line: {line}")
            continue
        expected, name = parts
        path = directory / name
        seen.add(name)
        if not path.is_file():
            problems.append(f"{source_id}: checksum target missing: {name}")
        elif digest(path) != expected:
            problems.append(f"{source_id}: checksum mismatch: {name}")
    actual = {path.name for path in directory.iterdir() if path.is_file() and path.name != checksum_path.name}
    if seen != actual:
        problems.append(f"{source_id}: checksum inventory differs from actual files")


def check_core(source_id: str, directory: Path, expected_count: int, problems: list[str]) -> list[dict[str, str]]:
    tsv = directory / "endpoints.tsv"
    bed = directory / "endpoints.bed"
    if not tsv.is_file() or not bed.is_file():
        problems.append(f"{source_id}: missing endpoints.tsv or endpoints.bed")
        return []
    columns, rows = read_tsv(tsv)
    if columns != v01.ENDPOINT_COLUMNS:
        problems.append(f"{source_id}: core table is not the stable 24-column schema")
    if len(rows) != expected_count:
        problems.append(f"{source_id}: core row count {len(rows)} != manifest {expected_count}")
    ids: set[str] = set()
    with bed.open(encoding="utf-8") as handle:
        bed_rows = [line.rstrip("\n").split("\t") for line in handle if line.strip()]
    if len(bed_rows) != len(rows):
        problems.append(f"{source_id}: BED row count differs from core table")
        return rows
    for number, (row, bed_row) in enumerate(zip(rows, bed_rows), start=2):
        if row["source_id"] != source_id:
            problems.append(f"{source_id}:{number}: source_id mismatch")
            break
        if row["end_id"] in ids:
            problems.append(f"{source_id}:{number}: duplicate end_id")
            break
        ids.add(row["end_id"])
        if row["evidence_class"] in FORBIDDEN_CORE_EVIDENCE:
            problems.append(f"{source_id}:{number}: forbidden public evidence class")
            break
        try:
            position = int(row["biological_coordinate_1based"])
        except ValueError:
            problems.append(f"{source_id}:{number}: non-integer coordinate")
            break
        expected_bed = [row["reference_name"], str(position - 1), str(position), row["end_id"], "0", row["strand"]]
        if bed_row != expected_bed:
            problems.append(f"{source_id}:{number}: BED6 conversion mismatch")
            break
    return rows


def check_source_annotations(
    source_id: str,
    directory: Path,
    core_rows: list[dict[str, str]],
    fields: dict[str, object],
    problems: list[str],
) -> None:
    spec = fields.get("source_annotations", {})
    status = spec.get("publication_status")
    original_columns = spec.get("source_input_columns", [])
    field_specs = spec.get("fields", [])
    if len(field_specs) != len(original_columns):
        problems.append(f"{source_id}: not every input column has a field-manifest entry")
    if {item.get("original_name") for item in field_specs} != set(original_columns):
        problems.append(f"{source_id}: field manifest does not exactly cover source input columns")
    if any(item.get("evidence_role") not in ALLOWED_ROLES for item in field_specs):
        problems.append(f"{source_id}: unknown source-field evidence role")

    annotation_path = directory / "source_annotations.tsv"
    if status == "withheld_external_link_only":
        if annotation_path.exists():
            problems.append(f"{source_id}: external-link-only annotations were copied publicly")
        if any(item.get("publication_status") != "withheld_external_link_only" for item in field_specs):
            problems.append(f"{source_id}: withheld fields are not explicitly labelled")
        return
    if status != "published":
        problems.append(f"{source_id}: unknown source annotation status {status!r}")
        return
    if not annotation_path.is_file():
        problems.append(f"{source_id}: source_annotations.tsv missing")
        return
    annotation_columns, annotation_rows = read_tsv(annotation_path)
    expected_columns = ["end_id", "source_record_id"] + [item["name"] for item in field_specs]
    if annotation_columns != expected_columns:
        problems.append(f"{source_id}: annotation columns differ from fields.json")
    if len(annotation_rows) != len(core_rows):
        problems.append(f"{source_id}: annotation row count differs from core")
    elif [row["end_id"] for row in annotation_rows] != [row["end_id"] for row in core_rows]:
        problems.append(f"{source_id}: annotation end_id order/linkage differs from core")


def main() -> int:
    problems: list[str] = []
    if not RELEASE_PATH.is_file():
        print(f"FAIL missing {RELEASE_PATH.relative_to(REPO_ROOT)}")
        return 1
    release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))
    sources = release.get("sources", {})
    if list(sources) != EXPECTED_SOURCES:
        problems.append("release manifest must contain BATTER_S1_001 through BATTER_S1_022 in order")

    total = 0
    public = 0
    audit = 0
    jbrowse = 0
    for source_id in EXPECTED_SOURCES:
        entry = sources.get(source_id, {})
        directory = RELEASE_ROOT / "records" / source_id
        if not directory.is_dir():
            problems.append(f"{source_id}: missing record directory")
            continue
        for name in ("manifest.json", "fields.json", "SHA256SUMS.txt"):
            if not (directory / name).is_file():
                problems.append(f"{source_id}: missing {name}")
        if problems and not (directory / "manifest.json").is_file():
            continue
        record_manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        fields = json.loads((directory / "fields.json").read_text(encoding="utf-8"))
        if record_manifest.get("release_version") != "v0.2.0":
            problems.append(f"{source_id}: record manifest release version mismatch")
        if record_manifest.get("source_id") != source_id:
            problems.append(f"{source_id}: record manifest source ID mismatch")
        for field in REQUIRED_URL_FIELDS:
            if not str(record_manifest.get(field, "")).startswith("https://"):
                problems.append(f"{source_id}: missing or non-HTTPS {field}")
        if bool(record_manifest.get("has_jbrowse")) != bool(entry.get("has_jbrowse")):
            problems.append(f"{source_id}: record/release JBrowse status mismatch")
        jbrowse += bool(entry.get("has_jbrowse"))

        if entry.get("release_status") == "audit_only":
            audit += 1
            if source_id != "BATTER_S1_002" or entry.get("has_jbrowse"):
                problems.append(f"{source_id}: only S1_002 may be audit-only and it must have no JBrowse")
            if (directory / "endpoints.tsv").exists() or (directory / "endpoints.bed").exists():
                problems.append(f"{source_id}: audit-only source contains endpoint assets")
            check_checksums(source_id, directory, problems)
            continue

        public += 1
        expected_count = int(entry.get("record_count", -1))
        total += expected_count
        core_rows = check_core(source_id, directory, expected_count, problems)
        check_source_annotations(source_id, directory, core_rows, fields, problems)
        check_checksums(source_id, directory, problems)

        for companion in fields.get("companion_tables", []):
            path = directory / companion["asset"]
            if not path.is_file():
                problems.append(f"{source_id}: missing companion table {companion['asset']}")
                continue
            _columns, rows = read_tsv(path)
            if len(rows) != companion["row_count"]:
                problems.append(f"{source_id}: companion row count mismatch for {companion['asset']}")
            if sum(row.get("link_status") == "linked" for row in rows) != companion["linked_rows"]:
                problems.append(f"{source_id}: companion linkage count mismatch for {companion['asset']}")

        if source_id == "BATTER_S1_005":
            contigs = {row["reference_name"] for row in core_rows}
            if contigs != {"CP009977.1", "CP009978.1"}:
                problems.append("BATTER_S1_005: both chromosomes must be present")
            if any(v01.id_token(row["reference_name"]) not in row["end_id"] for row in core_rows):
                problems.append("BATTER_S1_005: canonical IDs must retain contig identity")
        if source_id == "BATTER_S1_020":
            if any("author_integrated" in path.name for path in directory.iterdir()):
                problems.append("BATTER_S1_020: mixed-evidence table copied into public release")
            if any(row["source_table_or_file"] != "Supplementary Table S2D" for row in core_rows):
                problems.append("BATTER_S1_020: public core contains a non-S2D record")
        if source_id == "BATTER_S1_022":
            if any("prediction_only" in path.name for path in directory.iterdir()):
                problems.append("BATTER_S1_022: prediction-only table copied into public release")

    summary = release.get("summary", {})
    expected_summary = {
        "source_count": 22,
        "published_standardized_sources": public,
        "audit_only_sources": audit,
        "published_record_count": total,
        "jbrowse_sources": jbrowse,
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            problems.append(f"summary {key} is {summary.get(key)!r}, expected {value!r}")
    if (public, audit, total, jbrowse) != (21, 1, 28_399, 21):
        problems.append("release gate requires 21 public, 1 audit-only, 28,399 records, and 21 JBrowse sources")

    for path in (LICENSE_PATH, STATUS_PATH):
        if not path.is_file():
            problems.append(f"missing registry file {path.relative_to(REPO_ROOT)}")
        else:
            _columns, rows = read_tsv(path)
            if [row["source_id"] for row in rows] != EXPECTED_SOURCES:
                problems.append(f"{path.name}: must contain exactly 22 ordered sources")

    root_checksum = RELEASE_ROOT / "SHA256SUMS.txt"
    if not root_checksum.is_file():
        problems.append("missing v0.2.0 release-root SHA256SUMS.txt")
    else:
        expected, name = root_checksum.read_text(encoding="utf-8").strip().split("  ", 1)
        target = RELEASE_ROOT / name
        if name != "release_manifest.json" or not target.is_file() or digest(target) != expected:
            problems.append("release-root checksum does not match release_manifest.json")

    print("=" * 64)
    print("BTED v0.2.0 release validation")
    print("checks: two-layer schema / field coverage / evidence / BED / checksum / licensing gate")
    print("=" * 64)
    if problems:
        for problem in problems:
            print(f"FAIL  {problem}")
        print(f"FAIL  {len(problems)} problem(s)")
        return 1
    print(f"PASS  {public} public sources, {audit} audit-only source, {total} core records, {jbrowse} JBrowse-ready sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
