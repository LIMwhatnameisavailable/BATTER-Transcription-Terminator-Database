#!/usr/bin/env python3
"""
Phase A: TERMITe Supplementary Table 2 — 数据标准化流水线
===========================================================
功能:
  1. 解析 Supplementary Table 2 (xlsx)
  2. 清洗列名、处理缺失值、坐标验证
  3. 按 (Species, chromosome, POT, strand) 去重
  4. 按 dataset 拆分输出 BED6+4、GFF3
  5. 输出去重日志 dedup_log.csv

输出目录结构:
  TERMITe/
    data/
      termite_parsed.csv          # 去重后完整数据
      dedup_log.csv               # 去重详情日志
      dedup_summary.txt           # 去重统计摘要
    tracks/
      {dataset_id}/
        {dataset_id}_terminators.bed
        {dataset_id}_terminators.gff3

坐标系说明:
  - 原始 Table S2 中 start/end/POT 均为 1-based
  - BED: chromStart = raw_start - 1 (0-based), chromEnd = raw_end (1-based)
  - GFF3: 直接使用 1-based start/end
"""

import pandas as pd
import numpy as np
import os
import re
from pathlib import Path

# =========================================================
# 0. 路径配置
# =========================================================
INPUT_FILE = Path(
    r"D:\SEU\实习\BATTER数据整理\TERMITe\gkaf553_supplemental_files"
    r"\Supplementary Table 2.xlsx"
)
OUTPUT_DIR = Path(r"D:\SEU\实习\BATTER数据整理\TERMITe")
DATA_DIR = OUTPUT_DIR / "data"
TRACKS_DIR = OUTPUT_DIR / "tracks"

# 染色体名称映射: "Chromosome" -> 实际 RefSeq accession
# (来自 TERMITe Supplementary Table 1 的菌株/Assembly 信息)
CHROMOSOME_MAP = {
    "Bacillus_subtilis_a": "NC_000964.3",
    "Bacillus_subtilis_b": "NC_000964.3",
    "Bacillus_subtilis_c": "NC_000964.3",
    "Bacillus_subtilis_d": "NC_000964.3",
    "Escherichia_coli_a": "NC_000913.3",
    "Escherichia_coli_b": "NC_000913.3",
    "Listeria_monocytogenes": "NC_003210.1",
}

# =========================================================
# 1. 读取原始数据
# =========================================================
print("=" * 60)
print("Phase A: TERMITe 数据标准化")
print("=" * 60)

print("\n[1/7] 读取 Supplementary Table 2...")
raw = pd.read_excel(
    INPUT_FILE,
    sheet_name="Atlas of intrinsic terminators",
    skiprows=1,  # 跳过标题行
    header=0,     # 第2行为列名
)
print(f"  → 读取 {len(raw)} 行, {len(raw.columns)} 列")

# =========================================================
# 2. 清洗列名
# =========================================================
print("\n[2/7] 清洗列名 & 处理缺失值...")

# 列名标准化: 去空格/特殊字符, 下划线命名
col_rename = {
    "Species": "Species",
    "chromosome": "chromosome",
    "start": "start",
    "end": "end",
    "POT": "POT",
    "strand": "strand",
    "termite id": "termite_id",
    "termite score": "termite_score",
    "average peak height": "avg_peak_height",
    "termination efficiency": "termination_efficiency",
    "IDR": "IDR",
    "summit coordinate": "summit_coordinate",
    "overlapping gene": "overlapping_gene",
    "upstream gene": "upstream_gene",
    "downstream gene": "downstream_gene",
    "overlapping feature types": "overlapping_feature_types",
    "transtermhp closest hairpin start": "transtermhp_hairpin_start",
    "transtermhp closest hairpin end": "transtermhp_hairpin_end",
    "transtermhp id": "transtermhp_id",
    "transtermhp confidence": "transtermhp_confidence",
    "transtermhp hairpin score": "transtermhp_hairpin_score",
    "transtermhp tail score": "transtermhp_tail_score",
    "transtermhp a tract": "transtermhp_a_tract",
    "transtermhp hairpin": "transtermhp_hairpin",
    "transtermhp u tract": "transtermhp_u_tract",
    "transtermhp POT distance to hairpin": "transtermhp_pot_dist",
    "rnafold a tract": "rnafold_a_tract",
    "rnafold hairpin": "rnafold_hairpin",
    "rnafold u tract": "rnafold_u_tract",
    "rnafold hairpin structure": "rnafold_hairpin_struct",
    "rnafold POT distance to hairpin": "rnafold_pot_dist",
    "rnafold energy": "rnafold_energy",
    "rnafold": "rnafold",
    "transtermhp": "transtermhp",
}
# 保留原始列名中未映射的列
used_cols = list(col_rename.keys())
df = raw[used_cols].rename(columns=col_rename).copy()

