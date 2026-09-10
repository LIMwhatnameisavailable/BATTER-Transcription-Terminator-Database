# BTED v0.3 数据库骨架

**部署状态：** 本 PostgreSQL/Neon schema 与 writer 是保留的 future/alternative path；当前
preview 使用 `prototype/accession-range/schema.sql` 的 Cloudflare D1 投影和
`scripts/generate_bted_d1.py`，不依赖 PostgreSQL、Neon 或 Render。

`schema.sql` 是 BTED v0.3 PostgreSQL 派生查询层的初始 DDL。它只定义表、约束、索引和
阻止非法公开 endpoint 的触发器，不导入数据，也不连接 Neon/Render。科研真源仍是
版本化 canonical release（manifest、24 列 `endpoints.tsv`、来源附表、BED、字段清单和
checksum）。数据库中的每个值都应该能沿 `release_version -> import_runs -> source /
endpoint / asset` 路径回到该 release。

## 表的用途

骨架覆盖：

- release/import provenance：`release_versions`、`import_runs`；
- 文献和参考：`publications`、`assemblies`、`contigs`；
- 来源和实验语境：`sources`、`source_accessions`、`samples`；
- 核心数据：保留 v0.2 全部 24 列的 `endpoints`，来源特异 JSONB 的
  `source_annotations`；
- 将来关联：`genes`、`endpoint_gene_context`（第一里程碑不计算 gene context）；
- 下载/浏览器对象：带 checksum、byte size、许可和 Range 标记的 `assets`。

endpoint 的 `evidence_class` 只接受 `observed_signal`、`called_endpoint`、
`author_called_endpoint`、`curated_record`。`author_integrated_mixed_evidence` 和
`prediction_only` 可以作为 source 审计状态或 JSONB 的预测注释被记录，但不能成为公开
endpoint 行。`BATTER_S1_002` 可有 source/manifest/accession 审计信息，但 audit-only
约束和触发器禁止它产生 endpoint、下载或 JBrowse 入口。

## 未来 importer 的安全流程

1. 读取 canonical release manifest，建立新的 `release_versions` 和 `import_runs`，
   将数据写入隔离的 staging schema/数据库；不要先修改当前 published release。
2. 按 publication → assembly/contig → source → accession/sample → endpoint/
   source_annotations → gene/asset 的顺序加载。每个输入文件保存路径、行引用、字节
   数、SHA-256 和许可状态；每个 endpoint 必须有 NOT NULL `sample_pk`，通过复合外键
   绑定同一 source 的 sample。
3. 在 staging 中运行 24 列表头/行数、坐标换算、strand、contig、evidence、
   `end_id`、source 状态、19/3 augmentation 计数和 assets checksum 校验。相同
   release/manifest 在 importer 修复后可以重新建立新的 `import_runs`，不能因历史
   失败 run 被唯一约束阻塞。任何
   失败都保留 `import_runs.run_status = failed` 与错误摘要，不删除审计记录。
4. 只有整批校验通过后，才在一个事务中把 run 标为 `committed`，并把新的 release
   置为可查询/当前版本；旧 release 保持只读。API 不应在事务中看到一半导入的数据。
5. 重新运行静态 schema 测试、`tests/test_bted_ingestion.py` 和 release/asset 校验，
   再允许应用层切换默认 release。

## 明确禁止

- 不在生产库执行 `DROP DATABASE`、`DROP TABLE`、`TRUNCATE` 或无 release 条件的
  `DELETE` 来“刷新”数据；
- 不在 v0.2.0 表/目录上原地覆盖值，修订必须生成新 release 并保留差异；
- 不用数据库中的手工修正覆盖 canonical release，不把预测输出补进实验 endpoint；
- 不接受任意 `?url=` 作为 asset origin。资产只能从 `assets` 中的登记和 checksum
  生成同源 `/api/v1/assets/{asset_id}` 代理。完整 SHA-256 在资产登记/import 阶段复算；
  每次 partial request 只校验 allowlist、登记 byte size、Content-Range 和返回长度；
- 不在第一里程碑导入 NCBI 新数据、外部协作者来源、gene clusters、Rfam 或训练
  endpoint 标签。

## 当前验证范围

本目录不要求本机安装 PostgreSQL。`schema.sql` 由静态 unittest 检查关键表、24 列
映射、release/source/contig/sample 外键、19/3 augmentation 边界和 prediction evidence
拒绝规则；未来连接 Neon 前还需要在目标 PostgreSQL 版本执行 DDL 并补充迁移 smoke test。

## v0.3 只读导入预检

