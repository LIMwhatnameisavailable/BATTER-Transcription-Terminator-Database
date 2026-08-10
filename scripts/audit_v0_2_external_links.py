#!/usr/bin/env python3
"""Audit v0.2 paper and public-data URLs and write a traceable TSV report."""

from __future__ import annotations

import csv
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RECORD_ROOT = ROOT / "data/public/v0.2.0/records"
OUTPUT = ROOT / "data/audit/v0.2.0/external_link_audit.tsv"
LINK_FIELDS = ("pubmed_url", "doi_url", "pmc_url", "raw_data_url")


def check(url: str) -> tuple[str, str]:
    result = subprocess.run(
        [
            "curl", "-L", "--max-time", "25", "--retry", "3", "--retry-all-errors", "--retry-delay", "1",
            "--user-agent", "BTED-link-audit/0.2",
            "--range", "0-0", "--output", "/dev/null", "--silent", "--show-error",
            "--write-out", "%{http_code}", url,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    code = result.stdout.strip()[-3:] if result.stdout.strip() else "000"
    if code.isdigit() and 200 <= int(code) < 400:
        return code, "reachable"
    if code in {"401", "403", "405", "429"}:
        return code, "reachable_restricted"
    return code, "failed"


def main() -> int:
    records: list[dict[str, str]] = []
    urls: set[str] = set()
    for manifest_path in sorted(RECORD_ROOT.glob("BATTER_S1_*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for field in LINK_FIELDS:
            url = str(manifest.get(field, ""))
            if not url or url == "NA":
                if field == "pmc_url":
                    continue
                records.append({
                    "source_id": manifest["source_id"], "link_type": field,
                    "url": url or "NA", "http_status": "NA", "audit_status": "missing_required",
                    "checked_date": "2026-08-10",
                })
                continue
            urls.add(url)
            records.append({
                "source_id": manifest["source_id"], "link_type": field,
                "url": url, "http_status": "", "audit_status": "",
                "checked_date": "2026-08-10",
            })

    # NCBI throttles burst traffic; low concurrency avoids turning valid links
    # into transient HTTP 000 failures.
    with ThreadPoolExecutor(max_workers=2) as executor:
        checked = dict(zip(sorted(urls), executor.map(check, sorted(urls))))
    for row in records:
        if row["url"] in checked:
            row["http_status"], row["audit_status"] = checked[row["url"]]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    columns = ["source_id", "link_type", "url", "http_status", "audit_status", "checked_date"]
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)

    failures = [row for row in records if row["audit_status"] in {"failed", "missing_required"}]
    restricted = sum(row["audit_status"] == "reachable_restricted" for row in records)
    if failures:
        for row in failures:
            print(f"FAIL {row['source_id']} {row['link_type']} {row['http_status']} {row['url']}")
        return 1
    print(f"PASS {len(records)} source-link records; {len(urls)} unique URLs; {restricted} restricted responses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
