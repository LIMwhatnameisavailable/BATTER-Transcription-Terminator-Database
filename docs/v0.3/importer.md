# BTED v0.3 canonical release 校验器与 PostgreSQL 导入

**状态：** v0.3.0（A/B1 只读、物化；B2 writer 已实现，待真实数据库 smoke test）
**实现：** `backend/importer/canonical.py`、`backend/importer/materialize.py`、`backend/importer/postgres.py`
**入口：** `scripts/import_bted_v03.py`

canonical validator 和 materializer 只读取一个已经冻结的 canonical release，检查将来
导入数据库时最容易出错的边界，并输出可复核的 import plan/JSONL staging bundle。B2
writer 只有在显式调用 `load-postgres --confirm-write` 且提供数据库 URL 环境变量时才会
打开 PostgreSQL 连接；默认命令不会连接数据库。数据库仍然只是 canonical release 的
派生查询层；校验、离线 fake 测试通过不等同于已经部署或已经写入 Neon。

## 运行

在仓库根目录执行：

```bash
python3 scripts/import_bted_v03.py validate \
  --release-root data/public/v0.2.0
```

命令在标准输出打印 JSON。`ok=true` 表示校验通过；`issues` 的每一项都带有
`source_id`、`file`、`line` 和具体问题，便于直接定位原始文件。非零退出码表示存在
问题，不会生成部分导入结果。

如需保存确定性计划：

```bash
python3 scripts/import_bted_v03.py validate \
  --release-root data/public/v0.2.0 \
  --plan-json /tmp/bted-v03-import-plan.json
```

默认会读取仓库内的
`data/registry/reference_contigs.v0.2.0.tsv`。如需审计一个副本，可以显式指定：

```bash
python3 scripts/import_bted_v03.py validate \
  --release-root data/public/v0.2.0 \
  --contig-registry /path/to/reference_contigs.tsv
```

测试 fixture 或复制出的 release 可以用 `--repo-root` 指定 registry 和来源 manifest
所在的仓库根目录：

```bash
python3 scripts/import_bted_v03.py validate \
  --repo-root /path/to/fixture \
  --release-root /path/to/fixture/data/public/v0.2.0
```

## 校验边界

校验器会读取：

1. `release_manifest.json`、22 个来源 entry 和
   `data/registry/batter_s1_source_registry.tsv`；
   根 `release_version` 必须符合 `vMAJOR.MINOR.PATCH`，例如 `v0.2.0`；
2. 每个 entry **声明并通过 checksum 校验的**
   `data/public/v0.2.0/records/BATTER_S1_NNN/manifest.json`（且 `record_root` 不能
   指向 registry 或 release 外部目录）。这是导入时的 canonical
   source manifest；`data/registry/manifests/BATTER_S1_NNN.json` 只是旧 registry
   audit 副本，用来交叉核对，不能替代 record 内的 manifest。canonical manifest 的
   `release_version` 也必须与根 release 一致；
3. 每个 source 至少声明并实际提供 `manifest.json`、`fields.json`、
   `SHA256SUMS.txt`。`published_standardized` 还必须有 `endpoints.tsv` 和
   `endpoints.bed`；`source_annotations_status=published` 还必须有
   `source_annotations.tsv`。状态为 `withheld_external_link_only` 的来源不因为缺少
   附表而失败；
4. 每个 source 的 `SHA256SUMS.txt`。文件名必须在 release entry 中声明，摘要必须同时
   与实际文件和 release entry 中的 SHA-256 相同；除 checksum 文件自身外，所有声明的
   发布文件都必须出现在该清单中；
5. 已发布 source 的 24 列 `endpoints.tsv` 与 `endpoints.bed`。
6. `data/registry/reference_contigs.v0.2.0.tsv`（或 `--contig-registry` 指定的副本）。
   该小表由 `scripts/build_reference_contig_registry.py` 从既有的 v0.2 JBrowse release
   bundle 生成，不下载新参考序列，也不从端点最大坐标猜长度。生成器要求每个 published
   source 的 config 使用带来源前缀的 `IndexedFastaAdapter`，FAI 中精确存在 endpoint
   contig，并且 FASTA/FAI/config 的摘要与 bundle 根 `SHA256SUMS.txt` 一致。

