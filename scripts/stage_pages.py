#!/usr/bin/env python3
"""Stage the BTED site, small data release and JBrowse bundle for Pages."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from build_assembly_downloads import build as build_assembly_downloads


REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jbrowse-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path(".pages-preview"))
    args = parser.parse_args()
    jbrowse = args.jbrowse_dir.expanduser().resolve()
    output = args.output_dir.expanduser().resolve()
    if not (jbrowse / "catalog.json").is_file():
        parser.error("--jbrowse-dir is not an unpacked BTED JBrowse package")
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(REPO_ROOT / "site", output)
    shutil.copytree(REPO_ROOT / "data/public/v0.2.0", output / "downloads")
    build_assembly_downloads(output / "downloads" / "assemblies")
    shutil.copytree(jbrowse, output / "jbrowse")
    print(f"PASS  Staged Pages preview at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
