# BTED v0.3 数据库契约

**实现骨架：** [`backend/database/schema.sql`](../../backend/database/schema.sql)
**数据角色：** PostgreSQL 派生查询层；canonical release 仍是科研真源

## 1. 设计原则

数据库按 release version 隔离。`v0.2.0` 的静态发布物和 `v0.3.0` 的数据库导入是
并行版本；相同的 `source_id` 或 `end_id` 在不同 release 中不能因为字符串相同而被
错误合并。所有可查询实体要么直接带 `release_version`，要么通过带 release 外键的
父表归属到一个版本。

关系表保存能跨来源检索的稳定字段，JSONB 保存来源特异、可能随论文变化的字段。每
条 endpoint 同时保留 v0.2 核心表的 24 列语义和内部关联键：内部 `endpoint_pk`、
`source_pk`、`contig_id`、`release_version` 只用于完整性和查询，不替换导出列。

表间关系的高层图如下：

```text
release_versions ──< import_runs
       │
       ├──< sources >── publications
       │       │  ├──< source_accessions
       │       │  └──< samples ──< endpoints >── contigs >── assemblies
       │                         │                 │
       │                         ├──< source_annotations (JSONB)
       │                         └──< endpoint_gene_context >── genes
       │
       └──< assets（release/assembly/source 的已登记下载资产）
```

`publications` 与 `sources` 有意不重复存储 PMID、发表年份或论文标题：同一篇论文在
Table S1 下可对应多个物种/菌株来源（例如 S1_001、S1_003–S1_005；这些来源共享
PMID 29606352，S1_002 不属于该论文）。`endpoints` 仍保留 24 列
接口中已有的 `pmid`/`doi`，以便无损导出 v0.2；导入器须检查它们与
`sources.publication_id -> publications` 一致，而不是把 endpoint 值当作另一篇论文。

## 2. 表与主外键

### 2.1 `release_versions`

一个 canonical release 一个 `release_version`（例如 `v0.2.0`、`v0.3.0`），以文本
主键保留用户可见版本号；另有内部递增 `release_id` 供排序。表保存 release 日期、
canonical manifest 路径/checksum、生命周期状态和是否当前版本。

关键约束：

- `release_version` 唯一且符合 `vMAJOR.MINOR.PATCH`；manifest SHA-256 必须为 64 个
  十六进制字符；
- 同时只能有一个 `is_current = TRUE` 的版本（部分唯一索引）；
- `is_current = TRUE` 时 `status` 必须为 `published`；
- `status` 为 `staged`、`validated`、`published` 或 `retired`；查询 API 只能默认
  选择 `published`，客户端也可以显式请求其他已授权版本。

### 2.2 `import_runs`

每次从 release 文件构建/验证数据库的运行记录。它保存 `release_version` 外键、
importer 名称/版本、输入 manifest 路径与 checksum、staging 来源、运行状态、时间戳和
验证摘要 JSONB。`(release_version, input_manifest_sha256, started_at)` 仅建立普通索引，
不设置唯一约束：同一 release/manifest 在 importer 修复后可以重新运行；每次 run 都保留
importer 版本、时间和结果，供审计比较。

`run_status` 从 `staging`、`validating`、`validated`、`committed`、`failed`、
`aborted` 中取值。只有完整校验的 run 才能被标记 `committed`，并在事务中将 release
切换为可查询状态；失败 run 保留错误摘要，不删除以掩盖问题。

### 2.3 `publications`

论文级事实表：`pmid`（规范化为文本，保留数字字符串）、`doi`、`pmc`、
`published_year`、`journal`、`paper_title` 和可选 citation JSONB。PMID 唯一；DOI 使用
不区分大小写的唯一索引。来源只存 `publication_id` 外键，不复制 `pmid`/year/title。

### 2.4 `assemblies`

参考组装级事实表。`assembly_accession` 是**带版本号**的唯一标识（例如
`GCF_000739105.1`），不可只保存不带版本的 accession。可选 `assembly_name`、物种、
`strain`、taxon id 与参考入口用于展示。

### 2.5 `contigs`

每个 replicon/contig 独立一行，通过 `assembly_id` 外键归属组装；保存带版本的
`contig_accession`、显示名称、长度和可选序列 SHA-256。`(assembly_id,
contig_accession)` 与 `(assembly_id, contig_name)` 均唯一。端点必须引用 `contig_id`，
而不是仅靠字符串匹配；这样 S1_005 的双 contig、S1_015 的双 replicon 和带质粒来源
不会混入同一条染色体。

