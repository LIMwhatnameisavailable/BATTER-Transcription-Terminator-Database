#!/usr/bin/env python3
"""Validate BTED's portable public release assets (standard library only).

Checks the v0.1 local-snapshot release manifest, the 22 source manifests and
source records, public 24-column tables, BED conversion, checksums, and the
evidence boundary.  It purposely does not require raw inputs or a browser
bundle, because those files are intentionally outside this Git release.

Usage:
    python3 scripts/validate_bted_release.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE = REPO_ROOT / "data/public/release_manifest.v0.1-local-snapshot.json"
STATUS = REPO_ROOT / "data/registry/batter_s1_publication_status.tsv"
MANIFEST_ROOT = REPO_ROOT / "data/registry/manifests"
SOURCE_DOC_ROOT = REPO_ROOT / "docs/sources"

EXPECTED_COLUMNS = [
    "end_id", "source_id", "sample_id", "assay", "evidence_class",
    "author_endpoint_id", "published_reference_accession",
    "reference_assembly", "reference_name", "replicon_label",
    "biological_coordinate_1based", "bed_start_0based", "bed_end_0based",
    "strand", "signal_or_score", "author_category",
    "associated_gene_or_locus", "pmid", "doi", "source_table_or_file",
    "coordinate_interpretation", "original_row_reference", "qc_status", "note",
]
PUBLIC_EVIDENCE = {
    "observed_signal", "called_endpoint", "author_called_endpoint", "curated_record",
}
EXPECTED_SOURCE_IDS = [f"BATTER_S1_{number:03d}" for number in range(1, 23)]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def check_bed(tsv_path: Path, bed_path: Path, rows: list[dict[str, str]], problems: list[str]) -> None:
    if not bed_path.is_file():
        problems.append(f"{bed_path.relative_to(REPO_ROOT)}: 缺少实验端点 BED")
        return
    with bed_path.open(encoding="utf-8") as handle:
        bed_rows = [line.rstrip("\n").split("\t") for line in handle if line.strip()]
    if len(bed_rows) != len(rows):
        problems.append(f"{bed_path.relative_to(REPO_ROOT)}: 行数 {len(bed_rows)} != TSV 行数 {len(rows)}")
        return
    for number, (bed, row) in enumerate(zip(bed_rows, rows), start=1):
        expected = [
            row["reference_name"], row["bed_start_0based"], row["bed_end_0based"],
            row["end_id"], "0", row["strand"],
        ]
        if bed != expected:
            problems.append(f"{bed_path.relative_to(REPO_ROOT)}:{number}: 与 TSV 的 BED6 表示不一致")
            break


def main() -> int:
    problems: list[str] = []
    if not RELEASE.is_file():
        print(f"FAIL  缺少 release manifest: {RELEASE.relative_to(REPO_ROOT)}")
        return 1
    if not STATUS.is_file():
        print(f"FAIL  缺少发布状态表: {STATUS.relative_to(REPO_ROOT)}")
        return 1

    release = json.loads(RELEASE.read_text(encoding="utf-8"))
    sources = release.get("sources", {})
    if sorted(sources) != EXPECTED_SOURCE_IDS:
        problems.append("release manifest 未恰好包含 BATTER_S1_001 至 BATTER_S1_022")

    with STATUS.open(encoding="utf-8", newline="") as handle:
        status_rows = list(csv.DictReader(handle, delimiter="\t"))
    if [row["source_id"] for row in status_rows] != EXPECTED_SOURCE_IDS:
        problems.append("发布状态表必须恰好按顺序包含 22 个 BATTER S1 来源")
    status_by_source = {row["source_id"]: row for row in status_rows}

    total_public_rows = 0
    public_sources = 0
    audit_sources = 0
    for source_id in EXPECTED_SOURCE_IDS:
        entry = sources.get(source_id)
        if not isinstance(entry, dict):
            continue
        source_doc = SOURCE_DOC_ROOT / source_id / "README.md"
        source_manifest = MANIFEST_ROOT / f"{source_id}.json"
        if not source_doc.is_file():
            problems.append(f"{source_id}: 缺少来源 README")
        if not source_manifest.is_file():
            problems.append(f"{source_id}: 缺少来源 manifest")
        else:
            source_metadata = json.loads(source_manifest.read_text(encoding="utf-8"))
            release_info = source_metadata.get("repository_release", {})
            if release_info.get("release_status") != entry.get("release_status"):
                problems.append(f"{source_id}: 来源 manifest 与 release manifest 的发布状态不一致")
            if source_metadata.get("has_jbrowse") and release_info.get("jbrowse_published_in_repository"):
                problems.append(f"{source_id}: 不应在未迁移浏览器资产时声称 JBrowse 已随仓库发布")

        status = entry.get("release_status")
        status_row = status_by_source.get(source_id, {})
        if status_row.get("release_status") != status:
            problems.append(f"{source_id}: 发布状态表与 release manifest 不一致")
        if status == "audit_only":
            audit_sources += 1
            if entry.get("public_asset"):
                problems.append(f"{source_id}: audit-only 来源不应具有 public_asset")
            continue
        if status != "published_standardized":
            problems.append(f"{source_id}: 未识别的 release_status {status!r}")
            continue

        public_sources += 1
        rel_path = entry.get("public_asset", "")
        tsv_path = REPO_ROOT / rel_path
        if not tsv_path.is_file():
            problems.append(f"{source_id}: 公开 TSV 不存在: {rel_path}")
            continue
        with tsv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames != EXPECTED_COLUMNS:
                problems.append(f"{rel_path}: 表头不是正式 24 列 schema")
            rows = list(reader)
        expected_rows = int(entry.get("record_count", -1))
        if len(rows) != expected_rows:
            problems.append(f"{rel_path}: 实际 {len(rows)} 行，release manifest 记录 {expected_rows} 行")
        if int(status_row.get("record_count", -1)) != expected_rows:
            problems.append(f"{source_id}: 发布状态表的 record_count 与 release manifest 不一致")
        total_public_rows += len(rows)
        end_ids: set[str] = set()
        for number, row in enumerate(rows, start=2):
            if row["source_id"] != source_id:
                problems.append(f"{rel_path}:{number}: source_id 不一致")
                break
            if row["evidence_class"] not in PUBLIC_EVIDENCE:
                problems.append(f"{rel_path}:{number}: 非公开 evidence_class {row['evidence_class']!r}")
                break
            if row["end_id"] in end_ids:
                problems.append(f"{rel_path}:{number}: end_id 重复")
                break
            end_ids.add(row["end_id"])
            try:
                position = int(row["biological_coordinate_1based"])
            except ValueError:
                problems.append(f"{rel_path}:{number}: biological_coordinate_1based 非整数")
                break
            if position < 1 or row["bed_start_0based"] != str(position - 1) or row["bed_end_0based"] != str(position):
                problems.append(f"{rel_path}:{number}: 1-based 到 BED 坐标转换错误")
                break
            if row["strand"] not in {"+", "-"}:
                problems.append(f"{rel_path}:{number}: strand 必须为 + 或 -")
                break
            if not row["end_id"].startswith(f"BTED_{source_id}"):
                problems.append(f"{rel_path}:{number}: end_id 未保留 source 标识")
                break
            if not row["reference_name"] or row["reference_name"] == "NA":
                problems.append(f"{rel_path}:{number}: reference_name 缺失")
                break

        expected_file_records = entry.get("files", [])
        expected_files = {item["path"]: item["sha256"] for item in expected_file_records}
        for file_rel, expected_sha in expected_files.items():
            file_path = REPO_ROOT / file_rel
            if not file_path.is_file():
                problems.append(f"{source_id}: release manifest 声明的文件不存在: {file_rel}")
            elif digest(file_path) != expected_sha:
                problems.append(f"{source_id}: SHA-256 不匹配: {file_rel}")
        if entry.get("evidence_class") != "curated_record":
            check_bed(tsv_path, tsv_path.with_suffix(".bed"), rows, problems)
        elif tsv_path.with_suffix(".bed").exists():
            problems.append(f"{source_id}: curated_record 不应在本 release 生成公开 BED")

    summary = release.get("summary", {})
    if summary.get("source_count") != 22:
        problems.append("release summary source_count 应为 22")
    if summary.get("published_standardized_sources") != public_sources:
        problems.append("release summary public source count 不匹配")
    if summary.get("audit_only_sources") != audit_sources:
        problems.append("release summary audit-only source count 不匹配")
    if summary.get("published_record_count") != total_public_rows:
        problems.append("release summary published record count 不匹配")

    print("=" * 60)
    print("BTED v0.1 local-snapshot release validation")
    print("检查项: 22 来源 / 来源记录 / 24 列 schema / 证据边界 / 坐标 / BED / SHA-256")
    print("=" * 60)
    if problems:
        for problem in problems:
            print(f"FAIL  {problem}")
        print(f"FAIL  共 {len(problems)} 个问题")
        return 1
    print(f"PASS  {public_sources} 个公开标准化来源，{audit_sources} 个仅审计来源，{total_public_rows} 条标准化记录")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
