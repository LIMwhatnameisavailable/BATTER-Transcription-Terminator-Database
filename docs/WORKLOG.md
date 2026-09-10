# 工作日志

## 2026-09-06 —— 全量维护交接包

**范围：** 将已部署 Cloudflare 基线、本地未提交改进、科学边界、运维步骤和权限要求整理为
同事可独立接手的维护入口；不修改 canonical `v0.2.0`、D1 schema、公开 API 或 endpoint 数，
不部署、不写远程 D1、不上传 HF 资产。

- 从 `131b70f` 建立 `handoff/bted-maintainer-2026-09`，保留 S1_003 仪表盘、regional
  BATTER-TPE pilot 和本地 asset fallback 的全部工作树改动。
- 将 `docs/HANDOFF.md` 收敛为当前有效状态；历史过程继续由本文件与 Git 保存。
- 新增 `docs/handoff/` 下的 operations、science/open work、access 和 demo/acceptance
  四份文档，明确 deployed baseline 与 handoff branch 的差异。
- README 与 Cloudflare prototype README 更新为固定 HF revision
  `463cfc8bd582a5ed9d2c426822148c3f1e56c4d0`、208 public objects、
  196,667,360 bytes 和当前 audit hash；`docs/current-bted-status.md` 标为历史快照。
- 明确线上技术栈是 Worker + D1（SQLite-compatible）+ Static Assets + pinned HF objects；
  未使用 MySQL，FastAPI/PostgreSQL/Next.js 是 future/alternative。
- C 类说明修正为“序列级训练数据存在，但当前 S1_003 reference mapping 未完成”。此前文件级
  调查数字保留为待复核证据；2026-09-06 临时文件已不存在，且本轮 Cloudflare/HF/外部来源
  HTTPS 连接超时，因此没有重新下载或冒充本轮复算。
- 本轮还确认本地 8787/8790 均未运行。远端连接超时只记为“当前环境未复核”，不宣称服务宕机。
- 权限交接只登记服务、角色和验证命令；未写入或转发现有 token、密码、SSH key 或恢复码。

交接分支按三组提交：Worker 修复 `8c37aae`、S1_003 功能 `393106e`，以及本交接文档提交。
2026-09-06 本轮实际验证为 focused 22/22 PASS、全量 141 tests PASS（3 个可选依赖 skip）、
Worker `node --check` PASS、site validator（515 个文件）PASS、交接文档内部链接检查 PASS、
canonical release summary 与固定 HF audit 文件离线核对 PASS、`git diff --check` PASS。
线上 HTTP 与 C 大文件下载仍因当前网络超时而未复核；本记录不把历史 smoke 当成本轮新测试。

## 2026-08-27 —— 本地 8787 asset proxy fallback 修复

**触发问题：** 本地 `GET /api/assets/v0.2.0--assembly-GCF_000009045.1--fai` 曾因 Wrangler
local workerd 无法连接固定的 Hugging Face origin 而抛出 HTTP 500（`Network connection lost`）。
登记的 FAI 资产本身没有损坏：仍是 29 bytes，SHA-256 为
`0576f9d30e1b56d95e928b5a19c622832e995a159cfc0281510a1d91e7f7b3c0`，固定 origin 的 HEAD/Range
审计结果正常。

### 修复范围

- `prototype/accession-range/src/worker.js` 增加受限的 `LOCAL_ASSET_BASE`：只有请求来自
  `localhost`/`127.0.0.1`，且该变量解析为无凭据、无 query/hash 的 HTTP loopback URL 时才使用本地
  origin；非 loopback 请求继续使用 HTTPS 且 hostname allowlisted 的固定 Hugging Face origin。
- upstream `fetch` 网络异常现在返回结构化 `502`：
  `{ "error": "asset_origin_unavailable", "asset_key": "..." }`，并设置 `Cache-Control: no-store`，
  不再把网络不可达伪装成无上下文的 500。502 只表示 origin 当前不可达，不表示资产内容恢复或被重新解释。
- 未修改 FAI/FASTA/GFF3/TBI/BigWig/BED 内容、manifest checksum、D1 catalog、canonical endpoint、
  evidence class 或接口路径；不把临时资产副本加入 Git，也未提交、推送或部署。

### 本地复现与验证环境

- 当前验证复用了已登记且 checksum 已核对的 S1_003 资产，在 `/private/tmp/bted-s1-003-assets.2DaVGK`
  建立只读 symlink 目录和支持 GET/HEAD/单 Range 的临时 HTTP origin `127.0.0.1:8790`。
- Wrangler local 在 `127.0.0.1:8787` 运行时显式传入
  `LOCAL_ASSET_BASE=http://127.0.0.1:8790`；临时目录和进程停止后不会成为项目依赖。重启时需按同一
  资产映射重新建立只读 origin，不能把大文件复制进仓库。
- FAI GET 返回 200/29 bytes；FASTA、GFF3、TBI、正/负链 BigWig 和 canonical endpoint BED 的
  单 Range 请求均返回 206，并保留登记的总长度与 asset headers。未使用 `wrangler --remote`，因为
  那会上传并执行 Worker，超出本轮“不部署”范围。

### 验证

- `tests/test_bted_worker_assets.py`：4/4 PASS，覆盖 loopback fallback、非 loopback 忽略本地 origin、
  非法 local origin 拒绝和网络异常结构化 502。
- 与证据仪表盘、browser wrapper、动态 JBrowse 和 ingestion 合并运行的 focused suite：22/22 PASS。
- `node --check prototype/accession-range/src/worker.js`：PASS；`python3 scripts/validate-site.py site`：
  PASS（515 个站点文件）；`git diff --check`：PASS。
- `python3 -m unittest discover -s tests -p 'test*.py' -q`：141 tests PASS，3 个可选依赖测试 skip。
- 真实浏览器审计已完成：仪表盘打开正常；点击入口后 JBrowse 在
  `NC_000964.3:18,000–28,000` 渲染 reference gene、正/负链 signal、Rend-seq endpoints 和
  BATTER-TPE prediction，预测记录 `REGIONAL_0011` 可见；未见 HTTP 500 或 `Network connection lost`，
  console 为 0 error / 0 warning。临时服务若退出，重启时仍需使用只读 loopback origin，勿改动科学数据。

## 2026-08-27 —— S1_003 用户友好的证据仪表盘

**范围：** 只调整 S1_003 证据展示页的文案、分组和响应式布局；不修改 Worker、pilot BED、canonical
endpoint、坐标、证据类别或记录计数，不提交、推送或部署。

- `site/evidence-layers-preview.html` 改为英文科研可视化仪表盘：标题为 “Explore the evidence
  behind this genome”，使用 Measured 3′-end signal、Curated endpoint records、Training
  augmentation examples 和 Model-predicted regions 四个自然名称，不再向用户展示分层字母。
- 页面将 measured signal 与 curated records 归入 **Experimental evidence**，把 augmentation
  examples 作为独立 **Model context**，把模型区间归入 **Computational output**；桌面端采用两列
  卡片，窄屏按分组纵向排列。
- 每张卡片保留一句易读解释、关键数字、状态和内联 SVG/CSS 图形；格式、evidence class、坐标和
  限制收进可展开的 `Technical details`。augmentation 继续显示 unavailable，不推测任何坐标。
- 模型卡片继续明确 `non-experimental` 与 `regional compatibility pilot`，保留 11 条区间、7 条
  正链/4 条负链、pilot BED 下载和 provenance 链接；动态浏览器入口仍传入
  `pilot=three-layer`。
- S1_003 record/assembly 入口和静态生成器同步改用 “See the evidence together / Open evidence
  dashboard”，避免重新生成页面后恢复旧的字母式 pilot 文案。

### 验证

- `python3 -m unittest -v tests/test_bted_three_layer_preview.py`：5/5 PASS。
- `python3 scripts/validate-site.py site`：PASS；页面文案通过证据标签、凭据、绝对路径和内部链接检查。
- `node --check prototype/accession-range/src/worker.js`：PASS。
- `python3 -m unittest discover -s tests -p 'test*.py' -q`：137 tests PASS，3 个可选依赖测试 skip。
- `git diff --check`：PASS。

## 2026-08-27 —— S1_003 证据层图例与 D 轨道减拥挤说明

- 在 `site/evidence-layers-preview.html` 增加 A/B/C/D 简洁图例；C 明确为 unavailable，图例字母
  表示 provenance 而非置信度排序。
- 保留 Worker 中 D track 的 `showLabels: false`，并在页面解释标签默认隐藏是为了减少 10 kb
  视野重叠；用户仍可点击区间查看 score。score 明确为模型置信度，不是验证概率。
- 未修改 pilot BED、canonical endpoint、坐标、证据类别或记录计数。

## 2026-08-24 —— S1_003 A/B/D evidence-layer preview

**分支：** `feature/three-layer-evidence-preview`
**范围：** 只做 *Bacillus subtilis* 168（`BATTER_S1_003`、`GCF_000009045.1`、
`NC_000964.3`）的 A/B/D 浏览器试点；不修改 v0.2 canonical endpoint 表，不新增 C 层伪数据，
本轮未提交、推送或部署。

### 完成内容

- 新增 `site/evidence-layers-preview.html`：以科研用户视角展示 A 实验信号、B 实验来源端点、
  D BATTER-TPE 预测；C 只保留一行 unavailable 说明，不生成 C track。
- `site/records/BATTER_S1_003.html`、`site/assemblies/GCF_000009045.1.html` 增加试点入口；
  `scripts/build_v0_2_site.py` 保证重新生成页面后入口仍保留。
- `prototype/accession-range/src/worker.js` 在 S1_003 的动态 JBrowse config 中按
  `reference gene → A raw signal → B endpoint → D model prediction` 顺序添加静态 D track。
  D track 使用 `evidence_class=model_prediction`，明确 `experimental=false`，不进入 D1 endpoint
  表，也不改变 S1_003 的 1,414 条 canonical `curated_record`。
- 试点入口给动态 config 传入 `pilot=three-layer`。Worker 因而把默认视野直接设为
  `NC_000964.3:18000–28000`，同时保留 default session 中全部五条 track；没有使用会覆盖
  default session 的 JBrowse `loc` 深链。
- 新增 `site/data/pilots/BATTER_S1_003_batter_tpe_regional_pilot.bed`，共 11 条官方 BATTER-TPE
  输出（7 条 `+`、4 条 `-`），坐标位于 `NC_000964.3:18000–28000`；通过 offset 17,999 从
  区域 BED 坐标恢复到全基因组 0-based BED 坐标。
- 新增同目录 provenance JSON：记录官方 GitHub commit
  `9133d2d36b60c238a1e36760a296eff9f001fb72`、`batter.mdl.pt` SHA-256、参考 FASTA SHA-256、
  输入范围、命令、模型输出数、正负链统计、环境兼容调整和限制。

### D 层真实运行与兼容性说明

- 使用官方仓库 `scripts/batter-tpe` 和官方 `model/batter.mdl.pt`。旧仓库依赖环境不能在当前
  Python 3.13/torch 2.11 直接加载：新 `transformers` 注册了 `position_ids` buffer，旧 CRF
  使用 `.view()` 对非 contiguous tensor 报错。只在 `/private/tmp` 的隔离执行副本中使用
  `strict=False`（唯一额外 state-dict key 为该 buffer）并将 CRF `.view()` 改为 `.reshape()`；
  官方 clone 未修改。
- 官方 E. coli 示例 `NC_000913.3:1–6000` 做 sanity check：参考 `TPE.bed` 中 7 条记录有
  6 条坐标、链和 score 完全一致；`5032–5075 (+, 0.902)` 在兼容环境中为 `5036–5078 (+,
  0.912)`。因此页面和轨道称为 **compatibility pilot**，不宣称复现作者旧环境的每个字节。
- S1_003 区域实际输出 11 条；D 是 BATTER-TPE 区间预测，不是单碱基实验端点，不能并入 B 表。

### 验证

- `python3 -m unittest -v tests/test_bted_three_layer_preview.py`：5/5 PASS。
- `python3 -m unittest -v tests/test_bted_browser_wrapper.py tests/test_bted_v03_browser.py tests/test_bted_ingestion.py`：13/13 PASS。
- `node --check prototype/accession-range/src/worker.js`：PASS。
- `python3 scripts/validate-site.py site`：PASS（站点允许小型 `site/data/pilots/*.bed` 试点资产）。
- `python3 -m unittest discover -s tests -p 'test*.py' -q`：137 tests PASS，3 个可选依赖测试 skip。
- 真实浏览器 smoke：试点入口打开后直接定位 `NC_000964.3:18,000–28,000`，依次显示 gene、
  A 正链信号、A 负链信号、B Rend-seq endpoints 和 D BATTER-TPE prediction；D 的 11 条区间
  均可见，页面 console 0 error / 0 warning。测试使用本地 Worker 静态站点与只读远程 D1 binding，
  未执行正式部署。
- `git diff --check`：PASS。

### 未完成

- 本轮未进行 Cloudflare Worker 正式部署；部署前仍需复核远程 preview 的静态 D BED 与动态
  config 使用同一版本代码。
- C 层仍未提供；只有取得 BATTER 扩增实例的可追溯坐标后再另行建轨道。

## 2026-08-23 —— JBrowse user-facing information wrapper

**范围：** 只调整浏览器入口和静态展示层；不修改 JBrowse bundle、canonical endpoint 数据、
证据类别或资产内容。

- 新增 `site/browser.html` 与 `site/assets/browser-wrapper.js`。公开的 source、assembly、
  record 和 accession-search 入口现在先进入 wrapper，再由 wrapper 在同一页面上方展示
  organism/strain、versioned assembly、source selector、Publication/PubMed/DOI、raw
  accession、Download BED、Dataset details 和 Genomes/assembly 入口；下方 iframe 继续加载
  原始 `site/jbrowse/index.html`。
- 同一 assembly 的多个 source 使用 `All source tracks` 或 source selector 切换；source_id
  被写回 JBrowse config query，来源仍是独立轨道，不生成共识。`loc`、`session`、`tracks`、
  `highlight` 和 `assembly` query 会传递给 iframe，wrapper 切换时保留深链接状态。
- 对 `/api/assemblies/<accession>/jbrowse-config` 只在 wrapper 中按当前页面 origin 重建
  config URL，避免静态生成时留下的 preview hostname 造成同源 Worker 部署的 CORS；外部、非
  BTED config 不做改写。共享 assembly 的全部来源视图直接列出每个 source 的 PubMed、DOI
  和 Dataset details，raw accession 仍保留且相同 accession 只显示一次。
- `site/data/assemblies.json` 的每个可发布 source track 增加 DOI/DOI URL、PMCID URL 和
  登记 BED asset URL；共享组装 `GCF_000739105.1` 的 S1_007/S1_013 已分别核对。S1_002
  仍没有 source selector、BED 或浏览器入口。
- Worker 动态 JBrowse track metadata 同步加入 `BED_download` 与 `BED_asset_key`，因此
  wrapper 的 Download BED 链接指向已登记同源资产，不复制大文件到网页。

### 验证

- `python3 scripts/build_v0_2_site.py`：20 个 assembly 页面、22 个 source 页面重新生成。
- `python3 -m unittest -v tests/test_bted_browser_wrapper.py`：5/5 PASS。
- `node --check site/assets/browser-wrapper.js site/assets/accession-range-demo.js prototype/accession-range/src/worker.js`：PASS。
- `git diff --check`：PASS。

### Git、部署与线上验收

