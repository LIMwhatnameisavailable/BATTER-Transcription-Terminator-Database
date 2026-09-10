# BTED v0.3 架构契约

**状态：** v0.3.0 Cloudflare developer preview（canonical bundle → D1 import generator、
Cloudflare Worker API、Worker Static Assets、同源 asset proxy、动态 JBrowse config 已实现；
Hugging Face public assets 已在固定 revision 完成远端 Range 审计；Worker/D1 已部署到免费
preview URL，尚不是正式数据 release）
**适用版本：** v0.2.0 与 v0.3.0 并行
**范围：** 当前仓库已经审计的 BATTER S1 内部数据

## 1. 核心决策

BTED 的 canonical release（目前为 `data/public/v0.2.0/`，后续为
`data/public/v0.3.0/`）是科研真源。release manifest、每个来源的
`manifest.json`、24 列 `endpoints.tsv`、`source_annotations.tsv`、BED、字段清单和
SHA-256 组成可下载、可复核的发布边界。发布文件一旦冻结，不能由网页或数据库查询
结果反向改写。

PostgreSQL 是 canonical release 的**派生查询层**，不是第二套科学数据真源。它把
manifest 和发布文件无损映射为可分页、可过滤和可关联查询的关系模型，并保留原始
provenance。每次导入必须绑定 release 版本、输入 manifest checksum 和 import run；
查询层损坏时可以从 canonical release 重建，不能用数据库中手工修改的值覆盖 release。

v0.2 与 v0.3 并行存在：

- v0.2.0 现有静态网站、下载物、JBrowse 配置和 release 资产保持原样，继续提供稳定
  的发布接口；
- v0.3.0 先建立数据库/API 的数据契约，初始内容只来自当前仓库内已经发布或审计的
  BATTER S1 来源，不重新解释端点，也不引入新 NCBI 数据；
- v0.3 的导入、修订和服务切换必须以新的 release version 记录，不能在 v0.2.0
  目录内原地改写；
- 两个版本可以在一段时间内同时被查询或下载。API 响应必须显式返回
  `release_version`，避免客户端把两个版本混成一个集合。

## 2. 当前部署拓扑

当前 preview 的责任边界如下；它是本分支实际执行和 smoke 的部署路径：

| 组件 | 责任 | 不承担的责任 |
| --- | --- | --- |
| Cloudflare Worker | `/api/*` catalogue/source/assembly/endpoint/augmentation API、动态 JBrowse config、登记资产 GET/HEAD/单 Range 代理；非 API 请求交给静态站点 | 不解释论文、不改变 endpoint evidence、不接受任意 URL |
| Cloudflare D1 | canonical `v0.2.0` 的 preview 查询投影：release/publication/assembly/source/accession/track/asset/endpoint；由生成器批次重建 | 不取代 canonical release；不保存当前页面未使用的 `genes` 或 `source_annotations` 行；不做 promotion |
| Worker Static Assets (`site/`) | 复用现有 BTED 静态 UX，使站点和 API 同一 Cloudflare deployment | 不复制科学数据到页面代码，不承担 D1 导入 |
| Hugging Face 资产 | 大型 FASTA/FAI/GFF3/TBI、BED 和小型登记文件的固定 revision `seu-yolo/BTED-v0.3-assets@463cfc8bd582a5ed9d2c426822148c3f1e56c4d0` | 不作为未登记 URL 的开放代理，不改变对象内容；3 个 audit-only/private 对象不上传 |

FastAPI/PostgreSQL/Next.js 代码保留为 future/alternative：它们继续通过现有契约和测试维护，
但不属于当前 Cloudflare deployment 的依赖。旧的 Render/Neon/Vercel 路线已停止，不应在本轮
创建或配置其资源。

请求路径的逻辑关系为：

