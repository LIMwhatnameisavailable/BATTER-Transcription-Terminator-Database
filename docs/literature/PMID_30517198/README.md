# PMID 30517198 — The Transcriptional landscape of Streptococcus pneumoniae TIGR4

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | The Transcriptional landscape of Streptococcus pneumoniae TIGR4 reveals a complex operon architecture and abundant riboregulation critical for growth and virulence |
| 作者/期刊 | Warrier et al. (2018), *PLoS Pathog*, 14(12):e1007461 |
| PMID | [30517198](https://pubmed.ncbi.nlm.nih.gov/30517198/) |
| DOI | [10.1371/journal.ppat.1007461](https://doi.org/10.1371/journal.ppat.1007461) |
| PMC | — |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_006 | *Streptococcus pneumoniae* TIGR4 | curated |

## 实验方法

Term-seq / 3′ end mapping。正文 Supporting Information 描述 S2 Table 为转录终止位点（TTS）坐标表。

## 公开数据

- SRA: [SRP136114](https://www.ncbi.nlm.nih.gov/sra?term=SRP136114) — 原始测序 reads（RNA-Seq、term-seq、5′ end-Seq）。
- GenBank: [NC_003028.3](https://www.ncbi.nlm.nih.gov/nuccore/NC_003028.3) — 参考基因组（TIGR4）。

## 补充表与坐标数据

- Supplementary S2 Table：List of all the transcription termination sites (TTSs) identified from term-seq，共 1,864 个 TTS。
- 数据字段包括 position、coverage、3′-UTR length、predicted stem-loop structure、upstream uridines 等（字段名需下载原表核实）。

## 证据类别

S2 Table 属于 `author_called_endpoint`。GitHub 仓库 [nikhilram/T4pipeline](https://github.com/nikhilram/T4pipeline) 中的 track 文件仅作可视化/交叉验证参考，其坐标是否完全等同于 S2 Table **待核查**。

## 参考序列与坐标

- 参考组装：GCF_000006885.1 / NC_003028.3
- 坐标体系：S2 Table 中 position 的具体 1-based / 0-based 约定及是否存在单独 Strand 列**待下载原表核查**。

## 入库决定

本地工作树已将 S1_006 标记为 `curated`；坐标数据尚未迁移到本仓库。

## 问题与待核查

- S2 Table 实际列名、坐标体系、链方向编码需下载原表核实；
- S1_006 注册表备注称“called at coverage ≥10 and ≥2-fold enrichment over background”，该筛选规则是否完全复现作者方法**待核查**。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/30517198/
- DOI: https://doi.org/10.1371/journal.ppat.1007461
- SRA: https://www.ncbi.nlm.nih.gov/sra?term=SRP136114
- 历史初评笔记：[docs/legacy/literature-initial-review/文献2-PMID30517198-README.md](../../legacy/literature-initial-review/文献2-PMID30517198-README.md)
