# PMID 31594819 — A rhlI 5′ UTR-Derived sRNA Regulates RhlR-Dependent Quorum Sensing

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | A rhlI 5′ UTR-Derived sRNA Regulates RhlR-Dependent Quorum Sensing in Pseudomonas aeruginosa |
| 作者/期刊 | Thomason et al. (2019), *mBio*, 10(5):e02253-19 |
| PMID | [31594819](https://pubmed.ncbi.nlm.nih.gov/31594819/) |
| DOI | [10.1128/mBio.02253-19](https://doi.org/10.1128/mBio.02253-19) |
| PMC | [PMC6750155](https://pmc.ncbi.nlm.nih.gov/articles/PMC6750155/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_008 | *Pseudomonas aeruginosa* PAO1 | curated |

## 实验方法

RNA-seq + term-seq。

## 公开数据

- ENA: [PRJEB31965](https://www.ebi.ac.uk/ena/browser/view/PRJEB31965) — 原始测序数据。

## 补充表与坐标数据

- Supplementary Table S1（`mbio.02253-19-st001.xlsx`）：
  - Tab A: 804 个与已注释基因/操纵子关联的 TTS（核心坐标数据）；
  - Tab B: 21 个 AHL 差异调控位点的 DESeq2 统计结果；
  - Tab C: TargetRNA2 预测靶点（与终止子坐标无关）；
  - Tab D: 菌株/质粒/引物信息。

## 证据类别

Tab A 属于 `author_called_endpoint`。Tab B 为差异表达统计，Tab C 为预测结果，均不作为端点数据发布。

## 参考序列与坐标

- 参考组装：GCF_000006765.1
- 坐标体系：Tab A 具体列名、坐标约定及 1-based/0-based 需下载原表核查。

## 入库决定

v0.1 local snapshot 已将 S1_008 的 1,965 条作者发表可重复 Term-seq 3′ site 标准化发布为 TSV 与 BED；基因关联表的计数差异仍保留在来源处理记录中。

## 问题与待核查

- 804 个 TTS 是否合并了 +AHL/-AHL 两种条件，或为代表性位点**待核查**；
- Tab A 列结构需下载原表确认。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/31594819/
- DOI: https://doi.org/10.1128/mBio.02253-19
- ENA: https://www.ebi.ac.uk/ena/browser/view/PRJEB31965
- 历史初评笔记：[docs/legacy/literature-initial-review/文献4-PMID31594819-README.md](../../legacy/literature-initial-review/文献4-PMID31594819-README.md)
