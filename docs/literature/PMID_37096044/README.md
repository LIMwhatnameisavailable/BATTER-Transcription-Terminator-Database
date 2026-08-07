# PMID 37096044 — Premature termination of transcription in Mycobacterium tuberculosis

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | Premature termination of transcription is shaped by Rho and translated uORFS in Mycobacterium tuberculosis |
| 作者/期刊 | D'Halluin et al. (2023), *iScience*, 26(4):106465 |
| PMID | [37096044](https://pubmed.ncbi.nlm.nih.gov/37096044/) |
| DOI | [10.1016/j.isci.2023.106465](https://doi.org/10.1016/j.isci.2023.106465) |
| PMC | [PMC10099124](https://pmc.ncbi.nlm.nih.gov/articles/PMC10099124/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_022 | *Mycobacterium tuberculosis* H37Rv | curated |

## 实验方法

RNA-seq / Term-seq / tagRNA-seq。

## 公开数据

- ArrayExpress: [E-MTAB-11753](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-11753) — 原始测序数据。
- GitHub: [ppolg/Mtb_termseq](https://github.com/ppolg/Mtb_termseq) — 分析代码。

## 补充表与坐标数据

- Table S3：2,567 个 author-called Term-seq TTS（核心坐标数据）。
- Table S3 同时包含 29,096 个 RhoTermPredict 预测 RDTS（预测层，不发布为实验端点）。
- Table S1（New TSS）、Table S2（Processing Sites）、Table S4/S5 为补充上下文。

## 证据类别

- Table S3 中 2,567 个 TTS：`author_called_endpoint`；
- Table S3 中 29,096 个 RhoTermPredict RDTS：`prediction_only`（内部审计）。

## 参考序列与坐标

- 参考组装：GCF_000195955.2 / NC_000962.3
- 注册表备注：AL123456.3 与 NC_000962.3 序列相同，坐标直接映射到 GCF_000195955.2 / NC_000962.3。
- 坐标体系：Table S3 列结构与坐标约定**待下载原表核查**。

## 入库决定

本地工作树已将 S1_022 标记为 `curated`，并已将预测-only 的 RUT 位点排除在公开层之外；坐标数据尚未迁移到本仓库。

## 问题与待核查

- Table S3 中 TTS 与 RDTS 是否在同一表格内分列存放**待核查**；
- 各 TTS 是否经独立功能验证**待核查**。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/37096044/
- DOI: https://doi.org/10.1016/j.isci.2023.106465
- ArrayExpress: https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-11753
- 历史初评笔记：[docs/legacy/literature-initial-review/文献12-PMID37096044-README.md](../../legacy/literature-initial-review/文献12-PMID37096044-README.md)
