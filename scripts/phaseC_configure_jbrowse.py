#!/usr/bin/env python3
"""
Phase C: JBrowse2 配置脚本 — 添加 assemblies 和 tracks
=======================================================
功能:
  1. 读取 assembly_map.csv 获取物种/assembly 映射
  2. 为每个物种添加 assembly（FASTA + .fai + 别名映射）
  3. 为每个物种添加 NCBI 基因注释轨道
  4. 为每个 dataset 添加 TERMITe 终止子轨道

输出: 修改 jbrowse/config.json
"""

import json
import os
import shutil
from pathlib import Path
from urllib.parse import quote

# =========================================================
# 0. 路径配置
# =========================================================
TERMITE_DIR = Path(r"D:\SEU\实习\BATTER数据整理\TERMITe")
GENOMES_DIR = TERMITE_DIR / "genomes"
TRACKS_DIR = TERMITE_DIR / "tracks"
JBROWSE_DIR = TERMITE_DIR / "jbrowse"
ALIASES_DIR = JBROWSE_DIR / "aliases"

# Assembly 信息（同 assembly_map.csv）
ASSEMBLIES = [
    # (dataset_id, display_name, assembly, chroms, has_aliases, track_datasets)
    ("Bacillus_subtilis", "Bacillus subtilis 168", "GCA_000009045",
     "NC_000964.3", True, ["Bacillus_subtilis_a", "Bacillus_subtilis_b",
                            "Bacillus_subtilis_c", "Bacillus_subtilis_d"]),
    ("Escherichia_coli", "Escherichia coli K-12 MG1655", "GCA_000005845",
     "NC_000913.3", True, ["Escherichia_coli_a", "Escherichia_coli_b"]),
    ("Listeria_monocytogenes", "Listeria monocytogenes EGD-e", "GCA_000196035",
     "NC_003210.1", True, ["Listeria_monocytogenes"]),
    ("Enterococcus_faecalis", "Enterococcus faecalis ATCC 29212", "GCF_000742975.1",
     "NZ_CP008814.1,NZ_CP008815.1,NZ_CP008816.1", False, ["Enterococcus_faecalis"]),
    ("Streptomyces_avermitilis", "Streptomyces avermitilis MA-4680", "GCF_000009765.2",
     "NC_003155.5,NC_004719.1", False, ["Streptomyces_avermitilis"]),
    ("Streptomyces_clavuligerus", "Streptomyces clavuligerus", "GCF_005519465.1",
     "NZ_CP027858.1,NZ_CP027859.1", False, ["Streptomyces_clavuligerus"]),
    ("Streptomyces_coelicolor", "Streptomyces coelicolor A3(2)", "GCA_000203835.1",
     "AL645882.2,AL589148.1,AL645771.1", False, ["Streptomyces_coelicolor"]),
    ("Streptomyces_griseus", "Streptomyces griseus NBRC 13350", "GCF_000010605.1",
     "NC_010572.1", False, ["Streptomyces_griseus"]),
    ("Streptomyces_lividans", "Streptomyces lividans TK24", "GCF_000739105.1",
     "NZ_CP009124.1", False, ["Streptomyces_lividans"]),
    ("Streptomyces_tsukubensis", "Streptomyces tsukubensis NBRC 108819", "GCF_003932715.1",
     "NZ_CP020700.1,NZ_CP020701.1,NZ_CP020702.1", False, ["Streptomyces_tsukubensis"]),
    ("Streptomyces_venezuelae", "Streptomyces venezuelae ATCC 15439", "GCF_015710995.1",
     "NZ_CP059991.1", False, ["Streptomyces_venezuelae"]),
    ("Synechocystis_sp", "Synechocystis sp. PCC 6803", "GCF_000009725.1",
     "NC_000911.1", False, ["Synechocystis_sp"]),
    ("Zymomonas_mobilis", "Zymomonas mobilis ZM4", "GCF_003054575.1",
     "NZ_CP023715.1", False, ["Zymomonas_mobilis"]),
]

# 别名映射文件（3 个物种需要）
ALIASES_MAP = {
    "GCA_000009045": "GCA_000009045.aliases.tsv",
    "GCA_000005845": "GCA_000005845.aliases.tsv",
    "GCA_000196035": "GCA_000196035.aliases.tsv",
}


