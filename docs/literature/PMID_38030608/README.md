# PMID 38030608 — TRS: a method for determining transcript termini from RNAtag-seq sequencing data

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | TRS: a method for determining transcript termini from RNAtag-seq sequencing data |
| 作者/期刊 | Bar et al. (2023), *Nat Commun*, 14(1):7843 |
| PMID | [38030608](https://pubmed.ncbi.nlm.nih.gov/38030608/) |
| DOI | [10.1038/s41467-023-43534-2](https://doi.org/10.1038/s41467-023-43534-2) |
| PMC | [PMC10687069](https://pmc.ncbi.nlm.nih.gov/articles/PMC10687069/) |

**注意**：旧调研笔记中 PMID 曾误写为 `38030638`，此处已按正式 PubMed 记录修正为 `38030608`。

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_002 | *Escherichia coli* str. K-12 substr. MG1655 | curated |

## 实验方法

RNAtag-seq / TRS（Transcriptome-wide RNA termini by sequencing）。

## 公开数据

- ArrayExpress: [E-MTAB-12429](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-12429) — RNAtag-seq + term-seq（*E. coli* K-12 MG1655，LB/EG 各三个重复）。
- GitHub: [amirbarHUJI/TRS](https://github.com/amirbarHUJI/TRS) — TRS 算法 Python 包。

## 补充表与坐标数据

- Supplementary Data 2：LB 指数期 RNAtag-seq 鉴定的 1,486 个 3′ termini。
- Supplementary Data 3：LB/EG 条件下 RNAtag-seq 与 term-seq 四组数据集鉴定的 3′ termini。
- Supplementary Data 1：登录号索引表（含 EPEC、ETEC、*Salmonella*、*Klebsiella*、*Shigella*、*Listeria* 等外部数据）。
- Supplementary Data 4 / 5：衍生分析结果，非完整坐标表。

## 证据类别

- Supplementary Data 2 / Data 3（*E. coli* K-12 MG1655）属于 `author_called_endpoint`；
- 其他菌种（EPEC、ETEC 等）的 TRS 坐标是否已作为补充表公开**待核查**；若未公开，需按 Data 1 登录号重新分析。

## 参考序列与坐标

- 参考组装：GCF_000005845.2 / NC_000913.3（正文提及用于 *E. coli* K-12 MG1655）。
- 坐标体系：Data 2 / Data 3 的列名、1-based/0-based 约定、dominant coordinate 处理方式**待下载原表核查**。注册表备注称 dominant coordinate 已按 1-based 处理。

## 入库决定

本地工作树已将 S1_002 标记为 `curated`；坐标数据尚未迁移到本仓库。

## 问题与待核查

- 注册表 `published_year` 为 2018，而 PMID 记录年份为 2023，已记录为 schema 改进问题（见 `data/registry/batter_s1_source_registry_dictionary.md`）；
- Data 2 / Data 3 的列结构、坐标约定、链方向需下载原表确认；
- 其他细菌菌种的 TRS 坐标表是否存在于 Supplementary Data 1 或正文中**待核查**。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/38030608/
- DOI: https://doi.org/10.1038/s41467-023-43534-2
- ArrayExpress: https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-12429
- 历史初评笔记（含旧笔误）：[docs/legacy/literature-initial-review/文献13-PMID38030608-README.md](../../legacy/literature-initial-review/文献13-PMID38030608-README.md)