- 实现提交为 `91820e1`，已推送到 `personal/feature/bted-v0.3-dynamic-service`；Cloudflare
  developer preview 已更新，Worker version ID 为 `679cff52-8779-4bdd-9346-63d180278b53`。
- 线上从共享 assembly `GCF_000739105.1` 的 **Open genome browser** 进入 wrapper：默认展示
  S1_007/S1_013 各自的 PubMed、DOI、Dataset details 和去重后的 ENA accession；iframe 正常
  加载 reference annotation 与两条独立 endpoint track。
- 切换到 `BATTER_S1_007` 后，页面显示 Publication、PubMed、DOI、ENA、Download BED 和
  Dataset details；JBrowse 只显示 reference annotation 与 S1_007 endpoint track。浏览器
  console 为 0 error / 0 warning，BED asset HEAD 返回 200、`Accept-Ranges: bytes`。
- `loc`、`session`、`tracks`、`highlight` 和 `assembly` 的代码级透传已由 focused test 覆盖；
  本轮没有人为构造新的 session snapshot。JBrowse 内部 bundle 仍按原始文件保留。

## 2026-08-22–23 —— v0.3 Cloudflare Worker + D1 catalogue preview

**分支：** `feature/bted-v0.3-dynamic-service`
**范围：** 停止 Render/Neon/Vercel 路线，改为 Cloudflare Worker + D1 + Worker Static Assets；
不修改 canonical v0.2 release、不 promote 数据版本、不提交巨型 seed 或凭据。

### 完成内容与真实测量

1. `scripts/generate_bted_d1.py` 从固定 HF verified bundle 生成 D1 `schema.sql`、元数据/资产/
   轨道批次和分片 endpoint INSERT；生成物只写到仓库外临时目录。D1 不保存当前 API 未使用
   的 `genes`/`source_annotations` 行，后二者仍由登记的 HF/metadata assets 保持。
2. `prototype/accession-range/schema.sql` 扩展到 release/publication/assembly/contig/source/
   accession/asset/track/endpoint catalogue；`status=preview` 明确是 `v0.2.0` 的查询投影。
3. `prototype/accession-range/src/worker.js` 提供 `/api/health`、stats、catalogue、sources、
   assemblies、endpoints、augmentation、动态 JBrowse config，以及登记 public asset 的
   GET/HEAD/单 Range 同源代理；静态请求交给现有 `site/`。代理拒绝未知/private key、
   任意 `?url=` 和非 allowlisted origin。
4. `prototype/accession-range/wrangler.jsonc` 固定 HF revision、D1 binding 和 `site/` Static
   Assets；`docs/v0.3/deployment.md`、`prototype/accession-range/README.md`、架构和资产
   handoff 文档同步标记 FastAPI/PostgreSQL/Next.js 为 future/alternative。
5. 本地 Wrangler 4.125 D1 实际导入最终计数：1 release、13 publications、20 assemblies、
   49 contigs、22 sources、32 source accessions、22 tracks、211 assets（164 public）和
   28,399 endpoints；SQLite 主库约 31 MB，含 WAL 的 local state 约 68 MB。Worker 有界 HTTP
   smoke：catalogue/source/assembly/endpoint/augmentation/JBrowse 全部 200；固定 HF FASTA
   与 BED HEAD 200、单 Range 206；`remote-data` alias 200，任意 origin 400，缺 public
   FASTA+FAI 的 assembly 404。

### Cloudflare 状态与边界

`CI=1 npx wrangler whoami` 已在非交互模式确认认证成功。远程免费/preview D1
`bted-catalogue-v03-preview` 已创建并按 schema、元数据、资产、轨道和 endpoints 顺序批量
导入；实际计数为 1 release、13 publications、20 assemblies、49 contigs、22 sources、32
source accessions、22 tracks、211 assets（164 public）和 28,399 endpoints，远程数据库大小
为 32.78 MB。Worker + Static Assets 已部署到
`https://bted-catalogue-v03-preview.bted-v0-3-dynamic-service.workers.dev`。

线上 smoke 已覆盖 health/stats/catalogue/sources/assemblies/endpoints/augmentation、source/
assembly/endpoint detail、动态 JBrowse config、公开 FASTA/BED HEAD 200 和单 Range 206、
同源 `remote-data` alias；未知/private asset 返回 404，任意 `?url=` 返回 400。首页、
`sources.html`、`catalog.html`、`accession-range-demo.html` 跟随 clean-path 重定向后均为
非空 200，页面未发现旧 localhost/127.0.0.1 入口；JBrowse config 请求均指向同一 Worker
origin。当前 URL 仍是 developer preview，不是正式
v0.3.0 release；workers.dev 发布提示过 subdomain 注册，但当前 URL 已可访问。

所有本地 `.wrangler` cache 和生成 SQL 都是临时物，不进入 Git；HF 固定 revision 与 164/164
audit 证据保持不变。FastAPI/PostgreSQL/Next.js 保留为 future/alternative，未创建或依赖
Neon/Render/Vercel 资源。

### 2026-08-23 JBrowse shell 缺口修复与线上浏览器验收

- 线上首次检查确认 `/jbrowse/index.html` 在 Worker 尚未提供 shell（404）。从既有
  v0.2.0 JBrowse 4.3.0 bundle 只提取一份 app shell 到 `site/jbrowse/`：455 个运行时文件、
  6,128,344 bytes（5.844 MiB），最大单文件 728,605 bytes；排除 FASTA/FAI/GFF3/BED/BigWig、
  21 份 source viewer、配置和 source maps。Worker Static Assets 总体积实测 6,568,327 bytes。
- `scripts/build_v0_2_site.py` 改为生成 Worker API config URL；source/assembly/record/
  catalogue 页面统一链接到同源 `/jbrowse/index.html?config=<absolute Worker API URL>`，
  accession 页面运行时按钮使用同源 `/jbrowse/index.html`。站点 validator 增加对当前同源
  `/api/assemblies` 配置链接的合法支持，但继续拒绝 localhost/127.0.0.1。
- 动态 config 补齐 JBrowse 4.3 default-session 的 view/track/display IDs。重新部署后，真实
  Playwright 共享 `GCF_000739105.1` 显示 gene annotation + `BATTER_S1_007`/`BATTER_S1_013`
  两条 source track；单 source `GCF_003054575.1` 显示 `BATTER_S1_009`。两个页面 console
  均 0 error / 0 warning；所有 config asset URI HEAD 200、单 Range 206。

## 2026-08-21 —— BTED v0.3 第一里程碑：架构契约与数据库骨架

**分支：** `feature/bted-v0.3-dynamic-service`
**范围：** 只建立 v0.3.0 的架构/数据库/API 契约和静态测试；没有导入 NCBI 新数据、
没有修改 v0.2 网站或科学数据、没有实现 Next.js/FastAPI、没有部署或创建真实
PostgreSQL 资源。

### 完成内容

1. 新增 `docs/v0.3/architecture.md`：冻结 canonical release 是科研真源、PostgreSQL
   是可重建的派生查询层；说明 v0.2/v0.3 并行，以及 Vercel Next.js、Render FastAPI、
   Neon PostgreSQL、Hugging Face 资产和同源 `/api/v1/assets/{asset_id}` Range 代理的
   责任边界。v0.3.0 只覆盖当前仓库的 BATTER S1 内部数据，外部协作者数据不在本轮。
2. 新增 `docs/v0.3/database-schema.md`：完整说明 release/import、publication、
   versioned assembly/contig、source/accession/sample、24 列 endpoint、JSONB 来源
   附表、genes/context 和 assets；记录主外键、唯一约束、1-based/BED 约束、证据拒绝、
   S1_002 audit-only 以及 Table S1 19/3 augmentation 的来源级边界。
3. 新增 `docs/v0.3/api-contract.md`：定义 stats、sources、assemblies、endpoints、
   genes、augmentation、endpoint downloads 和 asset Range API，含分页/过滤、
   provenance、404/422、JBrowse deep link、206/416 headers。augmentation 第一版只
   表示 19 个 Table S1 TRUE 来源，不宣称逐端点训练；gene clusters/Rfam 不纳入。
4. 新增 `backend/database/schema.sql`：无 seed data 的 PostgreSQL DDL 骨架。`endpoints`
   明确保留当前 v0.2 `endpoints.tsv` 的全部 24 列，`signal_or_score` 用 text 保留
   `NA`；contig/sample/release/source 通过外键与触发器隔离，source_annotations 使用
   JSONB，prediction/mixed evidence 不能成为公开 endpoint。
5. 新增 `backend/database/README.md`：说明 staging/校验/atomic switch 流程，并明确
   禁止直接 drop/truncate 生产数据库或覆盖既有 release。
6. 新增 `tests/test_bted_v03_schema.py`：无 PostgreSQL 依赖的静态 unittest，检查关键
   表、24 列、坐标/contig/sample/release、S1_002、19/3 augmentation 和 prediction
   evidence 边界。
7. 根据 Sol 第一轮审查补齐四类详情 API，page_size 上限收敛为 100；修正资产 full
   SHA-256 只在登记/import 阶段验证的 Range 语义；将 sample 关联改为 NOT NULL 复合
   外键，保留 Table S1 原始 augmentation 列，允许 import run 重试；publication/assembly
   增加 journal/strain，genes/context 按 release 和 GFF3 asset 隔离，source_annotations
   支持一对多来源观察，并增加 contig 长度边界。
8. 新增 `docs/v0.3/browser-ui-contract.md`，冻结 Search by accession、19 个来源级
   augmentation、详情链接、基因/端点分级缩放、raw BigWig 和 GFF3/TBI 展示要求，并由
   architecture/HANDOFF 引用。
9. 修正 publication 的 S1 来源示例为非连续且准确的 `S1_001、S1_003–S1_005`，并为
   `release_versions` 增加 `is_current` 只能指向 `published` release 的约束及静态断言。

### 验证

- `python -m unittest -v tests/test_bted_v03_schema.py`：11/11 PASS；
- `python -m unittest -v tests/test_bted_ingestion.py`：4/4 PASS；
- `python -m unittest -v tests/test_bted_v03_schema.py tests/test_bted_ingestion.py`：15/15 PASS；
- `python -m unittest discover -s tests -p 'test*.py' -v`：32/32 PASS；
- `git diff --check`：PASS（无输出）。

### 未完成与风险

- 尚未在真实 PostgreSQL/Neon 实例执行 DDL；下一阶段需在目标 PostgreSQL 版本做迁移
  smoke test，再实现 importer 的 staging/atomic switch。
- FastAPI/Next.js、真实资产上传/Range 代理、gene context 计算、训练集生成和新数据
  导入均未开始；本轮不应把静态契约误认为已部署服务。
- DDL 无 seed data，v0.3.0 的首次数据导入必须重新核对 release manifest checksum、
  source manifest、许可和 24 列行数，保持 v0.2 文件不变。

## 2026-08-21 —— v0.3 第二里程碑：只读 canonical 校验与导入计划

**分支：** `feature/bted-v0.3-dynamic-service`
**范围：** 只检查当前 v0.2.0 canonical release，并输出未来写入 PostgreSQL 的确定性
行数/键摘要；没有连接数据库、没有写库、没有修改 v0.2 数据或网站。

### 完成内容

1. 新增 `backend/importer/canonical.py` 和 `backend/importer/__init__.py`：先解析 release
   entry 声明且 checksum 验证通过的 `records/<source>/manifest.json` 作为 canonical
   source manifest；`data/registry/manifests` 仅作 audit 交叉核对。同步读取 24 列
   endpoint、BED、许可允许的来源附表和 SHA-256；错误保留 source/file/line 定位。
2. 校验 source/end_id/sample、`+/-` strand、1-based 与 BED6 的单碱基转换、endpoint
   evidence、PMID/DOI 一致性、annotation `end_id` 外键和 S1_002 audit-only 边界；不跨
   contig 匹配，不把预测/混合证据升级为实验端点。
3. 强制每个 source 声明并实际提供基础文件；published source 还需 endpoint BED/TSV，
   `source_annotations_status=published` 还需附表。逐条核验 `SHA256SUMS.txt` 与实际
   文件及 release entry 的摘要；release/registry source 集必须完全一致，相同 PMID 和
   带版本 assembly 的元数据必须一致。
4. 新增 `scripts/import_bted_v03.py validate`。真实 v0.2.0 结果为 22 source、21
   published、1 audit-only、28,399 endpoint、19/3 augmentation、13 publication、20
   assembly、47 contig、21 sample、32 source accession、17 个来源附表（24,887 行），
   并规划 127 个已验证小型 canonical assets。`--plan-json` 可保存不写库的确定性计划；
   计划增加 `import_runs`、assets、schema 对齐的 `accession_namespace`/accession/raw_value
   和零行的 genes/endpoint_gene_context；asset_id 改为不含 `/` 的单段 API key，asset_kind
   使用 schema 枚举，字段使用 `is_public`。未知 contig 长度保留为 unresolved，计划明确
   `canonical_validation_status=validated` 但 `postgresql_ready=false`。
5. 新增 `docs/v0.3/importer.md`，补充 canonical manifest、必要文件、checksum、资产、
   命名空间、校验边界、命令、当前统计、错误含义和后续 staging importer 约束；同步
   更新 `backend/database/README.md`、本交接日志和 HANDOFF。
6. 新增 `tests/test_bted_v03_importer.py`：真实 release happy path，以及临时小 fixture
   下的坐标错误、annotation orphan、audit-only 错误 endpoint、canonical manifest 篡改、
   必要文件缺失/未声明、SHA256SUMS 不一致/未声明条目、registry extra source、相同 PMID
   元数据冲突、错误 release version 和 CLI plan 输出；不复制完整大型 release。

### 验证

- `python3 -m unittest -v tests/test_bted_v03_importer.py`：15/15 PASS；
- `python3 -m unittest -v tests/test_bted_v03_schema.py tests/test_bted_ingestion.py`：15/15 PASS；
- `python3 -m unittest discover -s tests -p 'test*.py' -v`：47/47 PASS；
- `python3 scripts/import_bted_v03.py validate --release-root data/public/v0.2.0`：JSON
  `ok=true`；
- `git diff --check`：PASS。

### 未完成与风险

- 还没有 psycopg/真实 PostgreSQL staging/atomic switch；`plan` 不是 INSERT 结果。
- 47 个 contig 的长度不在 endpoint 表中，必须从各自参考 FASTA/assembly metadata 核实，
  当前不猜测；随后才能满足 schema `contigs.length_bp`。
- FastAPI/Next.js、Range 资产代理、JBrowse 服务配置、Neon/Render/Vercel 部署仍未开始。

## 2026-08-21 —— v0.3 第三阶段 A：参考 contig 长度与 provenance 注册

**分支：** `feature/bted-v0.3-dynamic-service`
**范围：** 只使用既有 v0.2 JBrowse release bundle 补齐查询层元数据；没有下载新参考
序列、没有修改 v0.2 canonical release/website、没有连接 PostgreSQL。

### 完成内容

1. 新增 `scripts/build_reference_contig_registry.py`。它解析每个 published source 的
   config 和 `IndexedFastaAdapter`，要求 source 前缀、FAI contig 精确命中 canonical
   endpoint，并核对 FASTA/FAI/config 与 bundle 根 `SHA256SUMS.txt` 的摘要；不从 endpoint
   最大坐标猜测 contig 长度。