参考 contig 注册表会进一步检查：它与 canonical endpoint 的 `(assembly, contig)` 集合
恰好相同；`length_bp` 大于或等于该 contig 的最大 1-based endpoint 坐标（endpoint 可以
正好位于 contig 的最后一个碱基）；共享 contig 的
supporting source、FASTA/FAI 摘要、生成器和 UTC 时间等 provenance 字段有效。FASTA/FAI
文件仍不进入 Git，也不会被 canonical `assets` 计划复制；注册表只保存可复核的来源和
checksum。

需要可重复生成同一 provenance 时间时，可以固定生成时间：

```bash
python3 scripts/build_reference_contig_registry.py \
  --release-root data/public/v0.2.0 \
  --jbrowse-bundle /path/to/BTED-v0.2.0-jbrowse \
  --generated-at-utc 2026-08-21T00:00:00Z
```

每个 endpoint 行检查：

- `source_id`、非空 `sample_id`、带来源前缀的 `end_id` 和重复键；
- `strand` 必须为 `+`/`-`；
- 1-based 位置与 BED 的严格关系：`start = position - 1`、`end = position`；
- endpoint evidence 必须属于 `observed_signal`、`called_endpoint`、
  `author_called_endpoint`、`curated_record`，并与来源 evidence 一致；
- endpoint 中的 PMID/DOI 必须与 registry 中的来源论文一致；
- BED6 行必须与同一行 TSV 的 contig、坐标、ID 和链方向一致；不跨 contig 合并。

`source_annotations.tsv` 只用稳定 `end_id` 做外键检查；它可以有来源特异列，但不能把
预测或混合证据提升为 endpoint evidence。`BATTER_S1_002` 保持 `audit_only`：必须是
零记录、无 endpoints 文件、无 JBrowse 配置；即使它的审计 metadata 存在，也不能在本
阶段生成伪端点。

此外，release 与 registry 的 source 集合必须完全相同。相同 PMID 的 canonical/audit
manifest 必须保持 DOI、标题和年份一致；相同带版本 assembly 也必须保持 species 一致。
这些比较是审计约束，不会根据某一份冲突文件猜测正确值。

## 当前 v0.2.0 校验结果

校验器从真实文件得到以下数字（不是手工写入）：

| 项目 | 数量 |
| --- | ---: |
| 来源 | 22 |
| `published_standardized` 来源 | 21 |
| `audit_only` 来源 | 1（S1_002） |
| 公开 endpoint | 28,399 |
| augmentation `TRUE` / `FALSE` | 19 / 3 |
| publication | 13 |
| reference assembly | 20 |
| endpoint contig | 47 |
| sample context | 21 |
| source accession | 32 |
| source annotation 文件 / 行 | 17 / 24,887 |

参考 contig 注册表已由现有 v0.2 JBrowse bundle 的 21 套 source config、FAI 和根
`SHA256SUMS.txt` 生成，覆盖全部 47 个 endpoint contig；因此当前真实 v0.2.0 plan 已
包含 `length_bp` 和对应 provenance，且 `postgresql_ready=true`。这不是一次新的参考
序列下载：注册表只是把既有发布资产的可复核长度和 checksum 提升为查询层元数据。

## import plan 的含义

`plan` 是将来写入 schema 的**行数与键摘要**，不是数据库快照，也不代表已经执行
INSERT。它包含 `release_versions`、`import_runs`、`publications`、`assemblies`、
`contigs`、`sources`、`source_accessions`、`samples`、`endpoints`、
`source_annotations`、`genes`、`endpoint_gene_context` 和 `assets` 的确定性统计；大型
endpoint/annotation 键集合以数量、首尾样本和集合 SHA-256 表示，避免把 28,399 条 ID
复制到一次命令输出中。`write_mode` 固定为 `not_written`。`canonical_validation_status`
单独表示 canonical 校验是否通过；`postgresql_ready` 则表示是否满足实际 schema 的
写库前提，不会因为校验通过就默认为 true。

`import_runs` 记录 release 版本和 release manifest SHA-256，状态为 `validated` 或
`failed`，但不会执行 INSERT。`assets` 只列出 release entry 已声明、实际存在、SHA-256
已验证且不超过 50 MiB 的小型 canonical 文件；每项含不带 `/` 的稳定 `asset_id`、逻辑
路径、来源、类型、摘要、字节数和 schema 对应的 `is_public` 标记，不生成 HF/origin URL。
`asset_kind` 使用数据库允许的枚举（如 `bed`、`metadata`、`checksum`）；`endpoints.bed` 映射为 `bed`，`SHA256SUMS.txt` 映射为
`checksum`，其它当前 JSON/TSV 映射为 `metadata`。`genes` 和
`endpoint_gene_context` 在本里程碑明确为零行。

