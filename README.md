# BTED — Bacterial Transcript 3′ End Database

BTED 将公开的细菌转录 3′ end 实验整理为可追溯、可下载、可在 JBrowse 中核对的标准数据。

本仓库保存数据标准、来源注册表、小型发布表、处理记录、构建脚本和网站源文件。原始 FASTQ/BAM/WIG、出版商工作簿与大型浏览器资产不进入 Git；它们通过公共 accession 或版本化 GitHub Release 提供。

## BTED v0.2.0

| 指标 | 当前数量 |
|---|---:|
| BATTER Table S1 来源记录 | 22 |
| 精确参考组装 | 20 |
| 原始研究论文 | 13 |
| 公开标准化来源 | 21 |
| `audit_only` 来源 | 1（BATTER_S1_002） |
| 核心记录 | 28,399 |
| 来源特异表 | 17 |
| JBrowse 数据集 | 21 |

v0.2.0 保留固定的 24 列核心端点表，并增加通过 `end_id` 关联的来源特异表、逐字段说明、manifest 和 checksum。纯预测和不可拆分的混合证据不会作为公开端点发布。

- [v0.2.0 发布说明](docs/releases/v0.2.0.md)
- [来源目录](data/registry/batter_s1_publication_status.v0.2.0.tsv)
- [发布 manifest](data/public/v0.2.0/release_manifest.json)
- [数据发布接口 v0.2](docs/standards/BTED_数据发布接口_v0.2.md)
- [数据入库 SOP v0.2](docs/standards/BTED_数据入库标准流程_v0.2.md)
- [可编辑 draw.io 流程图](docs/diagrams/BTED_v0.2_数据入库与发布流程.drawio)

## BTED v0.3 developer preview

已部署基线来自 `feature/bted-v0.3-dynamic-service`；当前维护交接入口是
[`docs/HANDOFF.md`](docs/HANDOFF.md)。该基线仍是 v0.3 Cloudflare developer preview。
当前部署路径是 Cloudflare Worker + D1 + Worker Static Assets：它复用现有 `site/`
静态 UX，提供 catalogue/source/assembly/endpoint/augmentation API、动态 JBrowse config 和
登记 HF asset 的同源 Range 代理。现有 FastAPI/PostgreSQL/Next.js 组件仍保留为
future/alternative，以 canonical release 和登记资产为真源，不改写 v0.2 发布目录。

当前 release/query layer 的计数如下：

| 指标 | 当前数量 |
|---|---:|
| 来源记录 | 22（21 `published_standardized` + 1 `audit_only`） |
| release 中的 assembly records | 20 |
| 去重后的 published browser assemblies | 19 |
| endpoint records | 28,399 |
| GFF-derived genes | 95,437 |
| materialized assets | 211（其中 208 个 public objects，已在固定 HF revision 通过 Range audit） |

本地前端开发入口（alternative Next.js path）：

```bash
cd frontend
cp .env.example .env.local
# 在 .env.local 设置 BTED_API_ORIGIN，例如 http://127.0.0.1:8017
pnpm install
pnpm run dev
```

契约检查和生产构建分别使用 `pnpm run check-contract` 与 `pnpm run build`；更多运行说明见
[`frontend/README.md`](frontend/README.md) 与 [`docs/v0.3/architecture.md`](docs/v0.3/architecture.md)。

