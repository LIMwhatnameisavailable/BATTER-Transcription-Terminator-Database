# PMID 32694125 — Genome-Scale Transcription-Translation Mapping of Zymomonas mobilis

## 文献信息

| 项目 | 内容 |
|------|------|
| 标题 | Genome-Scale Transcription-Translation Mapping Reveals Features of Zymomonas mobilis Transcription Units and Promoters |
| 作者/期刊 | Vera et al. (2020), *mSystems*, 5(4):e00250-20 |
| PMID | [32694125](https://pubmed.ncbi.nlm.nih.gov/32694125/) |
| DOI | [10.1128/mSystems.00250-20](https://doi.org/10.1128/mSystems.00250-20) |
| PMC | [PMC7361605](https://pmc.ncbi.nlm.nih.gov/articles/PMC7361605/) |

## 关联来源（BATTER_S1）

| source_id | 物种/菌株 | 处理状态 |
|-----------|-----------|----------|
| BATTER_S1_009 | *Zymomonas mobilis* subsp. *mobilis* ZM4 | curated |

## 实验方法

RNA-seq / TSS-seq / term-seq / ribo-seq。

## 公开数据

- GEO: [GSE139939](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE139939) — 原始测序数据。
- PRIDE: [PXD016962](https://www.ebi.ac.uk/pride/archive/projects/PXD016962) — 蛋白质质谱数据（与终止子无关）。
- GitHub: [jmvera255/Vera_2020_mSystems](https://github.com/jmvera255/Vera_2020_mSystems) — σ70/σA 启动子建模脚本。

## 补充表与坐标数据

- Supplementary Data Set S3（`msystems.00250-20-sd003.xlsx`）：
  - Sheet 3: 2,091 个 transcription termination sites (TTSs)（核心实验端点数据）；
  - Sheet 4: TTS 与 TransTermHP 预测终止子的匹配结果（混合证据，仅内部审计）；
  - Sheet 5: TransTermHP 预测的全部 1,746 个 intrinsic terminator（`prediction_only`，不发布为实验端点）。

## 证据类别

- Sheet 3 TTS：`author_called_endpoint`；
- Sheet 4 匹配结果：`author_integrated_mixed_evidence`（内部审计）；
- Sheet 5 TransTermHP 预测：`prediction_only`（内部审计）。

## 参考序列与坐标

- 参考组装：GCF_003054575.1
- 覆盖范围：染色体 + 4 个质粒，6 种生长条件。
- 坐标体系：Sheet 3 具体列名与坐标约定**待下载原表核查**。

## 入库决定

v0.1 local snapshot 已将 S1_009 的 2,091 条作者发表、经 processing-site 过滤的 Term-seq TTS 标准化发布为 TSV 与 BED；纯预测继续排除在公开端点层之外。

## 问题与待核查

- Data Set S3 列结构需下载原表确认；
- Sheet 4 中“r”标记反向补充终止子的坐标表示方式**待核查**。

## 来源链接

- PubMed: https://pubmed.ncbi.nlm.nih.gov/32694125/
- DOI: https://doi.org/10.1128/mSystems.00250-20
- GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE139939
- 历史初评笔记：[docs/legacy/literature-initial-review/文献5-PMID32694125-README.md](../../legacy/literature-initial-review/文献5-PMID32694125-README.md)