第二里程碑新增 `backend/importer/canonical.py` 和
`scripts/import_bted_v03.py`。它们只读取 canonical release，先解析并 checksum 验证
每个 release entry 声明的 `records/<source>/manifest.json`，再验证 registry 交叉审计、
24 列 endpoint、BED 坐标、证据类别、论文 PMID/DOI、来源附表外键、所有发布文件的
`SHA256SUMS.txt` 以及 S1_002 的 audit-only 边界；不会连接 PostgreSQL，也不会写入任何
表。运行方式和错误定位见 [`docs/v0.3/importer.md`](../../docs/v0.3/importer.md)。

```bash
python3 scripts/import_bted_v03.py validate \
  --release-root data/public/v0.2.0 \
  --plan-json /tmp/bted-v03-import-plan.json
```

输出的 `plan` 只是一份确定性的未来写库行数/键摘要，`write_mode` 为
`not_written`；它不是 PostgreSQL 快照，且明确包含 `import_runs`、`assets`、零行的
`genes`/`endpoint_gene_context`。当前真实 v0.2.0 预检为 22 个 source、21 个
published、1 个 audit-only、28,399 条 endpoint，publication/assembly/contig/sample/
accession/source-annotation 数量分别为 13/20/47/21/32/17 个文件（24,887 行附表），
并规划 127 个已验证的小型 canonical assets。47 个 contig 的长度和 provenance 已由
现有 v0.2 JBrowse release bundle 中的 FAI、config 和根 `SHA256SUMS.txt` 交叉核实，并
保存为 `data/registry/reference_contigs.v0.2.0.tsv` 及其 JSON provenance；没有下载新
参考序列，也没有从 endpoint 最大坐标猜测长度。因此当前
`canonical_validation_status=validated` 且 `postgresql_ready=true`，但这仍只表示满足
写库前预检，不表示已经执行 INSERT。缺少或不通过该 registry 时，canonical 校验仍可
保持 validated，但 `postgresql_ready=false`。长度边界允许 endpoint 正好落在 contig
最后一个碱基上，即 `length_bp >= max_endpoint_position_1based`。

plan 中的 assets 使用无 `/` 的稳定 asset_id、schema 允许的 `asset_kind` 和 `is_public`
字段；source accession 使用 `accession_namespace`，不把别名当作物理列。参考 FASTA/FAI
不进入 Git 或当前 canonical asset 计划，registry 只记录可复核的 asset basename 和
checksum。builder 和检查命令见 [`docs/v0.3/importer.md`](../../docs/v0.3/importer.md)。

## B1 行物化（仍未写库）

第三阶段 B1 在 `backend/importer/materialize.py` 中把通过上述校验、且
`postgresql_ready=true` 的 release 物化为确定性的 JSONL staging bundle。它覆盖
schema 中的 release/import、publication、assembly/contig、source/accession/sample、
endpoint、source annotation、asset 以及明确的零行 gene/context 表；当前真实快照的
行数为 `1/1/13/20/47/22/32/21/28,399/81,477/0/0/127`。它不安装或调用 psycopg，不
连接 PostgreSQL，也不下载远程对象。

运行时必须显式指定空的输出目录和 HTTPS `--asset-origin-base`。origin 仅用于生成未来
同源代理的计划 URL，manifest 标为 `planned_not_verified`，不代表对象已经上线。固定
`--generated-at-utc` 后，同一 canonical release 可复建相同 checksum；非空目录不会被覆盖。
在远端对象通过 HTTP 206/Range 审计之前，物化 `assets.supports_range` 固定为 `false`，
不从本地文件或计划 URL 推断远程能力。

JSONL 保留 schema 对应字段，并额外提供 `source_id_ref`、`assembly_id_ref`、
`contig_id_ref`、`sample_id_ref` 等自然键辅助列，供下一阶段 writer 解析 identity 外键；
这些 `_ref` 不是数据库新增列。来源附表按 `fields.json` 的 evidence role 分组进入
`annotation_json`，预测角色保持 `prediction_annotation`，不会升级 endpoint 证据。原始
附表的所有列至少出现在一个分组 JSON 中；`provenance_json` 保存来源文件、行定位、
未映射 helper 列和必要的证据边界，不在每行重复整组字段字典。标准角色由
`annotation_kind` 表示；只有 `author_called_endpoint → author_annotation` 的容器映射
保留紧凑的 `original_evidence_roles`。完整字段定义及 `fields.json`/`source_annotations.tsv`
的摘要在物化 manifest 的 `annotation_field_provenance` 中按 source 各登记一次。
`source_annotations.tsv` 属于 schema 已有的 `metadata` asset_kind，不会引入
`source_annotation` 枚举；`assets` 行也不添加只用于 bundle 的 `origin_status`。

