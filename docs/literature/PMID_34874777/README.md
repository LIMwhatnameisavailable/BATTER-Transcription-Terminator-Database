# PMID 34874777 — Different Regulatory Modes of Synechocystis sp. PCC 6803

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | Different Regulatory Modes of Synechocystis sp. PCC 6803 in Response to Photosynthesis Inhibitory Conditions |
| 作者/期刊 | Cho et al. (2021), *mSystems*, 6(6):e00943-21 |
| PMID | [34874777](https://pubmed.ncbi.nlm.nih.gov/34874777/) |
| DOI | [10.1128/mSystems.00943-21](https://doi.org/10.1128/mSystems.00943-21) |
| PMC | [PMC8616245](https://pmc.ncbi.nlm.nih.gov/articles/PMC8616245/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_019 | *Synechocystis* sp. PCC 6803 | curated |

## 实验方法

RNA-seq / Ribo-seq / Term-seq。

## 公开数据

- BioProject: [PRJNA666973](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA666973) — 原始测序 reads。
- RefSeq: GCF_000009725.1 / NC_000911.1 — 参考基因组。

## 补充表与坐标数据

- Table S5（`msystems.00943-21-st005.xlsx`）：784 个 transcript 3′-end positions（TEPs），按 P/S/I/A/U 五类分类。
- Table S6（`msystems.00943-21-st006.xlsx`）：315 个 transcription units（TUs），作为 TEP 上下文补充。

## 证据类别

Table S5 属于 `author_called_endpoint`。

## 参考序列与坐标

- 参考组装：GCF_000009725.1 / NC_000911.1
- 坐标体系：Table S5 实际列名、单碱基坐标或相对坐标、1-based/0-based 约定**待下载原表核查**。

## 入库决定

v0.1 local snapshot 已将 S1_019 的 784 条作者发表、人工整理的 Term-seq TEP 标准化发布为 TSV 与 BED。

## 问题与待核查

- 注册表 `published_year` 为 2022，而 PMID 记录年份为 2021，已记录为 schema 改进问题（见 `data/registry/batter_s1_source_registry_dictionary.md`）；
- Table S5 列结构需下载原表确认。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/34874777/
- DOI: https://doi.org/10.1128/mSystems.00943-21
- 历史初评笔记：[docs/legacy/literature-initial-review/文献9-PMID34874777-README.md](../../legacy/literature-initial-review/文献9-PMID34874777-README.md)
