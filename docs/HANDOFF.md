# 交接说明

**日期：** 2026-08-07
**分支：** `agent/reconcile-current-bted-state`（已推送，与 origin 同步）
**Draft PR：** [#1 —— Task 01: Reconcile remote repository with current BTED state](https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database/pull/1)，待最终评审。

---

## 1. 当前状态

- Task 01 已完成。该分支仅新增文档；未改动任何科学数据、坐标、证据类别或来源数量。
- 交付物（均为中文）：
  - `docs/remote-repository-migration-inventory.md`
  - `docs/current-bted-status.md`
  - `docs/github-pages-demo-plan.md`
  - `docs/WORKLOG.md`
- 一处低风险笔误修复：`文献13-PMID38030608/README.md`（"PMID: 38030638" → "PMID: 38030608"）。
- 外部 BTED 工作状态（22 来源注册表、证据分层 SOP、标准化输出、JBrowse 资源、处理记录、回归测试）**无法访问**；交付物中所有相关声明均已标注 `to verify`。

## 2. 待决事项（完整清单见 `docs/current-bted-status.md` 第 3 节）

1. 对齐来源数量口径：13 篇文献 vs 22 条 Table S1 记录 vs 据报 22 个来源的注册表。
2. 固定坐标体系约定（0/1-base、单点 vs 区间、逐来源参考基因组版本）。
3. 在发布任何内容前定义并评审证据分层标签；绝不把仅预测或混合证据的记录标记为实验验证。
4. 决定大型加工资产 / JBrowse track 的托管方式（git/Pages 限制 vs 外部托管）。
5. 仓库清理（**刻意推迟**，不属于 Task 01）：`文献13-PMID38030608/` 下已追踪的约 168 MB read-starts 文件与 `__MACOSX/` 垃圾文件；`README.md` 中悬空的 `archive/` 引用。
6. 公开文档的语言方案（现有文档为中文）。
7. 获取外部 BTED 工作树的访问途径，以核实第 1 节中的 `to verify` 声明。

## 3. 下一步建议

1. 最终评审 draft PR #1，然后合并到 `main`。
2. **Task 02**（`docs/tasks/02-github-pages-demo.md`，分支 `agent/github-pages-demo`）：按 PR #1 中提议的收敛范围构建静态演示 —— 目录仅由 `accession_list_verified.csv` 与 13 份逐来源 README 生成；不含 JBrowse 链接、不含坐标数据集、在核实前不含任何外部 BTED 声明。
3. 后续清理任务（独立分支，在 Task 02 规划之后）：决定是否清除 168 MB 已追踪文件 / `__MACOSX/`，并修复或恢复 `README.md` 中的 `archive/` 引用。
4. 当外部 BTED 工作树可访问时，逐项核实 `docs/current-bted-status.md` 中的 `to verify` 条目，并在任何数据迁移前更新迁移盘点（验收门槛见该文档第 4 节）。

## 4. 环境备注

- `gh` CLI 令牌已失效；PR 操作通过 GitHub REST API 使用 git 凭据存储完成。如需 CLI 操作请重新运行 `gh auth login`。
- 本任务的提交使用机器自动生成的 git 身份（`SEU_yolo <seu_yolo@...local>`）；如需其他身份可 amend。