2. 从只读 bundle
   `/Users/seu_yolo/Desktop/BGIRNA/.worktrees/bted-v0.2/dist/BTED-v0.2.0-jbrowse/`
   生成并追踪 `data/registry/reference_contigs.v0.2.0.tsv` 与对应 JSON provenance。注册
   表覆盖 21 个 published source、47 个 endpoint contig；共享 contig 的 source ID、FAI
   长度、FASTA/FAI checksum 不一致会阻断生成。参考 FASTA/FAI 本身不进入 Git。
3. 扩展 `backend/importer/canonical.py`：默认读取该小表，也支持 CLI
   `--contig-registry`；检查 release version、精确 assembly/contig 集合、最大 endpoint
   坐标覆盖（允许 endpoint 正好位于 contig 最后一个碱基）、supporting source 排序/唯一性、
   摘要和 provenance 字段。通过后 plan 的 contig rows 带
   `length_bp` 和 provenance，真实 v0.2.0 的 `postgresql_ready=true`；缺失 registry 时
   保持 canonical 校验可通过但 `postgresql_ready=false`，不会降级为猜测长度。
4. builder CLI 增加可选 `--generated-at-utc`，在重建 registry 时可以固定 provenance
   时间；默认不传时仍使用当前 UTC 时间。`scripts/import_bted_v03.py validate` 的计划继续是只读、`write_mode=not_written`；
   参考 registry 只保存既有 JBrowse 资产的 provenance，不加入 canonical `assets` 127 项。

### 验证

- 真实 builder：21 source / 47 contig，生成成功；S1_007/S1_013 的共享 contig 被合并为
  一条 provenance 记录但 endpoint/source track 仍保持独立。
- `tests/test_bted_v03_importer.py`：24/24 PASS；覆盖真实 registry happy path、缺失/长度
  不足/缺失与额外 contig、tiny FAI、共享 contig 冲突、bundle checksum 失败和 CLI 计划。
- 真实 importer：22 source / 21 published / 1 audit-only / 28,399 endpoint，contig 47，
  `canonical_validation_status=validated`、`postgresql_ready=true`、unresolved 为空。

### 未完成与风险

- 尚未执行 PostgreSQL staging/atomic switch；`postgresql_ready=true` 只是满足 schema
  预检，不代表已写库。
- registry provenance 追溯的是既有 JBrowse bundle；若未来 bundle 重建，需重新生成并
  审核新 release/version，不应原地覆盖已发布 registry。
## 2026-08-18 —— BTED v0.2 网站静态化并部署到个人仓库 GitHub Pages

**分支：** `feature/research-user-dataset-context-v0.1` → `integration/bted-v0.2-site-release` → `seu-yolo/main`
**范围：** 将 accession 查询页面从本地 Python API 迁移到静态 JSON，修复 Release JBrowse 资产，完成 GitHub Pages 部署和线上验证；没有修改端点坐标、BED、证据类别或记录数。

### 完成内容

1. `scripts/build_v0_2_site.py` 新增 `build_assemblies_json()`，自动生成 `site/data/assemblies.json`，覆盖 20 个组装、22 个来源、28,399 条记录。
2. `site/assets/accession-range-demo.js` 改为读取 `data/assemblies.json` 并按 accession 查找；移除所有 `localhost`、`127.0.0.1` 和 `/api/assemblies` 依赖。
3. 为每个来源卡片增加状态标签：`Signal + endpoints` / `Endpoints only` / `Metadata only`。
4. `S1_002`（audit_only）不显示 JBrowse 入口或 BED 下载；Rend-seq 来源保持 `signal_endpoints`。
5. `scripts/validate-site.py` 新增 localhost/API 依赖扫描；`scripts/validate_repo_layout.py` 允许保留 `prototype/`。
6. 新增回归测试 `test_static_assemblies_json_powers_accession_search`。
7. 发现个人仓库 `preview-v0.2.0` Release 的 JBrowse 资产缺少本地 dist 中已验证的 `.gff3` 文件，导致首次 Pages 部署失败；用本地 `dist/BTED-v0.2.0-jbrowse-assets.tar.gz` 替换 Release 资产并更新 checksum。
8. 推送 `integration/bted-v0.2-site-release` 到个人仓库，创建 PR #2，合并到 `main`；触发并等待 Pages 部署成功。
9. 线上验证：首页、Genomes 目录、accession 查询、中英文切换、`GCF_000739105.1` 页面、JBrowse 配置与下载链接均正常返回 200。

### 验证

- `python3 -m unittest -v tests/test_bted_ingestion.py tests/test_bted_v0_2.py tests/test_accession_range_prototype.py`：21/21 PASS。
- `python3 scripts/validate-site.py site` / `.pages-preview`：PASS。
- `python3 scripts/validate_jbrowse_release.py .pages-preview/jbrowse`：PASS。
- `node --check site/assets/accession-range-demo.js`：PASS。
- GitHub Actions `Deploy BTED Pages` run 32054805656：completed success。

### 线上地址

- 网站：https://seu-yolo.github.io/BATTER-Transcription-Terminator-Database/
- PR：https://github.com/seu-yolo/BATTER-Transcription-Terminator-Database/pull/2
- Actions：https://github.com/seu-yolo/BATTER-Transcription-Terminator-Database/actions/runs/32054805656
- Release tag：`preview-v0.2.0`（JBrowse 资产已替换，sha256 同步更新）
- 合并 commit：`f9b3205926b8223f7427d1f7e8758ab0b267bc92`

### 未完成 / 需后续关注

- 本地沙箱无法启动普通静态服务器，浏览器 JS 实际渲染和 JBrowse 交互未在本地实测；已通过文件系统路径验证和线上 HTTP 200 检查覆盖。
- 线上 JBrowse 的 track 实际加载和 peak 显示已在本日（2026-08-18）通过 Playwright 线上浏览器验证。

## 2026-08-18（续）—— 文档 PR 清理与线上浏览器验收

**分支：** `docs/bted-v0.2-handoff-v2` → `seu-yolo/main`
**范围：** 清理冲突的 docs PR，完成线上真实浏览器验证；未修改科学数据。

### 完成内容

1. 确认 PR #3（`docs/bted-v0.2-handoff`）因包含已 squash 进 main 的代码提交而处于 `mergeable_state: dirty`。
2. 从 `personal/main`（`f9b3205`）新建 docs-only 分支 `docs/bted-v0.2-handoff-v2`，仅保留 `docs/WORKLOG.md` 与 `docs/HANDOFF.md` 更新，并推送到个人仓库。
3. 使用 Playwright 对线上站点进行真实浏览器验证：
   - 首页标题、导航、统计数字正确（20 assemblies / 22 source tracks / 28,399 records）。
   - `GCF_000739105.1` 中文 accession 页面显示 2 来源、2,848 记录、两篇论文、PRJEB31507、作者定义端点、BED/metadata 下载。
   - JBrowse 加载 1 个共享参考 + 2 条独立来源 track（S1_007、S1_013），控制台无 error，网络请求无 404。
   - `BATTER_S1_002` 页面为 `Metadata only` / `audit_only`，无 JBrowse 入口。
   - `BATTER_S1_001` Rend-seq 页面保留 BigWig signal track 与候选端点 track。
4. 本地测试与校验脚本全部 PASS（`test_bted_ingestion.py`、`validate-site.py`、`validate_jbrowse_release.py`、`validate_repo_layout.py`）。

### 阻塞与待人工步骤

- GitHub 连接器仅有只读权限，`gh` CLI token 失效，无法自动创建/合并 PR 或关闭 PR #3。
- 需人工在浏览器中：关闭 PR #3，创建并合并 `docs/bted-v0.2-handoff-v2` → `main` 的 PR。

### 验证

- Playwright 线上验收：PASS（无 console error、无 404）。
- `python -m unittest -v tests/test_bted_ingestion.py`：4/4 PASS。
- `python scripts/validate-site.py site`：PASS。
- `python scripts/validate-site.py .pages-preview`：PASS。
- `python scripts/validate_jbrowse_release.py`：PASS。
- `python scripts/validate_repo_layout.py`：PASS。

### 参考链接

- 线上站点：https://seu-yolo.github.io/BATTER-Transcription-Terminator-Database/
- PR #2（已合并）：https://github.com/seu-yolo/BATTER-Transcription-Terminator-Database/pull/2
- 冲突 PR #3（待关闭）：https://github.com/seu-yolo/BATTER-Transcription-Terminator-Database/pull/3
- 干净 docs 分支比较：https://github.com/seu-yolo/BATTER-Transcription-Terminator-Database/compare/main...docs/bted-v0.2-handoff-v2
- Actions 成功部署 run：`32054805656`



## 2026-08-17 —— accession 页面收敛为既有核心字段

**分支：** `feature/research-user-dataset-context-v0.1`
**范围：** 根据用户反馈简化试点页面；没有修改端点坐标、BED、证据类别或记录数。

### 完成内容

1. 移除“数据由谁产生，如何测量？”以及研究单位、实验室、通讯作者、培养、采样、测序平台和测序机构等扩展字段。
2. 页面只使用此前已整理的核心字段：物种、菌株、assembly/contig、论文、实验方法、原始数据 accession 和证据类型；同时保留记录数、下载和 JBrowse 操作入口。
3. 来源区改为 `Publications and experimental data / 论文与实验数据`，每个来源继续作为独立 track，不合并端点表。
4. D1 试点仅为物种和菌株增加结构化列，其余论文、assay、accession 和 evidence 字段沿用现有 registry。

### 结论

现有 22 个来源已经足以生成该核心信息界面，不需要为了网页重新逐篇整理机构与详细实验条件。S1_002 继续保持 `audit_only`。

## 2026-08-17 —— accession 页面科研背景信息试版

**分支：** `feature/research-user-dataset-context-v0.1`
**范围：** `GCF_000739105.1` 的 accession 检索页面、试点注册表和 D1 兼容字段；没有修改端点坐标、BED、证据类别或记录数。

### 完成内容

1. 页面第一层改为物种、菌株和精确参考组装；第二层按来源展示主要研究单位、实验室/院系、通讯作者、培养与采样设计、测序平台、read layout、生物学重复和数据入口；技术架构继续隐藏在后台。
2. S1_007/013 均以 KAIST 为论文主要单位和 ENA submitting center；因论文与 ENA 未单独报告测序机构，页面明确显示 `Not separately reported`，不把提交中心推断为测序设施。
3. 明确两个来源共同使用 `PRJEB31507`：它们是同一原始项目上的两份独立发表端点表，不再称为两次独立测序实验；在 JBrowse 中仍保持两条 source track。
4. 试点 registry、D1 schema/seed、Worker API 和本地等价 API 增加结构化 `study_context`，中英文页面均由同一字段生成。
5. 新增 `prototype/accession-range/STUDY_CONTEXT.md`，记录页面归属字段的论文依据和机构命名规则。

### 验证

- 浏览器实测中英文切换、物种概况、两张研究来源卡、论文/ENA/详情/BED/metadata/JBrowse 链接均正确；
- 页面可见内容不显示 D1、API、对象路径或 Range 测试；
- `python3 -m unittest -v tests/test_accession_range_prototype.py`：5/5 PASS；完整回归和站点验证在提交前执行。

## 2026-08-16 —— accession 页面用户化与中英文切换

**分支：** `feature/accession-range-prototype-v0.1`
**范围：** accession 检索页面及其入口文案；没有修改端点坐标、BED、证据类别或记录数。

### 完成内容

1. 将原来的架构演示页改为科研用户任务流：输入 assembly accession → 查看基因组概况 → 查看独立研究 → 打开 JBrowse 或下载 BED/metadata。
2. 从用户主界面移除编号架构图、D1、API route、对象路径和 128-byte Range 测试；底层 D1/Range 实现与测试仍保留在 `prototype/accession-range/`。
3. 增加 EN/中文切换，覆盖页面导航、检索表单、状态消息、统计、研究表、证据标签、下载区和页脚，并通过 URL/localStorage 保留选择。
4. S1_007/013 track 元数据补充发表年份、PMID 与站内来源详情链接；两项研究继续作为独立 `author_called_endpoint` 轨道展示。
5. assembly 页和 Genomes 页入口改为 `Find this genome by accession / Quick search`，不再向普通用户显示 `API pilot / Architecture prototype`。
6. 页面增加三项用户数据导读：收录范围、单条记录定义和“3′ 端不自动等同于功能性终止子”的证据边界。
7. 动态研究表补充论文标题、PubMed、原始测序 accession/ENA 入口；增加来源特异的 TEP/TTS 解读、适用分析和不可直接推断的结论。

### 验证

- 浏览器实测英文与中文页面均返回 2 项研究、2,848 条记录，年份分别为 2019/2020；PubMed、PRJEB31507、BED、metadata、来源详情和 JBrowse 链接均生成正确；
- 页面可见文本中不再出现 D1、API route、对象路径或 Range 测试；
- `python3 -m unittest -v tests/test_accession_range_prototype.py`：5/5 PASS；完整回归、站点验证见本次提交的最终测试记录。

## 2026-08-15 —— accession 查询与 Range 远程加载原型

**分支：** `feature/accession-range-prototype-v0.1`
**范围：** 共享组装 `GCF_000739105.1` 的部署架构试点；未修改 BATTER_S1_007/013 的核心端点表、BED 坐标、证据类别或记录数。

### 做这个原型的原因

- 当前完整 Pages 预览约 447 MB，其中 JBrowse 约 408 MB；继续把每个来源的参考 FASTA/GFF3 和轨道全部复制进静态站点，不适合大量 assembly 扩展。
- S1_007 与 S1_013 使用完全相同的 assembly/contig。核对确认两份 FASTA、FAI、gene GFF3 和 TBI 的 SHA-256 分别完全相等，因此可以按 assembly 只保留一组参考对象，同时保留两条独立实验 track。

### 完成内容

1. 建立 D1 兼容的 `assemblies / assets / tracks` schema 和单 assembly seed；accession 是参考资源主键，source ID 仍是实验 track 身份。
2. 建立 checksum 冻结的 6 对象注册表：1 FASTA、1 FAI、1 GFF3、1 TBI 和 2 个来源 BED；共享参考/注释避免重复 8,628,614 bytes。
3. 实现生产形态 Cloudflare Worker：
   - `GET /api/assemblies/{accession}`；
   - `GET /api/assemblies/{accession}/jbrowse-config`；
   - `GET|HEAD /api/remote-data/{asset_key}`。
4. `/api/remote-data` 只接受 D1 中注册的 asset key，生产代码限制为允许的 Hugging Face host，不接受任意 `?url=`，避免成为开放代理。
5. 实现本地 API-aware server，在不上传外部对象和不需要 Cloudflare 凭据的情况下复现同一浏览器/API contract；启动时逐对象复算 byte size 与 SHA-256。
6. 网站新增 accession-loading prototype 页面、Range 检查和动态 JBrowse 入口；`GCF_000739105.1` 详情页和 Genomes 行提供明确的 experimental pilot 入口。

### 验证

- API：`GCF_000739105.1` 返回 2,848 records、6 objects、2 independent tracks；
- Range：FASTA 请求 `bytes=0-127` 返回 `206 Partial Content`、`Content-Range: bytes 0-127/8484410` 和 128 bytes；
- JBrowse：动态 config 返回 1 assembly、1 shared gene track、2 source tracks；实际浏览器可见基因及 S1_007/S1_013，0 warning/error；
- `python3 -m unittest -v tests/test_accession_range_prototype.py tests/test_bted_v0_2.py tests/test_bted_ingestion.py`：20/20 PASS；
- `validate-site.py site` 与完整 `.pages-preview`：PASS。

