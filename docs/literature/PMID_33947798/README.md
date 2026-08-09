# PMID 33947798 — Elucidating the Regulatory Elements for Transcription Termination in Streptomyces clavuligerus

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | Elucidating the Regulatory Elements for Transcription Termination and Posttranscriptional Processing in the Streptomyces clavuligerus Genome |
| 作者/期刊 | Hwang et al. (2021), *mSystems*, 6(3):e01013-20 |
| PMID | [33947798](https://pubmed.ncbi.nlm.nih.gov/33947798/) |
| DOI | [10.1128/mSystems.01013-20](https://doi.org/10.1128/mSystems.01013-20) |
| PMC | [PMC8171581](https://pmc.ncbi.nlm.nih.gov/articles/PMC8171581/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_017 | *Streptomyces clavuligerus* ATCC 27064 | curated |

## 实验方法

RNA-seq / dRNA-seq / ribo-seq / Term-seq。

## 公开数据

- GenBank: [CP027858](https://www.ncbi.nlm.nih.gov/nuccore/CP027858) / [CP027859](https://www.ncbi.nlm.nih.gov/nuccore/CP027859) — 染色体与质粒参考序列。
- GEO: [GSE128216](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE128216) — RNA-seq / dRNA-seq / ribosome profiling。
- GEO: [GSE138325](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE138325) — Term-seq。

## 补充表与坐标数据

- Supplemental Material Data Set S1（`msystems.01013-20-sd001.xlsx`），Sheet 1：
  - 1,427 个 transcript 3′ end sites（TEPs）
  - 1,648 个 transcription units（TU）
  - 610 个 transcription unit clusters（TUC）
  - 字段包括 TEP 分类（P/S/Pre/A/N）、folding free energy、avg. readthrough fraction、TU 类别等。

## 证据类别

Data Set S1 Sheet 1 属于 `author_called_endpoint`。机器学习脚本与 KNN 分类器托管于 [cholab.or.kr](http://cholab.or.kr)，属于代码，不作为坐标数据。

## 参考序列与坐标

- 参考组装：GCF_005519465.1（CP027858 + CP027859）
- 坐标体系：Data Set S1 中 TEP 是单点坐标还是 Start-End、1-based/0-based 约定**待下载原表核查**。

## 入库决定

v0.1 local snapshot 已将 S1_017 的 1,427 条作者发表 Term-seq TEP 标准化发布为 TSV 与 BED，并保持与 S1_015 独立的来源身份。

## 问题与待核查

- Sheet 1 是否包含显式 Chromosome/Strand/Position 列**待核查**；
- Sheet 2 的 Bi-TEP 信息是否需作为补充注释**待核查**。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/33947798/
- DOI: https://doi.org/10.1128/mSystems.01013-20
- 历史初评笔记：[docs/legacy/literature-initial-review/文献7-PMID33947798-README.md](../../legacy/literature-initial-review/文献7-PMID33947798-README.md)
