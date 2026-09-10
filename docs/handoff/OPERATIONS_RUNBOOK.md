# BTED 维护与运行手册

**当前部署形态：** Cloudflare Worker + D1 + Worker Static Assets + Hugging Face 固定版本对象

**canonical 数据版本：** `v0.2.0`

**状态：** developer preview，不是正式 `v0.3.0` 数据发布

## 1. 资源定位

| 资源 | 当前值 |
|---|---|
| Worker | `bted-catalogue-v03-preview` |
| 线上地址 | `https://bted-catalogue-v03-preview.bted-v0-3-dynamic-service.workers.dev` |
| D1 数据库 / binding | `bted-catalogue-v03-preview` / `BTED_DB` |
| Wrangler 配置 | `prototype/accession-range/wrangler.jsonc` |
| HF dataset | `seu-yolo/BTED-v0.3-assets` |
| HF 固定 revision | `463cfc8bd582a5ed9d2c426822148c3f1e56c4d0` |
| 资产审计证据 | `data/registry/remote_asset_audit.v0.2.0-hf.json` |

线上最后一次完整记录为 2026-08-23：208 个 public objects 全部通过 HEAD 200 和单字节
Range 206。2026-09-06 本机访问 Cloudflare 与 Hugging Face 均在 HTTPS 建连时超时；这只能
记为“当前执行环境未复核”，不能据此断言服务宕机。

## 2. 第一次接手

```bash
git clone git@github.com:seu-yolo/BATTER-Transcription-Terminator-Database.git
cd BATTER-Transcription-Terminator-Database
git switch handoff/bted-maintainer-2026-09
git status -sb
```

依次阅读 `AGENTS.md`、`docs/HANDOFF.md`、本目录四份交接文档、数据入库 SOP、目标来源
manifest 和 processing record。不要把 `/private/tmp`、`.wrangler/`、数据库 URL、token
或原始大文件加入 Git。

## 3. 本地数据与 D1

D1 是 SQLite-compatible 的线上查询投影；BTED 没有使用 MySQL。FastAPI/PostgreSQL/Next.js
代码是 future/alternative path，不是当前部署依赖。

从 verified bundle 生成临时 SQL：

```bash
python3 scripts/generate_bted_d1.py \
  --bundle-dir /path/to/verified-bundle \
  --output-dir /private/tmp/bted-v03-d1-import \
  --batch-size 1000
```

本地导入：

```bash
npx wrangler d1 execute bted-catalogue-v03-preview --local \
  --file /private/tmp/bted-v03-d1-import/schema.sql \
  --config prototype/accession-range/wrangler.jsonc

for f in /private/tmp/bted-v03-d1-import/[0-8][0-9]*.sql; do
  npx wrangler d1 execute bted-catalogue-v03-preview --local \
    --file "$f" --config prototype/accession-range/wrangler.jsonc || exit 1
done
```

预期投影计数：1 release、13 publications、20 assemblies、49 contigs、22 sources、
32 accessions、211 assets（208 public）、22 tracks、28,399 endpoints，以及 19 个
source-level augmentation summaries。95,437 个 GFF-derived genes 存在于物化结果，
但当前 D1 catalogue 不查询 genes。

## 4. 本地 Worker 与 JBrowse

普通本地启动：

```bash
npx wrangler dev --local \
  --config prototype/accession-range/wrangler.jsonc \
  --port 8787 --ip 127.0.0.1
```

本机 workerd 无法访问 HF 时，可把已登记且校验过的资产放在仓库外，以只读 HTTP 服务监听
`127.0.0.1:8790`，再显式设置：

```bash
LOCAL_ASSET_BASE=http://127.0.0.1:8790 \
  npx wrangler dev --local \
  --config prototype/accession-range/wrangler.jsonc \
  --port 8787 --ip 127.0.0.1
```

`LOCAL_ASSET_BASE` 仅对来自 `localhost`/`127.0.0.1` 的请求生效，且只接受无凭据、
无 query/hash 的 loopback HTTP URL。非 loopback 请求仍固定走 allowlisted HF HTTPS origin。
2026-09-06 检查时 8787 和 8790 均未运行；临时资产目录已经不存在，必须从登记资产重新构建，
不能把旧绝对路径当成项目依赖。

本地入口：

- 仪表盘：`http://127.0.0.1:8787/evidence-layers-preview`
- JBrowse：由仪表盘按钮进入，config 保留 `source_id=BATTER_S1_003&pilot=three-layer`

## 5. API smoke

至少核验：

```text
/api/health
/api/stats
/api/catalogue?page_size=1
/api/sources
/api/assemblies
/api/endpoints?page_size=1
/api/augmentation
/api/assemblies/GCF_000009045.1/jbrowse-config?source_id=BATTER_S1_003
/api/assets/{registered_public_asset_key}
/api/remote-data/{registered_public_asset_key}
```

公开资产 HEAD 应为 200，`Range: bytes=0-0` 应为 206。未知/private asset 应为 404，
任意 `?url=` origin 尝试必须被拒绝。

## 6. 500/502 排障

- `500 Network connection lost`：旧行为，多见于 local workerd 无法访问固定 HF origin。
- `502 asset_origin_unavailable`：新结构化行为，表示当前 origin 不可达；不代表资产损坏，
  也不代表 JBrowse 数据已恢复。
- FAI/BigWig/BED 失败时先核对 D1 中的 asset key、logical path、public 状态和 checksum，
  再查网络；不要绕过登记表直接代理任意 URL。
- JBrowse 空白时检查 config、FASTA+FAI、GFF3+TBI、BigWig/BED 的 HEAD/Range，以及浏览器 console。
- CORS 不应是同源 Worker 路线的正常问题；若未来拆分静态域名，必须重新设计 CORS。

## 7. 验证与部署

```bash
python3 -m unittest -v \
  tests/test_bted_worker_assets.py \
  tests/test_bted_three_layer_preview.py \
  tests/test_bted_browser_wrapper.py \
  tests/test_bted_v03_browser.py \
  tests/test_bted_ingestion.py
python3 -m unittest discover -s tests -p 'test*.py' -q
node --check prototype/accession-range/src/worker.js
python3 scripts/validate-site.py site
git diff --check
```

部署前先只读检查身份、当前 deployments、D1 计数和固定 HF revision。部署命令是：

```bash
npx wrangler deploy --config prototype/accession-range/wrangler.jsonc
```

该命令会真实改变线上状态，只能在明确发布授权后执行。本交接分支未执行 deploy、D1 写入或
HF 上传。固定 revision 未变化时无需重复上传；仅在对象集合/origin 改变或抽样失败时重跑完整
208-object remote audit。
