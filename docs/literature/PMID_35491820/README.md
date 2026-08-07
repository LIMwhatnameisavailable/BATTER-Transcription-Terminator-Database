# PMID 35491820 — Mapping the Complex Transcriptional Landscape of Dickeya dadantii

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | Mapping the Complex Transcriptional Landscape of the Phytopathogenic Bacterium Dickeya dadantii |
| 作者/期刊 | Forquet et al. (2022), *mBio*, 13(3):e00524-22 |
| PMID | [35491820](https://pubmed.ncbi.nlm.nih.gov/35491820/) |
| DOI | [10.1128/mbio.00524-22](https://doi.org/10.1128/mbio.00524-22) |
| PMC | [PMC9147293](https://pmc.ncbi.nlm.nih.gov/articles/PMC9147293/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_020 | *Dickeya dadantii* 3937 | curated |

## 实验方法

RNA-seq / dRNA-seq / Nanopore native RNA-seq。

## 公开数据

- ArrayExpress: [E-MTAB-7650](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-7650) — RNA-seq。
- ArrayExpress: [E-MTAB-541](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-541) — DNA microarray。
- ArrayExpress: [E-MTAB-10482](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-10482) — Nanopore native RNA-seq。
- ArrayExpress: [E-MTAB-9075](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-9075) — dRNA-seq。
- GEO: [GSE94713](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE94713) — in planta DNA microarray。
- RefSeq: NC_014500.1 — 参考基因组。

## 补充表与坐标数据

- Supplementary Table S2（`mbio.00524-22-st002.xlsx`）：
  - S2B: 3,564 个 putative rho-independent TTS（ARNold 预测）；
  - S2C: 5,851 个 putative rho-dependent TTS（RhoTermPredict 预测）；
  - S2D: 1,165 个 Nanopore native RNA-seq 实验 TTS。

## 证据类别

- S2D Nanopore 实验 TTS：`author_called_endpoint`（公开实验层）；
- S2B ARNold 预测与 S2C RhoTermPredict 预测：`prediction_only`（内部审计，不发布为实验端点）；
- S2A 为 dRNA-seq TSS，与终止子坐标无关。

## 参考序列与坐标

- 参考组装：GCF_000147055.1 / NC_014500.1
- 坐标体系：各 sheet 列名与坐标约定**待下载原表核查**。

## 入库决定

本地工作树已将 S1_020 标记为 `curated`，仅将 S2D 作为公开实验层；S2B/S2C 预测保留为内部审计。坐标数据尚未迁移到本仓库。

## 问题与待核查

- S2D 与 S2B/S2C 的列结构是否一致**待核查**；
- Nanopore TTS 是否经过独立功能验证**待核查**。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/35491820/
- DOI: https://doi.org/10.1128/mbio.00524-22
- 历史初评笔记：[docs/legacy/literature-initial-review/文献10-PMID35491820-README.md](../../legacy/literature-initial-review/文献10-PMID35491820-README.md)
