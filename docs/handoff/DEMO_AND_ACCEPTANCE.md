# BTED 同事演示与接手验收

## 1. 交接目标

完成本流程后，同事应能独立回答：

1. BTED 收录什么，以及哪些内容不是实验端点；
2. canonical `v0.2.0`、Cloudflare developer preview 与本地 handoff 分支有何区别；
3. 数据、D1、Worker、HF 资产和 JBrowse 如何串联；
4. 如何运行测试、复现本地页面、核验线上资源并排查 500/502；
5. C 类、signed-log 信号和 GTDB 扩展下一步缺什么。

## 2. 20 分钟讲解顺序

### 0–4 分钟：项目与数据

- 打开 `README.md` 和 `docs/HANDOFF.md`。
- 说明当前是 13 篇论文、22 个来源、19 个可浏览 assembly、28,399 个 endpoint。
- 强调 `BATTER_S1_002` 是 `audit_only`，预测数据不进入实验端点总数。

### 4–8 分钟：当前架构

```text
canonical v0.2 files + registries
          ↓
materialized/verified bundle
          ↓
Cloudflare D1 query projection
          ↓
Worker API + dynamic JBrowse config
          ↓
same-origin asset proxy
          ↓
pinned Hugging Face objects
```

说明当前没有 MySQL；D1 是 SQLite-compatible 查询投影，PostgreSQL/FastAPI/Next.js 是备选路线。

### 8–13 分钟：已部署与本地改进

先展示已部署基线，再打开本地 `evidence-layers-preview`：

- 已部署基线最后一次完整验证到 2026-08-23；
- 本地分支增加自然名称证据仪表盘、S1_003 regional BATTER-TPE pilot 和 loopback asset fallback；
- 本交接过程未把这些改进部署上线。

在仪表盘解释 measured signal、curated endpoints、training augmentation context 和
model-predicted regions。强调 11 条 D 区间是 non-experimental compatibility pilot。

### 13–17 分钟：维护流程

- 演示 focused tests、全量测试、site validator 和 Worker syntax check。
- 打开 `OPERATIONS_RUNBOOK.md`，说明 D1 重建、8787/8790 和 502 排障。
- 打开 `ACCESS_CHECKLIST.md`，确认同事使用自己的账号。

### 17–20 分钟：未完成工作

- C 数据已有序列级内容，但 S1_003 reference mapping 未完成；
- signed-log 只应作为派生显示，raw 值必须保留；
- GTDB 扩展先做 reference/version 映射和代表性批次；
- `endpoint_gene_context` 尚未定义；
- production/custom domain 和本地改进部署仍需单独决策。

## 3. 干净 clone 验证

```bash
cd /private/tmp
git clone git@github.com:seu-yolo/BATTER-Transcription-Terminator-Database.git bted-handoff-check
cd bted-handoff-check
git switch handoff/bted-maintainer-2026-09
git status -sb
git log --oneline -4
```

期望工作树 clean，并看到独立的 Worker 修复、S1_003 功能和交接文档提交。不要删除操作者已有目录；
若 `/private/tmp/bted-handoff-check` 已存在，改用新的临时目录。

## 4. 离线验收

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

可选依赖测试若 skip，必须记录具体测试与原因，不能把 skip 写成 pass。

## 5. 本地页面验收

完整动态 JBrowse 不是“仅 clone 即可”的纯静态页面：需要本地 D1 投影，并需要可访问固定 HF origin，
或在仓库外准备已校验的本地资产 origin。按 `OPERATIONS_RUNBOOK.md` 生成/导入 D1 后启动 Worker。

检查：

- `/evidence-layers-preview` 无横向溢出或重复卡片；
- 页面无面向用户的 A/B/C/D 字母标签；
- 显示 1,414 curated records、11 predictions、7 + / 4 −；
- augmentation 不伪造坐标轨道；
- JBrowse 默认视野是 `NC_000964.3:18,000–28,000`；
- gene、正/负链 raw signal、curated endpoint 和 prediction track 可加载；
- 浏览器 console 无 error/warning；
- 代表性 FAI/FASTA/GFF3/TBI/BigWig/BED 的 HEAD/Range 正常。

若外网不可用，使用明确的 loopback asset origin；若本地资产也未准备，记录为环境阻塞，不把静态页面
成功等同于 JBrowse 数据已恢复。

## 6. 线上只读验收

```bash
curl -fsS --max-time 20 \
  https://bted-catalogue-v03-preview.bted-v0-3-dynamic-service.workers.dev/api/health
curl -fsS --max-time 20 \
  https://bted-catalogue-v03-preview.bted-v0-3-dynamic-service.workers.dev/api/stats
```

再检查 catalogue、source、assembly、endpoint、augmentation、dynamic config，以及一个登记公开资产
的 HEAD 200/Range 206。线上失败时从另一网络和 Cloudflare deployments 状态交叉验证；单一环境连接
超时不能直接判定 Worker 宕机。

## 7. 权限验收

- GitHub：同事可以 clone/fetch，并向自己的测试分支 push。
- Cloudflare：可以查看 deployments，执行只读 D1 SELECT。
- Hugging Face：可以读取固定 revision；只有承担资产发布时才需要 write。
- 不要求同事接收任何旧 token、个人 SSH key、密码或 2FA 恢复码。

## 8. 完成记录

交接会议结束时共同记录：

- 验收日期和参与者；
- 实际使用的 Git commit；
- 本地/线上测试结果与网络环境；
- 已授予的角色，不记录 secret；
- 同事接手的第一项任务；
- 仍由原维护者保留的权限或待决发布事项。