### 尚未执行的外部部署

- 尚未创建真实 Cloudflare D1，也未把对象上传到 Hugging Face；`wrangler.jsonc` 中保持显式占位符。
- 生产迁移前还需确定对象仓库、许可、缓存策略、自定义域名和费用，并对真实 origin 重跑 HEAD/206/checksum 验收。

## 2026-08-14 —— Genomes 目录页科研用户体验改版

**分支：** `feature/genomes-catalog-ux-v0.2`
**范围：** Genomes 目录、目录筛选和按基因组批量下载；未修改端点数据、BED 坐标、证据类别、详情页或 JBrowse 科学资产。

### 完成内容

1. 参考 NCBI 的 assembly 入口、ENCODE 的筛选/选择与 Bacteroides/JBrowse 的独立 track 组织，将 Genomes 页明确为“查找基因组—选择数据—进入详情或浏览器”的目录。
2. 表格从 7 列收敛为 5 个用户概念：`Genome / Experimental data / Evidence / 3′ ends / Access`；物种与菌株升为主标题，assembly accession 放在下方并直连 NCBI。
3. 移除目录主视图中重复的 Source ID、Tracks 和 Status 列；将 track 数换成 `1 study / 2 studies`，仅对异常来源显示 `Metadata only`。
4. 筛选改为物种、实验方法与证据类别；搜索继续支持物种、菌株、assembly、Source ID 和原始数据 accession。
5. 在 Genomes 页增加复选框、`Select visible`、已选数量/记录数和 `Download BED + metadata`；沿用现有无依赖 ZIP 打包，每个 assembly 仍保持独立目录。
6. `site/data/catalog.json` 新增 assembly 级 `evidence_classes`，作为页面自动生成与筛选依据。

### 验证

- `python3 scripts/validate-site.py site`：PASS；
- `python3 -m unittest -v tests/test_bted_v0_2.py tests/test_bted_ingestion.py`：15/15 PASS；
- 浏览器实测搜索、证据筛选、动态可见数量、`Select visible` 和下载按钮状态，控制台无 warning/error；
- `git diff --check`：PASS。

## 2026-08-14 —— Rend-seq 浏览器可读性与端点详情补强

**分支：** `agent/assembly-track-download-demo`
**范围：** S1_001、S1_003、S1_004、S1_005 的 JBrowse 展示和对应网站说明；未修改核心端点表、标准 BED、原始信号或证据类别。

### 完成内容

1. 四个来源的默认窗口不再取第一个端点，而是确定性选择最早一组相邻、距离不超过 500 nt 的异链候选，并在其两侧各扩展 1.5 kb；打开即能同时看到正、负链箭头。
2. 轨道标题直接作为图例：`blue + above zero / orange − below zero`，候选轨道显示 `blue → + strand / orange ← − strand`，避免只靠隐含颜色判断。
3. 浏览器专用候选文件由匿名 BED6 改为富属性 GFF3。点击端点可见稳定 `end_id`、1-based 坐标、strand、原始 read support、BED6 capped score、样本、基因语境、`called_endpoint` 和“不是已证明终止子”的证据警告。
4. 标准公开 `endpoints.bed` 与 canonical candidate BED 保持不变；GFF3 只服务交互展示，不替代 BED 下载接口。
5. Rend-seq 来源页和 assembly 页增加简短读图卡，解释正负链配色、箭头、零线和点击详情；非 Rend-seq 页面不显示该专用说明。
6. 网站 JBrowse URL 加入编码后的配置版本参数，避免浏览器继续使用旧配置缓存。

### 遇到的问题与解决

- **默认窗口只有单一链，造成“箭头方向都一样”的错觉。** 底层 BED strand 核查正常；问题来自首端点窗口的抽样位置。默认窗口改为明确含两种 strand 的展示区域，并由发布校验器逐来源检查。
- **GFF3 即使 display 层写 `showLabels: false` 仍显示长名称。** JBrowse 的该开关属于 renderer 配置；已移动到 `SvgFeatureRenderer`，默认只画紧凑箭头，点击后再展开完整详情。
- **压缩显示 BigWig 在 JBrowse 2.17 的部分窗口报 `invalid cirTree magic`。** UCSC `bigWigInfo` 能读取，但浏览器实际 range 读取失败。构建器改为 `bedGraphToBigWig -unc` 生成 display-only signed-log v4 BigWig；浏览器错误清零。原始压缩 BigWig 不变并保留在 `Full evidence view`。Release 解包体积增加，但归档仍由 gzip 压缩且未进入 Git。

### 验证

- JBrowse validator 检查四个默认窗口均含 `+/-`、GFF3 弹窗必填属性、显示 BigWig v4/uncompressed header、21 套配置和 checksum；
- 实际浏览器核查 S1_003：信号和端点均正常加载，0 alert；蓝色箭头向右、橙色箭头向左；点击 `NC_000964.3:22,416 (+)` 可看到稳定 ID、raw support 652、证据类别和警告；
- 站点与完整 Pages 预览校验通过，15 项 v0.2/ingestion 回归全部通过。

## 2026-08-13 —— Rend-seq 正负链紧凑浏览视图

**分支：** `agent/assembly-track-download-demo`
**范围：** 4 个 Lalanne Rend-seq 来源的 JBrowse 展示与发布构建；没有修改核心端点表、原始信号或证据类别。

### 完成内容

1. S1_001、S1_003、S1_004、S1_005 的默认视图由 5–7 条轨道收敛为三条：基因注释、正负链配对实验信号、正负链合并候选端点。
2. 生成仅用于显示的 signed-log BigWig：`+` 链为 `+log10(1+raw signal)`，`-` 链为 `-log10(1+raw signal)`。负值只编码链方向，不表示负的实验丰度。
3. 合并端点 BED 只做逐行拼接和坐标排序，保留 BED6 的原坐标、score 和 strand；蓝色右向为 `+`，橙色左向为 `-`。
4. 原始正/负链 BigWig 与原始正/负链候选 BED 均保留在 `Full evidence view` 分类中，可从 Track selector 打开核查。
5. 默认会话只打开三条紧凑轨道；非 Rend-seq 来源和共享 assembly 多来源视图保持原有独立来源轨道逻辑。

### 遇到的问题与解决

- **E. coli 浏览器专用 gene-proximal BED 被 B. subtilis 同名文件覆盖。** 构建器首次生成合并 BED 时触发 `NC_000964.3` 不在 E. coli FAI 的硬失败。核心数据库与各来源 `processed/` 规范文件未受影响。发布构建器现从四个来源各自的 canonical processed BED 复制，并逐行检查 BED6 与预期 strand，避免再使用易冲突的旧 viewer 副本。
- **未转换的多 BigWig 叠加不能形成清楚的上下镜像。** 新增可复现的 display-only signed-log 变换；原始信号轨道继续保留，显示变换写入 track metadata 和名称。
- **E. coli 旧配置还含两条全量候选轨道。** 紧凑公开配置不再引用它们，打包器同步删除未引用的来源资产；完整规范数据仍留在本地处理目录。

### 验证

- JBrowse 构建：21 个来源配置、2 个共享 assembly 配置、133 个来源前缀资产；
- JBrowse 与 Pages 校验全部通过；15 项 v0.2/ingestion 回归全部通过；
- 实际浏览器核查 S1_003：默认只显示 3 条轨道，正链位于零线上方、负链位于零线下方，端点正负链位于同一轨道；控制台 0 warning / 0 error。

### 已知限制

- signed-log 是显示变换，不能用其纵轴值替代原始 read support；科研分析应使用原始 BigWig/TSV。
- 当前 JBrowse 的合并端点轨道依靠颜色和箭头表达链方向，尚未强制把 `+`/`-` 端点分别置于同一轨道的上下两行。

## 2026-08-13 —— 纯英文网站与 accession 导航

**分支：** `agent/assembly-track-download-demo`
**范围：** 网站生成、原始数据导航和前端回归；未修改科学记录或证据解释。

### 完成内容

1. 移除当前网页中的中文副本和语言选择按钮，全站暂时只输出英文。
2. 英文标签保留稳定的 `data-i18n-key`，后续可以用审校后的翻译字典实现语言切换，无需复制页面模板。
3. 为 GEO（GSE）、SRA（SRP/SRX）、BioProject（PRJNA）、ENA（PRJEB）和 BioStudies/ArrayExpress（E-MTAB）建立 accession 路由。
4. 22 个来源页新增 **Raw data accessions** 区域；多个 accession 分别显示和跳转，不再只提供一个笼统的 repository 链接。
5. 参考 assembly accession 链接到 NCBI Datasets；assembly 页面同时显示各来源的原始数据 accession。
6. `site/data/catalog.json` 新增 accession 与 raw-data URL，Genomes 搜索支持 accession number。

### 验证

- `python3 scripts/validate-site.py site` 与完整 Pages 预览验证通过；
- `tests/test_bted_v0_2.py` 10/10、`tests/test_bted_ingestion.py` 4/4 通过；
- v0.2 数据验证保持 21 个公开来源、1 个 audit-only 来源、28,399 条记录；
- 浏览器实测 S1_017 的 2 个 GEO accession 与 S1_020 的 5 个 BioStudies/GEO accession，链接类型正确、可见中文字符为 0、控制台无 warning/error。

### 后续决定

- 本轮不提供中文翻译；后续语言切换应使用经过人工审校的翻译字典，而不是重新在生成器中维护两套页面文案。

## 2026-08-12 —— 按导师意见完成组装中心网站演示版

**分支：** `agent/assembly-track-download-demo`
**范围：** 网站、下载与 JBrowse 共享基础设施；未修改或重新解释已冻结的科学记录。

### 完成内容

1. 将网站主入口由 22 条来源记录改为 20 个精确参考组装；完整 assembly accession 一致的 S1_007/S1_013 与 S1_015/S1_017 分别在同一组装页中显示为两个独立来源 track。
2. 保留 22 个来源详情页用于文献、accession、证据类别和限制追溯；常规坐标换算、许可字段和多份技术文件不再占据主要界面。
3. 新增组装级下载构建器。每个组装公开一份 `metadata.json`；19 个有端点数据的组装另有 `endpoints.bed`。聚合 BED 不去重，稳定 `end_id` 继续保留来源身份；S1_002 只有 metadata。
4. 下载页新增全选、清空、多选统计和无第三方依赖的浏览器端 ZIP 打包。ZIP 以组装分目录，避免不同基因组 contig 混入同一 BED。
5. 新增两套多 track JBrowse 配置。构建时比较共享来源的 FASTA/FAI SHA-256，只有参考内容一致才生成共享视图；默认会话打开即显示基因注释和两个来源 track。
6. 首页、Genomes、Download、组装页、来源页和数据说明页均保持中英文切换，并更新为个人仓库链接。
7. 新增 `docs/demo/BTED_组会展示教程_2026-08-12.md`，包含 5–7 分钟演示顺序、讲稿、问答、故障备份和不得夸大的证据边界。
8. 为个人仓库 Pages 增加 140 KB 的配置覆盖层：部署时复用现有 Release 的 123 个大型资产，只替换 21 个单来源配置、增加 2 个多 track 配置并重算 checksum；无需重复发布 93 MB 压缩包。
9. 在个人仓库 feature 分支试运行 Pages：build、资产下载、覆盖层、checksum、JBrowse/站点验证和 artifact 上传全部成功；deploy job 因 `github-pages` 环境只允许受保护分支而未启动。未绕过保护，正式 workflow 改为仅在合并 `main` 后自动部署。

### 遇到的问题与解决

- **合并 JBrowse 初次进入只显示 Launch view。** 为多 track 配置增加确定性的默认线性视图，在首条已发布端点附近打开 10 kb 窗口，并自动加载基因与两个来源 track。
- **子目录配置的参考索引返回 404。** 合并配置位于 `jbrowse/assemblies/`，资源 URI 改为 `../assets/`；校验器同时验证相对路径、来源资产范围和 FASTA/FAI hash。
- **跨组装 BED 直接拼接会产生 contig 语义冲突。** 批量下载改为 ZIP，每个 assembly 独立目录；只在同一精确 assembly 内汇集来源 BED。
- **浏览器动态下载是否有效。** 用实际浏览器选择两个组装生成 ZIP，再用 `unzip -t` 核验 4 个文件无错误；metadata 中的来源和记录数与页面一致。

### 验证

- v0.2 数据与站点回归：12/12 unittest PASS；
- 20 个组装页、22 个来源页、19 个组装 BED、20 个 metadata，总记录数 28,399；
- 两个共享组装分别为 2,848 与 2,567 条记录，来源 ID 均保留；
- 21 个来源 JBrowse 配置和 2 个多 track 组装配置通过校验；
- 完整 Pages 产物通过文件、链接、证据标签和资源路径检查；
- Playwright 桌面/移动端、中英文、筛选、多选 ZIP 和 JBrowse 实测；最终 JBrowse 控制台 0 error / 0 warning；
- `git diff --check` 通过。

## 2026-08-10 —— BTED v0.2.0 自有数据公开演示构建

**分支：** `agent/bted-v0.2-public-demo`

**范围：** 只处理 BATTER S1 自有数据与共享基础设施，不合并协作者外部来源。

### 完成内容

1. 保持 v0.1 的 24 列核心接口，新增来源特异 `source_annotations.tsv`、逐字段 `fields.json`、逐来源 manifest/BED/checksum 和少数一对多附表。
2. 冻结 22 个来源：21 个公开标准化来源、1 个 `audit_only`（S1_002），共 28,399 条核心记录。
3. 建立许可登记。17 个来源发布来源特异表；4 个 Lalanne 来源标为 `external_link_only`，逐字段登记但不复制完整补充字段。
4. 生成 21 套来源独立 JBrowse 配置、123 个带来源前缀的引用资产；S1_002 无配置。Lalanne 公开配置移除受限制的文献整理 overlay。
5. 完成 S1_005、S1_020、S1_022 的确定性数据库工程审计：双 contig、BED 转换、唯一键、证据层和参考映射检查结果写入 `data/audit/v0.2.0/priority_source_audit.json`。
6. 重构双语静态网站：英文默认/中文切换、22 个来源详情页、筛选目录、下载、原始数据入口和 21 个 JBrowse 链接。
7. 生成数据与 JBrowse Release 压缩包；增加 GitHub Actions CI 与 Pages 工作流，Pages 在部署时下载固定版本 JBrowse 资产。
8. 新增 v0.2 SOP、发布接口、版本说明、来源处理记录和可编辑 draw.io 流程图。
9. 联网审计 88 条逐来源链接（61 个唯一 URL）：83 条正常可达，5 条返回访问限制状态；无 404/410、网络失败或缺失必填入口。S1_015 的 SRA 入口已补齐。

### 遇到的问题与解决

- **作者原字段在 v0.1 核心表中会丢失。** v0.2 增加来源特异表和逐列字段清单，要求每个原列被发布、映射或明确说明未发布原因。
- **JBrowse 官方压缩代码触发站点凭据/路径扫描误报。** 供应商 runtime 改为由 JBrowse package checksum 验证；BTED 自有 HTML、JS、配置和目录数据继续严格扫描。
- **S1_008 基因关联表不是全部可一对一连接。** 805 条记录全部保留，460 条连接到稳定 `end_id`，345 条明确标记 `unlinked_author_annotation`，不强配、不丢弃。
- **S1_020 混合层容易被误用。** v0.2 公开数据和 JBrowse 只保留 S2D 的 1,165 条端点，S1C 仅在内部审计和处理记录中出现。
- **合并时 Pages 会在尚未启用且 Release 仍为草稿的状态下自动失败。** 最终审阅将 Pages workflow 收窄为 `workflow_dispatch` 手动触发；正式发布 Release、管理员启用 Pages 后再部署。

