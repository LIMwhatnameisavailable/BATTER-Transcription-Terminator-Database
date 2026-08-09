# PMID 31555254 — The Transcription Unit Architecture of Streptomyces lividans TK24

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | The Transcription Unit Architecture of Streptomyces lividans TK24 |
| 作者/期刊 | Lee et al. (2019), *Front Microbiol*, 10:2074 |
| PMID | [31555254](https://pubmed.ncbi.nlm.nih.gov/31555254/) |
| DOI | [10.3389/fmicb.2019.02074](https://doi.org/10.3389/fmicb.2019.02074) |
| PMC | [PMC6791967](https://pmc.ncbi.nlm.nih.gov/articles/PMC6791967/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_007 | *Streptomyces lividans* TK24 | curated |

## 实验方法

dRNA-seq / Term-seq / RNA-seq / Ribo-seq。

## 公开数据

- ENA: [PRJEB31507](https://www.ebi.ac.uk/ena/browser/view/PRJEB31507) — 原始测序数据。
- 参考基因组：CP009124 — *S. lividans* TK24。

## 补充表与坐标数据

- Supplementary Dataset 3：1,640 个 transcript 3′-end positions（TEPs），对应 Figure 4A。
- TEP 按与邻近基因位置关系分为 P/S/A/C/N 五类（Primary/Secondary/Antisense/Cis-regulatory/Intergenic）。

## 证据类别

Supplementary Dataset 3 属于 `author_called_endpoint`。终止与 RNA processing 是否完全区分：**待核查**（注册表已记录该问题）。

## 参考序列与坐标

- 参考组装：GCF_000739105.1 / CP009124
- 坐标体系：Dataset 3 具体列名、单点坐标或区间、1-based/0-based 约定**待下载原表核查**。

## 入库决定

v0.1 local snapshot 已将 S1_007 的 1,640 条作者发表 TEP 标准化发布为 TSV 与 BED；端点仍按 transcript 3′ end position 表述，不改称逐位点终止子。

## 问题与待核查

- Dataset 3 是否包含明确的 Chromosome/Strand/Position 列**待核查**；
- Term-seq 与 RNA processing site 的区分方式**待核查**。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/31555254/
- DOI: https://doi.org/10.3389/fmicb.2019.02074
- 历史初评笔记：[docs/legacy/literature-initial-review/文献3-PMID31555254-README.md](../../legacy/literature-initial-review/文献3-PMID31555254-README.md)
