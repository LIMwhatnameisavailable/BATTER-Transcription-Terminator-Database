#!/usr/bin/env python3
"""Validate an unpacked BTED v0.2.0 JBrowse release directory."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED = [f"BATTER_S1_{number:03d}" for number in range(1, 23) if number != 2]
LALANNE = {"BATTER_S1_001", "BATTER_S1_003", "BATTER_S1_004", "BATTER_S1_005"}
FORBIDDEN_TEXT = ("prediction_only", "author_integrated_mixed_evidence", "bar2023_ecoli_trs")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def uris(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        if isinstance(value.get("uri"), str):
            found.append(value["uri"])
        for child in value.values():
            found.extend(uris(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(uris(child))
    return found


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/BTED-v0.2.0-jbrowse").resolve()
    problems: list[str] = []
    if not root.is_dir():
        print(f"FAIL missing package directory: {root}")
        return 1
    catalog_path = root / "catalog.json"
    if not catalog_path.is_file():
        print("FAIL missing catalog.json")
        return 1
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if list(catalog.get("sources", {})) != EXPECTED:
        problems.append("catalog must contain exactly the 21 publishable S1 sources in order")
    if catalog.get("excluded_sources") != ["BATTER_S1_002"]:
        problems.append("catalog must explicitly exclude BATTER_S1_002")

    for forbidden_dir in ("test_data", "trix"):
        if (root / forbidden_dir).exists():
            problems.append(f"unnecessary JBrowse directory included: {forbidden_dir}")
    if any("bar2023" in path.name.lower() for path in root.rglob("*")):
        problems.append("BATTER_S1_002 asset/config was included")

    for source_id in EXPECTED:
        entry = catalog.get("sources", {}).get(source_id, {})
        config_path = root / str(entry.get("config", ""))
        if not config_path.is_file():
            problems.append(f"{source_id}: missing config")
            continue
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config_text = json.dumps(config, ensure_ascii=False).lower()
        if any(token in config_text for token in FORBIDDEN_TEXT):
            problems.append(f"{source_id}: forbidden evidence text in config")
        if source_id in LALANNE and ("literature" in config_text or "curated_terminator" in config_text):
            problems.append(f"{source_id}: restricted literature-curated overlay remains")
        track_ids = [track.get("trackId") for track in config.get("tracks", [])]
        if not track_ids or len(track_ids) != len(set(track_ids)):
            problems.append(f"{source_id}: missing or duplicate track IDs")
        configured_uris = sorted(set(uris(config)))
        if configured_uris != entry.get("assets"):
            problems.append(f"{source_id}: config URI inventory differs from catalog")
        for uri in configured_uris:
            if "://" in uri or uri.startswith("/") or ".." in Path(uri).parts:
                problems.append(f"{source_id}: non-portable URI {uri}")
                continue
            path = root / uri
            if not path.is_file():
                problems.append(f"{source_id}: missing asset {uri}")
            if not path.name.startswith(f"{source_id}__"):
                problems.append(f"{source_id}: asset lacks source prefix: {path.name}")

    vnat_config = json.loads((root / "BATTER_S1_005.config.json").read_text(encoding="utf-8"))
    fai_uris = [uri for uri in uris(vnat_config) if uri.endswith(".fai")]
    if len(fai_uris) != 1:
        problems.append("BATTER_S1_005: expected one multi-contig FAI")
    else:
        contigs = {line.split("\t", 1)[0] for line in (root / fai_uris[0]).read_text(encoding="utf-8").splitlines() if line}
        if contigs != {"CP009977.1", "CP009978.1"}:
            problems.append(f"BATTER_S1_005: FAI contigs are {sorted(contigs)}")

    checksum_path = root / "SHA256SUMS.txt"
    if not checksum_path.is_file():
        problems.append("missing SHA256SUMS.txt")
    else:
        seen: set[str] = set()
        for line in checksum_path.read_text(encoding="utf-8").splitlines():
            expected, name = line.split("  ", 1)
            seen.add(name)
            path = root / name
            if not path.is_file() or digest(path) != expected:
                problems.append(f"checksum mismatch or missing file: {name}")
        actual = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file() and path.name != checksum_path.name}
        if seen != actual:
            problems.append("checksum inventory does not match package files")

    print("=" * 64)
    print("BTED v0.2.0 JBrowse release validation")
    print("checks: 21 configs / evidence boundary / URI portability / assets / multi-contig / checksums")
    print("=" * 64)
    if problems:
        for problem in problems:
            print(f"FAIL  {problem}")
        print(f"FAIL  {len(problems)} problem(s)")
        return 1
    print(f"PASS  {len(EXPECTED)} configs and {sum(item['asset_count'] for item in catalog['sources'].values())} source-scoped assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