```text
浏览器 / site/ 静态页面
        │ same-origin /api
        ▼
Cloudflare Worker ── D1 ──> preview catalogue projection
        │
        └── registered public asset + checksum ──> Hugging Face（固定 revision）

canonical release / verified bundle ── generator + SQL batches ──> D1 local/preview
```

这里的“同源”指浏览器看到的资产入口始终是部署域名下的
`/api/v1/assets/{asset_id}`；FastAPI 后端才根据数据库中的登记信息访问允许的
Hugging Face 对象。对象的 byte size、SHA-256、媒体类型、是否支持 Range 和来源/组装
归属均由 `assets` 表记录。完整 SHA-256 在资产登记/import 阶段复算；partial request
只校验 allowlist、登记 byte size、Content-Range 和返回长度，不在每次请求重算整文件。

当前 Worker 只读取 D1 中登记的 public asset key，再根据配置中的固定 HF origin 构造 URL；
请求中的 `?url=`、未登记 key、private asset 和非 allowlisted origin 都被拒绝。D1 的 release
状态明确为 `preview`，保持 canonical `release_version=v0.2.0`，不代表新的 `v0.3.0` 数据
release。完整命令和远程登录边界见 [`deployment.md`](deployment.md)。

浏览器的信息层级、缩放行为、证据措辞和入口布局由单独的
[`browser-ui-contract.md`](browser-ui-contract.md) 冻结；它是 Next.js/JBrowse 实现的
产品契约，不改变本架构的 canonical release 或 evidence boundary。

## 3. 发布和导入边界

### 3.1 canonical release -> database

当前 v0.3 importer 先离线解析并验证 release manifest 与文件，物化为 staging bundle；
PostgreSQL writer 再使用一个 `SERIALIZABLE` transaction 写入。production 表不通过 `DROP` 重置，不在已有版本上
覆盖行。详细的 staging/atomic switch 原则见
[`backend/database/README.md`](../../backend/database/README.md)。

导入时至少保留这些 provenance：

1. release 根 manifest 的路径、版本和 SHA-256；
2. `import_runs` 的输入目录/commit、导入器版本、开始/结束时间、校验结果；
3. source manifest、publication、raw accession、assembly/contig 和 sample 的稳定
   关联；
4. 每个 endpoint 的原 24 列、`source_table_or_file`、`original_row_reference`、
   `coordinate_interpretation`、`qc_status` 和 `note`；
5. `source_annotations` 的来源特异 JSONB 和原表行引用；
6. 可下载/浏览器资产的对象地址（仅登记后的地址）、checksum 和 Range 能力。

### 3.2 科学边界

数据库层保持 v0.2 的证据分层：`observed_signal`、`called_endpoint`、
`author_called_endpoint` 和 `curated_record` 才能出现在公开 `endpoints`。预测字段可
作为 `source_annotations` 的 `prediction_annotation`，但不得提升端点证据，也不得
生成公开预测 endpoint。`author_integrated_mixed_evidence` 与 `prediction_only` 在
公开 endpoint 表中被拒绝；不能拆分的混合来源停留在 source 的 `audit_only`、
`to_review` 或 `blocked` 状态。

`BATTER_S1_002` 是这一规则的具体例子：其作者摘要把多个实验系统整合在一起，当前
逐记录实验 provenance 无法可靠拆开。因此 v0.3 可以保存 publication、source、raw
accession、manifest 和审计备注，但该 source 不得有 endpoint 行、endpoint 下载或
JBrowse deep link。

Table S1 的 `used_for_batter_augmentation` 是**来源级**布尔字段。当前 22 个 BATTER
S1 来源中 19 个为 `TRUE`、3 个为 `FALSE`；它不表示 19 个来源的每一条端点都已经
逐条进入训练集，也不表示数据库会发布训练样本。v0.3.0 的 augmentation API 只返回
这 19 个来源的登记和 provenance；gene clusters、Rfam 和逐端点训练标注不在本里程碑。

## 4. v0.3.0 明确范围