# 生成 dataset_id (物种名 snake_case + 后缀)
def make_dataset_id(species):
    species = species.strip()
    # 替换括号和空格
    species = species.replace("(", "_").replace(")", "").replace(" ", "_")
    # 特殊字符替换
    species = re.sub(r"[^a-zA-Z0-9_]", "_", species)
    # 合并连续下划线
    species = re.sub(r"_+", "_", species)
    species = species.strip("_")
    return species

df["dataset_id"] = df["Species"].map(make_dataset_id)
print(f"  → 共 {df['dataset_id'].nunique()} 个独特 dataset")

# 打印 dataset 分布
print("\n  Dataset 分布:")
for ds_id, cnt in df["dataset_id"].value_counts().sort_index().items():
    print(f"    {ds_id:40s}  {cnt:5d} 条")

# 缺失值处理: "." -> NaN
df.replace(r"^\.$", np.nan, regex=True, inplace=True)
df.replace(".", np.nan, inplace=True)

# 坐标字段类型转换
for col in ["start", "end", "POT"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

# 数值字段类型转换
for col in ["termite_score", "transtermhp_confidence", "IDR", "rnafold_energy"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# 验证坐标一致性
invalid = df[df["start"] > df["end"]]
if len(invalid) > 0:
    print(f"  ⚠ 发现 {len(invalid)} 条 start > end 的记录，已标记")
    df.loc[invalid.index, "coord_valid"] = False
else:
    df["coord_valid"] = True

# =========================================================
# 3. 染色体名称映射
# =========================================================
print("\n[3/7] 染色体名称映射...")

# 对 "Chromosome" 条目按 dataset_id 映射到 RefSeq accession
chrom_mapped = df["chromosome"].copy()
for ds_id, refseq in CHROMOSOME_MAP.items():
    mask = (df["dataset_id"] == ds_id) & (df["chromosome"] == "Chromosome")
    if mask.any():
        chrom_mapped.loc[mask] = refseq
        print(f"  {ds_id:40s}  Chromosome → {refseq}  ({mask.sum()} 条)")

df["chrom"] = chrom_mapped
print(f"  → 染色体名称映射完成")

# 检查是否有未映射的 "Chromosome"
unmapped = df[df["chrom"] == "Chromosome"]
if len(unmapped) > 0:
    print(f"  ⚠ 仍有 {len(unmapped)} 条 'Chromosome' 未映射:")
    for ds in unmapped["dataset_id"].unique():
        print(f"      {ds}")

# =========================================================
# 4. 去重
# =========================================================
print("\n[4/7] 按 (Species, chromosome, POT, strand) 去重...")

dedup_cols = ["Species", "chromosome", "POT", "strand"]
dup_mask = df.duplicated(subset=dedup_cols, keep=False)
n_dup_groups = df[dup_mask].groupby(dedup_cols).ngroups
print(f"  → 找到 {n_dup_groups} 个重复组, 涉及 {dup_mask.sum()} 条记录")

# 构建去重日志
dedup_log_entries = []

# 去重排序优先级: termite_score 高 → rnafold 确认(+) → 原顺序
# 先评分数值(越高越好)，再评 rnafold 确认
def priority_sort_key(group):
    """返回排序后的 DataFrame，第一行为保留记录"""
    g = group.copy()
    # 排序: termite_score 降序
    g = g.sort_values("termite_score", ascending=False, na_position="last")
    # 在 termite_score 相同时，rnafold="+" 优先
    # 使用 stable sort 保持 termite_score 排序
    rnafold_order = g["rnafold"].map({"+": 0, np.nan: 1, "-": 2}).fillna(2)
    g = g.assign(_rnafold_order=rnafold_order).sort_values(
        ["termite_score", "_rnafold_order"],
        ascending=[False, True],
        na_position="last",
    )
    return g.drop(columns="_rnafold_order")

# 收集被丢弃的记录
discarded_records = []

for (species, chrom, pot, strand), group in df[dup_mask].groupby(
    dedup_cols, sort=False
):
    group_sorted = priority_sort_key(group)
    keep_idx = group_sorted.index[0]
    discard_idxs = group_sorted.index[1:]

    # 记录去重日志
    log_entry = {
        "Species": species,
        "chromosome": chrom,
        "POT": pot,
        "strand": strand,
        "n_candidates": len(group),
        "kept_row_index": keep_idx,
        "kept_termite_id": df.loc[keep_idx, "termite_id"],
        "kept_termite_score": df.loc[keep_idx, "termite_score"],
        "kept_transtermhp_conf": df.loc[keep_idx, "transtermhp_confidence"],
        "kept_rnafold": df.loc[keep_idx, "rnafold"],
        "kept_rnafold_energy": df.loc[keep_idx, "rnafold_energy"],
    }
    dedup_log_entries.append(log_entry)

    # 记录被丢弃的候选
    for discard_idx in discard_idxs:
        discarded_records.append(
            {
                "Species": species,
                "chromosome": chrom,
                "POT": pot,
                "strand": strand,
                "discarded_termite_id": df.loc[discard_idx, "termite_id"],
                "discarded_termite_score": df.loc[discard_idx, "termite_score"],
                "discarded_transtermhp_conf": df.loc[
                    discard_idx, "transtermhp_confidence"
                ],
                "discarded_rnafold": df.loc[discard_idx, "rnafold"],
                "discarded_rnafold_energy": df.loc[discard_idx, "rnafold_energy"],
            }
        )

# 去重: 保留每组的第一条
keep_indices = (
    df[~dup_mask].index.tolist()
    + [entry["kept_row_index"] for entry in dedup_log_entries]
)
df_deduped = df.loc[keep_indices].sort_index().reset_index(drop=True)
n_discarded = len(discarded_records)

print(f"  → 去重完成: 丢弃 {n_discarded} 条, 保留 {len(df_deduped)} 条")

# 输出去重日志
dedup_log_df = pd.DataFrame(dedup_log_entries)
discarded_log_df = pd.DataFrame(discarded_records)

# 合并完整去重日志
dedup_log_full = dedup_log_df.merge(
    discarded_log_df,
    on=["Species", "chromosome", "POT", "strand"],
    how="left",
)

# =========================================================
# 5. 写入清洗后数据
# =========================================================
print("\n[5/7] 写入清洗后数据...")

DATA_DIR.mkdir(parents=True, exist_ok=True)

# 去重后完整数据
df_deduped.to_csv(DATA_DIR / "termite_parsed.csv", index=False)
print(f"  → termite_parsed.csv ({len(df_deduped)} 行)")

# 去重日志
dedup_log_full.to_csv(DATA_DIR / "dedup_log.csv", index=False)
print(f"  → dedup_log.csv ({len(dedup_log_full)} 行)")

# 去重统计摘要
with open(DATA_DIR / "dedup_summary.txt", "w", encoding="utf-8") as f:
    f.write("TERMITe 数据去重统计摘要\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"去重前总记录数: {len(df)}\n")
    f.write(f"去重后总记录数: {len(df_deduped)}\n")
    f.write(f"丢弃记录数: {n_discarded}\n")
    f.write(f"重复组数: {n_dup_groups}\n\n")
    f.write("按 dataset 去重统计:\n")
    f.write("-" * 60 + "\n")
    for ds_id in sorted(df_deduped["dataset_id"].unique()):
        before = len(df[df["dataset_id"] == ds_id])
        after = len(df_deduped[df_deduped["dataset_id"] == ds_id])
        discarded = before - after
        f.write(f"  {ds_id:40s}  {before:5d} → {after:5d}  (丢弃 {discarded})\n")

print(f"  → dedup_summary.txt")

# =========================================================
# 6. 按 dataset 拆分输出 BED6+4 + GFF3
# =========================================================
print("\n[6/7] 按 dataset 拆分输出 BED + GFF3...")

TRACKS_DIR.mkdir(parents=True, exist_ok=True)

for ds_id, grp in df_deduped.groupby("dataset_id"):
    grp = grp.sort_values(["chrom", "start", "POT"])

    ds_dir = TRACKS_DIR / ds_id
    ds_dir.mkdir(parents=True, exist_ok=True)

    chroms = grp["chrom"].unique()
    n_records = len(grp)
    n_plus = (grp["strand"] == "+").sum()
    n_minus = (grp["strand"] == "-").sum()

    # ---------- BED6+4 ----------
    # 1.chrom  2.chromStart(0-based)  3.chromEnd(1-based)
    # 4.name="POT:{POT}_{strand}"  5.score=termite_score  6.strand
    # 7.termite_score  8.IDR  9.rnafold_energy  10.transtermhp_confidence
    bed_rows = []
    for _, row in grp.iterrows():
        bed_start = row["start"] - 1  # 0-based
        bed_end = row["end"]
        name = f"POT:{row['POT']}_{row['strand']}"
        score = int(row["termite_score"]) if pd.notna(row["termite_score"]) else 0
        score = max(0, min(1000, score))  # BED score 0-1000

        strand = row["strand"]
        ts = row["termite_score"] if pd.notna(row["termite_score"]) else "."
        idr = row["IDR"] if pd.notna(row["IDR"]) else "."
        re = row["rnafold_energy"] if pd.notna(row["rnafold_energy"]) else "."
        tc = (
            row["transtermhp_confidence"]
            if pd.notna(row["transtermhp_confidence"])
            else "."
        )

        bed_rows.append(
            f"{row['chrom']}\t{bed_start}\t{bed_end}\t{name}\t{score}\t{strand}\t"
            f"{ts}\t{idr}\t{re}\t{tc}"
        )

    bed_path = ds_dir / f"{ds_id}_terminators.bed"
    with open(bed_path, "w", encoding="utf-8") as f:
        f.write("\n".join(bed_rows) + "\n")

    # ---------- GFF3 ----------
    # 1.seqid  2.source  3.type  4.start(1-based)  5.end(1-based)
    # 6.score  7.strand  8.phase  9.attributes
    gff_lines = [
        "##gff-version 3",
        f"# source: TERMITe (Kosiński et al. 2025, NAR)",
        f"# dataset: {ds_id}",
        f"# records: {n_records}",
        "# sequence-region information is per-assembly, not listed here",
    ]

    for _, row in grp.iterrows():
        score = int(row["termite_score"]) if pd.notna(row["termite_score"]) else "."
        strand = row["strand"]

        # Filter out empty URLs for the OnTerminatorLink attribute
        # Build attributes
        attrs = [
            f"ID={row['termite_id']}",
            f"POT={row['POT']}",
            f"termite_score={row['termite_score']}" if pd.notna(row["termite_score"]) else "",
            f"IDR={row['IDR']}" if pd.notna(row["IDR"]) else "",
            f"rnafold_energy={row['rnafold_energy']}" if pd.notna(row["rnafold_energy"]) else "",
            f"transtermhp_confidence={row['transtermhp_confidence']}" if pd.notna(row["transtermhp_confidence"]) else "",
            f"transtermhp={row['transtermhp']}" if pd.notna(row["transtermhp"]) else "",
            f"rnafold={row['rnafold']}" if pd.notna(row["rnafold"]) else "",
            f"overlapping_gene={row['overlapping_gene']}" if pd.notna(row["overlapping_gene"]) and row["overlapping_gene"] != "." else "",
            f"upstream_gene={row['upstream_gene']}" if pd.notna(row["upstream_gene"]) and row["upstream_gene"] != "." else "",
            f"downstream_gene={row['downstream_gene']}" if pd.notna(row["downstream_gene"]) and row["downstream_gene"] != "." else "",
            f"avg_peak_height={row['avg_peak_height']}" if pd.notna(row["avg_peak_height"]) else "",
            f"termination_efficiency={row['termination_efficiency']}" if pd.notna(row["termination_efficiency"]) else "",
            f"dataset={ds_id}",
        ]
        # Filter empty strings
        attrs = [a for a in attrs if a]

        gff_line = (
            f"{row['chrom']}\tTERMITe\tintrinsic_terminator\t"
            f"{row['start']}\t{row['end']}\t{score}\t{strand}\t.\t{';'.join(attrs)}"
        )
        gff_lines.append(gff_line)

    gff_path = ds_dir / f"{ds_id}_terminators.gff3"
    with open(gff_path, "w", encoding="utf-8") as f:
        f.write("\n".join(gff_lines) + "\n")

    print(f"  {ds_id:40s}  BED {n_records:5d} 条  GFF {n_records:5d} 条  "
          f"chroms={len(chroms)}  [+:{n_plus}  -:{n_minus}]")

# =========================================================
# 7. 汇总报告
# =========================================================
print("\n[7/7] 生成汇总报告...")

summary_lines = [
    "=" * 60,
    "TERMITe 数据标准化 Phase A 完成报告",
    "=" * 60,
    "",
    f"输入文件: {INPUT_FILE}",
    f"清洗后数据: {DATA_DIR / 'termite_parsed.csv'}",
    f"去重日志: {DATA_DIR / 'dedup_log.csv'}",
    f"去重统计: {DATA_DIR / 'dedup_summary.txt'}",
    "",
    f"原始记录数: {len(raw)}",
    f"去重后记录数: {len(df_deduped)}",
    f"丢弃记录数: {n_discarded}",
    f"重复组数: {n_dup_groups}",
    "",
    "数据集输出:",
]

for ds_id in sorted(df_deduped["dataset_id"].unique()):
    n = len(df_deduped[df_deduped["dataset_id"] == ds_id])
    summary_lines.append(f"  {ds_id:40s}  {n:5d} 条终止子")

summary_lines.extend([
    "",
    f"输出目录: {TRACKS_DIR}",
    "=" * 60,
])

summary_text = "\n".join(summary_lines)
print(summary_text)

# 保存报告到 data 目录
with open(DATA_DIR / "phaseA_report.txt", "w", encoding="utf-8") as f:
    f.write(summary_text)

print("\n*** Phase A 完成! ***")