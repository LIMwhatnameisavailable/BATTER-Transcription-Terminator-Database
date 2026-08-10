# PMID 34054774 — Multi-Omic Analyses Reveal Habitat Adaptation of Synechocystis sp. PCC 7338

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | Multi-Omic Analyses Reveal Habitat Adaptation of Marine Cyanobacterium Synechocystis sp. PCC 7338 |
| 作者/期刊 | Jeong et al. (2021), *Front Microbiol*, 12:667450 |
| PMID | [34054774](https://pubmed.ncbi.nlm.nih.gov/34054774/) |
| DOI | [10.3389/fmicb.2021.667450](https://doi.org/10.3389/fmicb.2021.667450) |
| PMC | [PMC8144842](https://pmc.ncbi.nlm.nih.gov/articles/PMC8144842/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_018 | *Synechocystis* sp. PCC 7338 | curated |

## 实验方法

全基因组测序 / dRNA-seq / Term-seq / RNA-seq。

## 公开数据

- BioProject: [PRJNA629670](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA629670) — 原始测序数据。
- SRA: SRR12763770、SRR12763771 — Term-seq reads（*Synechocystis* sp. PCC 6803 对照物种，来自 Cho and Jeong 2020，非本文一手产出）。

## 补充表与坐标数据

- Supplementary Data 2：487 个 TEP（transcript 3′-end positions），对应 Figure 2H。
- Supplementary Data 1：TSS 列表（非终止子数据）。
- Supplementary Data 3：终止子区域在两物种间的保守性比较分类（下游分析结果）。
- Supplementary Data 4：差异表达基因列表（与终止子无关）。

## 证据类别

Supplementary Data 2 属于 `author_called_endpoint`。L-shaped/I-shaped 终止子形状分类是否也在 Data 2 中**待核查**。

## 参考序列与坐标

- 参考组装：GCF_018282115.1 / CP054306.1 染色体 + 三个质粒
- 坐标体系：Data 2 的具体列名与坐标约定**待下载原表核查**；文中提到 5′ 端位置经 reverse 处理，3′ 端坐标处理方向**待核查**。

## 入库决定

v0.1 local snapshot 已将 S1_018 的 487 条作者发表 Term-seq TEP 标准化发布为 TSV 与 BED；四个 replicon 均保留。

## 问题与待核查

- Frontiers 官网“Download source data”共 5 个文件，需确认哪个对应 Supplementary Data 2；
- TEP 坐标精度与链方向标注方式**待核查**。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/34054774/
- DOI: https://doi.org/10.3389/fmicb.2021.667450
- BioProject: https://www.ncbi.nlm.nih.gov/bioproject/PRJNA629670
- 历史初评笔记：[docs/legacy/literature-initial-review/文献8-PMID34054774-README.md](../../legacy/literature-initial-review/文献8-PMID34054774-README.md)