本版本只导入当前 BTED 仓库内的 BATTER S1 数据和其发布/审计元数据：22 个来源、
21 个 `published_standardized` 来源和 1 个 `audit_only` 来源的状态边界由
`data/public/v0.2.0/release_manifest.json` 冻结。这里的“当前内部数据”包括已有的
canonical 小表及其 provenance，不包括重新下载的原始测序数据。

外部协作者数据、尚未通过 BTED 证据/参考/坐标/许可检查的来源、未审计的 NCBI 新
数据、预测位点、gene clusters、Rfam 和 gene-context 计算均不在 v0.3.0 第一里程碑。
后续若接入，必须先生成新的 source manifest 和 processing record，经过单独审核后
增加 release version；不能借助数据库表的空字段先行发布。

## 5. 兼容性与不可变约束

- biological coordinate 永远是 1-based；单碱基 BED 永远是
  `bed_start_0based = position - 1`、`bed_end_0based = position`；
- contig 是显式外键，任何 endpoint 去重、上下文关联或 JBrowse 链接不得跨 contig；
- `end_id` 保留来源、样本、contig、strand 和序列身份；同一坐标在不同来源/contig/
  strand 不得静默合并；
- endpoint 的核心 24 列仍可逐列导出为 v0.2 `endpoints.tsv`；数据库新增的内部主键
  或外键只用于关联，不替换这些字段；
- API 必须返回 release 和 provenance 摘要，下载 API 返回对应 canonical asset 或
  明确的版本化文件引用；
- 资产 Range 代理只能服务登记且 checksum 可验证的对象，不能把 FastAPI 变成任意
  URL 代理。

## 6. C1/C2/D1/D2/D3 已做与当前边界

C1 在 `backend/app/` 已实现只读 FastAPI read layer：查询只读 PostgreSQL、按 release 和
公开证据边界分页返回 sources/assemblies/endpoints/genes/augmentation，并提供 endpoint
TSV/BED6 导出；service/repository 可用 fake repository 离线测试。它不改变 canonical release
或 v0.2 网站。

C2 已增加 `/api/v1/assets/{asset_id}` 的登记资产 GET/HEAD/单 Range 同源代理：只允许
published release 中 `is_public=true` 的资产，origin 必须是登记的 HTTPS URL，JBrowse config
链接也通过该同源入口生成。C2 本身不实现多 Range、缓存、重试、整文件运行时 hash、HF
上传或真实网络 smoke test；Next.js 页面和动态 JBrowse config 已在 D1/D2 实现。

D1/D2/D3 已实现 Next.js App Router 页面、客户端动态 `/explore`、动态 JBrowse config 以及
基于真实 GFF/FAI 的 gene query；importer/materializer 和 PostgreSQL writer 也已实现真实
GFF gene rows 的物化与批量写入。当前计数为 22 个来源（21 published + 1 audit-only）、
20 个 release assembly records、19 个去重 published browser assemblies、28,399 个
endpoints、95,437 个 genes 和 211 个 materialized assets（208 个 public objects）。

这些结果和测试包含本地与 Cloudflare preview 实测；Hugging Face 的真实固定 revision 远端证据另由
`data/registry/remote_asset_audit.v0.2.0-hf.json` 保存（208/208 HEAD 200 + Range 206，
208 对象共 196,667,360 bytes）。该证据对应 canonical `release_version=v0.2.0`，不代表
已发布 `v0.3.0` 数据。D1 local/remote import 与 Worker HTTP smoke 已完成；线上 preview URL
为 `https://bted-catalogue-v03-preview.bted-v0-3-dynamic-service.workers.dev`；单份 4.3.0
JBrowse shell 已从既有 v0.2 bundle 提取到 `site/jbrowse/`（约 5.84 MiB，不含科学资产），
source/assembly/record 页面均使用 Worker config URL。`endpoint_gene_context`
尚未定义或计算。使用 `resolve/main` 生成的旧 verified bundle 已被固定 revision 结果取代，
不作为最终交付。