### 已完成验证

- `validate_bted_templates.py`、v0.1 compatibility validator、v0.2 validator；
- S1_005/020/022 priority audit；
- 21 配置 JBrowse package validator；
- source-only 和完整 Pages artifact validator；
- v0.1 + v0.2 共 11 项 unittest；
- `validate_bted_templates.py`：PASS；
- `validate_bted_release.py`：PASS（v0.1 回归不变）；
- `audit_v0_2_priority_sources.py` / `validate_bted_v0_2.py`：PASS；
- `validate_jbrowse_release.py`：PASS（21 配置、123 个来源前缀资产）；
- `validate-site.py site` 与完整 `.pages-preview`：PASS（完整产物 1,150 个文件）；
- `tests/test_bted_ingestion.py` + `tests/test_bted_v0_2.py`：11/11 PASS；
- draw.io XML、GitHub Actions YAML、Python syntax 和 `git diff --check`：PASS。

### 发布状态

本地数据、站点、JBrowse 和 Release 资产已构建。GitHub 推送、Release 和 Pages 激活需要有效的 GitHub CLI 登录及维护者评审；不在本地构建阶段猜测或绕过认证。

## 2026-08-10 —— PR #3 仓库根目录与 legacy 向前清理

**来源提交：** `61318db` | **状态：** 已同步进 v0.2 分支，未改写历史

### 完成内容

1. 将根目录旧报告归入 `docs/legacy/project-reports/`，将登录号快照归入 `data/audit/legacy/`。
2. 从当前 Git 树移除重复的 `docs/legacy/original-directories/`、约 168 MB read-starts 文本和 `__MACOSX`；独立调研记录已保留到项目报告目录。
3. 新增 `scripts/validate_repo_layout.py`，并更新 README、目录规范、历史索引、迁移记录和 `.gitignore`。
4. 清理是普通可逆提交，没有删除标准化公开数据，也没有执行 `git filter-repo` 或 force push。

### 验证

- 仓库布局、模板、v0.1 发布、站点和 4 项 v0.1 unittest 全部通过；
- 同步至 v0.2 后重新执行 v0.1/v0.2/JBrowse/站点完整回归。

## 2026-08-10 —— v0.1 local snapshot：本地 BTED 结果首次进入 Git

**分支：** `refactor/project-structure-and-literature-notes-v0.1`
**状态：** 已完成构建、校验与文档更新；待提交并推送。

### 完成内容

1. 审计本地 BGIRNA 工作树的 22 个 `BATTER_S1` 来源、处理记录与证据边界；将 13 篇论文与 22 个来源的统计口径明确分开。
2. 新增 `scripts/build_local_snapshot_release.py`：将本地已整理的小型结果迁入正式目录，统一为 24 列 TSV；实验端点另生成 BED6；不复制原始测序、出版商工作簿、FASTA/GFF、BigWig 或 JBrowse 包。
3. 新增 `scripts/validate_bted_release.py`：检查 22 来源齐全、来源 README/manifest、公开 evidence class、1-based→BED、链、ID、文件行数及 SHA-256。
4. 生成 `data/public/records/`：21 个 `published_standardized` 来源、28,399 条记录；17 个作者发表端点来源有 TSV+BED，4 个 Lalanne 2018 来源以 `curated_record` TSV 发布。
5. `BATTER_S1_002` 标为 `audit_only`。其作者整合 TRS 表与数据集级观察表不复制到公开端点层；`BATTER_S1_020` 的混合表和 `BATTER_S1_022` 的纯预测表也只保留公开的 checksum 审计摘要。
6. 新增 22 个 `data/registry/manifests/BATTER_S1_*.json`、22 个 `docs/sources/<source_id>/README.md`、可用的详细处理记录副本，以及发布状态表 `data/registry/batter_s1_publication_status.tsv`。
7. 更新 `README.md`、贡献指南、`data/public`/`data/audit`/`data/registry` 说明、来源索引、GitHub Pages 来源目录和方法页面；新增发布说明 `docs/releases/v0.1-local-snapshot.md`。

### 关键判断

- 本地工作不是“没做”，而是此前没有被 Git 追踪、没有统一公共 schema，也没有跨来源自动校验。
- 本版没有把 BATTER、RhoTermPredict、TransTermHP 等预测结果伪装为实验端点。
- `curated_record` 与 `author_called_endpoint` 同样可追溯，但不可使用同一种“终止子功能”措辞；浏览器发布留待下一版本。

### 验证

- `python3 scripts/build_local_snapshot_release.py --input-root /path/to/BGIRNA`：PASS（21 来源 / 28,399 条记录；实际本地快照路径未写入 Git）。
- `python3 scripts/validate_bted_release.py`：PASS（22 来源、24 列 schema、证据边界、坐标、BED、SHA-256）。
- `python3 scripts/validate_bted_templates.py`：PASS。
- `python3 scripts/build_sources_page.py`：PASS（22 来源、21 个已发布来源、28,399 条记录）。
- `python3 scripts/validate-site.py`：PASS。
- `git diff --check`：PASS。

### 后续优先级

1. 提交并推送本次 v0.1 local snapshot；开 Draft PR 前由项目成员复核许可/再分发条件。
2. 为 `BATTER_S1_002` 建立逐观测 provenance 表，判断能否拆成纯实验端点。
3. 补写 `BATTER_S1_005`、`BATTER_S1_022` 的独立详细处理记录。
4. 将本地 JBrowse 以独立、版本化、可校验的浏览器发布物部署；不能把未审计的大轨道直接塞入 Git。

## 2026-08-09 —— 外部来源正式整合入库要求 v0.1

**分支：** `refactor/project-structure-and-literature-notes-v0.1` | **状态：** 已完成文档与目录入口建设，未接收任何外部端点数据

### 完成内容

1. 新增 `docs/standards/外部来源正式整合入库要求_v0.1.md`，明确“来源搜集 ≠ 已入库”、四类来源的处置边界、批次交接包、逐来源标准化门槛、选择性合并原则和 PR 检查清单。
2. 新增 `docs/integration/README.md` 与 `data/registry/submissions/README.md`，分别作为批次整合决定与协作者来源登记快照的固定入口。
3. 在根目录 `README.md` 和 `CONTRIBUTING.md` 加入正式入口；更新目录规范中已过时的历史目录说明和 `data/audit` 的公开审计摘要定位。
4. 本轮只建立协作规范：未复制任何原始文件、未接收或发布 Fuchs / Cascino / TERMITe 的端点记录、未改动证据字段字典的正式枚举。

### 验证

- `python3 scripts/validate_bted_templates.py`：PASS。
- `python3 scripts/validate-site.py`：PASS。
- `git diff --check`：PASS。

### 待后续团队确认

- 是否正式采用 `algorithm_called_endpoint` 与 `excluded_duplicate` 两个枚举值；确认前，相关外部来源保持 `to_review` / `NA`，不得作为已标准化数据发布。
- 选择性接收协作者外部来源登记快照和核验材料时，须另开整合分支和 Draft PR，不直接合并资料搜集分支。

## 2026-08-07 —— Task 01：对照远程仓库与当前 BTED 工作状态

