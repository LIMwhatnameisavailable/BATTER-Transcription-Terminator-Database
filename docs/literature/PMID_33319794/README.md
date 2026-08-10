# PMID 33319794 — Genome-scale determination of 5′ and 3′ boundaries in Streptomyces genomes

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | Genome-scale determination of 5′ and 3′ boundaries of RNA transcripts in Streptomyces genomes |
| 作者/期刊 | Lee et al. (2020), *Sci Data*, 7(1):436 |
| PMID | [33319794](https://pubmed.ncbi.nlm.nih.gov/33319794/) |
| DOI | [10.1038/s41597-020-00775-w](https://doi.org/10.1038/s41597-020-00775-w) |
| PMC | [PMC7708941](https://pmc.ncbi.nlm.nih.gov/articles/PMC7708941/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_010 | *Streptomyces avermitilis* MA-4680 | curated |
| BATTER_S1_011 | *Streptomyces griseus* subsp. *griseus* NBRC 13350 | curated |
| BATTER_S1_012 | *Streptomyces coelicolor* A3(2) | curated |
| BATTER_S1_013 | *Streptomyces lividans* TK24 | curated |
| BATTER_S1_014 | *Streptomyces tsukubensis* | curated |
| BATTER_S1_015 | *Streptomyces clavuligerus* | curated |
| BATTER_S1_016 | *Streptomyces venezuelae* | curated |

**统计口径**：本论文贡献 7 条 BATTER Table S1 来源记录；论文数 ≠ 来源记录数。

## 实验方法

dRNA-seq / Term-seq / RNA-seq。

## 公开数据

- SRA/ENA 原始数据登录号：SRP158023、SRP188290、SRP103795、SRP058830、SRX6937123/24、PRJEB40918、PRJEB31507、PRJEB36379、PRJEB34219（详见注册表 `raw_data_accessions`）。
- Figshare collection: [10.6084/m9.figshare.c.5044730](https://doi.org/10.6084/m9.figshare.c.5044730) — 预测的 TSS/TTS 坐标数据与分析脚本（正文 Data Records 明确说明）。

## 补充表与坐标数据

- Figshare collection 中的 TTS 坐标文件：7 个物种，平均每物种约 1,285 个 TTS。
- 文件格式与具体列名**待下载 Figshare 文件核实**。

## 证据类别

Figshare 中 TTS 坐标表为作者发布的实验端点结果，属于 `author_called_endpoint`。论文 Methods 中基于 z-score 算法，各 TTS 是否为独立功能验证终止子**待核查**。

## 参考序列与坐标

| source_id | 参考组装 | 备注 |
|-----------|----------|------|
| S1_010 | GCF_000009765.2 / NC_003155.5 | BA000030.4 与 RefSeq NC_003155.5 序列相同 |
| S1_011 | GCF_000010605.1 / NC_010572.1 | — |
| S1_012 | GCF_000203835.1 / NC_003888.3 | — |
| S1_013 | GCF_000739105.1 / CP009124 | — |
| S1_014 | GCF_003932715.1 / CP020700.1 | — |
| S1_015 | GCF_005519465.1 / CP027858.1 + CP027859.1 | 双 replicon |
| S1_016 | GCF_015710995.1 / CP059991.1 | 物种标签存在历史/命名冲突，见注册表备注 |

- 坐标体系：Figshare 文件中坐标约定**待下载原表核查**。

## 入库决定

v0.1 local snapshot 已将本论文的 7 个来源标准化发布为作者发表 Term-seq endpoint TSV 与 BED；每个来源保持独立 source ID、参考与 checksum。

## 问题与待核查

- Figshare collection 中 TTS 文件的具体字段格式**待核查**；
- S1_016 物种/菌株命名在论文、ENA、ATCC 与 NCBI 之间存在不一致，已记录为已知冲突；
- 各物种 TTS 是否按生长阶段分别列出**待核查**。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/33319794/
- DOI: https://doi.org/10.1038/s41597-020-00775-w
- Figshare: https://doi.org/10.6084/m9.figshare.c.5044730
- 历史初评笔记：[docs/legacy/literature-initial-review/文献6-PMID33319794-README.md](../../legacy/literature-initial-review/文献6-PMID33319794-README.md)
