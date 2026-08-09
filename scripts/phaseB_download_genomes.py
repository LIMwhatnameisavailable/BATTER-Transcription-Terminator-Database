#!/usr/bin/env python3
"""
Phase B: TERMITe 参考基因组下载 + 索引
========================================
功能:
  1. 根据 assembly_map 下载每个物种的基因组 FASTA + GFF3 注释
  2. 用 pyfaidx 生成 FASTA 索引 (.fai)
  3. 整理文件到 genomes/ 目录

依赖:
  - datasets (NCBI Datasets CLI) — 在 bgi conda 环境中
  - pyfaidx — Python 包 (pip install pyfaidx)

使用方式:
  conda activate bgi
  python phaseB_download_genomes.py

输出目录结构:
  TERMITe/
    genomes/
      assembly_map.csv          # 物种 ↔ assembly 映射表
      {assembly_accession}/
        {assembly_accession}.fna   # 基因组 FASTA
        {assembly_accession}.fna.fai  # FASTA 索引
        genomic.gff                # 基因注释 GFF3
"""

import subprocess
import csv
import os
import sys
import shutil
from pathlib import Path
from zipfile import ZipFile

# =========================================================
# 0. 路径配置
# =========================================================
OUTPUT_DIR = Path(r"D:\SEU\实习\BATTER数据整理\TERMITe")
GENOMES_DIR = OUTPUT_DIR / "genomes"
TRACKS_DIR = OUTPUT_DIR / "tracks"

# =========================================================
# 1. Assembly 映射表
# =========================================================
# 来源: TERMITe Supplementary Table 1
# 列: dataset_id, species_name, strain, assembly_accession, chromosome_accessions, notes
ASSEMBLY_MAP = [
    # (dataset_id, species_display, strain, assembly, chrom_accessions, notes)
    # B. subtilis (a/b/c/d) 共用同一基因组
    ("Bacillus_subtilis", "Bacillus subtilis", "subsp. subtilis str. 168",
     "GCA_000009045", "NC_000964.3", "ASM904v1; 共用 (a)(b)(c)(d)"),
    # E. coli (a/b) 共用同一基因组
    ("Escherichia_coli", "Escherichia coli", "K-12 substr. MG1655",
     "GCA_000005845", "NC_000913.3", "ASM584v2; 共用 (a)(b)"),
    # 各物种单独
    ("Listeria_monocytogenes", "Listeria monocytogenes", "EGD-e",
     "GCA_000196035", "NC_003210.1", "ASM19603v1"),
    ("Enterococcus_faecalis", "Enterococcus faecalis", "ATCC 29212",
     "GCF_000742975.1", "NZ_CP008814.1,NZ_CP008815.1,NZ_CP008816.1", "ASM74297v1"),
    ("Streptomyces_avermitilis", "Streptomyces avermitilis", "MA-4680 = NBRC 14893",
     "GCF_000009765.2", "NC_003155.5,NC_004719.1", "ASM976v2"),
    ("Streptomyces_clavuligerus", "Streptomyces clavuligerus", "",
     "GCF_005519465.1", "NZ_CP027858.1,NZ_CP027859.1", "ASM551946v1"),
    ("Streptomyces_coelicolor", "Streptomyces coelicolor", "A3(2)",
     "GCA_000203835.1", "AL645882.2", "ASM20383v1"),
    ("Streptomyces_griseus", "Streptomyces griseus", "subsp. griseus NBRC 13350",
     "GCF_000010605.1", "NC_010572.1", "ASM1060v1"),
    ("Streptomyces_lividans", "Streptomyces lividans", "TK24",
     "GCF_000739105.1", "NZ_CP009124.1", "ASM73910v1"),
    ("Streptomyces_tsukubensis", "Streptomyces tsukubensis", "NBRC 108819",
     "GCF_003932715.1", "NZ_CP020700.1,NZ_CP020701.1,NZ_CP020702.1", "ASM393271v1"),
    ("Streptomyces_venezuelae", "Streptomyces venezuelae", "ATCC 15439",
     "GCF_015710995.1", "NZ_CP059991.1", "ASM1571099v1"),
    ("Synechocystis_sp", "Synechocystis sp.", "PCC 6803",
     "GCF_000009725.1", "NC_000911.1", "ASM972v1"),
    ("Zymomonas_mobilis", "Zymomonas mobilis", "subsp. mobilis ZM4 = ATCC 31821",
     "GCF_003054575.1", "NZ_CP023715.1", "ASM305457v1"),
]

# =========================================================
# 2. 写入 assembly_map.csv
# =========================================================
print("=" * 60)
print("Phase B: 参考基因组下载与索引")
print("=" * 60)

GENOMES_DIR.mkdir(parents=True, exist_ok=True)