### 2.6 `sources`

Table S1 的来源/物种记录，是 release 内的 provenance 边界。主键为内部
`source_pk`，业务键为 `(release_version, source_id)`。表保存 species、phylum、
assay family、release/processing/accessibility/coordinate/redistribution 状态、
来源 manifest 路径与 checksum、发布记录数、JBrowse 标记和**来源级**
`used_for_batter_augmentation`（API/查询别名 `augmentation_eligible`）；论文通过
`publication_id`，参考组装通过 `assembly_id`。

`sources` 不保存 `pmid`、发表年份或用分号拼接的 raw accession；这些分别来自
`publications` 和 `source_accessions`。`record_count` 是该 source 在该 release 的
公开核心行数，不能用作跨 source 去重后的数量。

允许的 source 状态包括 `published_standardized`、`audit_only`、`to_review` 和
`blocked`。数据库约束进一步规定：

- `published_standardized` 必须有正记录数和四种公开 evidence class 之一；
- `audit_only` 必须为零 endpoint、零 JBrowse 入口、`record_count = 0`，evidence
  class 为 `NA`；
- `to_review`/`blocked` 可以保留 source/manifest 审计元数据，但不能被 endpoint 查询
  当作公开发布。

### 2.7 `source_accessions`

一个 source 的每个原始数据 accession 一行，避免 `GSE...;SRX...` 这样的拼接字符串
成为不可检索字段。`accession_namespace`（GEO、SRA、ENA、BioStudies 等）、规范化
`accession`、原始写法 `raw_value`、类型、顺序和外部 URL 均保存；规范化键
`(source_pk, accession_namespace, accession)` 唯一。规范化不丢原始字符串，也不把
accession 当作 endpoint 或 publication。

### 2.8 `samples`

来源内的实验样本/表格语境。一行有 `source_pk`、`sample_id`、可选 label、条件、
replicate、样本 accession 和 metadata JSONB；`(source_pk, sample_id)` 唯一。endpoint
的 24 列仍直接保留 `sample_id`，同时以 NOT NULL `sample_pk` 和复合外键绑定到同一
`source_pk + sample_id` 的 samples 行，不能通过 NULL 绕过真实样本关联。样本是
source-scoped，不能把同名 sample ID 跨来源相连。

### 2.9 `endpoints`

公开端点核心表。每行有内部 `endpoint_pk`、`release_version`、`source_pk`、
`contig_id`，以及下面完整的 v0.2 24 列。`(release_version, end_id)` 唯一；同一
release 内即使坐标相同，只要 source、sample、contig、strand 或序列身份不同也保留
为不同 `end_id`。

`signal_or_score` 在数据库中使用 text 而不是强制 numeric：当前 v0.2 同时存在数值
字符串和字面量 `NA`（例如 S1_018–021），强转会丢失信息。需要数值排序的查询可以
在经过明确规则的 view/import 派生字段上进行，但 canonical 24 列导出必须保留原值。

#### 24 列无损映射