def get_relative_url(path: Path, jbrowse_dir: Path) -> str:
    """获取文件相对于 jbrowse 目录的 URL 路径（使用正斜杠）"""
    rel = path.relative_to(jbrowse_dir)
    return str(rel).replace("\\", "/")


def copy_to_jbrowse(src: Path, jbrowse_dir: Path, subdir: str) -> Path:
    """复制文件到 jbrowse 的子目录，保留目录结构避免冲突"""
    target_dir = jbrowse_dir / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / src.name
    shutil.copy2(src, target)
    return target


def main():
    print("=" * 60)
    print("Phase C: JBrowse2 配置")
    print("=" * 60)

    # 读取现有 config.json
    config_path = JBROWSE_DIR / "config.json"
    if not config_path.exists():
        # 创建最小配置
        config = {
            "configuration": {
                "theme": {"palette": {"primary": {"main": "#311b92"}}}
            },
            "assemblies": [],
            "tracks": [],
            "defaultSession": {
                "name": "TERMITe Browser",
                "view": {
                    "id": "linearGenomeView",
                    "type": "LinearGenomeView"
                }
            },
            "plugins": [],
            "internetAccount": {
                "type": "InternetAccount"
            }
        }
        print("\n[1] 创建新的 config.json")
    else:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print(f"\n[1] 读取现有 config.json（{len(config.get('assemblies', []))} 个 assemblies）")

    # 清空现有 assemblies 和 tracks（重新生成）
    config["assemblies"] = []
    config["tracks"] = []

    # 为每个 assembly 创建数据目录
    jbrowse_data = JBROWSE_DIR / "data"
    jbrowse_data.mkdir(parents=True, exist_ok=True)

    # 跟踪已处理的 assembly
    processed_assemblies = set()

    for ds_id, display_name, assembly, chroms_str, has_aliases, track_datasets in ASSEMBLIES:
        assembly_dir = GENOMES_DIR / assembly

        # ---- 检查基因组文件 ----
        fna_path = assembly_dir / f"{assembly}.fna"
        fai_path = assembly_dir / f"{assembly}.fna.fai"
        gff_path = assembly_dir / "genomic.gff"

        if not fna_path.exists():
            print(f"\n  [跳过] {assembly} FASTA 文件不存在: {fna_path}")
            continue

        print(f"\n  [{assembly}] {display_name}")

        # ---- 复制文件到 jbrowse/data ----
        data_dir = JBROWSE_DIR / "data" / assembly
        data_dir.mkdir(parents=True, exist_ok=True)

        # 复制 FASTA 和索引
        target_fna = data_dir / f"{assembly}.fna"
        if not target_fna.exists():
            shutil.copy2(fna_path, target_fna)
            print(f"    → data/{assembly}/{assembly}.fna")

        # 复制 FAI
        if fai_path.exists():
            target_fai = data_dir / f"{assembly}.fna.fai"
            if not target_fai.exists():
                shutil.copy2(fai_path, target_fai)
            fai_url = f"data/{assembly}/{assembly}.fna.fai"
        else:
            print(f"    ⚠ FAI 索引不存在: {fai_path}")
            fai_url = None

        # 复制 GFF3（基因注释轨道）
        target_gff = data_dir / "genomic.gff"
        if gff_path.exists() and not target_gff.exists():
            shutil.copy2(gff_path, target_gff)
            print(f"    → data/{assembly}/genomic.gff")

        # 复制 TERMITe 轨道文件
        track_files = []
        for td in track_datasets:
            track_dir = TRACKS_DIR / td
            bed_path = track_dir / f"{td}_terminators.bed"
            gff_track_path = track_dir / f"{td}_terminators.gff3"
            if bed_path.exists():
                target_bed = data_dir / f"{td}_terminators.bed"
                if not target_bed.exists():
                    shutil.copy2(bed_path, target_bed)
                track_files.append((td, target_bed))
            if gff_track_path.exists():
                target_gff_track = data_dir / f"{td}_terminators.gff3"
                if not target_gff_track.exists():
                    shutil.copy2(gff_track_path, target_gff_track)

        # ---- 构建 assembly 配置 ----
        fasta_url = f"data/{assembly}/{assembly}.fna"

        assembly_config = {
            "name": assembly,
            "displayName": display_name,
            "aliases": chroms_str.split(",") if chroms_str else [],
            "sequence": {
                "type": "ReferenceSequenceTrack",
                "trackId": f"{assembly}-refseq",
                "adapter": {
                    "type": "IndexedFastaAdapter",
                    "fastaLocation": {"uri": fasta_url},
                    "faiLocation": {"uri": fai_url},
                },
            },
        }

        # 添加别名映射
        if has_aliases and assembly in ALIASES_MAP:
            alias_file = ALIASES_DIR / ALIASES_MAP[assembly]
            if alias_file.exists():
                # 复制别名字到 data 目录
                target_alias = data_dir / ALIASES_MAP[assembly]
                if not target_alias.exists():
                    shutil.copy2(alias_file, target_alias)
                alias_url = f"data/{assembly}/{ALIASES_MAP[assembly]}"
                assembly_config["refNameAliases"] = {
                    "adapter": {
                        "type": "RefNameAliasAdapter",
                        "location": {"uri": alias_url},
                    }
                }
                print(f"    → data/{assembly}/{ALIASES_MAP[assembly]}")

        config["assemblies"].append(assembly_config)

        # ---- 添加基因注释轨道 ----
        if gff_path.exists():
            gene_track = {
                "type": "FeatureTrack",
                "trackId": f"{assembly}-ncbi-genes",
                "name": f"{ds_id} NCBI genes",
                "assemblyNames": [assembly],
                "category": ["NCBI Genes"],
                "adapter": {
                    "type": "Gff3Adapter",
                    "gffLocation": {"uri": f"data/{assembly}/genomic.gff"},
                },
            }
            config["tracks"].append(gene_track)
            print(f"    + 轨道: {ds_id} NCBI genes")

        # ---- 添加 TERMITe 终止子轨道 ----
        for td, track_bed_path in track_files:
            # 统计轨道信息
            with open(track_bed_path, "r") as f:
                n_records = sum(1 for _ in f)

            terminator_track = {
                "type": "FeatureTrack",
                "trackId": f"{td}-terminators",
                "name": f"{td} terminators",
                "assemblyNames": [assembly],
                "category": ["TERMITe Terminators"],
                "description": f"TERMITe intrinsic terminators - {td} ({n_records} records)",
                "adapter": {
                    "type": "BedAdapter",
                    "bedLocation": {"uri": f"data/{assembly}/{td}_terminators.bed"},
                    # JBrowse2 的 columnNames 是"完整表头行"语义（names[i] 逐列对应 splitLine[i]），
                    # 必须列出全部 10 列的名称，不能只列附加列。
                    # 前 6 列为 BED 标准字段，后 4 列对应原始 Supplementary Table 2 的列名：
                    #   col7=termite score(col9), col8=IDR(col12),
                    #   col9=rnafold energy(col33), col10=transtermhp confidence(col21)
                    "columnNames": [
                        "chrom", "chromStart", "chromEnd", "name", "score", "strand",
                        "termite_score", "IDR", "rnafold_energy", "transtermhp_confidence",
                    ],
                },
                # 渲染配置：按链方向着色
                "renderers": {
                    "FeatureRenderer": {
                        "type": "SvgFeatureRenderer",
                        "color1": "#1f77b4",
                        "color2": "#d62728",
                    }
                },
            }
            config["tracks"].append(terminator_track)
            print(f"    + 轨道: {td} terminators ({n_records} 条)")

        processed_assemblies.add(assembly)

    # ---- 保存 config.json ----
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"配置完成！")
    print(f"  Assemblies: {len(config['assemblies'])}")
    print(f"  Tracks: {len(config['tracks'])}")
    print(f"  配置文件: {config_path}")

    # ---- 输出汇总 ----
    print(f"\n  Assembly 列表:")
    for a in config["assemblies"]:
        n_tracks = sum(1 for t in config["tracks"] if a["name"] in t["assemblyNames"])
        print(f"    {a['name']:30s}  {a['displayName']:35s}  {n_tracks} 轨道")

    print(f"\n  轨道列表:")
    for t in config["tracks"]:
        print(f"    {t['trackId']:45s}  [{t['type']}]  {t['name']}")


if __name__ == "__main__":
    main()