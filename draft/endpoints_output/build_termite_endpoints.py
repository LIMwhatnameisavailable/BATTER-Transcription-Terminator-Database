#!/usr/bin/env python3
"""构建 TERMITe 8 来源端点表 (BTED_EXT_2026_006~013)。

数据来源:
- TERMITe/data/termite_parsed.csv (37 列, 已含 summit_coordinate/termite_score 等)
- TERMITe/tracks/<dataset>/<dataset>_terminators.bed (chrom 标签 = 实际参考 accession)

规则:
- 仅 coord_valid=True 的行入端点表 (全库均 True)
- dataset_id→source_id 映射 (与 termite_new_sources.tsv 一致):
  Bacillus_subtilis_a→006, b→007, c→008, Enterococcus_faecalis→009,
  Listeria_monocytogenes→010, Bacillus_subtilis_d→011, Escherichia_coli_b→012,
  Escherichia_coli_a→013
- 坐标 = summit_coordinate (1-based, ==POT 经验证); bed_start=summit-1, bed_end=summit
- strand 取行内 strand 列
- signal_or_score = termite_score; author_category = "TERMITe intrinsic terminator"
- evidence_class = algorithm_called_endpoint (draft/dictionary_patch_proposal.md 提案二
  建议端点表新增, 2026-08-10 使用, 待维护者确认)
- note 列验证状态措辞分两组:
  Group 1 (四项独立验证): Enterococcus_faecalis(009), Escherichia_coli_a(013)
  Group 2 (流水线推定): Bacillus_subtilis_a/b/c/d(006/007/008/011),
    Escherichia_coli_b(012), Listeria_monocytogenes(010)

输出:
- BTED_EXT_2026_0XX_termite_<dataset_id小写>_endpoints.tsv (8 个)
- termite_endpoints_summary.txt
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent.parent  # D:\SEU\实习\BATTER数据整理
OUTDIR = ROOT / "draft" / "endpoints_output"
PARSED = ROOT / "TERMITe" / "data" / "termite_parsed.csv"
TRACKS = ROOT / "TERMITe" / "tracks"
INTAKE = ROOT / "draft" / "termite_new_sources.tsv"

# dataset_id → source_id (与任务及 termite_new_sources.tsv 一致)
DS_TO_SOURCE = {
    "Bacillus_subtilis_a": "BTED_EXT_2026_006",
    "Bacillus_subtilis_b": "BTED_EXT_2026_007",
    "Bacillus_subtilis_c": "BTED_EXT_2026_008",
    "Enterococcus_faecalis": "BTED_EXT_2026_009",
    "Listeria_monocytogenes": "BTED_EXT_2026_010",
    "Bacillus_subtilis_d": "BTED_EXT_2026_011",
    "Escherichia_coli_b": "BTED_EXT_2026_012",
    "Escherichia_coli_a": "BTED_EXT_2026_013",
}

# Group 1: 四项独立验证数据集 (note 措辞一)
GROUP1 = {"Enterococcus_faecalis", "Escherichia_coli_a"}
NOTE_GROUP1 = ("端点坐标验证状态: 已通过summit==POT一致性、BED偏移换算、U-tract序列比对、"
               "T-run富集统计四项独立验证 (详见 draft/termite_coord_validation.md)")
NOTE_GROUP2 = ("端点坐标验证状态: 坐标体系依据同一TERMITe流水线代码推定成立，"
               "未对本数据集单独做U-tract序列比对或T-run富集验证")

SCHEMA = [
    "end_id", "source_id", "sample_id", "assay", "evidence_class",
    "author_endpoint_id", "published_reference_accession", "reference_assembly",
    "reference_name", "replicon_label", "biological_coordinate_1based",
    "bed_start_0based", "bed_end_0based", "strand", "signal_or_score",
    "author_category", "associated_gene_or_locus", "pmid", "doi",
    "source_table_or_file", "coordinate_interpretation", "original_row_reference",
    "qc_status", "note",
]


def load_intake() -> dict[str, dict]:
    """读取 termite_new_sources.tsv, 返回 {dataset_id: row}。"""
    with INTAKE.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        out = {}
        for row in r:
            # endpoint_source_file 里提取 dataset_id
            m = re.search(r"dataset_id=([A-Za-z_]+)", row["endpoint_source_file"])
            if m:
                out[m.group(1)] = row
        return out


def bed_chrom_labels(dataset_id: str) -> dict[str, str]:
    """读取 BED tracks 第一列 (chrom) 的唯一值集合。"""
    bed = TRACKS / dataset_id / f"{dataset_id}_terminators.bed"
    labels = set()
    with bed.open(encoding="utf-8") as f:
        for line in f:
            labels.add(line.split("\t")[0])
    return labels


def extract_gene_id(s: str) -> str:
    """从 upstream_gene 形如 'gene-CAC98217 - 45bp' / 'gene:DR75_RS00125 - 61bp' 提取基因 ID。"""
    if not s:
        return "NA"
    s = s.strip()
    s = re.sub(r"^gene[-:]", "", s)
    s = re.sub(r"\s*-\s*\d+bp.*$", "", s)
    return s


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    intake = load_intake()
    print(f"intake 中识别到 {len(intake)} 个 dataset_id")

    with PARSED.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        all_rows = list(r)
    print(f"termite_parsed.csv 总行数: {len(all_rows)}")

    summary_lines: list[str] = []
    summary_lines.append("TERMITe 8 来源端点表构建摘要")
    summary_lines.append("生成日期: 2026-08-10")
    summary_lines.append(f"termite_parsed.csv 总行数: {len(all_rows)}")
    summary_lines.append("")

    ok = True
    for dataset_id, source_id in DS_TO_SOURCE.items():
        rows = [row for row in all_rows if row["dataset_id"] == dataset_id]
        valid = [row for row in rows if str(row["coord_valid"]).strip() == "True"]
        intake_row = intake[dataset_id]

        # reference_name: E.faecalis 按行取 chromosome 列 (已是 accession); 其他取 BED chrom 标签
        chrom_labels = bed_chrom_labels(dataset_id)
        print(f"{dataset_id} ({source_id}): 原始 {len(rows)} 行, coord_valid=True {len(valid)} 行, BED chrom={sorted(chrom_labels)}")
        if len(chrom_labels) == 1:
            default_ref = next(iter(chrom_labels))
        else:
            default_ref = None  # 多染色体, 逐行用 chromosome 列

        endpoints = []
        seq = 0
        pot_mismatch = 0
        for row in valid:
            summit = int(row["summit_coordinate"])
            pot = int(row["POT"])
            strand_val = row["strand"].strip()
            if strand_val not in ("+", "-"):
                print(f"FATAL: {dataset_id} 行 strand={strand_val!r}")
                return 1
            strand_code = "F" if strand_val == "+" else "R"
            # reference_name 解析
            if default_ref is not None:
                ref_name = default_ref
            else:
                ref_name = row["chromosome"].strip()
                if ref_name not in chrom_labels:
                    print(f"FATAL: {dataset_id} chromosome={ref_name!r} 不在 BED chrom {chrom_labels}")
                    return 1
            seq += 1
            sample_id = intake_row["sample_id_or_condition"].split("(")[0].strip()
            end_id = f"{source_id}_{sample_id}_{ref_name}_{strand_code}_{seq:06d}"
            note_parts = []
            if dataset_id in GROUP1:
                note_parts.append(NOTE_GROUP1)
            else:
                note_parts.append(NOTE_GROUP2)
            if summit != pot:
                pot_mismatch += 1
                note_parts.append(
                    f"POT({pot}) != summit_coordinate({summit}), 差{abs(pot - summit)}bp; "
                    "按任务规则坐标取 summit_coordinate"
                )
            note_parts.append(
                f"author_category=TERMITe intrinsic terminator; transtermhp={row['transtermhp']}, "
                f"rnafold={row['rnafold']}, transtermhp_confidence={row['transtermhp_confidence'] or 'NA'}, "
                f"IDR={row['IDR'] or 'NA'}, rnafold_energy={row['rnafold_energy'] or 'NA'}"
            )
            note_parts.append(f"upstream_gene={row['upstream_gene'] or 'NA'}")
            endpoints.append({
                "end_id": end_id,
                "source_id": source_id,
                "sample_id": sample_id,
                "assay": intake_row["assay"],
                "evidence_class": "algorithm_called_endpoint",
                "author_endpoint_id": row["termite_id"],
                "published_reference_accession": intake_row["published_reference_accession"],
                "reference_assembly": intake_row["reference_assembly"],
                "reference_name": ref_name,
                "replicon_label": "chromosome",
                "biological_coordinate_1based": summit,
                "bed_start_0based": summit - 1,
                "bed_end_0based": summit,
                "strand": strand_val,
                "signal_or_score": row["termite_score"],
                "author_category": "TERMITe intrinsic terminator",
                "associated_gene_or_locus": extract_gene_id(row["upstream_gene"]),
                "pmid": intake_row["pmid"],
                "doi": intake_row["doi"],
                "source_table_or_file": f"TERMITe data/termite_parsed.csv (dataset_id={dataset_id})",
                "coordinate_interpretation": "TERMITe parsed.csv summit_coordinate 为参考基因组 1-based 单碱基坐标 "
                                             "(经验证 summit==POT, BED offset=-1); biological_coordinate_1based=summit; "
                                             "bed_start_0based=summit-1; bed_end_0based=summit (单碱基 BED)",
                "original_row_reference": f"TERMITe data/termite_parsed.csv (dataset_id={dataset_id}, termite_id={row['termite_id']})",
                "qc_status": "pass",
                "note": "; ".join(note_parts),
            })
        print(f"  端点表行数: {len(endpoints)}, POT!=summit 行数: {pot_mismatch}")
        if len(endpoints) != len(valid):
            print(f"FATAL: {dataset_id} 端点 {len(endpoints)} != valid {len(valid)}")
            ok = False

        # 写出
        fname = f"{source_id}_termite_{dataset_id.lower()}_endpoints.tsv"
        path = OUTDIR / fname
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=SCHEMA, delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(endpoints)
        print(f"  已写出: {path.name} ({len(endpoints)} 行)")

        summary_lines.append(f"== {dataset_id} ({source_id}) ==")
        summary_lines.append(f"  原始行数: {len(rows)}")
        summary_lines.append(f"  coord_valid=True: {len(valid)}")
        summary_lines.append(f"  最终端点行数: {len(endpoints)}")
        summary_lines.append(f"  POT!=summit 行数: {pot_mismatch}")
        summary_lines.append("")

    # 汇总文件
    summary_path = OUTDIR / "termite_endpoints_summary.txt"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"已写出: {summary_path}")

    if not ok:
        return 1
    print("RESULT: ALL_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
