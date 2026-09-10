# BTED v0.3 Cloudflare preview deployment

当前可执行部署路线是一个 Cloudflare Worker + D1 + Worker Static Assets
deployment。它复用仓库现有的 `site/` 静态 UX，Worker 负责 `/api/*` 查询、动态
JBrowse config 和登记资产的同源 GET/HEAD/单 Range 代理。现有 FastAPI/PostgreSQL/Next.js
实现保留为 future/alternative，不是本路线的依赖；Render/Neon/Vercel 不在当前任务中创建。

## 已验证的输入

- canonical `release_version` 保持 `v0.2.0`；D1 行的 `status=preview` 只是查询投影，
  不是 promotion 或新的 `v0.3.0` data release。
- verified bundle 来源为固定 Hugging Face revision：
  `https://huggingface.co/datasets/seu-yolo/BTED-v0.3-assets/resolve/463cfc8bd582a5ed9d2c426822148c3f1e56c4d0`。
- bundle materializes 22 sources、20 release assemblies、49 contigs、32 accessions、
  211 registered assets（208 public）、22 tracks 和 28,399 endpoints；19 sources
  qualify for source-level augmentation。source annotations 保留在 HF/metadata asset，
  genes 未进入 D1，因为当前 catalogue 页面/API 不查询它们。
- 208 public objects 已由固定 revision 的真实 audit 通过 HEAD 200 + 单 Range 206；
  private/external 3 项 S1_002 audit-only 对象只留 D1 登记和不可代理状态。

## Worker 配置

`prototype/accession-range/wrangler.jsonc` 是唯一当前部署配置：

- `assets.directory` 指向仓库既有 `site/`，不重做页面；
- D1 binding 名为 `BTED_DB`，数据库名为 `bted-catalogue-v03-preview`；
- `HF_RESOLVE_BASE` 已固定到上述 revision，`ALLOWED_ORIGIN_HOST` 为
  `huggingface.co`；
- `database_id` 在远程 D1 创建后才填入，不把 token、密码或个人 URL 写进 Git。

## 生成并导入 D1

生成器只读取 verified bundle，并把可重建 SQL 批次写到仓库外的明确临时目录；不会在 Git
中写入巨型 seed：

```bash
python3 scripts/generate_bted_d1.py \
  --bundle-dir /path/to/verified-bundle \
  --output-dir /private/tmp/bted-v03-d1-import \
  --batch-size 1000
```

生成 `schema.sql`、`00_release.sql` 到 `07_tracks.sql`、分片的
`08_endpoints_*.sql` 和 `IMPORT_SUMMARY.json`。首次创建本地 D1 后按文件名顺序执行：

```bash
npx wrangler d1 execute bted-catalogue-v03-preview --local \
  --file /private/tmp/bted-v03-d1-import/schema.sql \
  --config prototype/accession-range/wrangler.jsonc

for f in /private/tmp/bted-v03-d1-import/[0-8][0-9]*.sql; do
  npx wrangler d1 execute bted-catalogue-v03-preview --local \
    --file "$f" --config prototype/accession-range/wrangler.jsonc || exit 1
done
```

Wrangler 4.125 的 local D1 executor 不接受 SQL 文件中的显式 `BEGIN/COMMIT`；生成器让
D1 自己处理 statement batching。实际 smoke 的最终计数为 1 release、13 publications、
20 assemblies、49 contigs、22 sources、32 accessions、211 assets、22 tracks 和 28,399
endpoints。生成批次和 `.wrangler/` local state 都是临时物，不应提交。

## Local Worker smoke

以有界进程运行，不要将 `wrangler dev` 作为交互式后台服务遗留：

```bash
npx wrangler dev --local \
  --config prototype/accession-range/wrangler.jsonc \
  --port 8787 --ip 127.0.0.1
```

至少检查：

```text
/api/health
/api/stats
/api/catalogue?page_size=1
/api/sources
/api/sources/{source_id}
/api/assemblies
/api/assemblies/{accession}
/api/endpoints?page_size=1
/api/endpoints/{end_id}
/api/augmentation
/api/assemblies/{accession}/jbrowse-config
/api/assets/{registered_public_asset_key}       HEAD and Range: bytes=0-0
/api/remote-data/{registered_public_asset_key}  alias
```