v0.3 仍不是生产上线。Hugging Face public object handoff 已完成，但它验证的是当前
canonical `release_version=v0.2.0`，不是一个新的 `v0.3.0` 数据 release：
[`seu-yolo/BTED-v0.3-assets`](https://huggingface.co/datasets/seu-yolo/BTED-v0.3-assets)
的固定 revision 为
`463cfc8bd582a5ed9d2c426822148c3f1e56c4d0`，208 个 public objects（196,667,360 bytes）
均通过 HEAD 200 + 单字节 Range 206；3 个 S1_002 audit-only/private objects 未上传。可复核证据位于
[`data/registry/remote_asset_audit.v0.2.0-hf.json`](data/registry/remote_asset_audit.v0.2.0-hf.json)，
其 SHA-256 为 `8df250f34c94f4ce858694575356649c4da1336ab6a1011e52a756bdd99551cf`。

Cloudflare D1 `bted-catalogue-v03-preview` 已完成真实批次导入（1 release、13 publications、
20 assemblies、49 contigs、22 sources、32 accessions、22 tracks、211 assets、28,399
endpoints；208 public assets、19 augmentation sources），远程库约 32.78 MB。Worker 已部署
到 [`bted-catalogue-v03-preview.bted-v0-3-dynamic-service.workers.dev`](https://bted-catalogue-v03-preview.bted-v0-3-dynamic-service.workers.dev)，
2026-08-23 记录的线上 HTTP/HEAD/Range/JBrowse/static-page smoke 已通过；Worker 同时部署了从既有 v0.2 bundle
提取的单份 JBrowse 4.3.0 shell（455 个运行时文件，约 5.84 MiB，不含大型科学资产）。它仍是
preview，不是正式 v0.3.0 release；`endpoint_gene_context` 尚未定义或计算。旧的 mutable
`resolve/main` verified bundle 不作为最终交付；本地 pinned verified bundle 是临时交接物，
不进入 Git。2026-09-06 本机访问 Cloudflare/HF 均连接超时，本轮未能重新确认线上可用性；
这不等同于已确认服务宕机，接手人应从独立网络并结合 Cloudflare deployments 状态复核。

## 数据边界

| 公开层 | 说明 |
|---|---|
| `observed_signal` | 经审计的实验信号展示层 |
| `called_endpoint` | 按公开规则从信号得到的本站候选端点 |
| `author_called_endpoint` | 作者补充表中的端点调用 |
| `curated_record` | 文献整理记录，保持其原始语境 |

`author_integrated_mixed_evidence` 与 `prediction_only` 只进入审计/注释层，不进入公开核心端点表。作者表中的预测支持列可以作为 `prediction_annotation` 保留，但不会改变端点的主要证据类别。

数据库中的“实验支持 3′ end”不等于每个位点均完成独立终止功能试验。

这里的 13 是原始研究论文数，22 是论文下拆分出的来源记录数，两者不是同一统计单位。v0.2.0 公开 21 个来源，`BATTER_S1_002` 仅保留来源审计，不能表述为“22 个来源均已公开发布”。

## 发布目录

```text
data/public/v0.2.0/records/<source_id>/
├── endpoints.tsv                 24 列核心表
├── source_annotations.tsv        来源字段，许可允许时提供
├── endpoints.bed                 BED6
├── fields.json                   字段类型、单位、原列名和证据属性
├── manifest.json                 来源、参考、状态与限制
└── SHA256SUMS.txt                 文件完整性
```

少数一对多信息使用单独附表，例如 `gene_associations.tsv` 和 `condition_observations.tsv`。`audit_only` 来源不会生成空端点表或 JBrowse 按钮。

## 本地构建

构建标准数据需要本地 BGIRNA 来源快照：

```bash
python3 scripts/build_v0_2_release.py --input-root /path/to/BGIRNA
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_bted_v0_2.py
python3 scripts/build_release_archives.py
```

构建 JBrowse 与网站：

```bash
python3 scripts/build_jbrowse_release.py --input-root /path/to/BGIRNA
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
python3 scripts/build_v0_2_site.py
python3 scripts/stage_pages.py \
  --jbrowse-dir dist/BTED-v0.2.0-jbrowse \
  --output-dir .pages-preview
python3 scripts/validate-site.py .pages-preview
python3 -m http.server 8000 --directory .pages-preview
```

随后访问 `http://localhost:8000/`。

## 验证

```bash
python3 scripts/validate_bted_templates.py
python3 scripts/validate_bted_release.py
python3 scripts/validate_repo_layout.py
python3 scripts/validate_bted_v0_2.py
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
python3 scripts/validate-site.py site
python3 -m unittest -v tests/test_bted_ingestion.py tests/test_bted_v0_2.py
git diff --check
```

## 网站与大型资产

`site/` 是英文默认、可切换中文的静态目录。网站以 20 个精确参考组装为主入口，同时保留 22 个来源详情页。参考组装完全相同的来源在一个基因组页面和 JBrowse 视图中显示为独立 track，不做跨来源去重或共识推断。

下载页支持按组装全选、多选并生成 ZIP。每个组装目录只突出 `endpoints.bed` 与一份汇总来源、文献、登录号、证据、限制和校验值的 `metadata.json`。GitHub Pages 工作流复用 `preview-v0.2.0` Release 中的固定 JBrowse 大型资产，再叠加仓库内 140 KB 的版本化配置覆盖层、生成组装级下载包并部署。

- [组会展示教程（2026-08-12）](docs/demo/BTED_组会展示教程_2026-08-12.md)

Release 资产：

- `BTED-v0.2.0-data.tar.gz`
- `BTED-v0.2.0-data.tar.gz.sha256`
- `BTED-v0.2.0-jbrowse-assets.tar.gz`
- `BTED-v0.2.0-jbrowse-assets.tar.gz.sha256`

## 项目结构

```text
.github/workflows/       CI 与 GitHub Pages 部署
data/registry/           22 来源注册表、manifest、许可与发布状态
data/public/v0.2.0/      可公开的小型标准数据
data/audit/v0.2.0/       工程审计结果
data/audit/legacy/       早期资料搜集阶段的小型元数据快照
docs/releases/           版本说明
docs/sources/            逐来源处理记录
docs/standards/          SOP、字段与发布接口
docs/diagrams/           可编辑流程图
docs/literature/         当前正式文献说明
docs/legacy/             早期探索笔记和项目报告（只读）
scripts/                 构建、校验和打包脚本
site/                    自动生成的静态网站
tests/                   v0.1/v0.2 回归测试
```

## 协作

新增来源或修改共享规则前，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)、[SOP v0.2](docs/standards/BTED_数据入库标准流程_v0.2.md) 和 [证据分层与发布边界](docs/standards/证据分层与发布边界.md)。一个来源的处理记录、manifest、输入指纹、输出和验证结果应在同一个 PR 中评审。

## 历史资料

- [`data/audit/legacy/accession_list_verified.csv`](data/audit/legacy/accession_list_verified.csv)：早期资料搜集阶段形成的公开登录号快照，不替代正式 registry/manifest；
- [`docs/legacy/project-reports/`](docs/legacy/project-reports/)：早期项目报告和补充材料核查记录；
- [`docs/legacy/literature-initial-review/`](docs/legacy/literature-initial-review/)：13 篇论文的早期探索笔记；
- [`docs/literature/`](docs/literature/)：当前正式文献说明。

重复的旧整目录副本和 read-starts 原始计数已从当前 Git 树移除，未改写历史。原始实验文件继续通过公共 accession 获取，不在仓库中重复保存。
