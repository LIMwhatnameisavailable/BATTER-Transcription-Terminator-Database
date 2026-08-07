# docs/literature — 13 篇来源论文总索引

本目录存放 BTED 项目当前关注的 **13 篇原始研究文献**（来自 BATTER Table S1）的正式调研 README。

**重要统计口径**：

- **13 篇论文** = 13 篇 PMID（本索引的每一行对应一篇论文）；
- **22 个来源记录** = BATTER Table S1 在这 13 篇 PMID 下拆分出的物种/菌株/实验体系记录数（见 `data/registry/batter_s1_source_registry.tsv`）；
- 论文数 ≠ 来源记录数。公开页面或图表中不得将两者混写为同一个“数据集数量”。

## 索引表

| PMID | DOI | 文章标题 | 关联 BATTER_S1 来源 | 实验方法 | 处理状态 | 正式 README |
|------|-----|----------|---------------------|----------|----------|-------------|
| 29606352 | [10.1016/j.cell.2018.03.007](https://doi.org/10.1016/j.cell.2018.03.007) | Evolutionary Convergence of Pathway-Specific Enzyme Expression Stoichiometry | BATTER_S1_001 / 003 / 004 / 005 | Rend-seq | curated | [PMID_29606352/README.md](PMID_29606352/README.md) |
| 30517198 | [10.1371/journal.ppat.1007461](https://doi.org/10.1371/journal.ppat.1007461) | The Transcriptional landscape of Streptococcus pneumoniae TIGR4 | BATTER_S1_006 | Term-seq / 3′ end mapping | curated | [PMID_30517198/README.md](PMID_30517198/README.md) |
| 31555254 | [10.3389/fmicb.2019.02074](https://doi.org/10.3389/fmicb.2019.02074) | The Transcription Unit Architecture of Streptomyces lividans TK24 | BATTER_S1_007 | dRNA-seq / Term-seq | curated | [PMID_31555254/README.md](PMID_31555254/README.md) |
| 31594819 | [10.1128/mBio.02253-19](https://doi.org/10.1128/mBio.02253-19) | A rhlI 5′ UTR-Derived sRNA Regulates RhlR-Dependent Quorum Sensing | BATTER_S1_008 | RNA-seq / term-seq | curated | [PMID_31594819/README.md](PMID_31594819/README.md) |
| 32694125 | [10.1128/mSystems.00250-20](https://doi.org/10.1128/mSystems.00250-20) | Genome-Scale Transcription-Translation Mapping of Zymomonas mobilis | BATTER_S1_009 | RNA-seq / term-seq / TSS-seq / ribo-seq | curated | [PMID_32694125/README.md](PMID_32694125/README.md) |
| 33319794 | [10.1038/s41597-020-00775-w](https://doi.org/10.1038/s41597-020-00775-w) | Genome-scale determination of 5′ and 3′ boundaries in Streptomyces genomes | BATTER_S1_010 / 011 / 012 / 013 / 014 / 015 / 016 | dRNA-seq / Term-seq | curated | [PMID_33319794/README.md](PMID_33319794/README.md) |
| 33947798 | [10.1128/mSystems.01013-20](https://doi.org/10.1128/mSystems.01013-20) | Elucidating the Regulatory Elements for Transcription Termination in Streptomyces clavuligerus | BATTER_S1_017 | RNA-seq / dRNA-seq / ribo-seq / Term-seq | curated | [PMID_33947798/README.md](PMID_33947798/README.md) |
| 34054774 | [10.3389/fmicb.2021.667450](https://doi.org/10.3389/fmicb.2021.667450) | Multi-Omic Analyses of Synechocystis sp. PCC 7338 | BATTER_S1_018 | dRNA-seq / Term-seq / RNA-seq / WGS | curated | [PMID_34054774/README.md](PMID_34054774/README.md) |
| 34874777 | [10.1128/mSystems.00943-21](https://doi.org/10.1128/mSystems.00943-21) | Different Regulatory Modes of Synechocystis sp. PCC 6803 | BATTER_S1_019 | RNA-seq / Ribo-seq / Term-seq | curated | [PMID_34874777/README.md](PMID_34874777/README.md) |
| 35491820 | [10.1128/mbio.00524-22](https://doi.org/10.1128/mbio.00524-22) | Mapping the Complex Transcriptional Landscape of Dickeya dadantii | BATTER_S1_020 | RNA-seq / dRNA-seq / Nanopore native RNA-seq | curated | [PMID_35491820/README.md](PMID_35491820/README.md) |
| 37096044 | [10.1016/j.isci.2023.106465](https://doi.org/10.1016/j.isci.2023.106465) | Premature termination of transcription in Mycobacterium tuberculosis | BATTER_S1_022 | RNA-seq / Term-seq / tagRNA-seq | curated | [PMID_37096044/README.md](PMID_37096044/README.md) |
| 37402717 | [10.1038/s41467-023-39576-1](https://doi.org/10.1038/s41467-023-39576-1) | RNA termination and regulation in Borrelia burgdorferi | BATTER_S1_021 | RNAtag-seq / Term-seq / bulk RNA-seq / 3′RNA-seq | curated | [PMID_37402717/README.md](PMID_37402717/README.md) |
| 38030608 | [10.1038/s41467-023-43534-2](https://doi.org/10.1038/s41467-023-43534-2) | TRS: a method for determining transcript termini from RNAtag-seq sequencing data | BATTER_S1_002 | RNAtag-seq / TRS | curated | [PMID_38030608/README.md](PMID_38030608/README.md) |

## 使用说明

1. 每篇论文的 README 只保留已核实事实；任何推断均标为“待核查”。
2. 处理状态 `curated` 表示来源注册表已收录并有人工整理记录，但不代表全部端点已完成参考版本/坐标体系审计或可以公开发布。
3. 如需接入新文献，请先阅读 [`docs/standards/协作者_新增文献收集与入库指南.md`](../standards/协作者_新增文献收集与入库指南.md) 与 [`CONTRIBUTING.md`](../../CONTRIBUTING.md)，然后在 `docs/literature/PMID_XXXXXXXX/` 创建新的正式调研 README。
4. 旧版探索性文献笔记已移入 [`docs/legacy/literature-initial-review/`](../legacy/literature-initial-review/)，仅作溯源，不作为当前标准结论。

## 统计口径提示

- 本索引共 13 行（13 篇论文）。
- `data/registry/batter_s1_source_registry.tsv` 共 22 行（22 个来源记录）。
- 例如 PMID 29606352 对应 4 个来源记录，PMID 33319794 对应 7 个来源记录。
