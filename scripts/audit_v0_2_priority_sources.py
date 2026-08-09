#!/usr/bin/env python3
"""Create the deterministic v0.2 engineering audit for S1_005/020/022.

This audit verifies database invariants only.  It does not reinterpret the
authors' endpoint calls or make a new biological claim.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RECORDS = ROOT / "data/public/v0.2.0/records"
OUTPUT = ROOT / "data/audit/v0.2.0/priority_source_audit.json"
SOURCE_IDS = ("BATTER_S1_005", "BATTER_S1_020", "BATTER_S1_022")


def rows(source_id: str) -> list[dict[str, str]]:
    with (RECORDS / source_id / "endpoints.tsv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sample_rows(records: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in records:
        grouped[(row["reference_name"], row["strand"])].append(row)
    selected: list[dict[str, str]] = []
    for key in sorted(grouped):
        group = sorted(grouped[key], key=lambda row: int(row["biological_coordinate_1based"]))
        for index in sorted({0, len(group) // 2, len(group) - 1}):
            row = group[index]
            selected.append({
                "end_id": row["end_id"],
                "reference_name": row["reference_name"],
                "coordinate_1based": int(row["biological_coordinate_1based"]),
                "bed_start_0based": int(row["bed_start_0based"]),
                "bed_end_0based": int(row["bed_end_0based"]),
                "strand": row["strand"],
            })
    return selected


def audit_source(source_id: str) -> dict[str, object]:
    records = rows(source_id)
    keys = [
        (row["reference_name"], row["biological_coordinate_1based"], row["strand"])
        for row in records
    ]
    coordinate_ok = all(
        int(row["bed_start_0based"]) == int(row["biological_coordinate_1based"]) - 1
        and int(row["bed_end_0based"]) == int(row["biological_coordinate_1based"])
        for row in records
    )
    result: dict[str, object] = {
        "record_count": len(records),
        "reference_counts": dict(sorted(Counter(row["reference_name"] for row in records).items())),
        "strand_counts": dict(sorted(Counter(row["strand"] for row in records).items())),
        "evidence_classes": sorted({row["evidence_class"] for row in records}),
        "source_tables": sorted({row["source_table_or_file"] for row in records}),
        "unique_reference_coordinate_strand": len(keys) == len(set(keys)),
        "bed_conversion_valid": coordinate_ok,
        "deterministic_spot_check": sample_rows(records),
    }
    if source_id == "BATTER_S1_005":
        expected = {"CP009977.1": 898, "CP009978.1": 256}
        result["multi_contig_expected"] = result["reference_counts"] == expected
        result["ids_retain_contig"] = all(
            row["reference_name"].replace(".", "-") in row["end_id"] for row in records
        )
    elif source_id == "BATTER_S1_020":
        result["experimental_layer_only"] = (
            result["source_tables"] == ["Supplementary Table S2D"]
            and result["evidence_classes"] == ["author_called_endpoint"]
        )
        result["mixed_layer_excluded"] = all(
            "S1C" not in row["source_table_or_file"] and "mixed" not in row["evidence_class"].lower()
            for row in records
        )
    elif source_id == "BATTER_S1_022":
        result["reference_mapping_consistent"] = all(
            row["published_reference_accession"] == "AL123456.3"
            and row["reference_name"] == "NC_000962.3"
            for row in records
        )
        result["prediction_only_rows_excluded"] = all(
            "prediction_only" not in row["evidence_class"].lower() for row in records
        )
    return result


def main() -> int:
    audit = {
        "release_version": "v0.2.0",
        "audit_date": "2026-08-10",
        "scope": "Database engineering invariants; no new biological interpretation.",
        "sources": {source_id: audit_source(source_id) for source_id in SOURCE_IDS},
    }
    failures: list[str] = []
    for source_id, result in audit["sources"].items():
        for key, value in result.items():
            if key.endswith(("_valid", "_expected", "_consistent", "_excluded", "_only")) or key in {
                "unique_reference_coordinate_strand", "ids_retain_contig"
            }:
                if value is not True:
                    failures.append(f"{source_id}: {key}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failures:
        print("FAIL " + "; ".join(failures))
        return 1
    print(f"PASS wrote {OUTPUT.relative_to(ROOT)} for {len(SOURCE_IDS)} priority sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