map_path = GENOMES_DIR / "assembly_map.csv"
with open(map_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "dataset_id", "species", "strain", "assembly_accession",
        "chromosome_accessions", "notes"
    ])
    for row in ASSEMBLY_MAP:
        writer.writerow(row)
print(f"\n[1] 写入 assembly_map.csv → {len(ASSEMBLY_MAP)} 个条目")

# =========================================================
# 3. 下载基因组
# =========================================================
def download_genome(assembly, species_name, out_dir):
    """使用 NCBI Datasets CLI 下载基因组 FASTA + GFF3"""
    print(f"\n  [{assembly}] 正在下载 {species_name}...")

    zip_path = out_dir / f"{assembly}.zip"

    # 检查是否已下载
    if (out_dir / f"{assembly}.fna").exists():
        print(f"    [跳过] {assembly}.fna 已存在")
        return True

    # 下载命令
    cmd = [
        "datasets", "download", "genome", "accession", assembly,
        "--include", "genome,gff3",
        "--filename", str(zip_path),
    ]

    print(f"    运行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        print(f"    [错误] 下载失败: {result.stderr[:200]}")
        return False

    # 解压
    try:
        with ZipFile(zip_path, "r") as zf:
            # 列出文件
            fna_files = [f for f in zf.namelist() if f.endswith(".fna")]
            gff_files = [f for f in zf.namelist() if f.endswith(".gff")]

            # 提取 FASTA
            for fna in fna_files:
                target = out_dir / f"{assembly}.fna"
                with zf.open(fna) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                print(f"    → {target.name} ({os.path.getsize(target) / 1e6:.1f} MB)")

            # 提取 GFF3
            for gff in gff_files:
                target = out_dir / "genomic.gff"
                with zf.open(gff) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                print(f"    → {target.name} ({os.path.getsize(target) / 1e6:.1f} MB)")

        # 删除 zip
        zip_path.unlink()
        print(f"    → 已删除临时文件 {zip_path.name}")

    except Exception as e:
        print(f"    [错误] 解压失败: {e}")
        return False

    return True


def index_fasta(fasta_path):
    """用 pyfaidx 创建 FASTA 索引 (.fai)"""
    print(f"    索引 {fasta_path.name}...")
    try:
        from pyfaidx import Fasta
        fasta = Fasta(str(fasta_path))
        # pyfaidx 在读取时自动创建 .fai
        fai_path = fasta_path.with_suffix(f"{fasta_path.suffix}.fai")
        if fai_path.exists():
            print(f"    → {fai_path.name} ({os.path.getsize(fai_path) / 1e3:.1f} KB)")
        # 显示染色体统计
        n_seqs = len(fasta.keys())
        total_len = sum(len(fasta[k]) for k in fasta.keys())
        print(f"    → {n_seqs} 条序列, 总长 {total_len / 1e6:.2f} Mb")
        return True
    except Exception as e:
        print(f"    [错误] 索引失败: {e}")
        return False


# =========================================================
# 4. 执行下载
# =========================================================
print("\n[2] 下载基因组文件...")

# 去重: 按 assembly 去重
seen_assemblies = set()
for entry in ASSEMBLY_MAP:
    ds_id, species_name, strain, assembly, chroms, notes = entry

    if assembly in seen_assemblies:
        continue
    seen_assemblies.add(assembly)

    out_dir = GENOMES_DIR / assembly
    out_dir.mkdir(parents=True, exist_ok=True)

    display_name = f"{species_name} {strain}".strip()
    ok = download_genome(assembly, display_name, out_dir)

    if ok:
        # 索引 FASTA
        fna_path = out_dir / f"{assembly}.fna"
        if fna_path.exists():
            index_fasta(fna_path)
    else:
        print(f"  [跳过索引] {assembly} 下载失败")

print("\n[3] 基因组下载完成！")
print(f"\n  输出目录: {GENOMES_DIR}")
print(f"  映射表: {map_path}")

# =========================================================
# 5. 输出汇总
# =========================================================
print("\n" + "=" * 60)
print("Phase B 汇总")
print("=" * 60)
print(f"\nAssembly 总数: {len(seen_assemblies)}")
print(f"下载目标: {GENOMES_DIR}")
print()
for entry in ASSEMBLY_MAP:
    ds_id, species_name, strain, assembly, chroms, notes = entry
    status = "✅" if (GENOMES_DIR / assembly / f"{assembly}.fna").exists() else "❌"
    print(f"  {status} {assembly:20s}  {species_name:30s}  {ds_id}")

# 检查是否有 B. subtilis 和 E. coli 的引用
print("\n  注意:")
print("  - B. subtilis (a)(b)(c)(d) 共用 GCA_000009045")
print("  - E. coli (a)(b) 共用 GCA_000005845")
print("  - 后续 Phase C 配置 JBrowse2 时，"
      "同一 assembly 下的多个 dataset 会作为同一条轨道添加")