#!/usr/bin/env python3
"""构建 Fuchs 2021 (C. difficile) 端点表。

数据来源:
- Dataset S4: new/PMID 34131082/pnas.2103579118.sd04.xlsx (sheet TTSs)
- 链方向推断: draft/fuchs_strand_inference_result.tsv

规则:
- confidence 为 高/低 的 1967 条 → 主端点表
  draft/endpoints_output/BTED_EXT_2026_001_fuchs2021_endpoints.tsv
- confidence 为 无法确定 的 75 条 → 单独文件
  draft/endpoints_output/fuchs_2021_unresolved_strand_75rows.tsv
- 主表 + unresolved = 2042
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent.parent  # D:\SEU\实习\BATTER数据整理
OUTDIR = ROOT / "draft" / "endpoints_output"
S4_XLSX = ROOT / "new" / "PMID 34131082" / "pnas.2103579118.sd04.xlsx"
STRAND_TSV = ROOT / "draft" / "fuchs_strand_inference_result.tsv"

SOURCE_ID = "BTED_EXT_2026_001"
SAMPLE_ID = "GSM4696498;GSM4696499;GSM4696500"  # RNAtag-seq LE-TY 1/2/3 (TTS 数据来源)
ASSAY = "RNAtag-seq (TTS)"
EVIDENCE_CLASS = "author_called_endpoint"
REF_ACC = "CP010905.2"
REF_ASSEMBLY = "GCF_000932055.2"
REF_NAME = "CP010905.2"
REPLICON = "chromosome"
PMID = "34131082"
DOI = "10.1073/pnas.2103579118"
SOURCE_TABLE = "pnas.2103579118.sd04.xlsx (Dataset S4, TTSs sheet)"

SCHEMA = [
    "end_id", "source_id", "sample_id", "assay", "evidence_class",
    "author_endpoint_id", "published_reference_accession", "reference_assembly",
    "reference_name", "replicon_label", "biological_coordinate_1based",
    "bed_start_0based", "bed_end_0based", "strand", "signal_or_score",
    "author_category", "associated_gene_or_locus", "pmid", "doi",
    "source_table_or_file", "coordinate_interpretation", "original_row_reference",
    "qc_status", "note",
]


def load_s4_tts() -> list[dict]:
    wb = openpyxl.load_workbook(S4_XLSX, read_only=True, data_only=True)
    ws = wb["TTSs"]
    rows = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        if row[0] is None:
            continue
        rows.append({
            "row": i,
            "locus_tag": str(row[0]),
            "old_locus": str(row[1]) if row[1] is not None else "",
            "name": str(row[2]) if row[2] is not None else "",
            "type": str(row[3]) if row[3] is not None else "",
            "start": row[4],
            "end": row[5],
            "tts": row[6],
            "location": str(row[7]) if row[7] is not None else "",
        })
    return rows


def load_strand() -> list[dict]:
    with STRAND_TSV.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        return [row for row in r]


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    s4 = load_s4_tts()
    strand = load_strand()
    print(f"Dataset S4 TTSs 数据行数: {len(s4)}")
    print(f"strand 推断行数: {len(strand)}")
    assert len(s4) == 2042 and len(strand) == 2042, "行数应均为 2042"

    # 关联校验: locus_tag + tts_position 必须与 S4 一致
    s4_by_tag: dict[str, list[dict]] = {}
    for x in s4:
        s4_by_tag.setdefault(x["locus_tag"], []).append(x)
    mismatch = []
    for row in strand:
        tag = row["locus_tag"]
        pos = row["tts_position"]
        cands = s4_by_tag.get(tag, [])
        if not any(str(c["tts"]) == str(pos) for c in cands):
            mismatch.append((tag, pos))
    if mismatch:
        print(f"FATAL: {len(mismatch)} 行 tts_position 与 S4 不一致: {mismatch[:5]}")
        return 1

    def coord(row: dict) -> int:
        return int(row["tts_position"])

    def make_row(s4row: dict, srow: dict, seq: int) -> dict:
        pos = coord(srow)
        strand_val = srow["inferred_strand"]
        strand_code = "F" if strand_val == "+" else "R"
        end_id = f"{SOURCE_ID}_{SAMPLE_ID.replace(';', ';')}_{REF_NAME}_{strand_code}_{seq:06d}"
        note_parts = []
        note_parts.append(f"链向: confidence={srow['confidence']}, gff_matched={srow['gff_matched']}")
        if srow["note"]:
            note_parts.append(srow["note"])
        note_parts.append("signal_or_score 填 NA: Dataset S4 folding sheet 提供的是折叠能量(kcal/mol)而非峰信号值, 且仅覆盖 2011/2042 个 TTS")
        return {
            "end_id": end_id,
            "source_id": SOURCE_ID,
            "sample_id": SAMPLE_ID,
            "assay": ASSAY,
            "evidence_class": EVIDENCE_CLASS,
            "author_endpoint_id": "NA",
            "published_reference_accession": REF_ACC,
            "reference_assembly": REF_ASSEMBLY,
            "reference_name": REF_NAME,
            "replicon_label": REPLICON,
            "biological_coordinate_1based": pos,
            "bed_start_0based": pos - 1,
            "bed_end_0based": pos,
            "strand": strand_val,
            "signal_or_score": "NA",
            "author_category": s4row["location"] if s4row["location"] else "NA",
            "associated_gene_or_locus": s4row["locus_tag"],
            "pmid": PMID,
            "doi": DOI,
            "source_table_or_file": SOURCE_TABLE,
            "coordinate_interpretation": "作者 TTS 坐标为 1-based (dnaA Start=1); biological_coordinate_1based=TTS; bed_start_0based=TTS-1; bed_end_0based=TTS (单碱基 BED)",
            "original_row_reference": f"pnas.2103579118.sd04.xlsx (Dataset S4, TTSs sheet row {s4row['row']})",
            "qc_status": "pass",
            "note": "; ".join(note_parts),
        }

    main_rows = []
    unresolved_rows = []
    seq = 0
    for srow in strand:
        tag = srow["locus_tag"]
        s4row = s4_by_tag[tag][0]  # 已确认 tts 一致
        if srow["confidence"] in ("高", "低"):
            seq += 1
            main_rows.append(make_row(s4row, srow, seq))
        elif srow["confidence"] == "无法确定":
            unresolved_rows.append(srow)
        else:
            print(f"FATAL: 未知 confidence 取值: {srow['confidence']!r} @ {tag}")
            return 1

    # 校验坐标与链向分布
    strand_cnt = Counter(r["strand"] for r in main_rows)
    print(f"主表行数: {len(main_rows)} (高+低)")
    print(f"主表链向分布: {dict(strand_cnt)}")
    print(f"unresolved 行数: {len(unresolved_rows)}")
    print(f"总和: {len(main_rows) + len(unresolved_rows)} (应为 2042)")

    # 输出主表
    main_path = OUTDIR / "BTED_EXT_2026_001_fuchs2021_endpoints.tsv"
    with main_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SCHEMA, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(main_rows)
    print(f"已写出: {main_path} ({len(main_rows)} 行)")

    # 输出 unresolved
    unres_path = OUTDIR / "fuchs_2021_unresolved_strand_75rows.tsv"
    unres_cols = ["locus_tag", "tts_position", "gff_matched", "confidence", "note"]
    with unres_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=unres_cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows([{k: r[k] for k in unres_cols} for r in unresolved_rows])
    print(f"已写出: {unres_path} ({len(unresolved_rows)} 行)")

    # 最终校验
    total = len(main_rows) + len(unresolved_rows)
    if total != 2042:
        print(f"FATAL: 主表({len(main_rows)}) + unresolved({len(unresolved_rows)}) = {total} != 2042")
        return 1
    print("校验通过: 主表 + unresolved = 2042")
    return 0


if __name__ == "__main__":
    sys.exit(main())