`source_accessions` 与 schema 对齐，使用 `accession_namespace`，同时保留 `accession` 和
`raw_value`，并记录 `accession_type=study` 与 ordinal。namespace 映射为：`GSE → GEO`、
`SR* / PRJNA → SRA`、`PRJEB → ENA`、`E-MTAB → BioStudies`（另记录 `ArrayExpress`
别名放在 plan metadata 中，不作为物理列）。未知前缀只进入 `unresolved`，不会猜测数据库。

当前真实 v0.2.0 的 `canonical_validation_status=validated`，且
`postgresql_ready=true`：47 个 contig 的 `length_bp` 均由既有 JBrowse FAI 核实并通过
checksum/provenance 检查。`postgresql_ready` 仍只表示满足写库前预检，不表示已经执行
PostgreSQL INSERT。

未来的 PostgreSQL importer 必须把该 plan 作为 staging 预检，然后按
`release -> publication/assembly -> source/accession/sample -> endpoint/annotation ->
asset` 顺序写入一个新的 release，并在事务内切换 published 状态。当前实现刻意不做
psycopg、Neon、Render 或生产写库。

## 第三阶段 B1：确定性 PostgreSQL 行物化包

`backend/importer/materialize.py` 提供真正写库前的第二层中间产物。它先重新运行
canonical validator；只有 `ok=true` 且 `postgresql_ready=true` 时才生成文件。它不使用
psycopg、不连接数据库、不发起网络请求，也不修改 `data/public/v0.2.0`。

```bash
python3 scripts/import_bted_v03.py materialize \
  --release-root data/public/v0.2.0 \
  --output-dir /tmp/bted-v03-staging \
  --asset-origin-base https://example.test/assets \
  --generated-at-utc 2026-08-21T00:00:00Z
```

默认不接入大型浏览器对象，继续生成 127 个 canonical 小型资产。需要把已经审计的
JBrowse 资产清单纳入同一个 staging bundle 时，必须显式传入 tracked inventory：

```bash
python3 scripts/import_bted_v03.py materialize \
  --release-root data/public/v0.2.0 \
  --output-dir /tmp/bted-v03-staging-with-browser \
  --asset-origin-base https://example.test/assets \
  --generated-at-utc 2026-08-21T00:00:00Z \
  --jbrowse-asset-inventory data/registry/jbrowse_assets.v0.2.0.tsv
```

当前 inventory 有 105 行：19 个 published assembly 的 76 个去重 FASTA/FAI/GFF3/TBI、
21 个 canonical `records/<source>/endpoints.bed` 和 4 个 Rend-seq 来源的 8 个 raw
forward/reverse BigWig。21 个 BED 使用相同 `logical_path` 替换原 canonical asset 行，
不会重复计数，因此最终 `assets.jsonl` 为 `127 - 21 + 105 = 211` 行。参考资产只关联
assembly；BED/BigWig 只关联 source；S1_002 不产生浏览器资产。

所有资产统一以 `logical_path` 生成计划 origin URL，即
`<asset_origin_base>/<logical_path>`；browser inventory 的 `object_path` 在物化后就是对应
`logical_path`。目录层级会保留，`asset_id` 只作数据库/API key，绝不替代远端对象路径。
物化阶段的默认状态仍记录为
`asset_origin_status=planned_not_verified`，所有资产 `supports_range=false`；这是上传前
bundle 的安全默认值。当前 canonical `release_version=v0.2.0` 的 public object handoff
已经在 Hugging Face dataset `seu-yolo/BTED-v0.3-assets` 的固定 revision
`463cfc8bd582a5ed9d2c426822148c3f1e56c4d0` 完成 208/208 HEAD 200 + Range 206 审计，证据
位于 `data/registry/remote_asset_audit.v0.2.0-hf.json`。只有使用该报告离线 apply 生成的
新 bundle 才能写成 `asset_origin_status=verified`；TSV 中
`external_link_only` 行必须 `is_public=false`；这一步只准备可审计写库行，不表示 URL
自动代表 JBrowse 或数据库已经上线。

`--output-dir` 和 `--asset-origin-base` 都必须显式给出；非空目录拒绝覆盖。origin 只
是未来服务层的 HTTPS 计划前缀，bundle 把状态写为 `planned_not_verified`，不表示远程
对象已经存在或可访问。物化行的 `supports_range` 默认是 `false`；只有未来对象上传后
通过 HTTP 206/Range 审计，资产注册阶段才可以改为 `true`。生成器先写临时目录，完成 checksum 后原子改名；固定同一个
`--generated-at-utc` 可得到相同内容和 SHA-256。

