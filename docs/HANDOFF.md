# BTED 当前维护交接

**更新日期：** 2026-09-06

**用途：** 同事从零接手代码、数据边界、预览站和后续开发

**当前工作树：** `/Users/seu_yolo/Desktop/BGIRNA/.worktrees/bted-v0.3-dynamic-service`

**交接分支：** `handoff/bted-maintainer-2026-09`，基于 `131b70f`

本文件只描述当前有效状态。完整开发历史保存在 `docs/WORKLOG.md` 和 Git；具体操作、科学边界、
权限与演示分别见：

- [维护与运行手册](handoff/OPERATIONS_RUNBOOK.md)
- [科学边界与未完成工作](handoff/SCIENCE_AND_OPEN_WORK.md)
- [权限交接清单](handoff/ACCESS_CHECKLIST.md)
- [同事演示与接手验收](handoff/DEMO_AND_ACCEPTANCE.md)

## 1. 项目与当前数据

BTED（Bacterial Transcript 3′ End Database）将公开细菌转录 3′ 端实验整理成可追溯、可下载、
可在 JBrowse 中核对的标准资源。

| 项目 | 当前值 |
|---|---:|
| canonical release | `v0.2.0` |
| 原始研究论文 | 13 |
| source records | 22 |
| `published_standardized` / `audit_only` | 21 / 1（S1_002） |
| assembly records / 去重可浏览 assembly | 20 / 19 |
| contigs / source accessions / tracks | 49 / 32 / 22 |
| endpoints | 28,399 |
| `author_called_endpoint` / `curated_record` | 24,887 / 3,512 |
| GFF-derived genes | 95,437（已物化，当前 D1 catalogue 不查询） |
| registered assets / public HF objects | 211 / 208 |

`v0.3` 是服务架构的 developer preview 名称，不是新的 `v0.3.0` biological data release。

## 2. 当前运行架构

```text
canonical v0.2 files + registries
          ↓
verified materialized bundle
          ↓
Cloudflare D1 query projection
          ↓
Worker API + Worker Static Assets + dynamic JBrowse config
          ↓
allowlisted same-origin asset proxy
          ↓
pinned Hugging Face objects
```

- Worker：`bted-catalogue-v03-preview`
- 线上地址：`https://bted-catalogue-v03-preview.bted-v0-3-dynamic-service.workers.dev`
- D1：`bted-catalogue-v03-preview`，binding `BTED_DB`
- HF dataset：`seu-yolo/BTED-v0.3-assets`
- 固定 revision：`463cfc8bd582a5ed9d2c426822148c3f1e56c4d0`
- 远端审计：208/208 objects，196,667,360 bytes；证据文件 SHA-256
  `8df250f34c94f4ce858694575356649c4da1336ab6a1011e52a756bdd99551cf`

当前系统没有使用 MySQL。D1 是 SQLite-compatible 查询投影；仓库中的 FastAPI/PostgreSQL/Next.js
是 future/alternative path，未作为线上服务运行。

## 3. 已部署基线与本地交接分支

| 能力 | 已部署基线 | 交接分支 | 是否上线 |
|---|---|---|---|
| catalogue/source/assembly/endpoint/augmentation API | 有 | 保留 | 是 |
| 动态 JBrowse config 与同源 HF Range proxy | 有 | 保留 | 是 |
| JBrowse 顶部论文、accession、BED 与详情入口 | 有 | 保留 | 是 |
| S1_003 自然名称证据仪表盘 | 无 | 有 | 否 |
| S1_003 BATTER-TPE regional compatibility pilot | 无 | 11 条，7 + / 4 − | 否 |
| loopback `LOCAL_ASSET_BASE` fallback | 无 | 有 | 否 |
| origin 网络异常结构化 `502 asset_origin_unavailable` | 无 | 有 | 否 |

最后一次完整线上验收记录为 2026-08-23，JBrowse wrapper 对应 Worker version
`679cff52-8779-4bdd-9346-63d180278b53`。2026-09-06 本机访问 Cloudflare 和 Hugging Face
均在 HTTPS 建连时超时；这表示本轮无法复核，不足以判断远端服务是否宕机。接手后应从独立网络并结合
Cloudflare deployments 状态复核。

## 4. S1_003 证据试点

