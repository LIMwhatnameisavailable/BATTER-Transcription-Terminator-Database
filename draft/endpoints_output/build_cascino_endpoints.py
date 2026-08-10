#!/usr/bin/env python3
"""构建 Cascino 2026 (S. elongatus PCC 7942, Rend-seq) 端点表 — 两级置信度版。

数据来源:
- new/PMID 42148773/msystems.01581-25-s0003.xlsx (Table S1)
  sheets: Syn_WT / Syn_∆mfd_rep1 / Syn_∆mfd_rep2
- 方法学: new/PMID 42148773/msystems.01581-25-s0002.docx (Supplementary Methods)

分类依据 (2026-08-10 依据 s0002.docx P32/P34/P77 作者原文核实, 见
cascino_reclassification_changelog.md):
- gene_term == "defined end":              最高置信度层, 坐标=gene_peak_posn,
                                           evidence_class=author_called_endpoint
- gene_term == "diffuse end (diffuse peak)": 次级置信度层, 坐标=gene_peak_posn
                                           (作者定义: 检测到候选终止峰后上游又发现
                                           额外3'峰, 存在多个候选位点, P32),
                                           evidence_class=called_endpoint
- gene_term == "unclear" 且 gene_peak_posn 有值: 次级置信度层, 坐标=gene_peak_posn
                                           (作者定义: 检测到3'峰但因下游5'峰干扰
                                           readthrough无法计算, P32 "undetermined"),
                                           evidence_class=called_endpoint
- gene_term == "unclear" 且 gene_peak_posn 为空: 完全排除 (无峰位可用, 共14行:
                                           Syn_WT 3 / rep1 6 / rep2 5)
- gene_term == "TU" / "diffuse end (no peak found)": 完全排除 (无检测到的终止信号 /
                                           无离散3'峰, 与 defined end 证据类型不同)

sheet→source_id 映射: Syn_WT→002, Syn_∆mfd_rep1→003, Syn_∆mfd_rep2→004

signal_or_score:
- = gene_peak_RT (作者给出的 peak 处 readthrough 分数)
- 空值填 NA (数据字段字典_v0.1.md 通用约定: 缺失信息一律填 NA, 不留空)

输出:
- BTED_EXT_2026_002_cascino_synwt_endpoints.tsv
- BTED_EXT_2026_003_cascino_mfdrep1_endpoints.tsv
- BTED_EXT_2026_004_cascino_mfdrep2_endpoints.tsv
- cascino_exclusion_report.txt (三档: 完全排除 / 次级置信度纳入 / 最高置信度纳入)
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
S1_XLSX = ROOT / "new" / "PMID 42148773" / "msystems.01581-25-s0003.xlsx"

PMID = "42148773"
DOI = "10.1128/msystems.01581-25"
REF_ACC = "CP000100.1"
REF_ASSEMBLY = "GCF_000012525.1"
REF_NAME = "CP000100.1"
REPLICON = "chromosome"
ASSAY = "Rend-seq"
SOURCE_FILE = "msystems.01581-25-s0003.xlsx (Table S1)"

# 两级置信度的 evidence_class (数据字段字典_v0.1.md 第54行端点表枚举:
# author_called_endpoint / called_endpoint / observed_signal / curated_record /
# author_integrated_mixed_evidence / prediction_only; 证据分层文档 六层定义)
EVIDENCE_PRIMARY = "author_called_endpoint"  # defined end: 作者发表的实验端点 (最高)
EVIDENCE_SECONDARY = "called_endpoint"       # diffuse peak / unclear(有峰): 作者表中候选端点 (次级)

# sheet → (source_id, sample_id, 条件描述)
SHEET_MAP = {
    "Syn_WT": ("BTED_EXT_2026_002", "GSM9264033;GSM9264034", "Syn, WT, rep 1+2 (技术重复)"),
    "Syn_∆mfd_rep1": ("BTED_EXT_2026_003", "GSM9264035", "Syn, Mfd_KO, rep 1 (生物学重复)"),
    "Syn_∆mfd_rep2": ("BTED_EXT_2026_004", "GSM9264036", "Syn, Mfd_KO, rep 2 (生物学重复)"),
}

NOTE_DIFFUSE_PEAK = ("作者判定为diffuse peak：检测到候选终止峰后，在上游又发现额外3'峰，"
                     "存在多个候选终止位点，本行坐标取自被重新分类前的候选defined end峰位"
                     "（gene_peak_posn），归属存在歧义")
NOTE_UNCLEAR = ("作者判定为undetermined：检测到3'峰，但因下游5'峰邻近干扰，"
                "readthrough无法计算，峰位置本身有效")

SCHEMA = [
    "end_id", "source_id", "sample_id", "assay", "evidence_class",
    "author_endpoint_id", "published_reference_accession", "reference_assembly",
    "reference_name", "replicon_label", "biological_coordinate_1based",
    "bed_start_0based", "bed_end_0based", "strand", "signal_or_score",
    "author_category", "associated_gene_or_locus", "pmid", "doi",
    "source_table_or_file", "coordinate_interpretation", "original_row_reference",
    "qc_status", "note",
]


def load_sheet(sheet: str) -> tuple[list[dict], dict[str, int]]:
    """返回 (行列表, gene_term 计数)。mfd_rep1 有尾随 None 列, 统一取前 8 列。"""
    wb = openpyxl.load_workbook(S1_XLSX, read_only=True, data_only=True)
    ws = wb[sheet]
    rows: list[dict] = []
    cnt: Counter[str] = Counter()
    for i, row in enumerate(ws.iter_rows(min_row=2, max_col=8, values_only=True)):
        # row: start, end, strand, notes, gene_term, post_stop_posn, gene_peak_posn, gene_peak_RT
        cnt[str(row[4])] += 1
        rows.append({
            "row": i + 2,
            "start": row[0],
            "end": row[1],
            "strand": str(row[2]),
            "notes": str(row[3]) if row[3] is not None else "",
            "gene_term": str(row[4]),
            "post_stop_posn": row[5],
            "gene_peak_posn": row[6],
            "gene_peak_RT": row[7],
        })
    return rows, dict(cnt)


def has_peak(r: dict) -> bool:
    v = r["gene_peak_posn"]
    return v is not None and not (isinstance(v, str) and v.strip() == "")


def parse_locus_tag(notes: str) -> str:
    m = re.search(r"locus_tag=([^;]+)", notes)
    return m.group(1) if m else "NA"


def build_sheet(sheet: str) -> tuple[list[dict], dict[str, int], dict[str, int]]:
    """返回 (端点行列表, 完全排除计数, 次级置信度入表计数)。"""
    rows, cnt = load_sheet(sheet)
    source_id, sample_id, cond = SHEET_MAP[sheet]
    out: list[dict] = []
    excluded: dict[str, int] = {}
    secondary: dict[str, int] = {}
    seq = 0
    for r in rows:
        term = r["gene_term"]
        peak = has_peak(r)
        if term == "defined end":
            if not peak:
                print(f"FATAL: {sheet} 行{r['row']} defined end 但 gene_peak_posn 为空")
                return [], cnt, secondary
            pos = int(r["gene_peak_posn"])
            evidence = EVIDENCE_PRIMARY
            author_cat = "defined end"
            note_extra = []
        elif term == "diffuse end (diffuse peak)" and peak:
            pos = int(r["gene_peak_posn"])
            evidence = EVIDENCE_SECONDARY
            author_cat = "diffuse end (diffuse peak)"
            note_extra = [NOTE_DIFFUSE_PEAK]
            secondary[term] = secondary.get(term, 0) + 1
        elif term == "unclear" and peak:
            pos = int(r["gene_peak_posn"])
            evidence = EVIDENCE_SECONDARY
            author_cat = "undetermined"
            note_extra = [NOTE_UNCLEAR]
            secondary[term] = secondary.get(term, 0) + 1
        else:
            # 完全排除: TU / diffuse end (no peak found) / unclear 无峰
            excluded[term] = excluded.get(term, 0) + 1
            continue

        strand_val = r["strand"]
        strand_code = "F" if strand_val == "+" else "R"
        seq += 1
        end_id = f"{source_id}_{sample_id}_{REF_NAME}_{strand_code}_{seq:06d}"
        note_parts = [
            f"条件: {cond}",
            f"evidence_class={evidence} (分层依据见证据分层与发布边界.md; 次级置信度层依据 "
            f"s0002.docx P32 作者定义, 详见 cascino_reclassification_changelog.md)",
            "基因名/COG 见源表 (Syn_WT 有 gene_name/COG_categories 列; mfd sheets 无此二列)",
            "signal_or_score=gene_peak_RT (作者给出的 peak 处 readthrough 分数)",
        ] + note_extra
        if source_id == "BTED_EXT_2026_002":
            note_parts.append(
                "本任务按指令用 s0003 Table S1 Syn_WT sheet 建表; "
                "登记表 endpoint_source_file 原记录为 s0004 Table S2, 二者为同一 WT 数据的不同呈现, 已按任务指定取 S1"
            )
        out.append({
            "end_id": end_id,
            "source_id": source_id,
            "sample_id": sample_id,
            "assay": ASSAY,
            "evidence_class": evidence,
            "author_endpoint_id": "NA",
            "published_reference_accession": REF_ACC,
            "reference_assembly": REF_ASSEMBLY,
            "reference_name": REF_NAME,
            "replicon_label": REPLICON,
            "biological_coordinate_1based": pos,
            "bed_start_0based": pos - 1,
            "bed_end_0based": pos,
            "strand": strand_val,
            "signal_or_score": str(r["gene_peak_RT"]) if r["gene_peak_RT"] is not None else "NA",
            "author_category": author_cat,
            "associated_gene_or_locus": parse_locus_tag(r["notes"]),
            "pmid": PMID,
            "doi": DOI,
            "source_table_or_file": f"{SOURCE_FILE}, sheet {sheet}",
            "coordinate_interpretation": "作者 gene_peak_posn 为 CP000100.1 1-based 单碱基位点 "
                                         "(defined end 的 3' 峰位; diffuse peak/unclear 行坐标同样取自该列); "
                                         "biological_coordinate_1based=gene_peak_posn; bed_start_0based=pos-1; "
                                         "bed_end_0based=pos (单碱基 BED)",
            "original_row_reference": f"msystems.01581-25-s0003.xlsx (Table S1, sheet {sheet}, row {r['row']})",
            "qc_status": "pass",
            "note": "; ".join(note_parts),
        })
    return out, excluded, secondary


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    exclusions: dict[str, dict[str, int]] = {}
    secondaries: dict[str, dict[str, int]] = {}
    summary: dict[str, dict] = {}
    ok = True

    for sheet, (source_id, _sid, _cond) in SHEET_MAP.items():
        rows_all, gt_cnt = load_sheet(sheet)
        endpoints, excluded, secondary = build_sheet(sheet)
        outfile = {
            "BTED_EXT_2026_002": "BTED_EXT_2026_002_cascino_synwt_endpoints.tsv",
            "BTED_EXT_2026_003": "BTED_EXT_2026_003_cascino_mfdrep1_endpoints.tsv",
            "BTED_EXT_2026_004": "BTED_EXT_2026_004_cascino_mfdrep2_endpoints.tsv",
        }[source_id]
        path = OUTDIR / outfile
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=SCHEMA, delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(endpoints)
        exclusions[sheet] = excluded
        secondaries[sheet] = secondary
        n_primary = gt_cnt.get("defined end", 0)
        n_secondary = sum(secondary.values())
        n_excluded = sum(excluded.values())
        total = len(rows_all)
        summary[sheet] = {
            "source_id": source_id,
            "total_rows": total,
            "n_primary": n_primary,
            "n_secondary": n_secondary,
            "n_excluded": n_excluded,
            "endpoints": len(endpoints),
            "excluded": excluded,
            "secondary": secondary,
            "gt_count": gt_cnt,
        }
        print(f"{sheet} ({source_id}): 总 {total} 行 -> 端点 {len(endpoints)} 行 "
              f"[最高 {n_primary} + 次级 {n_secondary}]")
        for term, c in sorted(excluded.items()):
            print(f"    完全排除 {term}: {c}")
        for term, c in sorted(secondary.items()):
            print(f"    次级纳入 {term}: {c}")
        # 校验: 最高 + 次级 + 完全排除 = 总行数
        if n_primary + n_secondary + n_excluded != total:
            print(f"FATAL: {sheet} 最高({n_primary}) + 次级({n_secondary}) + 排除({n_excluded}) "
                  f"= {n_primary + n_secondary + n_excluded} != 总行数 {total}")
            ok = False
        if len(endpoints) != n_primary + n_secondary:
            print(f"FATAL: {sheet} 端点行数 {len(endpoints)} != 最高+次级 {n_primary + n_secondary}")
            ok = False
        # 次级层 evidence_class 校验
        sec_classes = {r["evidence_class"] for r in endpoints if r["evidence_class"] != EVIDENCE_PRIMARY}
        if sec_classes != {EVIDENCE_SECONDARY}:
            print(f"FATAL: {sheet} 次级层 evidence_class 异常: {sec_classes}")
            ok = False

    # 排除报告 (三档)
    excl_path = OUTDIR / "cascino_exclusion_report.txt"
    lines: list[str] = []
    lines.append("Cascino 2026 (PMID 42148773) Table S1 端点表分级报告")
    lines.append("生成: 2026-08-10")
    lines.append("分级依据: s0002.docx P32/P34/P77 作者原文 (详见 cascino_reclassification_changelog.md)")
    lines.append("  - 最高置信度纳入: gene_term=='defined end' (evidence_class=author_called_endpoint)")
    lines.append("  - 次级置信度纳入: 'diffuse end (diffuse peak)' 与 'unclear'(gene_peak_posn有值)")
    lines.append("                 (evidence_class=called_endpoint; 坐标=gene_peak_posn)")
    lines.append("  - 完全排除: 'TU' / 'diffuse end (no peak found)' / 'unclear'(gene_peak_posn为空)")
    lines.append("")
    grand = {"total": 0, "primary": 0, "secondary": 0, "excluded": 0}
    for sheet in ["Syn_WT", "Syn_∆mfd_rep1", "Syn_∆mfd_rep2"]:
        s = summary[sheet]
        lines.append("=" * 66)
        lines.append(f"sheet: {sheet}  source_id: {s['source_id']}")
        lines.append(f"  总行数(不含表头): {s['total_rows']}")
        lines.append(f"  最高置信度纳入 (defined end): {s['n_primary']}")
        lines.append(f"  次级置信度纳入: {s['n_secondary']} 行")
        for term, c in sorted(s["secondary"].items()):
            lines.append(f"      {term}: {c}")
        lines.append(f"  完全排除: {s['n_excluded']} 行")
        for term, c in sorted(s["excluded"].items()):
            lines.append(f"      {term}: {c}")
        lines.append(f"  端点表行数: {s['endpoints']}")
        lines.append(f"  校验: 最高+次级+排除 = {s['n_primary'] + s['n_secondary'] + s['n_excluded']} "
                     f"(应为 {s['total_rows']})")
        grand["total"] += s["total_rows"]
        grand["primary"] += s["n_primary"]
        grand["secondary"] += s["n_secondary"]
        grand["excluded"] += s["n_excluded"]
    lines.append("")
    lines.append("=" * 66)
    lines.append("总计: 总行数 %d | 最高置信度 %d | 次级置信度 %d | 完全排除 %d"
                 % (grand["total"], grand["primary"], grand["secondary"], grand["excluded"]))
    lines.append("三档相加 = 总行数 校验: %d" % (grand["primary"] + grand["secondary"] + grand["excluded"]))
    excl_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已写出: {excl_path}")

    if not ok:
        return 1
    print("RESULT: ALL_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
