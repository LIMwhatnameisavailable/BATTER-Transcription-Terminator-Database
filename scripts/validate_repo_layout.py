#!/usr/bin/env python3
"""Validate the public repository layout without inspecting biological data."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TOP_LEVEL = {
    ".github",
    ".gitignore",
    "CONTRIBUTING.md",
    "README.md",
    "data",
    "docs",
    "scripts",
    "site",
    "tests",
}
REQUIRED_PATHS = {
    "data/audit/legacy/README.md",
    "data/audit/legacy/accession_list_verified.csv",
    "docs/legacy/project-reports/README.md",
    "docs/legacy/project-reports/PROGRESS.md",
    "docs/legacy/project-reports/data_verification_report.md",
    "docs/legacy/project-reports/report_BATTER_supplementary.md",
    "docs/legacy/project-reports/report_zenodo_and_documents.md",
    "docs/legacy/project-reports/PMID_38030608_supplementary_data_1to5_findings.md",
}
REMOVED_ROOT_FILES = {
    "PROGRESS.md",
    "accession_list_verified.csv",
    "data_verification_report.md",
    "report_BATTER_supplementary.md",
    "report_zenodo_and_documents.md",
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> int:
    tracked = tracked_files()
    tracked_set = set(tracked)
    errors: list[str] = []

    top_level = {path.split("/", 1)[0] for path in tracked}
    unexpected = sorted(top_level - ALLOWED_TOP_LEVEL)
    if unexpected:
        errors.append(f"unexpected top-level tracked entries: {unexpected}")

    missing = sorted(REQUIRED_PATHS - tracked_set)
    if missing:
        errors.append(f"required archive paths are not tracked: {missing}")

    lingering_root = sorted(REMOVED_ROOT_FILES & tracked_set)
    if lingering_root:
        errors.append(f"legacy files remain at repository root: {lingering_root}")

    forbidden = sorted(
        path
        for path in tracked
        if path.startswith("docs/legacy/original-directories/")
        or "/__MACOSX/" in f"/{path}"
        or Path(path).name.startswith("._")
        or Path(path).name.endswith("_read_starts.txt")
    )
    if forbidden:
        errors.append(f"forbidden legacy/raw paths remain tracked: {forbidden}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print(
        "PASS: repository root is project-focused; legacy reports and accession "
        "snapshot are archived; original-directories/read-starts/macOS junk are untracked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