输出目录包含每张表一个 JSONL、`manifest.json` 和 `SHA256SUMS.txt`。当前真实 v0.2.0
未传入浏览器 inventory 时，物化行数为：`release_versions` 1、`import_runs` 1、`publications` 13、`assemblies` 20、
`contigs` 47、`sources` 22、`source_accessions` 32、`samples` 21、`endpoints` 28,399、
`source_annotations` 81,477、`genes` 0、`endpoint_gene_context` 0、`assets` 127。
附表的 81,477 行来自按字段证据角色分组后的行：每个原始附表行可以产生多个
`experimental_measurement`、`author_annotation`、`prediction_annotation` 或
`curation_metadata` 行；字段值在各自的 `annotation_json` 中保留。每条行级
`provenance_json` 只保留来源文件、行号、source record、endpoint evidence、未映射
helper 列和必要的证据边界；标准角色已经由 `annotation_kind` 表示，不重复嵌入整组
`field_roles`/`field_definitions`。`author_called_endpoint` 映射为
`author_annotation` 时，行级 provenance 只保留一个紧凑的
`original_evidence_roles` 映射。每个来源的完整字段字典、`fields.json` 摘要以及
`source_annotations.tsv` 的摘要只在物化 `manifest.json` 的
`annotation_field_provenance` 中登记一次。这样仍能联合 `annotation_json` 覆盖所有
原始附表列，同时避免 81,477 行重复字段定义。`author_called_endpoint` 角色不会重复
制造实验 endpoint；预测字段也不会改变核心表的 `evidence_class`。每个来源的原始
附表表头都由测试与物化前检查覆盖，禁止静默丢列。

当前真实 bundle 的 `source_annotations.jsonl` 约 77 MiB、总目录约 115 MiB，分别低于
100 MiB 和 150 MiB 的回归阈值；旧实现把字段字典重复写入每条行级 provenance，单个
附表文件约 248 MiB，因此体积阈值用于防止这一类可避免的元数据膨胀，而不是丢弃数据。

JSONL 中带 `_ref` 的键是给下一阶段 writer 使用的自然键辅助列，不是 schema 中新增的
物理列：例如 `source_id_ref`、`assembly_id_ref`、`contig_id_ref` 和 `sample_id_ref`。
writer 应先解析这些键得到 PostgreSQL identity，再按外键顺序插入。核心 endpoint 的
24 列原值全部保留；坐标三个整数转为 JSON 数字。当前物化的 `assets.asset_kind` 使用
schema 已允许的 `bed`、`metadata`、`checksum` 等枚举；`source_annotations.tsv` 作为
metadata asset，不添加 schema 没有的 `source_annotation` 枚举。`origin_status` 只存在
bundle manifest 的 `asset_origin` 对象中，不写进 assets 行；source accession 的
`ArrayExpress` 只是 URL/namespace 解释，不作为额外物理列。

S1_002 仍为 `audit_only`：物化中保留 source/publication/assembly/accession 等审计行，
但没有 endpoint、source annotation 或 JBrowse 资产入口。物化 manifest 记录 canonical
release checksum、reference-contig registry checksum、表行数与表 checksum、自然键模式、
origin 计划状态和 unresolved；`write_mode` 始终为 `not_written`。

### GFF-derived genes（可选查询层）

默认 materialization 继续保持 `contigs=47`、`genes=0`。需要导入真实 GFF gene 查询层时，
必须同时提供 tracked inventory 和本地 bundle root：

```bash
python3 scripts/import_bted_v03.py materialize \
  --release-root data/public/v0.2.0 \
  --output-dir /tmp/bted-v03-staging-with-genes \
  --asset-origin-base https://example.test/assets \
  --generated-at-utc 2026-08-22T00:00:00Z \
  --jbrowse-asset-inventory data/registry/jbrowse_assets.v0.2.0.tsv \
  --jbrowse-bundle-root /path/to/BTED-v0.2.0-jbrowse
```

`--jbrowse-bundle-root` 没有 inventory 时会被拒绝；只有 inventory 而没有 bundle root
时仍只合并 browser assets，不读取 GFF，genes 保持零行。当前实现只支持已经核验的
gene-only bgzip GFF3 与对应 FAI：对每个 assembly 校验 inventory `bundle_path` 的
存在性、byte size、SHA-256，并要求 GFF/FAI contig 集一致。GFF3 inventory asset 会在
`assets.jsonl` 中先注册，gene 行通过 `annotation_asset_id`/`annotation_sha256` 引用它。

