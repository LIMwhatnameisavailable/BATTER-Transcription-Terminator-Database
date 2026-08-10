# BATTER_S1 来源注册表数据字典

本文件说明 `data/registry/batter_s1_source_registry.tsv` 的列含义、取值规则与已知的 schema 改进问题。注册表本身是历史工作产物，本分支不静默修改其数据，仅补充说明与改进方案。

## 列说明（16 列）

| 中文字段名 | 英文列名 | 含义 | 是否允许 NA | 示例 | 备注 |
|------------|----------|------|-------------|------|------|
| 来源编号 | `source_id` | BATTER Table S1 来源唯一编号 | 否 | `BATTER_S1_001` | 新外部来源使用 `BTED_EXT_年份_序号` |
| 发表年份 | `published_year` | 当前注册表中的年份字段 | 否 | `2018` | **含义不明，存在冲突，见下方 schema 改进说明** |
| 物种/菌株 | `species` | 论文中使用的物种与菌株名 | 否 | `Escherichia coli str. K-12 substr. MG1655` | 按论文原文；菌株层级尽量拆到 `strain` 字段（schema 改进） |
| 门 | `phylum` | 物种所属门 | 否 | `Proteobacteria` | 便于分类浏览 |
| 参考基因组 | `reference_genome` | 本地处理使用的 NCBI Assembly | 否 | `GCF_000005845.1` | 含版本号；多 contig 时在 `blocker_or_note` 中补充 |
| PubMed 编号 | `pmid` | 来源对应论文的 PMID | 否 | `29606352` | 同一 PMID 可对应多个 source |
| 论文标题 | `paper_title` | 论文英文标题 | 否 | `Evolutionary Convergence of...` | 与 PMID 一致 |
| DOI | `doi` | 论文 DOI | 否 | `10.1016/j.cell.2018.03.007` | 不带前缀 |
| PMC | `pmc` | PubMed Central 编号 | 可 | `PMC5978003` | 无 PMC 时填 `NA` |
| 原始数据登录号 | `raw_data_accessions` | GEO/SRA/ENA/ArrayExpress 等原始数据登录号 | 可 | `GSE95211` | 多个用分号分隔 |
| 实验方法族 | `assay_family` | 实验方法大类 | 否 | `Rend-seq` / `Term-seq / dRNA-seq` | 按论文方法原文归类 |
| 是否用于 BATTER 增强 | `used_for_batter_augmentation` | 是否被 BATTER 论文用于增强训练 | 否 | `TRUE` / `FALSE` | 来自 BATTER Table S1 标注 |
| 可访问性状态 | `accessibility_status` | 数据是否可公开定位 | 否 | `accessible` | 历史字段；新模板使用 `processing_status` |
| 坐标核查状态 | `coordinate_status` | 坐标体系是否已核实 | 否 | `verified` / `verified_with_metadata_conflict` | `verified_with_metadata_conflict` 表示 contig/参考版本存在已知冲突 |
| 处理状态 | `processing_status` | 本地工作树处理状态 | 否 | `curated` | 六状态定义见 `docs/standards/BTED_数据入库标准流程_v0.1.md` |
| 阻塞/备注 | `blocker_or_note` | 问题、恢复条件、处理细节 | 可 | `NA` 或描述 | 不得包含本地路径或私密信息 |

## 年份字段的 schema 改进方案

当前单列 `published_year` 被发现存在含义不明及与 PMID 记录冲突的情况。例如：

| source_id | `published_year` | PMID 记录年份 | 说明 |
|-----------|------------------|---------------|------|
| `BATTER_S1_002` | 2018 | 2023 | PMID 38030608（TRS 方法论文）为 2023 年发表，注册表记为 2018，存在明显冲突 |
| `BATTER_S1_019` | 2022 | 2021 | PMID 34874777（Cho et al., mSystems）PubMed 记录为 2021，注册表记为 2022 |

**处理原则：不得静默修改 `published_year` 原值。** 建议后续 schema 拆分为两列：

- `paper_publication_year`：从 PubMed/DOI 元数据核实的正式发表年份；
- `batter_table_s1_reported_year`：BATTER Table S1 中实际打印/报告的年份（可能是 online-first、issue 或录入年份）。

迁移时保留旧列作为历史字段，新增两列并逐步回填；所有回填须有 PMID/DOI 记录作为证据。冲突行在 `blocker_or_note` 中引用本文件。

## 与当前协作模板的关系

新外部来源使用 `data/registry/templates/external_literature_source_intake.tsv`（26 列），字段更细。未来 BATTER_S1 注册表如需迁移到统一 schema，应通过显式映射和审计完成，不直接覆盖历史字段。