**分支：** `agent/reconcile-current-bted-state` | **Draft PR：** [#1](https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database/pull/1) | **状态：** 已完成第一轮并按 OpenAI 审核意见完成文档修订；修订尚未提交，待用户提交推送后最终评审

### 完成内容

1. 读取了仓库现状文档：`README.md`、`PROGRESS.md`、`data_verification_report.md`、`report_BATTER_supplementary.md`、`report_zenodo_and_documents.md`、`accession_list_verified.csv`，以及全部 13 份逐来源 README（`文献1`–`文献13`）。
2. 通过 `git ls-files` 核实了被追踪文件清单（外部 BTED 工作树无法访问；所有外部声明均标注 `to verify`）。
3. 分支相对 origin/main 的净变更为**新增 8 个 Markdown 文件，不修改任何现有文件**：
   - `docs/remote-repository-migration-inventory.md` —— 已核实的远程清单；候选材料分组（文档 / 来源元数据 / 代码 / 加工后公开资产 / 原始输入 / 临时产物），含权威来源、预期大小、公开适用性、迁移风险；禁止复制清单。
   - `docs/current-bted-status.md` —— 仓库已核实现状 vs 据报告的外部 BTED 状态（全部 `to verify`）；7 项待决事项；后续数据迁移的 8 条验收门槛。
   - `docs/github-pages-demo-plan.md` —— 静态站点范围、页面地图、公开资产、外部原始数据链接（只链接不复制）、Pages 部署与验证方案；明确 Pages 无服务端数据库或私有数据访问。
   - `docs/WORKLOG.md`、`docs/HANDOFF.md` —— 工作日志与交接说明。
   - `docs/tasks/README.md`、`docs/tasks/01-reconcile-current-bted-state.md`、`docs/tasks/02-github-pages-demo.md` —— 分支任务计划（来自本分支较早提交 `6d596a1`）。
4. 推送了提交 `f5868ae`（任务文档）与后续收尾提交（`ee039bb`、`85776aa`）；将已存在的 draft PR #1 的标题与描述更新为 Task 01 交付内容。revert 提交 `43fcc5f` 目前仅在本地，尚未推送。
5. 收尾提交后，应要求将 Task 01 的全部文档改写为中文（任务计划文件 `docs/tasks/` 为流程定义，保持英文）。

### 记录备查、本任务未处理的发现

- `docs/legacy/original-directories/文献13-PMID38030608/` 下追踪了约 168 MB 的 read-starts 文本文件与 `__MACOSX/` AppleDouble 垃圾文件。
- `README.md` 引用的 `archive/` 目录在仓库中不存在。
- 来源数量口径：13 篇 PMID（本仓库核实）vs BATTER Table S1 在这 13 篇 PMID 下列出的 22 条记录 vs 外部工作树据报的 22 来源注册表；外部注册表与 Table S1 的 22 条记录是否一一对应尚未核实。

### 收尾提交与范围修正

- 新增 `docs/WORKLOG.md`（本文件）与 `docs/HANDOFF.md`（提交 `ee039bb`）。
- `docs/legacy/original-directories/文献13-PMID38030608/README.md` 的 PMID 笔误修复（"PMID: 38030638" → "PMID: 38030608"）曾包含在提交 `ee039bb` 中，已经 revert 提交 `43fcc5f` **移出 Task 01 范围**，留待后续单独处理；Task 01 不再包含、也不再声称该修复。

## 2026-08-07 —— OpenAI 审核修订（10 项）

按 OpenAI 审核意见对 Task 01 文档完成以下修订（仅改动 `docs/` 下的文件）：

1. 纠正分支范围声明：相对 origin/main 为新增 8 个 Markdown 文件、无现有文件被修改（分支历史曾含 1 处 README 笔误修复，已 revert 移出）；不再声称"只新增 3 个文件"。
2. PMID 笔误修复已移出 Task 01，WORKLOG/HANDOFF 不再声称 Task 01 修复了它。
3. 收敛"13/13 验证通过"表述：改为"13/13 来源均确认存在包含坐标字段的核心补充表；行数核对总体相符，但部分来源存在筛选口径、混合表内容或小幅行数差异，尚不能据此将表内每条记录统一视为实验验证终点"。
4. 收敛 A 类表述：A 类补充表"可作为后续标准化和逐记录证据审核的候选输入"，不暗示可直接用于数据库构建。
5. 澄清"22"的口径：区分 13 篇 PMID、Table S1 的 22 条记录、外部工作树据报的 22 来源注册表；注明外部注册表与 Table S1 是否一一对应尚未核实。
6. 修正仓库体积描述：当前 git pack 约 30.72 MiB；read-starts 文件对压缩后 pack 大小的具体贡献未单独核实。
7. 修正 Task 02 启动条件：Task 02 先实现静态骨架；元数据 schema 与证据口径获批前不生成带科学结论的完整目录。
8. 保持 Pages 硬边界：确认 Task 02 不包含 FASTQ、出版商工作簿、私有数据、坐标数据集、JBrowse、服务端代码。
9. 使 WORKLOG、HANDOFF 内容一致；draft PR #1 的标题与描述需按修订后的文档同步更新（PR 操作需用户执行）。
10. 重新验证：以下五条命令已于本轮修订后运行，结果见下节。

### 验证（本轮修订后）

- `git diff --check`：干净（无输出，退出码 0）。
- `git status -sb`：分支 `agent/reconcile-current-bted-state` 领先 origin 1 个提交（revert `43fcc5f` 未推送）；工作区含 6 个已修改的 docs 文档（本轮修订，未提交）。
- `git diff origin/main...HEAD --name-status`：8 个新增 Markdown，无修改、无删除。
- `git diff origin/main...HEAD --stat`：8 个文件，+468 行。
- `git log --oneline -5`：`43fcc5f`（revert 笔误修复）、`85776aa`（中文化）、`ee039bb`（收尾）、`f5868ae`（任务文档）、`6d596a1`（任务计划）。

## 2026-08-07 —— Task 02：GitHub Pages 静态演示站点骨架

**分支：** 实际执行于 `agent/reconcile-current-bted-state`（任务说明称当前分支为 `agent/github-pages-demo`，与实际不符；按约束未新建分支、未执行任何 git 提交/推送/PR 操作） | **状态：** 骨架已完成并通过本地验证，待提交与评审

### 完成内容

1. 读取任务上下文：`docs/tasks/02-github-pages-demo.md`、`docs/github-pages-demo-plan.md`、`docs/current-bted-status.md`、`README.md`、`accession_list_verified.csv`。
2. 新增静态站点骨架（纯 HTML + CSS，无构建工具链、无 JavaScript、无服务端代码）：
   - `site/index.html` —— 项目目的、证据边界、范围说明（13 篇 PMID / Table S1 22 条记录 / 外部据报 22 来源注册表三口径区分）、数据来源声明、局限性。
   - `site/catalog.html` —— 书目级元数据表（45 行），由 `accession_list_verified.csv` 派生；仅 PMID、物种/菌株、期刊年份、数据库名称、登录号/DOI、数据类型六列；刻意排除 3 行基因组序列登录号（GenBank CP027858、CP027859、NC_014500.1，因参考基因组版本对齐未完成）；不含坐标、证据类别、参考基因组、记录级状态；登录号链接至 GEO/SRA/ENA/ArrayExpress/BioProject/PRIDE/DOI/GitHub 等外部公开页面。
   - `site/methodology.html` —— 数据来自公开文献补充材料（只链接不复制）、当前处于标准化阶段（坐标体系/参考基因组/证据分层 SOP/schema 均未定稿）、外部 BTED 状态全部待核实且不入站、排除项清单、可复现性说明。
   - `site/about.html` —— 项目信息、贡献者（占位）、许可证（占位，明确发布前需完成许可证/再分发检查）、反馈渠道（占位）。
   - `site/css/style.css` —— 基础样式（响应式、表格横向滚动、无外部资源引用）。
   - `site/.nojekyll` —— 令 GitHub Pages 跳过 Jekyll 处理。
3. 新增 `scripts/validate-site.py`：检查必需文件存在；产物中无 FASTQ/xlsx/zip/BED/GFF 等原始数据或坐标文件、单文件 ≤1 MiB；无根相对链接与本地绝对路径；无 API key/密码/令牌等凭据字样；无未批准证据标签（"experimentally validated"、"实验验证" 等，含否定语境一律禁止）；HTML 内部相对链接全部可解析。
4. 全部内部链接使用相对路径（如 `catalog.html`、`css/style.css`），兼容 GitHub Pages 项目子路径 `/<仓库名>/` 部署。

### 骨架阶段刻意未做的内容

- 不含任何坐标数据、记录级条目、证据类别标签、JBrowse 配置或链接。
- 不含客户端搜索/过滤（纯 HTML + CSS 约束；待元数据 schema 获批后再评估引入少量 vanilla JS）。
- 未导入外部 BTED 工作树的任何内容；未执行 git commit/push/PR 操作；未删除任何文件；未改动科学数据。

### 验证（本轮）

- `python3 scripts/validate-site.py`：PASS（6 个文件，33,127 字节，全部检查通过）。
- 负向自检：构造含 FASTQ、根相对链接、本地绝对路径、`api_key` 字样、"experimentally validated" 字样的临时目录，脚本正确报告 13 个问题并以退出码 1 结束。
- 子路径冒烟测试：以符号链接构造 `/BATTER-Transcription-Terminator-Database/` 路径前缀，`python3 -m http.server` 下 index/catalog/methodology/about/css/.nojekyll 及目录索引全部返回 HTTP 200。
- 渲染检查：Playwright 截图确认桌面（1280px）与移动（390px）视口下四页排版正常，表格横向滚动，无重叠（截图存于 /tmp，未入库）。
- `git diff --check`：干净。

## 2026-08-07 —— Task 03：仓库卫生清理方案（仅文档，未执行清理）

**分支：** 实际执行于 `agent/reconcile-current-bted-state`（任务说明称当前分支为自 `main` 新建的 `agent/cleanup-proposal`，与实际不符；按约束未新建分支、未执行任何 git 提交/推送/合并/PR 操作） | **状态：** 方案文档已完成，待评审与维护者决策

### 完成内容

1. 只读事实核查（全部命令与结果记录在 `docs/cleanup-proposal.md` 附录 A）：
   - `docs/legacy/original-directories/文献13-PMID38030608/` 下 6 个 `*_read_starts.txt` 已追踪，工作区合计 168.0 MB（33.8 / 17.1 / 44.8 / 21.4 / 33.9 / 17.0 MB），自初始提交 `b59e72a` 起入库；当前 git pack 30.72 MiB。
   - `docs/legacy/original-directories/文献13-PMID38030608/__MACOSX/` 下 6 个 `._*` AppleDouble 文件已追踪（每个约 178 B）。
   - `README.md:59` 引用的 `archive/` 目录在磁盘与全部可达历史中均不存在（`git log --all -- archive/` 无输出）。
2. 新增 `docs/cleanup-proposal.md`，包含：当前问题清单；四个清理选项（`git rm --cached` 停止追踪 / `git filter-repo` 清除历史 / BFG Repo-Cleaner / Git LFS）的逐项利弊；风险分析（历史重写对协作者、draft PR #1、文档 SHA 引用的影响）；分阶段推荐方案；精确执行命令；回滚方案。
3. 推荐结论（详见方案文档第 4 节）：**阶段 A** 立即以 `git rm --cached` + `.gitignore` + 删除 README 悬空行解决卫生问题（普通提交、零协作冲击、完全可逆）；**阶段 B** 的 filter-repo 历史重写设四道门槛暂缓（PR #1 合并、托管策略定案、镜像备份与协作冻结、SHA 引用加注）。

### 本任务刻意未做

- 未删除任何文件；未运行 `git rm`；未修改 `.gitignore`、`README.md` 或任何科学数据。
- 未运行任何改写 git 历史的命令（filter-repo / BFG / LFS migrate 均未触碰）。
- 未执行 git commit / push / merge / PR 操作；未创建分支。
- 此前工作区已有内容（OpenAI 审核修订的 6 个 docs、Task 02 的 `site/` 与 `scripts/`）保持原样，未受影响。

### 验证（本轮）

- `git diff --check`：干净。
- 方案文档中的全部事实声明均以只读命令复核（见附录 A）；未运行任何写操作。

## 2026-08-07 —— 提交与推送

经维护者确认，Task 02/03 产出直接提交到 `agent/reconcile-current-bted-state`（不再移植到独立分支）。本轮提交：

- `b453404` —— Task 01 交付文档与 Task 02 计划的评审修订（4 个 docs）。
- `7e48745` —— Task 02 静态站点骨架（`site/`）与验证脚本（`scripts/validate-site.py`）。
- `1c16af3` —— Task 03 仓库卫生清理方案（`docs/cleanup-proposal.md`，仅文档）。
- 本提交 —— WORKLOG/HANDOFF 收尾记录。

上述提交连同此前未推送的 revert `43fcc5f` 一并推送至 origin；draft PR #1 现涵盖 Task 01–03，标题与描述已同步更新，仍待最终评审。

## 2026-08-07 —— 协作入库标准 v0.1（feature/bted-v0.1-standards-and-structure）

**分支：** `feature/bted-v0.1-standards-and-structure`（基于 `origin/agent/reconcile-current-bted-state`，因后者尚未合并入 main） | **PR 基线：** `agent/reconcile-current-bted-state` | **状态：** 完成并推送，Draft PR 待评审

### 完成内容

1. 只读核查：确认 `agent/reconcile-current-bted-state` 未合并入 main、工作区干净、存在未合并 Draft PR #1；完整阅读本地 BTED 工作树的 AGENTS.md、SOP v0.2、WORKLOG、HANDOFF 与两个外部文献模板，以及本仓库 README、Pages 计划、迁移盘点、状态文档。
2. 新增 `docs/standards/` 五份标准文档：SOP v0.1（以本地 SOP v0.2 为科学基础，剔除本地路径与单机脚本）、协作者新增文献收集与入库指南、数据字段字典 v0.1（覆盖两个模板全部 50 列）、证据分层与发布边界、项目目录与协作规范。
3. 迁移两个模板至 `data/registry/templates/`（来源表 26 列 / 端点表 24 列；修正本地模板表头拼写 `axonomy_id` → `taxonomy_id`）；新增 `data/registry`、`data/public`、`data/audit` 三个 README 说明用途与边界。
4. 新增 `scripts/validate_bted_templates.py`（无第三方依赖）：检查表头存在、列数 26/24、重复列名、必备核心列、规范列名与顺序，输出 PASS/FAIL。
5. 重写 README：确立正式名称 BTED（Bacterial Transcript 3′ End Database）、协作与可复现性主仓库定位、收/不收边界、统计口径（13 篇论文 vs 22 条来源记录不混写）、协作者入口与校验命令；移除"补充表坐标可直接用于数据库构建"的旧表述。
6. 更新 `.gitignore`：追加 .DS_Store、`__MACOSX/`、`._*`、`data/local/`、`raw/`、FASTQ/BAM/CRAM/BigWig 等原始数据类型、缓存/临时/本地环境文件；未删除任何已追踪文件、未改写历史（清理建议见 `docs/cleanup-proposal.md` 与 `docs/standards/项目目录与协作规范.md`）。
7. `site/` 最小改动：methodology.html 增加"入库标准与证据边界"一节（链接 GitHub 文档）、更新外部工作树状态描述；about.html 更正项目英文名；保持 demo/骨架性质，未加 JBrowse、未加坐标数据、未加记录级条目。
8. 本轮未做：完整数据迁移、JBrowse 发布、原始数据上传、`文献N-PMID*` 目录重排、历史大文件清理。

### 验证

- `git diff --check`：干净。
- `python3 scripts/validate_bted_templates.py`：PASS（来源表 26 列、端点表 24 列）。
- `python3 scripts/validate-site.py`：PASS。
- 全仓库新增/修改文档无 `/Users/` 本地绝对路径；无新增 xlsx/pdf/zip/FASTQ/BAM/BigWig 文件。

### 遗留

- 22 个 BATTER_S1 来源的数据迁移尚未开始，须按 `docs/current-bted-status.md` 验收门槛逐来源审计。
- `文献13` 已追踪大文件与 `__MACOSX/` 的清理仍待维护者按 `docs/cleanup-proposal.md` 决策。
- `docs/standards/` 五份文档为 v0.1，接入首批真实外部文献后应回顾修订。

## 2026-08-10 —— BTED 自有数据 v0.2.0 本地交付

**分支：** `agent/bted-v0.2-public-demo` | **实现提交：** `142e371` | **状态：** 已推送，Draft PR #4 与 v0.2.0 Release 草稿已建立

### 完成内容

1. 22 个 BATTER S1 来源均生成 v0.2 manifest 和网站详情页；21 个来源发布 28,399 条统一端点记录，S1_002 保持 `audit_only`。
2. 建立核心端点表、来源特异附表、字段清单、BED6、manifest 和 SHA-256 的两层发布接口；混合证据与预测注释不进入实验端点层。
3. 完成 S1_005 双 contig、S1_020 分层和 S1_022 参考版本的重点工程审计。
4. 生成 21 套独立 JBrowse 配置、双语静态网站、22 个来源页、CI/Pages 工作流、Release 压缩包和 draw.io 流程图。
5. 完整本地验收通过：模板/v0.1/v0.2/JBrowse/网站/Pages/坐标/checksum/11 项单元测试均通过；外部链接审计无失败和必填缺失。

### GitHub 上传问题与解决

- 已创建本地提交 `142e371 feat: build BTED v0.2 public demo`，工作树干净。
- 2026-08-10 先后使用默认 HTTP、HTTP/1.1、HTTP/1.1 + 500 MiB `http.postBuffer` 推送，均未改变数据或提交。
- 失败信息包括 `Could not resolve host`、`Failed to connect to github.com port 443` 和 `HTTP2 framing layer`；随后 `curl -I --connect-timeout 15 https://github.com` 同样超时。
- 网络恢复后，HTTPS 推送因当前 OAuth 令牌缺少修改 `.github/workflows/` 所需的 `workflow` scope 被拒绝；该拒绝与数据内容无关。
- `ssh -T git@github.com` 确认本机 SSH 身份有效，随后通过 SSH 成功推送完整分支，保留 CI 与 Pages workflow。
- 已创建 Draft PR #4：`https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database/pull/4`，基线为 PR #3 的 `refactor/project-structure-and-literature-notes-v0.1`；CI `BTED validation` 通过。
- 已创建 `v0.2.0` GitHub Release 草稿并上传数据包、JBrowse 包及两个 SHA-256 文件。Release 尚未发布，Pages workflow 尚未触发。

## 2026-08-21 —— v0.3 第三阶段 B1：确定性 PostgreSQL 行物化包

**分支：** `feature/bted-v0.3-dynamic-service` | **状态：** 已实现，待主代理审查；本轮未提交、未推送、未连接数据库

### 完成内容

1. 新增 `backend/importer/materialize.py`，在 canonical validator 通过且
   `postgresql_ready=true` 后生成确定性 JSONL staging bundle；新增
   `MaterializationResult`/`MaterializationError` 和公开 `materialize_release`、
   `build_materialization_bundle` 接口。
2. canonical validator 增加只读 `export_snapshot()`，只向物化器暴露已验证的来源 manifest、
   核心 endpoint、附表原始行、registry、contig provenance 和已校验 assets；失败或长度未
   核实的 release 不可导出。
3. 新增 `materialize` CLI：要求显式输出目录和 HTTPS origin；非空目录拒绝覆盖，临时目录
   完成后原子改名；不发起远端请求、不生成数据库连接信息。manifest 保存 canonical/contig
   registry checksum、表行数/checksum、自然键辅助列模式、`planned_not_verified` origin
   状态和 `write_mode=not_written`。
4. 物化结果覆盖真实 v0.2.0：1/1/13/20/47/22/32/21/28,399/81,477/0/0/127 行
   （release_versions/import_runs/publications/assemblies/contigs/sources/accessions/
   samples/endpoints/source_annotations/genes/context/assets）。S1_002 只保留审计关联，
   无 endpoint、附表或 JBrowse 资产入口。
5. 附表按 `fields.json` evidence role 分组；`author_called_endpoint` 映射为
   `author_annotation`，预测字段保持 `prediction_annotation`，不提升核心 endpoint 证据。
   每个原始附表字段均在至少一个 `annotation_json` 分组中保留，行级 provenance 保存定位、
   证据边界和必要的角色映射；完整字段定义集中到 manifest 的 source-level provenance，
   不重复复制整行。source-specific `source_annotations.tsv` 的 asset_kind 使用 schema
   已有的 `metadata`，不扩展数据库枚举。
6. 新增 B1 回归测试：真实行数、24 列、自然键/外键闭包、S1_002 边界、附表字段覆盖与
   prediction 分层、合法 asset_kind、非法 origin、非空目录保护、固定时间 checksum 一致、
   canonical 失败不生成文件。

### B1 性能修正（主审反馈）

- 行级 `source_annotations.jsonl` 的 provenance 不再重复写入整组 `field_roles` 和
  `field_definitions`；只保留来源文件/行号、source record、未映射列、endpoint evidence、
  必要边界，以及 `author_called_endpoint → author_annotation` 的紧凑
  `original_evidence_roles`。
- 物化 manifest 新增每个 source 一条 `annotation_field_provenance`，集中保存相对的
  `fields.json` 路径与 SHA-256、完整字段定义，以及 `source_annotations.tsv` 的路径、
  SHA-256 和行数；不写入本机绝对路径。
- 真实构建后 `source_annotations.jsonl` 为约 77 MiB、总 bundle 约 115 MiB（原实现约
  248 MiB 的附表文件）；新增 100 MiB/150 MiB 体积回归测试。所有 81,477 条分组行和原始
  字段覆盖保持不变。
- 资产的 `supports_range` 在 planned origin 尚未通过 HTTP 206 审计前统一为 `false`；
  不从本地文件或计划 URL 推断远程 Range 能力。

### 验证

- `python3 -m unittest -v tests/test_bted_v03_importer.py`：32/32 PASS。
- 真实 `/tmp/bted-b1-real` 物化成功，表计数与上面一致；两次固定时间构建的
  `SHA256SUMS.txt` 一致；附表 JSONL 约 77 MiB、总目录约 115 MiB。
- `python3 -m unittest discover -s tests -p 'test*.py' -q`：64/64 PASS；
  `python3 -m unittest -v tests/test_bted_ingestion.py`：4/4 PASS；真实 validate 与
  `git diff --check` 通过。

### 未完成/边界

- 这是写库前可审计中间层，不是 PostgreSQL INSERT；下一阶段仍需独立 writer、DDL smoke
  test、事务切换和 API 查询实现。
- `assets.origin_url` 仅是 HTTPS 计划 URL；远程 origin 是否存在、Range 是否可用尚未验证。
- `genes` 与 `endpoint_gene_context` 仍为零行；参考 FASTA/FAI 不复制进 Git 或当前 bundle。

## 2026-08-22 —— v0.3 第三阶段 B2：PostgreSQL 事务 writer

**分支：** `feature/bted-v0.3-dynamic-service`
**状态：** 已实现离线可审计 writer，待主代理审查；未提交、未推送、未连接真实数据库

### 完成内容

1. 新增 `backend/importer/postgres.py`：提供 `verify_bundle`、`load_bundle`、
   `promote_bundle` 和环境变量连接辅助。验证阶段流式读取 13 个 JSONL 表，检查 release/
   schema/version、SHA256SUMS、表 checksum/byte size/row count、严格字段 allowlist、自然
   键和外键闭包；未知字段、缺失字段、非有限 JSON 数值、额外文件/目录/符号链接都会失败。
2. writer 只接受 HTTPS origin，核对 `origin_host`；`planned_not_verified` 时强制所有
   `supports_range=false`。S1_002 和其它非 published source 的 endpoint/sample/annotation
   边界在 preflight 中统一检查，endpoint 位置必须不超过已核实 contig length，且 assembly/
   contig 不能错配。
3. 事务按 release/import run → publication/assembly → contig → source → accession/sample
   → endpoint → annotation → asset → count audit 顺序执行，设置 SERIALIZABLE 和 advisory
   transaction lock，endpoint/annotation 默认每 1,000 行批量写入；异常 rollback，未使用
   `DROP`、`TRUNCATE` 或无条件 `DELETE`。同一 release 拒绝重复导入，已有 publication/
   assembly/contig 仅在全部自然键字段兼容时复用。
4. 增加每 source 的 endpoint `record_count`、annotation 行数审计，并让 promotion 复用同
   一审计。`load-postgres` 只生成 staged/validated、`is_current=false` 的 release；
   `promote-postgres` 要求 bundle 与最新 committed run 均明确 `asset_origin_status=verified`。
5. CLI 增加 `verify-bundle`、`load-postgres --confirm-write` 和
   `promote-postgres --confirm-promote`；URL 只从显式环境变量读取且不打印。新增
   `requirements-v03.txt`，声明 psycopg3 但本轮未安装。

### 验证

- `python3 -m unittest -q tests/test_bted_v03_postgres.py`：12/12 PASS。
- 覆盖真实 B1 bundle 的 22/21/28,399/81,477/127 行数、批量边界、自然键复用/冲突、
  rollback、重复 release、planned origin promotion 拒绝、额外文件/目录/符号链接、
  checksum/row count、origin host/Range 和严格 JSON 检查。
- 真实 `verify-bundle --bundle-dir /tmp/bted-b1-range-final`：通过；release `v0.2.0`，
  origin 状态 `planned_not_verified`。

### 未完成/边界

- 当前没有 psycopg3、PostgreSQL 服务或目标环境 DDL smoke test；fake connection 通过不
  等同于真实数据库写入成功。接入前需在隔离数据库执行 schema、load、重复 release 拒绝、
  rollback 和 count audit。
- 未修改 v0.2 canonical release、网站或参考 FASTA/FAI；没有下载或发布远程资产。当前
  127 个 asset 仍是计划 origin，不能 promotion。

## 2026-08-22 —— v0.3 第三阶段 C1：只读 FastAPI 查询层

**分支：** `feature/bted-v0.3-dynamic-service`
**状态：** 已实现，待主代理审查；未提交、未推送、未连接真实 PostgreSQL

### 完成内容

1. 新增 `backend/app/`：`ReadService` 独立实现 release 选择、分页、固定排序白名单、
   公开证据过滤、1-based/BED6 规则和 S1_002 audit-only 边界；`PostgresReadRepository`
   只执行参数化 SELECT，并为每次操作创建/关闭连接；`main.py:create_app()` 支持注入 fake
   repository，避免测试依赖数据库或 FastAPI。
2. 提供 `/api/v1/health`、`stats`、`sources`（列表/详情）、`assemblies`（列表/详情）、
   `endpoints`（列表/详情）、`genes`（列表/详情）、来源级 `augmentation` 和流式
   `downloads/endpoints` TSV/BED6。响应带 `release` 摘要和 provenance；endpoint JSON/TSV
   保留 v0.2 全部 24 列，BED6 用 `position - 1`/`position` 转换。
3. source 结果提供完整 publication、raw accession、source track 和已登记下载入口；endpoint
   详情只从现有 24 列提供 PMID/DOI，并链接回 source detail 查看完整 publication。只有
   published source 才生成 endpoint 下载入口，S1_002 不生成空 endpoint/JBrowse 链接。JBrowse
   config 在 assets API 尚未实现时显示 null/pending note，避免死链接。
   `include_annotations=true` 在 C1 明确返回 422，避免未经审定的附表导出边界。
4. `requirements-v03.txt` 增加 FastAPI、uvicorn、httpx 的可选依赖；没有自动安装。更新
   `docs/v0.3/api-contract.md`、`docs/v0.3/architecture.md` 与 `backend/database/README.md`，
   明确 C1 已覆盖的路由和未实现的资产 Range/Next.js/真实 DB 边界。

### 验证

- `python3 -m unittest -q tests/test_bted_v03_api.py`：10 个测试通过，FastAPI runtime 测试
  因环境未安装 FastAPI 明确 skipped。
- `python3 -m unittest discover -s tests -p 'test*.py' -q`、
  `python3 -m unittest -q tests/test_bted_ingestion.py`、`git diff --check` 应在主代理
  收尾时再次执行；本阶段不把 skipped runtime 或 fake repository 结果表述为真实 HTTP/
  PostgreSQL smoke test。

### 未完成/边界

- 未实现 `/api/v1/assets/{asset_id}`、HTTP Range/HEAD 代理、Next.js 页面、gene context、
  annotation 下载或真实 PostgreSQL/psycopg smoke test；C1 不改变 canonical release 和
  v0.2 网站。
- BED6 的 score 是格式占位 `0`，原始 `signal_or_score` 仍在 TSV/JSON；不能把 BED6 score
  解释为 coverage 或实验强度。

### C1 主审修正

- endpoint provenance 的 `release_version` 改为使用当前选定 `ReleaseContext`，不再误取
  `manifest_sha256`；endpoint/list/download SQL 显式限制 `s.release_status =
  'published_standardized'`。
- endpoint/download 的 source 校验支持 `published_only`，因此 audit-only S1_002 会返回
  404 而不是成功生成空文件。endpoint 详情保留 24 列中的 PMID/DOI，并增加
  source-annotation 行数/annotation kind 摘要；完整 publication 信息从 source detail 获取，
  附表未加载时返回明确状态。
- C1 尚未提供 `/api/v1/assets`，所以 source 详情不会生成裸 config asset ID 的 JBrowse
  死链接；已登记 config 显示 null/待 assets phase 说明。FastAPI runtime contract test
  统一预期 `invalid_pagination`，并覆盖未知 release、非法 evidence、S1_002 下载和 24 列
  endpoint 响应。

## 2026-08-22 —— v0.3 第三阶段 C2：同源公开资产代理

**范围：** 在 C1 只读查询层上增加登记资产的 GET/HEAD/单 Range 读取入口；没有连接真实
PostgreSQL、没有访问真实远端对象、没有上传 Hugging Face 或修改 v0.2 canonical 数据。

### 完成内容

1. `PostgresReadRepository.get_public_asset()` 以参数化查询读取选定 published release 中
   `is_public = TRUE` 的资产登记行，返回 origin URL/host、byte size、SHA-256、MIME、Range
   标记和 release 身份；未知或非公开 asset 不返回。
2. 新增 `backend/app/assets.py` 的 `AssetProxyService`。origin 只来自登记行，必须为
   HTTPS 且 hostname 与 `origin_host` 一致；没有 `url` 查询参数入口。GET/HEAD 使用登记
   headers，单个 `bytes=start-end`、`start-`、`-suffix` 通过上游 Range 返回 206；非法、
   多段或资产不支持 Range 返回 416 和 `Content-Range: bytes */size`。不实现多 Range、
   缓存、重试、运行时整文件 hash 或远端对象上传。
3. `ReadService` 和 `create_app()` 增加可注入 httpx client/factory；source 的 JBrowse
   config 链接改为同源 `/api/v1/assets/{asset_id}` URL-encoded `config` 参数，不再生成
   裸 asset ID 或 pending 死链接；S1_002 仍无 endpoint/JBrowse 入口。
4. 新增 `tests/test_bted_v03_assets.py`，用 `httpx.MockTransport` 覆盖 GET、HEAD、206、
   416、404、公开边界和未知 `url` 查询不影响登记 origin 的纯服务测试；FastAPI route 测试
   在未安装 FastAPI 的环境明确 skipped。

### 验证与限制

- 默认环境专项 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests/test_bted_v03_assets.py tests/test_bted_v03_api.py`：18 tests，15 passed，3 skipped（FastAPI runtime 可选依赖缺失）。
- 主代理在隔离 venv 安装 `requirements-v03.txt` 后验证 API/assets：18/18 PASS；全量
  `unittest discover`：95/95 PASS（仅有 Starlette TestClient deprecation warning）。
- 尚未执行真实远端 origin、Content-Range 远端审计、PostgreSQL 查询或部署 smoke test；离线
  MockTransport/隔离 venv 结果不等同于生产对象可访问性。

## 2026-08-22 —— v0.3 第三阶段 D1：科研用户前端骨架

**范围：** 在现有只读 API C1/C2 之上新增独立 `frontend/` Next.js App Router 界面；不修改
v0.2 canonical release、旧 site 或数据文件，不安装依赖，不连接数据库或远端服务。

### 完成内容

1. 建立 English-only 的 NCBI 风格目录界面：首页从 `/api/v1/stats` 动态显示 release、
   source、endpoint、assembly 和 augmentation 摘要，并提供 accession/assembly 搜索与
   augmentation 两个入口。
2. 提供 `/sources`、`/sources/[sourceId]`、`/assemblies`、`/assemblies/[assemblyId]`、
   `/explore`、`/endpoints/[endId]` 和 `/augmentation` 页面。页面展示物种、菌株、版本化
   assembly、论文、实验方法、原始 accession、证据类别与记录数；同一 assembly 下不同
   source 保持独立 track。`audit_only` 不显示 endpoint download 或 JBrowse 入口。
3. `frontend/lib/api.ts` 统一封装服务端/浏览器 API 请求；服务端使用显式
   `BTED_API_ORIGIN`，浏览器使用同源 `/api/v1`，rewrite 不硬编码 localhost。新增 loading、
   error、empty 状态、响应式样式和前端 README。
4. 新增不依赖 npm 包的 `frontend/scripts/check-contract.mjs`，检查必需路由、API wrapper、
   rewrite 和关键边界文案。

### 验证与限制

- `node frontend/scripts/check-contract.mjs`：通过（12 个路由/配置文件及关键契约文案）。
- 在已有 Node 依赖环境执行 `pnpm run build`：通过（Next.js 编译、类型检查、静态页面生成
  均成功）。本轮没有执行真实浏览器 smoke test 或生产 API/数据库连接。
- 前端只消费 C1/C2 已有 API；尚未实现多语言、gene context 计算或生产部署。

## 2026-08-22 —— v0.3 第三阶段 D2：assembly 级动态 JBrowse 配置

**范围：** 增加只读动态浏览器配置查询；假定 FASTA/FAI/GFF3/TBI/BigWig/BED 已作为
checksum 资产登记在当前 release 的 `assets` 表中。不下载新数据、不修改 v0.2 canonical
release/site、不连接真实数据库、不提交推送。

### 完成内容

1. 新增 `GET /api/v1/assemblies/{assembly_id}/jbrowse-config`。repository 返回一个
   assembly bundle（assembly 公共资产 + published source 公共资产），service 用固定
   builder 生成 JBrowse JSON；所有轨道 URL 均为同源 `/api/v1/assets/{asset_id}`。
2. 一个 assembly 共用一套 reference sequence；每个 published source 仍是独立 BED
   endpoint track。轨道 metadata 保留 paper PMID/DOI、raw GEO/SRA/ENA accession URL、
   evidence、record count 和 manifest provenance。S1_002/audit-only source 被排除。
3. GFF3+TBI 存在时生成参考注释轨道，并在 metadata 说明标准 GFF3 strand/arrow direction。
   BigWig 只有在已登记时显示；+/- 两个 raw BigWig 合并为一个 `MultiQuantitativeTrack`，
   不取负、不 log、不归一化，metadata 明确 `normalization=none` 和
   `display_transform=none`；单个 BigWig 保持单轨道。
4. source/assembly API 的 JBrowse 链接改为动态 config endpoint；source link 将
   `source_id` 放在 config endpoint 内部并整体 URL encode，assembly detail 在有 FASTA+FAI
   和 published browser source 时提供 `Open JBrowse` 链接。前端 assembly detail 已显示该
   按钮，缺资产时不伪造按钮。

### 验证与限制

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests/test_bted_v03_browser.py tests/test_bted_v03_api.py tests/test_bted_v03_assets.py`：默认环境 21 项中 18 passed、3 项 FastAPI runtime skipped；主代理在隔离 venv 安装 `requirements-v03.txt` 后完成 FastAPI runtime 验收，API/assets 与全量 `unittest discover` 均为 98/98 PASS（仅有 Starlette deprecation warning）。
- `tests/test_bted_v03_browser.py` 覆盖 shared assembly、2 个 source（含 audit-only 排除）、
  GFF3、metadata links、无 BigWig、双 BigWig compact raw signal 和 source 默认轨道。
- 尚未在真实 PostgreSQL 或真实 JBrowse 浏览器中 smoke test；当前 v0.2 B1 小型 canonical
  assets 尚未包含浏览器参考/信号资产，因此实际数据入库需下一阶段补齐并重新物化，不在本轮
  猜测生成 FASTA/GFF3/BigWig。

## 2026-08-22 —— v0.3 第三阶段 D3：浏览器资产 inventory 接入 materializer

**范围：** 只读取 tracked `data/registry/jbrowse_assets.v0.2.0.tsv` 并生成 PostgreSQL
写库前 staging 行；没有上传对象、连接数据库、修改 v0.2 canonical release 或声明远端
URL 已可访问。

### 完成内容

1. `scripts/build_v03_jbrowse_asset_inventory.py` 从既有 v0.2 JBrowse bundle 的配置、
   `SHA256SUMS.txt` 与 canonical endpoint BED 生成 tracked TSV/JSON inventory。最初按
   20 个 published assembly、109 行估算；核对 registry 和 checksum 后确认 21 个
   published source 实际对应 19 个唯一 assembly：`BATTER_S1_007`/`BATTER_S1_013`
   共享 `GCF_000739105.1`，`BATTER_S1_015`/`BATTER_S1_017` 共享
   `GCF_005519465.1`。共享参考资产按 checksum 一致性去重，因此最终为 105 行。
2. `materialize` 增加显式 `--jbrowse-asset-inventory`；未提供时保持原 127 个 canonical
   小型资产。提供当前 105 行 inventory 时，21 个 canonical BED 按相同 logical path
   替换旧行，再加入 76 个 assembly-scoped reference asset 和 8 个 source-scoped raw
   BigWig，最终为 211 行。
3. inventory 与 release version、21 个 published source、19 个 published assembly、
   canonical BED checksum/size 和 source/assembly 关系交叉核对。S1_002 不允许出现浏览器
   资产；reference asset 写 `assembly_id_ref`，BED/BigWig 写 `source_id_ref`。
4. browser asset 的计划 origin 使用安全 `object_path` 并保留目录斜杠；所有
   `supports_range=false`。核验后将 28 个 `external_link_only` 对象明确设为
   `is_public=false`。manifest 记录 inventory 相对路径、SHA-256、105/21/76/8 统计和
   `planned_not_verified` 状态。

### 验证与限制

- focused inventory materialization：4/4 PASS；主代理使用含 FastAPI 依赖的
  `/private/tmp/bted-v03-api-venv` 运行全量 `unittest discover`：107/107 PASS、无 skip
  （仅有 Starlette `TestClient` deprecation warning）；ingestion 回归 4/4 PASS。真实
  bundle 为 211 assets，PostgreSQL `verify_bundle()` 通过。
- 既有无参数 127-asset 回归继续由 importer/postgres 测试覆盖。
- 对象尚未上传，也未做 HTTP 206、真实 PostgreSQL 或真实 JBrowse smoke test；当前清单
  只是确定性 inventory/import 中间层。

## 2026-08-22 —— v0.3 GFF-derived genes：真实查询层物化

**范围：** 仅把 tracked JBrowse reference GFF3/FAI 派生为可查询 genes 和必要的 assembly
contigs；不修改 canonical v0.2 endpoint、canonical contig registry 或计算
`endpoint_gene_context`，也没有上传对象或连接 PostgreSQL。

### 完成内容

1. `backend/importer/materialize.py` / `scripts/import_bted_v03.py` 支持可选
   `--jbrowse-bundle-root`。只有同时提供 `--jbrowse-asset-inventory` 才启用 gene 导入；
   inventory 中 19 个去重 `reference_gff3` 与对应 FAI 的 bundle path、size、SHA-256 均
   经校验。GFF3 当前按已验证的 gene-only 格式读取，gene ID 为稳定全局
   `<assembly_accession>:<original GFF ID>`，attributes JSON 保留原始字段（URL-decoded
   供页面显示），gene_name 为 `gene` 优先、否则 `Name`。
2. 当前真实 bundle 物化得到 95,437 genes、49 contigs、0
   `endpoint_gene_context`；GCF_000008685.2 的两个 FAI-only endpoint registry 之外
   contig 被补入派生 query layer。5 条环状 replicon unrolled 坐标超过线性 FAI 长度，
   保留 GFF 原始 start/end，并以 `_bted_coordinate_note`/`_bted_contig_length` 记录
   caveat；未裁剪坐标。
3. `backend/importer/postgres.py` preflight 增加 genes natural-key/坐标/strand/asset
   校验，context 继续强制为空；writer 在 assets 后按 batch 插入 genes，audit 在启用
   gene 时核对 genes/context 数量。`backend/database/schema.sql` gene trigger 保留
   assembly/contig 和 GFF3 asset/sha 检查，不把线性 FAI 上限用于环状 unrolled 坐标。
4. 新增 `tests/test_bted_v03_genes.py`：fake preflight + assets-before-genes writer
   顺序测试，以及本地 bundle 可用时核对 49/95,437/0 和 5 条 unrolled 坐标的真实 focused
   test。无 bundle 的 CI 仍执行默认 47/0 路径及语法/结构检查。

### 验证

- 本地真实 materialization：`contigs=49`、`genes=95,437`、
  `endpoint_gene_context=0`；`verify_bundle()` 和 `_preflight()` 均通过。
- `python -m unittest -v tests/test_bted_v03_genes.py`：2/2 PASS（含本地真实 bundle）。
- `python -m unittest -v tests/test_bted_v03_postgres.py`：13/13 PASS。
- `git diff --check`：PASS。

### 后续限制

- gene 是 GFF-derived query layer，不替代 endpoint evidence，也不改变 canonical release。
- endpoint_gene_context 仍需未来单独算法/审核任务；本轮不生成任何上下文结果。
- 真实 PostgreSQL/远端对象/JBrowse 浏览器 smoke test 仍未执行。

## 2026-08-22 —— v0.3 公共浏览器资产远端交接准备

**范围：** 只补充 CI 覆盖和维护者操作说明；没有上传对象、联网审计、连接 PostgreSQL
或修改 materializer/importer 实现。

### 已核实事实

- tracked browser inventory 共 105 行，覆盖 19 个唯一 assembly。
- `prepare_v03_public_asset_objects.py` 按
  `is_public=true AND redistribution_status=verified_redistributable` 选择 77 个可再分发
  object；另有 28 个 `external_link_only` object，均为 `is_public=false`。
- 当前真实 GFF/FAI bundle 的 gene query layer 为 95,437 genes；
  `endpoint_gene_context` 仍为 0。
- 没有任何实际对象上传，也没有远端 HTTP 206 审计结果；origin 仍不能标为 verified。

### CI 与交接

1. CI 增加 gene importer、public-object preparation 和 remote-audit 的专项 unittest，
   同时将 `prepare_v03_public_asset_objects.py`、`audit_v03_remote_assets.py` 以及
   `backend/importer/{canonical,materialize,postgres}.py` 纳入 `py_compile`。
2. 新增 `docs/v0.3/deploy-assets.md`，固定 materialized assets → 164 objects → 外部/人工上传 →
   HEAD/单字节 Range 206 audit → 后续 verified bundle/import verification 的最短顺序。
   文档明确仓库不实现上传、不保存凭据，离线 mock transport 不是远端可用性证据。

## 2026-08-22 —— v0.3 远端资产审核报告应用步骤

- `audit_v03_remote_assets.py` 的确定性报告补充 `object_path` 和 `byte_size` 身份字段。
- 新增 `apply_v03_remote_asset_audit.py`：required 集合来自 materialized assets 中全部
  public + verified_redistributable 行（当前 164），而不是只取 77 行 browser inventory；
  tracked inventory 仅对 browser subset 做额外 provenance 核对。
- 只有 164/164 的身份、HEAD 200 与 Range 206 均通过时，才输出
  `asset_origin_status=verified` 的新 bundle 并将这些行设为 `supports_range=true`；private/
  `external_link_only` 对象保持 false。完整 materialized prepare 产生 164-object manifest；
  仅含 77 个 browser 对象的旧 report 会被拒绝。
- focused audit/apply tests：8/8 PASS；默认环境全量 `unittest discover`：118 tests
  PASS（3 个可选 FastAPI runtime skipped）；`git diff --check`：PASS。

## 2026-08-22 —— v0.3 完整 public-object preparation 修正

上一条交接记录中的 inventory-only 77-object preparation 已扩展为完整
materialized asset preparation。带 JBrowse inventory 的 planned bundle 当前有 211 行：
其中 164 行同时满足 `is_public=true` 与
`redistribution_status=verified_redistributable`，47 行 private/external 被排除。
77 个 tracked inventory browser 行仍作为 identity/provenance cross-check；其余 87 个
canonical metadata、checksum、endpoint/annotation 等 API 小文件由同一个
`assets.jsonl` 选择，不再手工补列。

`scripts/prepare_v03_public_asset_objects.py` 现在要求 `--materialized-bundle`，从该
bundle 的 `assets.jsonl` 读取完整清单，并按 inventory 的 `bundle_path`、canonical
release 的 `records/` 路径解析本地源文件。每个 `ASSET_OBJECTS.json` 行均保留
`asset_id`、`object_path`、`byte_size`、`sha256`；本地源文件在复制前后都核对大小和
SHA-256。新增专项测试核对真实 164/47/77 计数、canonical/JBrowse 源解析、确定性输出和
private/external 排除。没有上传对象、联网审计或修改 canonical release。

本轮 `tests/test_prepare_v03_public_asset_objects.py`：2/2 PASS；默认环境全量
`unittest discover`：123 tests（3 个可选 FastAPI runtime skipped）通过，
`git diff --check` 与相关脚本 `py_compile` 通过。

## 2026-08-22 —— v0.3 public-link availability 修正

ReadService 与动态 JBrowse builder 现在按公开资产判定浏览器可用性：source 必须同时
满足 `published_standardized`、`record_count > 0` 和公开 endpoint BED；assembly 还必须
有公开 FASTA+FAI 且至少存在一个这样的 source。旧 `has_jbrowse` 标志不再单独生成链接，
`external_link_only` 的原始 accession/repository 链接仍保留。新增 API/browser focused
tests 覆盖缺失或私有 BED、私有参考资产及默认 source 选择边界；未修改生物数据或上传对象。

## 2026-08-22 —— remote-audit apply CLI 入口修正

真实端到端命令从仓库根运行 `python3 scripts/apply_v03_remote_asset_audit.py ...` 时，曾因
Python 只把 `scripts/` 放入 module search path 而触发 `ModuleNotFoundError: backend`。
现按 `scripts/import_bted_v03.py` 的既有方式，在导入 `backend` 前加入解析后的仓库根路径。
新增 subprocess `--help` 测试，从仓库根直接启动并确认 CLI 参数可用；未联网、上传或写库。

## 2026-08-22 —— materialized asset origin 路径统一

真实端到端演练发现 87 个 public canonical 小文件仍按 `asset_id` 生成 origin URL，与
public-object preparation/audit 使用的 `records/<source>/...` logical path 不一致。现将
127 个默认 canonical asset 与接入 inventory 后的 211 个 asset 全部统一为
`<asset_origin_base>/<logical_path>`；`asset_id` 只保留为数据库/API key。

materializer version 升为 `bted-materializer-0.3.0-b2`，因此重新物化时资产表、manifest 与
bundle checksum 会确定性变化，表行数仍保持默认 127、inventory 模式 211。PostgreSQL
preflight 同步要求 manifest origin base/host 有效，并拒绝 origin URL 与 logical path
不一致的 bundle。

## 2026-08-22 —— v0.3 client-side endpoint explorer

`/explore` 改为 client-side 查询视图：过滤条件和页码保留在 URL，可在页面内更新、用浏览器
前进/后退恢复，并显示 loading/error/empty 状态。当前过滤条件可分别下载 TSV 与 BED6；
downloads endpoint 同步接收 `gene_or_locus`、`position_min`、`position_max`，沿用既有
endpoint 过滤和 1-based 坐标语义。未改变 canonical 数据或 endpoint_gene_context。

Endpoint detail 现在按 assembly browser availability 生成真实 `loc` deep link（±500 bp）；
无公开 JBrowse 时明确显示 unavailable。Explore 表仅提供 `View record`/`Assembly details`
链接，不再把 assembly hash 伪称为已定位浏览器入口。

## 2026-08-22 —— v0.3 gene query 用户入口

assembly list/detail 现在返回同一 release 的 `gene_count`；新增 `/genes` 前端目录，调用
现有 `GET /api/v1/genes` 支持 assembly、contig、locus tag、stable gene ID、feature type
和 1-based start 区间过滤。列表提供 gene detail 与 assembly context 入口，导航增加 Genes。
本轮只呈现 GFF-derived annotation，不计算 `endpoint_gene_context`，也未修改生物数据。

## 2026-08-23 —— Lalanne 四来源资产级许可修正与 JBrowse 恢复

1. 复现 `BATTER_S1_001` JBrowse 404，定位为文章开放获取状态被错误扩展到所有数据资产：
   FASTA/FAI/GFF3/TBI、BED 和 BigWig 均被标为 `external_link_only`。
2. 新增 `data/registry/batter_s1_asset_redistribution.v0.3.tsv`，按资产类型记录许可：NCBI
   reference、GEO signal、BTED standardized output 可公开；作者特异补充字段继续排除。
   没有修改端点坐标、证据类别、参考版本或 S1_002 的 audit-only 边界。
3. 重新生成 105 行 JBrowse inventory；materialized 仍为 211 assets，public 从 164 增至
   208，private 仅剩 S1_002 的 3 个 metadata/checksum objects。HF 新固定 revision 为
   `463cfc8bd582a5ed9d2c426822148c3f1e56c4d0`，208/208 对象通过 HEAD 200 与单字节
   Range 206；audit 文件 SHA-256 为
   `8df250f34c94f4ce858694575356649c4da1336ab6a1011e52a756bdd99551cf`。
4. Cloudflare D1 以 `migrations/0002_restore_lalanne_assets.sql` 定向更新四个来源、相关
   tracks 与 assets，没有删除或重导 endpoints。Worker 更新 HF revision 并重新部署。
5. 动态 JBrowse 现在为四个 Rend-seq 来源展示 reference gene、原始 +/− strand BigWig
   和独立 endpoint BED；信号未由 BTED 归一化。每个 source track metadata 提供论文题目、
   PubMed、DOI、GEO/raw accession 与 BTED record URL。
6. 线上 E. coli 真实页面加载成功；FASTA、BED、forward BigWig 均 HEAD 200、Range 206，
   返回 1 byte。首次部署的 Worker 500 源于 gene track 没有显式 displays 数组，已用正常
   display fallback 修复并保留问题记录。
7. 最终回归：127 tests PASS（3 个可选 FastAPI tests skipped），ingestion 4/4 PASS，site
   validator、Worker syntax 与 `git diff --check` PASS。四个修复来源的 config 均 HTTP 200，
   各含 gene、raw + signal、raw − signal、endpoint 四条 track；远程 D1 为 211 assets =
   208 public + 3 private。

## 2026-08-22 —— v0.3 Hugging Face public asset handoff：固定 revision 完成

**范围：** 只上传并审计已登记的 public objects；没有上传 private/external objects，没有
连接 PostgreSQL、没有 promote、没有修改 canonical `v0.2.0` 数据或 Git 历史。

### 完成内容

1. 以账户 `seu-yolo` 创建并使用 public dataset
   `https://huggingface.co/datasets/seu-yolo/BTED-v0.3-assets`。最终固定 revision 为
   `d12190e434057edaf2c2bdbf19132f1e41873c38`；pinned origin 为
   `https://huggingface.co/datasets/seu-yolo/BTED-v0.3-assets/resolve/d12190e434057edaf2c2bdbf19132f1e41873c38`。
2. 带当前 105 行 browser inventory 重新 materialize canonical `release_version=v0.2.0`：
   211 行 assets，其中 164 行满足 `is_public=true` 与
   `redistribution_status=verified_redistributable`，47 行 private/external 被排除；
   164 个 public object 的本地登记字节总数为 126,280,212。
3. 使用 resumable `hf upload-large-folder` 提交 164 个 object 加
   `ASSET_OBJECTS.json` 与 `SHA256SUMS.txt`；远端 snapshot 另含 Hub 自动生成的
   `.gitattributes`。没有上传 staging JSONL、audit report、token 或 private 文件。
4. 对 pinned origin 重新执行真实逐对象 HEAD 与单字节 Range audit：164/164 HEAD `200`、
   164/164 Range `206`，每行 `supports_range=true`/`ok=true`。证据已纳入
   `data/registry/remote_asset_audit.v0.2.0-hf.json`，SHA-256 为
   `3c4fed76dbd996164229605bc32eb52afed68c94a56bfb4233df2e6f492f46e0`。
5. 以 pinned audit 离线 apply 生成 `asset_origin_status=verified` bundle；verified
   manifest SHA-256 为
   `849876269dd1827014f1a75daacd2fdf418c642eb96fd39984d58641913f2264`，并通过
   `verify-bundle`（211 assets、28,399 endpoints、95,437 genes、0
   `endpoint_gene_context`）。最终 bundle 是本机临时交接物，不提交到 Git；旧 mutable
   `resolve/main` bundle 不作为最终交付。

### 验证与剩余事项

- `python3 -m unittest -v tests.test_bted_v03_assets tests.test_audit_v03_remote_assets tests.test_apply_v03_remote_asset_audit`：17 tests，16 passed、1 个 FastAPI optional test skipped。
- `python -m unittest -v tests/test_bted_ingestion.py`：4/4 PASS。
- `git diff --check`：待本轮文档修改完成后运行。
- 剩余：真实 PostgreSQL/container import smoke、Render/Neon/Vercel deployment、轻量
  JBrowse shell 打包，以及 `endpoint_gene_context` 算法定义/审核；本次资产证据不代表
  `v0.3.0` 数据 release 或 production promotion。