gene 的稳定 ID 是 `<assembly_accession>:<original GFF ID>`。`attributes_json` 保存
GFF3 的 `ID`、`Name`、`gene`、`locus_tag`、`product` 及其它 attributes；标准 GFF3
percent escapes 会 URL-decode 供页面显示，原始文件仍由 registered asset SHA-256 保真。
`gene_name` 优先使用 `gene`，否则 `Name`；`locus_tag` 只取显式 `locus_tag`。gene 行
通过 `assembly_id_ref` 与 {assembly_accession, contig_accession} 的 `contig_id_ref`
连接自然键，不会修改 canonical endpoint contig registry。

真实当前 bundle 的结果是 49 contigs、95,437 genes、0
`endpoint_gene_context`。GCF_000008685.2 的 `NC_000957.1` 与 `NC_001904.1` 仅由
FAI/GFF 派生并补入 gene query layer，canonical v0.2 registry 仍为 47 行。5 条环状
replicon 的 GFF3 unrolled `end` 超过线性 FAI 长度；它们保留原始 start/end，并在
`attributes_json` 增加 `_bted_coordinate_note` 与 `_bted_contig_length`，不裁剪坐标。
这不是 endpoint evidence，也不计算任何 gene context。manifest 顶层记录
`gene_count`/`endpoint_gene_context_count`，`gene_import` 记录 assembly、contig 和
asset provenance。

## 测试

```bash
python3 -m unittest -v tests/test_bted_v03_importer.py
python3 -m unittest -v tests/test_bted_ingestion.py
python3 -m unittest discover -s tests -p 'test*.py' -v
git diff --check
```

测试包含真实 v0.2.0 happy path（47 个 contig/ready）、既有 JBrowse bundle 的真实 registry
构建，以及只复制少量文件到临时目录后模拟的坐标错误、
annotation orphan、audit-only 错误 endpoint、release row-count mismatch、canonical
manifest 篡改、必要文件缺失/未声明、SHA256SUMS 不一致、registry extra source、相同
PMID 元数据冲突、未声明 checksum 条目、错误 release version 和 CLI plan 输出；不会复制
整个大型 release，也不会修改仓库内的原始数据。builder 测试还覆盖 tiny FAI、共享
contig 长度冲突、缺失/额外 contig 和 bundle checksum 失败。

## 第三阶段 B2：PostgreSQL 事务 writer

`backend/importer/postgres.py` 读取 B1 bundle，并在真正写库前重新执行 bundle、checksum、
JSONL 行数、schema 字段 allowlist 和自然键闭包检查。它不会读取或修改 v0.2 canonical
目录，也不会下载参考序列或资产。B2 的目标是提供一个可审计的写库边界；当前工作树
没有 PostgreSQL/psycopg3 服务，因此下面的事务行为只由离线 fake connection 测试验证。

先做纯本地验证：

```bash
python3 scripts/import_bted_v03.py verify-bundle \
  --bundle-dir /tmp/bted-v03-staging
```

验证会拒绝根目录额外文件、目录或符号链接，也拒绝预期文件的符号链接；每个 JSONL
按流式方式读取，不将 28,399 个 endpoint 或 81,477 个附表行一次性装入内存。`NaN`、
`Infinity` 等非标准 JSON 数值也会被拒绝。`assets.origin_url` 必须是 HTTPS，且主机名
必须与 `origin_host` 相同；当 bundle 的 `asset_origin_status=planned_not_verified`
时，所有资产的 `supports_range` 必须为 `false`。这表示远端对象和 HTTP Range 尚未
验证，不能把计划 URL 当成已上线服务。

离线 writer 测试入口：

```bash
python3 -m unittest -q tests/test_bted_v03_postgres.py
```

正式写库需要显式确认、显式环境变量和 psycopg3：

```bash
export BTED_DATABASE_URL='postgresql://user:password@host/dbname'
python3 scripts/import_bted_v03.py load-postgres \
  --bundle-dir /tmp/bted-v03-staging \
  --confirm-write \
  --batch-size 1000
```

