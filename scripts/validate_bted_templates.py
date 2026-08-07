#!/usr/bin/env python3
"""BTED 协作入库模板结构校验脚本（仅依赖 Python 标准库）。

校验来源登记模板与端点标准模板的表头结构，任一检查失败即以退出码 1 结束：

1. 文件存在、可读取，首行表头非空；
2. 来源模板恰为 26 列，端点模板恰为 24 列；
3. 无重复列名；
4. 必备核心列均存在；
5. 不出现模板规范之外的列名，且列顺序与规范一致。

用法：
    python3 scripts/validate_bted_templates.py
    python3 scripts/validate_bted_templates.py 来源表.tsv 端点表.tsv
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_SOURCE = REPO_ROOT / "data/registry/templates/external_literature_source_intake.tsv"
DEFAULT_ENDPOINT = REPO_ROOT / "data/registry/templates/external_literature_endpoint_schema.tsv"

SOURCE_EXPECTED = [
    "source_id", "dataset_id", "paper_title", "paper_publication_year",
    "pmid", "doi", "pmc_or_fulltext_url", "species", "strain",
    "taxonomy_id", "assay", "primary_evidence_class",
    "sample_id_or_condition", "raw_data_accessions",
    "raw_or_supplement_url", "endpoint_source_file",
    "published_reference_accession", "reference_assembly",
    "reference_sequence_accession_or_contigs", "coordinate_convention",
    "strand_definition", "license_or_reuse_note", "processing_status",
    "curator", "intake_date", "blocker_or_note",
]

ENDPOINT_EXPECTED = [
    "end_id", "source_id", "sample_id", "assay", "evidence_class",
    "author_endpoint_id", "published_reference_accession",
    "reference_assembly", "reference_name", "replicon_label",
    "biological_coordinate_1based", "bed_start_0based", "bed_end_0based",
    "strand", "signal_or_score", "author_category",
    "associated_gene_or_locus", "pmid", "doi", "source_table_or_file",
    "coordinate_interpretation", "original_row_reference", "qc_status",
    "note",
]

# 登记与标准化流程中不可缺少的核心列（规范全集的子集）
SOURCE_REQUIRED = [
    "source_id", "dataset_id", "paper_title", "species", "strain",
    "assay", "primary_evidence_class", "processing_status",
    "published_reference_accession", "reference_assembly",
    "coordinate_convention", "strand_definition",
]

ENDPOINT_REQUIRED = [
    "end_id", "source_id", "sample_id", "assay", "evidence_class",
    "reference_name", "biological_coordinate_1based",
    "bed_start_0based", "bed_end_0based", "strand", "qc_status",
]


def check_template(label: str, path: Path, expected: list[str], required: list[str]) -> list[str]:
    """校验单个模板文件，返回问题列表（空列表表示通过）。"""
    problems: list[str] = []

    if not path.is_file():
        return [f"{label}: 文件不存在: {path}"]
    try:
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
    except (UnicodeDecodeError, IndexError):
        return [f"{label}: 文件为空或不是有效的 UTF-8 文本: {path}"]

    header = first_line.split("\t")
    if len(header) == 1 and "," in first_line:
        problems.append(f"{label}: 表头疑似使用逗号分隔，模板要求制表符（TSV）分隔")

    # 1. 列数
    if len(header) != len(expected):
        problems.append(f"{label}: 列数为 {len(header)}，应为 {len(expected)}")

    # 2. 重复列名
    seen: set[str] = set()
    for col in header:
        if col in seen:
            problems.append(f"{label}: 重复列名: {col}")
        seen.add(col)

    # 3. 必备核心列
    for col in required:
        if col not in header:
            problems.append(f"{label}: 缺少必备核心列: {col}")

    # 4. 规范之外的列
    for col in header:
        if col not in expected:
            problems.append(f"{label}: 规范之外的列名: {col!r}（请核对是否拼写错误）")

    # 5. 列顺序
    if header != expected and not any("列数为" in p or "规范之外" in p for p in problems):
        for i, (got, want) in enumerate(zip(header, expected)):
            if got != want:
                problems.append(
                    f"{label}: 第 {i + 1} 列顺序不符: 实际为 {got!r}，应为 {want!r}"
                )
                break

    return problems


def main() -> int:
    source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    endpoint_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_ENDPOINT

    print("=" * 60)
    print("BTED 协作入库模板结构校验")
    print("检查项: 表头存在 / 列数 26·24 / 重复列名 / 必备核心列 / 规范列名与顺序")
    print("=" * 60)

    all_problems: list[str] = []
    for label, path, expected, required in [
        ("来源登记模板", source_path, SOURCE_EXPECTED, SOURCE_REQUIRED),
        ("端点标准模板", endpoint_path, ENDPOINT_EXPECTED, ENDPOINT_REQUIRED),
    ]:
        problems = check_template(label, path, expected, required)
        if problems:
            for p in problems:
                print(f"FAIL  {p}")
            all_problems.extend(problems)
        else:
            print(f"PASS  {label}: {path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path}（{len(expected)} 列）")

    print("=" * 60)
    if all_problems:
        print(f"FAIL  共 {len(all_problems)} 个问题，请修正后重试。")
        return 1
    print("PASS  两个模板全部检查通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
