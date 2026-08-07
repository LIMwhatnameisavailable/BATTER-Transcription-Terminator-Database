# PMID 29606352 — Evolutionary Convergence of Pathway-Specific Enzyme Expression Stoichiometry

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | Evolutionary Convergence of Pathway-Specific Enzyme Expression Stoichiometry |
| 作者/期刊 | Lalanne et al. (2018), *Cell*, 173(3):749-761.e38 |
| PMID | [29606352](https://pubmed.ncbi.nlm.nih.gov/29606352/) |
| DOI | [10.1016/j.cell.2018.03.007](https://doi.org/10.1016/j.cell.2018.03.007) |
| PMC | [PMC5978003](https://pmc.ncbi.nlm.nih.gov/articles/PMC5978003/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_001 | *Escherichia coli* str. K-12 substr. MG1655 | curated |
| BATTER_S1_003 | *Bacillus subtilis* subsp. *subtilis* str. 168 | curated |
| BATTER_S1_004 | *Caulobacter vibrioides* NA1000 | curated |
| BATTER_S1_005 | *Vibrio natriegens* NBRC 15636 | curated |

**统计口径**：本论文贡献 4 条 BATTER Table S1 来源记录；论文数 ≠ 来源记录数。

## 实验方法

Rend-seq。正文 STAR Methods 描述了基于 peak z-score 的终止子鉴定流程。

## 公开数据

- GEO: [GSE95211](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE95211) — 原始测序 reads 及 pile-up wig 文件（4 物种，18 个 Rend-seq + 3 个 ribosome profiling 样本）。
- Mendeley Data: [10.17632/ncm3s3pk2t.1](https://doi.org/10.17632/ncm3s3pk2t.1) — 验证数据、mRNA 丰度、翻译效率、Northern blot 原始图像。
- GitHub: [jblalanne/Rend_seq_core_scripts](https://github.com/jblalanne/Rend_seq_core_scripts) — 分析脚本。

## 补充表与坐标数据

- Supplementary Table S3：*Intrinsic Terminators and Readthrough Fractions Determined by Rend-Seq, Related to Figures 4 and S3*（Spreadsheet，约 507 KB），共 8 个 sheet：
  - Sheet 1: *B. subtilis* 终止子（约 1,486 个）
  - Sheet 2: *E. coli* 终止子（约 630 个）
  - Sheet 3: *V. natriegens* 终止子（约 1,257 个）
  - Sheet 4: *C. vibrioides* 终止子（约 374 个）
  - Sheet 5-8: 四物种 tuned terminators 子集
- 原始 xlsx 文件未进入本仓库，按 DOI 引用。

## 证据类别

- Supplementary Table S3 作者发表的坐标表：按 BTED SOP 属于 `author_called_endpoint`；
- 从 Rend-seq WIG 信号按公开规则调用的峰：属于 `called_endpoint`（候选端点，非终止子结论）；
- 原始 WIG/BigWig 信号：属于 `observed_signal`；
- Table S3 中每个位点是否经独立遗传学功能验证：**待核查**；原文仅说明基于 Rend-seq 信号鉴定。

## 参考序列与坐标

| source_id | 参考组装 | 备注 |
|-----------|----------|------|
| S1_001 | GCF_000005845.1 | — |
| S1_003 | GCF_000009045.1 | — |
| S1_004 | GCF_000022005.1 | 注册表 `coordinate_status` 为 `verified_with_metadata_conflict`（CP001340.1 权威 vs GEO 复制行 NC_000913.2） |
| S1_005 | GCF_001456255.1 | 本地处理使用 CP009977.1 / CP009978.1，手动复核待完成 |

- 坐标体系：Table S3 描述为基因组位置；具体 1-based / 0-based 及列名格式**待下载原表核查**。

## 入库决定

本地工作树已将四物种来源标记为 `curated`。坐标数据、端点表与 JBrowse 资源**尚未迁移**到本仓库；迁移前须按验收门槛逐来源审计。

## 问题与待核查

- Table S3 实际列名、坐标体系、链方向编码需下载 xlsx 原表核实；
- S1_004 的 contig 权威版本存在 metadata 冲突，已在注册表 `blocker_or_note` 记录；
- S1_005 两个 contig 的手动复核状态为 `manual review pending`。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/29606352/
- DOI: https://doi.org/10.1016/j.cell.2018.03.007
- GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE95211
- 历史初评笔记（含未核实推断）：[docs/legacy/literature-initial-review/文献1-PMID29606352-README.md](../../legacy/literature-initial-review/文献1-PMID29606352-README.md)