当前真实 v0.2.0 的物化 bundle 中，`source_annotations.jsonl` 约 77 MiB、总目录约
115 MiB；测试将其限制在 100 MiB/150 MiB 以下，以防止重复 provenance 再次导致不必要
的体积增长。该限制不改变 81,477 条附表分组行或其原始字段覆盖。

物化输出是可审计中间层，不是 PostgreSQL 快照，不表示已经执行 INSERT。真正 writer 仍
需在新 release 的 staging schema 中按外键顺序插入，并在单事务中切换发布状态。

## B2 PostgreSQL writer（离线实现，未做真实 DB smoke test）

`backend/importer/postgres.py` 是 B1 JSONL bundle 到 PostgreSQL 的事务写入边界。它先
流式验证 bundle 根目录、SHA256SUMS、表文件 checksum/行数、物理列 allowlist、自然键
和外键闭包，再打开事务。`verify-bundle` 始终是纯本地命令；`load-postgres` 只有同时
提供 `--confirm-write` 和显式数据库 URL 环境变量时才会尝试导入 psycopg3。URL 不写入
日志、测试输出或 bundle。依赖声明见仓库根目录的 `requirements-v03.txt`，本轮不自动
安装依赖。

写入顺序固定为 release/import run、publication/assembly、contig、source、accession/
sample、endpoint、source annotation、asset，最后做全局及逐 source 计数审计并把 run
标为 `committed`。事务使用 `SERIALIZABLE` 和 advisory transaction lock，批量行使用
参数化 SQL；任何错误 rollback，代码不使用 `DROP`、`TRUNCATE` 或无条件 `DELETE`。已有
publication/assembly/contig 只有自然键对应字段全部兼容时才复用，不做静默 UPDATE；已有
release 则拒绝整批导入。

B1 的 `planned_not_verified` origin 可以进入 staged/validated、`is_current=false` 的
release，但不能 promotion。`promote-postgres` 还要求 bundle 与最新 committed run 的
`asset_origin_status=verified`，并再次通过全局和逐 source endpoint/annotation 计数审计。
在远端对象完成 HTTP 206/Range 审计前，`supports_range=false` 不是已验证的远端能力。

目前 writer 只由离线 fake connection 覆盖 happy path、批量、回滚、自然键冲突和 promotion
拒绝；这不等同于目标 PostgreSQL 版本上的 DDL、权限、连接和网络 smoke test。真正接入 API
前，应在隔离 PostgreSQL 实例执行 `schema.sql` 并用测试凭据验证一次完整 load/重复 release
拒绝/回滚/count audit。writer 只搬运 canonical release 的已确认数据，不新增生物学解释，
也不把预测或混合证据提升为实验 endpoint。

## C1/C2 只读查询层（已实现，仍不写库）

`backend/app/` 提供一个不修改数据库的查询层：`ReadService` 负责 release 选择、公开证据
边界、分页和响应结构，`PostgresReadRepository` 只执行参数化的 SELECT。每次 repository
操作独立创建并关闭连接；排序字段来自固定白名单，查询参数不能成为 SQL 片段。
`backend/app/main.py:create_app()` 是 FastAPI app factory，可以注入 fake repository 做离线
契约测试，也可以在安装 `requirements-v03.txt` 后从 `BTED_DATABASE_URL` 创建生产 repository。

C1 已覆盖 health、stats、sources、assemblies、endpoints、genes、来源级 augmentation，
以及 endpoint 的流式 TSV/BED6 下载。默认查询 current published release，显式未知版本返回
404。endpoint JSON/TSV 保留 v0.2 全部 24 列；BED6 使用
`start = biological_coordinate_1based - 1`、`end = biological_coordinate_1based`，其
`score` 暂写 `0` 作为 BED6 格式占位，原始 `signal_or_score` 不丢失且不被称为 coverage。
S1_002 继续只返回 source 审计信息，不提供 endpoint、下载或 JBrowse 入口。endpoint 详情
会从 `source_annotations` 返回行数和 annotation kind 摘要；fake repository 没有该摘要时
使用带状态的未实现说明，不填充虚构字段。

C2 已实现不写库的 `/api/v1/assets/{asset_id}` GET/HEAD/单 Range 代理：只读取 published
release 中 `is_public=true` 的登记资产，origin 必须为登记的 HTTPS URL，不能使用任意
`?url=`；JBrowse config 链接也通过该同源入口生成。当前仍不实现真实数据库 smoke test、
写入、Next.js 页面、远端对象 Range 审计或部署。`include_annotations=true` 明确返回 422，
避免在附表许可和导出格式尚未单独审定前把来源特异字段误当作核心 endpoint。FastAPI/uvicorn/
httpx/psycopg3 没有在本环境自动安装；缺少 FastAPI 时 runtime test 会跳过，离线测试通过
不等于 HTTP 或 PostgreSQL 已部署成功。