`/api/assets/*` 只接受 D1 中登记、active、public 的 key；`?url=`、private asset、未知
key 和未列入 allowlist 的 origin 必须被拒绝。实际本地 smoke 结果：health/stats/catalogue/
sources/assemblies/endpoints/augmentation/JBrowse 均 200；FASTA 与 BED HEAD 为 200、单字节
Range 为 206；任意 origin 尝试为 400；缺 public FASTA+FAI 的 assembly 返回 404。

## Remote Cloudflare preview

本轮已完成短的非交互认证检查、D1 创建/导入和 Worker 部署：

```bash
CI=1 npx wrangler whoami
```

认证成功；远程 D1 名称为 `bted-catalogue-v03-preview`，已导入并查询到 1 release、13
publications、20 assemblies、49 contigs、22 sources、32 accessions、22 tracks、211
assets（208 public）、28,399 endpoints 和 19 augmentation sources。远程 D1 实测库大小
约 32.78 MB，D1 行状态为 `v0.2.0/preview`，没有执行 promotion。

Worker + Static Assets 已部署到：

`https://bted-catalogue-v03-preview.bted-v0-3-dynamic-service.workers.dev`

线上 smoke 已验证 health/stats/catalogue/sources/assemblies/endpoints/augmentation、
source/assembly/endpoint detail、JBrowse config 均 `200`；固定 HF FASTA/BED HEAD 为
`200`，单字节 Range 为 `206` 且返回 1 byte；`remote-data` alias 为 `200`；unknown/private
asset 为 `404`；任意 `?url=` 为 `400`。Worker Static Assets 的 `.html` 入口会返回
Cloudflare clean-URL `307`，浏览器跟随后 `/sources`、`/catalog`、`/accession-range-demo`
等科研页面均 `200` 且内容非空；页面没有 localhost/旧 local API 引用。

2026-08-23 资产级许可修正后，HF 固定 revision 更新为
`463cfc8bd582a5ed9d2c426822148c3f1e56c4d0`，208/208 public objects 通过 HEAD 200 与
Range 206。四个 Lalanne Rend-seq 来源恢复 reference、BED、原始正负链 BigWig；S1_002 的
3 个 audit-only objects 仍不公开。JBrowse source tracks 的 metadata 现提供 PubMed、DOI、
GEO/raw accession 与 BTED record URL，信号按仓库原值展示，不做 BTED 归一化。

### JBrowse shell 与真实浏览器 smoke

`site/jbrowse/` 只从既有 v0.2 JBrowse release bundle 提取一份 4.3.0 app shell：
`index.html`、manifest/favicon、运行时 JavaScript/CSS/fonts 共 455 个文件、6,128,344
bytes（5.844 MiB），最大单文件 728,605 bytes。没有复制 v0.2 bundle 的 FASTA、FAI、GFF3、
BED、BigWig、配置或 source maps；这些对象继续由登记的 HF asset 代理提供。静态 site 总体积
实测为 6,568,327 bytes，满足本 preview 的 Worker Static Assets 体积边界。

`scripts/build_v0_2_site.py` 现在为 source、assembly、record 和 catalogue 的 JBrowse
按钮生成部署域名内的
`/jbrowse/index.html?config=<encoded https://.../api/assemblies/{accession}/jbrowse-config[?source_id=...]>`；
`BTED_PREVIEW_ORIGIN` 可在重新生成 site 时覆盖默认 preview origin。accession 页面运行时
按钮同样指向同源 `/jbrowse/index.html`，并使用静态 payload 中的 Worker config URL。Worker
Static Assets 对显式 `index.html` 返回 clean-path `307`，浏览器跟随至 `/jbrowse/` 后 shell
为非空 `200`（577 bytes），config query 会保留。

真实 Playwright smoke：共享 assembly `GCF_000739105.1` 打开 `CP009124.1`，显示
`Reference gene annotation`、`BATTER_S1_007` 和 `BATTER_S1_013` 两条 source track，console
为 0 error / 0 warning；单 source assembly `GCF_003054575.1` 显示 gene annotation 和
`BATTER_S1_009` track，console 同样为 0 error / 0 warning。两份 config 发出的所有 FASTA/
FAI/GFF3/TBI/BED asset URL 均实测 HEAD `200`、单 Range `206`。

部署命令使用：

```bash
npx wrangler deploy --config prototype/accession-range/wrangler.jsonc
```

后续若需修改 preview，仍需先用非交互 `CI=1 npx wrangler whoami` 检查认证；不要在 Git、
shell history、日志或聊天中粘贴 API token、密码或带凭据的 URL。不要对该 preview 使用
DROP/TRUNCATE/DELETE，也不要把它写成 canonical v0.3.0 release。