| 顺序 | v0.2 列 | PostgreSQL 列 | 语义/保留规则 |
| ---: | --- | --- | --- |
| 1 | `end_id` | `end_id` | 发布版本内稳定端点 ID；保留 source/sample/contig/strand/序列身份 |
| 2 | `source_id` | `source_id` | 与 `sources.source_id` 对应的兼容列；`source_pk` 是完整性外键 |
| 3 | `sample_id` | `sample_id` | 来源语境/样本 ID；不跨 source 解释 |
| 4 | `assay` | `assay` | 该行实验方法 |
| 5 | `evidence_class` | `evidence_class` | 仅公开四层：`observed_signal`、`called_endpoint`、`author_called_endpoint`、`curated_record` |
| 6 | `author_endpoint_id` | `author_endpoint_id` | 作者原始端点/TEP ID；不可用内部 PK 替代 |
| 7 | `published_reference_accession` | `published_reference_accession` | 作者表中使用的参考/contig accession，含版本 |
| 8 | `reference_assembly` | `reference_assembly` | 作者/BTED 参考组装 accession，含版本；与 source assembly 做导入核对 |
| 9 | `reference_name` | `reference_name` | 发布表中的参考名称原文 |
| 10 | `replicon_label` | `replicon_label` | replicon/contig 标签原文 |
| 11 | `biological_coordinate_1based` | `biological_coordinate_1based` | BTED 生物学坐标，`>= 1` |
| 12 | `bed_start_0based` | `bed_start_0based` | 单碱基 BED 起点，必须等于 position - 1 |
| 13 | `bed_end_0based` | `bed_end_0based` | 单碱基 BED 终点，必须等于 position |
| 14 | `strand` | `strand` | 只能为 `+` 或 `-` |
| 15 | `signal_or_score` | `signal_or_score` | 原始发布字符串；数值或 `NA` 都不静默改写 |
| 16 | `author_category` | `author_category` | 作者分类/类别原文 |
| 17 | `associated_gene_or_locus` | `associated_gene_or_locus` | 作者关联基因或 locus 原文，不强配 gene |
| 18 | `pmid` | `pmid` | 为 v0.2 导出兼容而保留的论文标识；须与 source publication 一致 |
| 19 | `doi` | `doi` | 为兼容而保留的 DOI；不替代 publication 外键 |
| 20 | `source_table_or_file` | `source_table_or_file` | 补充表/文件名，保留 provenance |
| 21 | `coordinate_interpretation` | `coordinate_interpretation` | 坐标判断原文，例如 1-based 与 BED 换算 |
| 22 | `original_row_reference` | `original_row_reference` | 原始文件/行号或稳定定位，禁止丢弃 |
| 23 | `qc_status` | `qc_status` | 坐标/迁移/核查状态 |
| 24 | `note` | `note` | 来源限制、证据措辞和其他逐行备注 |

坐标 CHECK 为 `biological_coordinate_1based >= 1`、
`bed_start_0based >= 0`、`bed_end_0based > bed_start_0based`，并严格要求
`bed_start_0based = biological_coordinate_1based - 1`、
`bed_end_0based = biological_coordinate_1based`。这只表示当前单碱基 endpoint 接口；
不能把区间或跨 contig 记录压缩成同一坐标。endpoint evidence CHECK 和触发器共同拒绝
`author_integrated_mixed_evidence`、`prediction_only` 等非公开层。

### 2.10 `source_annotations`（JSONB）

用于 v0.2 `source_annotations.tsv` 及少数一对多来源附表的无损承载。每行关联一个
`(release_version, end_id, annotation_kind, source_record_id, ordinal)`，其中
`annotation_json JSONB` 保存来源特异字段对象，`provenance_json JSONB` 保存原表/行和
字段属性；`source_pk` 与 endpoint 使用三列外键绑定，不能把某个来源的 annotation 挂到
另一个来源的同名 ID。`source_record_id`/`ordinal` 允许同一 endpoint、同一 annotation
kind 保存多条来源观察，不被错误地压缩成一行。`annotation_kind` 为
`experimental_measurement`、`author_annotation`、`prediction_annotation` 或
`curation_metadata`；预测字段只能标成 `prediction_annotation`，它们不能修改
`endpoints.evidence_class`。

JSONB 对象允许保存作者字段名、`NA`、条件、多值关系、序列/结构和作者预测支持等，
避免将未知字段硬塞进 24 列或静默丢弃。许可不允许复制时，可只保存字段清单、外部
链接和 withheld 原因，而不把受限原表内容写入 JSONB。

### 2.11 `genes`

参考组装的 gene feature 表：`release_version`、`assembly_id`、`contig_id`、稳定 gene
ID/locus tag、feature type、1-based 起止坐标、strand、attributes JSONB，以及必填的
`annotation_asset_id`/`annotation_sha256`。`(release_version, assembly_id, contig_id,
gene_id)` 唯一；复合外键保证 gene 的 assembly/contig 对应同一个 `contigs` 行，gene
的 release 和 GFF3 asset 也必须一致。触发器进一步检查 `end_1based <= contig.length_bp`
和 asset checksum，避免同一 assembly 的不同 GFF3 在不同 release 中互相覆盖。当前只为
将来的基因上下文准备；本里程碑不计算、不发布 gene clusters，也不纳入 Rfam。

### 2.12 `endpoint_gene_context`

