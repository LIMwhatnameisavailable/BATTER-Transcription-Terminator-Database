#!/usr/bin/env python3
"""Create the versioned BTED v0.2.0 data archive for GitHub Release."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import tarfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data/public/v0.2.0"


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def normalized(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    args = parser.parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / "BTED-v0.2.0-data.tar.gz"
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")

    if not (DATA_ROOT / "release_manifest.json").is_file():
        raise FileNotFoundError("Run scripts/build_v0_2_release.py before creating the archive")
    with archive_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for path in sorted(DATA_ROOT.rglob("*")):
                    arcname = Path("BTED-v0.2.0-data") / path.relative_to(DATA_ROOT)
                    archive.add(path, arcname=str(arcname), recursive=False, filter=normalized)
    checksum_path.write_text(f"{sha256(archive_path)}  {archive_path.name}\n", encoding="utf-8")
    print(f"PASS  {archive_path.name}: {archive_path.stat().st_size / 1024 / 1024:.1f} MiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
