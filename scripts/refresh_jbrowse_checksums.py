#!/usr/bin/env python3
"""Regenerate SHA256SUMS.txt for an unpacked BTED JBrowse directory."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/BTED-v0.2.0-jbrowse").resolve()
    if not root.is_dir():
        print(f"FAIL missing JBrowse directory: {root}")
        return 1
    output = root / "SHA256SUMS.txt"
    files = sorted(path for path in root.rglob("*") if path.is_file() and path != output)
    output.write_text(
        "".join(f"{sha256(path)}  {path.relative_to(root)}\n" for path in files),
        encoding="utf-8",
    )
    print(f"PASS  refreshed checksums for {len(files)} JBrowse files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