可选派生关联表，保存 endpoint 与 gene 的 `relation_type`（如 upstream、downstream、
overlap、nearest）、距离、计算方法/版本和 context JSONB。endpoint 和 gene 都通过
`(release_version, *_pk)` 复合外键绑定到同一个 release，避免同一个 ID 在不同 GFF3/
release 混用。导入/计算器必须检查 endpoint 与 gene 属于同一个 assembly 和 contig；
不能跨 contig 生成“最近基因”。第一里程碑只建立表，不插入计算结果。

### 2.13 `assets`

资产登记表。`asset_id` 是 API 稳定路径标识；每行绑定 release，必要时绑定 source 或
assembly，保存 `asset_kind`、逻辑路径、允许的 origin URL/host、byte size、SHA-256、
MIME type、`supports_range`、许可状态和公开标记。`(release_version, logical_path)`
唯一；`asset_kind` 包括 fasta/fai/gff3/tbi/bigwig/bed/config/metadata/checksum/archive
等，不包括 prediction endpoint。

只有表中已登记的 origin 才能被 `/api/v1/assets/{asset_id}` 代理；FastAPI 依据
`supports_range` 和 byte size 执行 `HEAD`/Range 合约，不能接受任意 URL。数据库不把
Hugging Face 对象当作 canonical release；对象变化必须新建 release 或新 checksum。
物化 origin 固定为 `<asset_origin_base>/<logical_path>`，并保留 `logical_path` 的目录层级；
`asset_id` 仅用于稳定 API 路由，不用作对象存储路径。

## 3. 证据、状态和 augmentation 约束

### 3.1 endpoint 公开证据

DDL 的 endpoint CHECK 只允许 `observed_signal`、`called_endpoint`、
`author_called_endpoint`、`curated_record`。显式禁止 `author_integrated_mixed_evidence`
和 `prediction_only`，并通过 endpoint/source 触发器禁止 audit-only、to_review 或
blocked source 产生公开 endpoint。预测结果可以留在 source_annotations 内，但不得
通过 JOIN 或统计被计为实验端点。

### 3.2 S1_002 audit-only

S1_002 记录 publication/source/assembly/accession 和 manifest 审计信息即可；其
`release_status = audit_only`、`record_count = 0`、`has_jbrowse = FALSE`、evidence
class = `NA`。数据库不创建占位 endpoint，也不生成空 BED、下载项或 JBrowse deep link。
只有未来能逐记录拆出纯实验 provenance 并形成新 release，才可改变状态。

### 3.3 19/3 augmentation 边界

`sources.used_for_batter_augmentation` 一一映射 Table S1 的原字段，
`augmentation_eligible` 只是 API/query 层的表达式别名（不是物理列）。当前 `TRUE` 19 个、
`FALSE` 3 个，计数由 source manifest/registry 校验，不在 endpoint 表复制一个会误导的训练标签。
`/api/v1/augmentation`
第一版只列出 19 个 TRUE 来源以及它们的 release、publication、assembly、evidence 和
记录数（即 source-level eligibility）；它不宣称每条端点逐条进入训练，不生成训练
split/label，也不提供 gene cluster 或 Rfam 结果。

## 4. 导入校验顺序

1. 读取 release manifest，插入 `release_versions` 和 `import_runs` 的 staging 记录；
2. 先导入 publication、assembly、contig、source，再规范化 source accession 和 sample；
3. 对每个 endpoint 检查 24 列表头、source/release、publication、contig、strand、
   1-based/BED 等式、证据层、原始行引用和 endpoint ID；
4. 将来源特异字段原样放入 `source_annotations.annotation_json`，逐字段带属性和
   provenance；预测字段明确 `prediction_annotation`；
5. 导入 genes/assets（如 release 已有），对每个文件复算 byte size/SHA-256；gene
   context 只有经过单独计算器才可追加；
6. 执行 focused validator 和全量回归，写入 `validation_summary`；全部通过后在原子
   事务中把 run 标为 `committed` 并发布 release；否则保留失败 run，不切换线上版本。

## 5. 不允许的简化

- 不把 `source_id + position` 当作 endpoint 主键；必须保留 `end_id`、sample、contig、
  strand 和序列身份；
- 不把同 PMID 的多个 source 合并成一条 source；publication 可以复用，source 不可；
- 不把 raw accession 存成一个不可检索分号字符串；
- 不用 numeric 列替换可能为 `NA` 的 `signal_or_score`；
- 不把 source_annotations 的作者预测字段写回 endpoints 的 evidence；
- 不以 `DROP DATABASE`、`DROP TABLE` 或清空生产表作为发布切换手段。