也可以用 `--database-url-env NAME` 指定其它环境变量。URL 只从环境变量读取，不写入
日志或 bundle；没有 `--confirm-write`、没有环境变量或没有 psycopg3 时命令会安全失败，
且不会开始事务。项目只声明依赖于 `requirements-v03.txt`，本轮不自动安装依赖。

writer 的事务顺序为：

`release_versions → import_runs → publications/assemblies → contigs → sources →
source_accessions/samples → endpoints → source_annotations → assets → genes → count audit →
import_run=committed`

当 `genes.jsonl` 非空时，writer 在 preflight 验证 assembly/contig natural refs、1-based
start/end 顺序、`+/-` strand、GFF3 asset kind 和 SHA-256 后批量写入；assets 必须先于
genes 进入数据库以满足 annotation asset 外键。`endpoint_gene_context.jsonl` 在本版本
仍必须为空，count audit 会明确核对该零值。gene 是 GFF-derived 查询层，不改变 canonical
endpoint 或其 evidence boundary。

事务开始后设置 `SERIALIZABLE` 和 advisory transaction lock；endpoint/annotation 等大表
按 `--batch-size` 使用参数化 `executemany`。任何异常都会 rollback，代码不包含
`DROP`、`TRUNCATE` 或无条件 `DELETE`。同一 `release_version` 已存在时整批拒绝；已有
publication、assembly 或 contig 只有在自然键对应的全部字段兼容时才复用 identity，冲突
会失败，不静默更新。写入前和写入后的 count audit 都检查全局表计数，以及每个 source
的 `sources.record_count == endpoints` 和 source annotation 行数；非 `published_standardized`
来源不能出现 endpoint/sample 行，S1_002 继续保持零 endpoint/零附表。

`load-postgres` 只会把当前 bundle 作为 staged/validated release 写入，且
`is_current=false`；`planned_not_verified` 不代表远端资产可发布。独立的 promotion 命令：

```bash
python3 scripts/import_bted_v03.py promote-postgres \
  --bundle-dir /tmp/bted-v03-staging \
  --confirm-promote
```

promotion 同样需要数据库环境变量，并且只有在 bundle 和最新 committed import run 的
`asset_origin_status` 都明确为 `verified`、计数审计通过时才允许；当前 v0.2 bundle 是
`planned_not_verified`，因此 promotion 必须被拒绝。远程资产的存在性和 HTTP 206 Range
能力需要另行审计并生成新的 verified bundle，不能由 writer 猜测。

远端审核通过后，不手工修改 JSONL。使用 report-driven 离线步骤生成新的 verified bundle：

```bash
python3 scripts/apply_v03_remote_asset_audit.py \
  --bundle-dir /tmp/bted-v03-staging-with-browser \
  --remote-audit /path/to/REMOTE_ASSET_AUDIT.json \
  --output-dir /tmp/bted-v03-verified
```

该命令可直接从仓库根目录按上述形式运行；脚本会像主 `import_bted_v03.py` CLI 一样先将
仓库根加入 Python module search path，不要求预先安装 BTED 为 Python package。

该步骤从 materialized `assets.jsonl` 选择全部 `is_public=true` 且
`redistribution_status=verified_redistributable` 的 required asset。当前 211 行中共有
208 行：105 个 browser asset 加 103 个 canonical metadata/checksum/annotation 等小文件。
tracked inventory 仅对 105 个 browser asset 做额外 provenance 核对，不能代替完整 required
集合。audit 中 208 个对象必须与物化行的 `asset_id`、`object_path`/`logical_path`、
`byte_size`、`sha256` 完全一致，且 HEAD/Range 均通过。只有全部满足时才把这些行的
`supports_range` 设为 `true` 并将 manifest 的
`asset_origin_status` 改为 `verified`；private/`external_link_only` 行保持 `false`。
脚本不联网、不上传、不连接数据库，输出到新的空目录并重建 checksum。

### B2 的边界

- `verify-bundle` 是本地文件验证，不是数据库连接测试。
- fake connection 的 happy path、批量、rollback、自然键复用/冲突和 promotion 拒绝测试
  通过，不等同于目标 PostgreSQL 版本上的 DDL/权限/网络 smoke test。
- 真实写库前仍需在隔离 PostgreSQL 实例执行 `schema.sql`，用不含生产凭据的测试 URL
  运行一次 load、重复 release 拒绝、事务回滚和 count audit，再决定是否接入 API。
- writer 不发布新的生物学解释；24 列 endpoint、证据类别、来源附表和坐标仍以 canonical
  release 为准，预测/混合证据不会升级为实验 endpoint。
