# PMID 37402717 — Extensive diversity in RNA termination and regulation in Borrelia burgdorferi

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | Extensive diversity in RNA termination and regulation revealed by transcriptome mapping for the Lyme pathogen Borrelia burgdorferi |
| 作者/期刊 | Petroni et al. (2023), *Nat Commun*, 14(1):3931 |
| PMID | [37402717](https://pubmed.ncbi.nlm.nih.gov/37402717/) |
| DOI | [10.1038/s41467-023-39576-1](https://doi.org/10.1038/s41467-023-39576-1) |
| PMC | [PMC10339582](https://pmc.ncbi.nlm.nih.gov/articles/PMC10339582/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_021 | *Borreliella burgdorferi* B31 | curated |

## 实验方法

RNAtag-seq / Term-seq / bulk RNA-seq / BCM RNA-seq / SPD RNA-seq / 3′RNA-seq。

## 公开数据

- GEO SuperSeries: [GSE222088](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE222088)
  - GSE222084: bulk RNA-seq
  - GSE222085: BCM RNA-seq（Rho 终止分析）
  - GSE222086: SPD RNA-seq
  - GSE222087: 3′RNA-seq / Term-seq
- GitHub:
  - [NICHD-BSPC/termseq-peaks](https://github.com/NICHD-BSPC/termseq-peaks)
  - [lcdb/lcdb-wf](https://github.com/lcdb/lcdb-wf)

## 补充表与坐标数据

- Supplementary Data 1：3′ end 坐标 + intrinsic termination score（log 期 1,333 个 / TS-stationary 期 944 个）。
- Supplementary Data 4：Rho termination regions 坐标。
- Supplementary Data 5：上游/ORF 内 3′ end 坐标 + spermidine-dependent score。

## 证据类别

Supplementary Data 1 与 Data 4 属于 `author_called_endpoint`。GitHub 仓库为分析代码；UCSC track hub 为可视化轨道，均不作为坐标数据本体。

## 参考序列与坐标

- 参考组装：GCF_000008685.2
- 覆盖范围：B31 菌株，log 与 TS-stationary 两种条件，22 个参考 replicon 中的 20 个。
- 坐标体系：Data 1/4/5 的列名、1-based/0-based 约定**待下载原表核查**。

## 入库决定

v0.1 local snapshot 已将 S1_021 的 1,905 条唯一 3′ RNA-seq site 标准化发布为 TSV 与 BED；条件级观察保留在本地审计流程中，不重复进主端点表。

## 问题与待核查

- log 期与 TS-stationary 期数据是否在同一文件的不同 sheet 中区分**待核查**；
- 论文中提及的跨物种比较（E. coli、P. aeruginosa、B. subtilis）坐标是否在该文献补充数据中提供**待核查**；若未提供，需按相应 SRA/BioProject 登录号重新分析。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/37402717/
- DOI: https://doi.org/10.1038/s41467-023-39576-1
- GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE222088
- 历史初评笔记：[docs/legacy/literature-initial-review/文献11-PMID37402717-README.md](../../legacy/literature-initial-review/文献11-PMID37402717-README.md)