- 对象：*Bacillus subtilis* 168，`BATTER_S1_003`
- assembly / contig：`GCF_000009045.1` / `NC_000964.3`
- 区域：18,000–28,000
- measured signal：Rend-seq 正/负链 raw BigWig
- curated endpoints：Lalanne Table S3，1,414 条
- training augmentation：有 BATTER 序列级训练数据背景，但当前 assembly 映射未完成，无坐标 track
- model output：BATTER-TPE regional compatibility pilot，11 条区间；`experimental=false`

页面是 `site/evidence-layers-preview.html`；dynamic config 参数为
`source_id=BATTER_S1_003&pilot=three-layer`。D 的 BED 和 provenance 位于
`site/data/pilots/`，不得并入 canonical endpoint 表。

## 5. 证据底线

- `observed_signal`、`called_endpoint`、`author_called_endpoint`、`curated_record`
  和 `model_prediction` 必须分开。
- prediction-only 或混合证据不得发布为 experimental endpoint。
- 生物学坐标是 1-based；单碱基 BED 是 0-based half-open。
- 不跨 contig 匹配；无法核实 evidence/reference/coordinate/strand 时标
  `blocked`/`to_review`，不得猜测。
- 3′ end record 不自动等于功能验证的转录终止子；模型 score 也不是现实世界验证概率。

## 6. Git、worktree 与远端

- `origin`：`LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database`
- `personal`：`seu-yolo/BATTER-Transcription-Terminator-Database`
- 当前交接分支推送目标：`personal/handoff/bted-maintainer-2026-09`

2026-09-06 的 worktree 快照：

| worktree | branch | 状态/用途 |
|---|---|---|
| `BATTER-Transcription-Terminator-Database` | `refactor/project-structure-and-literature-notes-v0.1` | clean；相对 origin behind 1 |
| `.worktrees/assembly-track-download-demo` | `docs/bted-v0.2-handoff-v2` | clean；历史 v0.2 交接，远端分支保留 |
| `.worktrees/bted-v0.2` | `agent/bted-v0.2-public-demo` | clean；历史 demo |
| `.worktrees/bted-v0.3-dynamic-service` | 本交接分支 | 当前维护线 |
| `.worktrees/pr3-cleanup` | `agent/pr3-layout-cleanup` | clean；历史 cleanup |

不要自动合并或删除这些历史分支/worktree；先根据 Git 历史判断是否已被当前维护线吸收。

## 7. 接手顺序

1. clone `personal` 仓库并切换 `handoff/bted-maintainer-2026-09`。
2. 阅读 `AGENTS.md`、本文件、四份 handoff 文档、数据入库 SOP。
3. 运行 focused/full tests、Worker syntax、site validator 和 `git diff --check`。
4. 使用自己的 GitHub/Cloudflare/HF 账号完成只读权限核验。
5. 从独立网络检查线上 API、JBrowse 和代表性资产 HEAD/Range。
6. 按 `DEMO_AND_ACCEPTANCE.md` 复现本地页面；不要依赖原维护者的 `/private/tmp`。
7. 将第一项工作限定为一个 source 或一个共享基础设施变更，继续更新 WORKLOG。

## 8. 优先未完成事项

1. 决定是否部署本分支的仪表盘、D pilot 和 local asset fallback；部署前必须重新验收。
2. 重新下载并复核 BATTER training FASTA，先形成序列级 catalogue，再单独做 assembly mapping。
3. 设计 signed-log 派生信号显示，同时保留 raw track 和原始数值。
4. 定义并验证 `endpoint_gene_context`；当前不能宣称已完成。
5. 以有实验来源的 assembly 和 GTDB representative genome 做扩展试点，不把预测混入实验数据。
6. 决定 developer preview 是否升级为 production/custom domain。

## 9. 不属于本次交接提交的操作

- 未部署 Worker，未写入远程 D1，未上传或重写 HF 对象；
- 未修改 canonical `v0.2.0`、D1 schema、公开 API 或 endpoint 数；
- 未添加 credential、数据库 dump、原始 FASTQ/BAM/WIG 或 BATTER 大文件；
- 未邀请同事账号：执行邀请仍需要其 GitHub、Cloudflare 和 Hugging Face 身份标识。
