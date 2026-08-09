# BTED 数据发布接口 v0.2

本文定义 BTED v0.2.0 每个来源对用户公开的文件接口。核心目标是同时满足跨来源检索、作者原始字段保留和可复现审计。

## 1. 一个来源，一个发布目录

```text
data/public/v0.2.0/records/BATTER_S1_NNN/
├── endpoints.tsv
├── source_annotations.tsv       # 许可允许时
├── endpoints.bed
├── fields.json
├── manifest.json
├── SHA256SUMS.txt
└── *_observations.tsv           # 少数来源的规范化附表
```

`audit_only` 来源只提供 `fields.json`、`manifest.json` 和 checksum，不生成空端点表或伪浏览器入口。

## 2. 核心表 `endpoints.tsv`

核心表固定为 24 列，保持与 v0.1 兼容。它只保存跨来源查询所需的稳定字段：稳定 ID、来源/样本、方法、证据类别、作者 ID、参考版本、contig、1-based/BED 坐标、strand、主分值/分类、基因、论文、原始行和 QC。

规则：

- 一行表示一个来源语境下的端点记录；
- `end_id` 在整个发布版本中唯一；
- `biological_coordinate_1based` 是 BTED 的生物学坐标；
- 单碱基 BED 必须满足 `bed_start_0based = position - 1`、`bed_end_0based = position`；
- 不同 contig 不得匹配或去重；
- `prediction_only` 和不可拆分的混合证据不得进入核心表。

## 3. 来源特异表 `source_annotations.tsv`

来源特异表通过 `end_id` 与核心表关联，并尽量无损保存作者原表字段，例如：

- read count、coverage、signal、fold change、显著性；
- 作者分类、条件、序列、结构和上下游关系；
- 作者附带的预测支持字段。

预测字段必须标记为 `prediction_annotation`；它们不会把端点提升为另一证据等级。若再发布许可未核实，不复制来源特异表，但 `fields.json` 仍逐列登记原字段和未发布原因，避免静默丢失。

## 4. 字段属性

`fields.json` 中每个来源字段使用以下属性之一：

| 属性 | 含义 |
|---|---|
| `experimental_measurement` | 实验产生的数值或条件观察 |
| `author_called_endpoint` | 作者端点 ID、位置、链和端点调用字段 |
| `author_annotation` | 作者对端点的分类或上下文注释 |
| `prediction_annotation` | 附着在已收录端点上的预测软件结果 |
| `curation_metadata` | 来源、参考、行号和处理信息 |

`publication_status` 必须是 `published` 或 `withheld_external_link_only`；后者需要 `withheld_reason`。

## 5. Manifest

`manifest.json` 至少记录：

- source ID、论文、PMID/DOI/PMC；
- 物种、菌株、实验方法、数据 accession；
- 作者参考、BTED assembly、contig 和坐标判断；
- `release_status`、`evidence_class`、记录数和 JBrowse 配置；
- 许可/再发布状态、处理决策和已知限制。

允许的发布状态：

- `published_standardized`：核心表、BED 和 JBrowse 均通过验证；
- `audit_only`：仅展示来源审计，不能下载端点或打开 JBrowse。

## 6. JBrowse 接口

- 一个来源一份配置，文件名为 `BATTER_S1_NNN.config.json`；
- 所有资产带来源前缀，防止同名文件覆盖；
- 多 contig 位于同一 assembly 中；
- 轨道名称明确区分 observed signal、本站 candidate、author endpoint 和 gene annotation；
- S1_002 不生成配置；混合证据和纯预测不生成公开轨道。

大型浏览器文件只进入 GitHub Release 资产，不进入 Git 历史。

## 7. 完整性与版本

- 每个来源目录有 `SHA256SUMS.txt`；
- 发布根目录有 `release_manifest.json` 和 checksum；
- Release 资产固定命名为 `BTED-v0.2.0-data.tar.gz` 与 `BTED-v0.2.0-jbrowse-assets.tar.gz`；
- 同一版本的已发布文件不得原地改写；修订必须增加版本并记录差异。

## 8. 验证命令

```bash
python3 scripts/validate_bted_v0_2.py
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
python3 scripts/validate-site.py site
python3 -m unittest -v tests/test_bted_ingestion.py tests/test_bted_v0_2.py
```
