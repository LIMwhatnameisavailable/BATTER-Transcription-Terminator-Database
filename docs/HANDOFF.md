# 交接说明

**日期：** 2026-08-07
**分支：** `agent/reconcile-current-bted-state`（已推送，与 origin 同步）
**Draft PR：** [#1](https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database/pull/1)，待最终评审。2026-08-07 起该分支同时承载 Task 02（站点骨架）与 Task 03（清理方案）的提交，PR #1 涵盖 Task 01–03，标题与描述已同步更新。

---

## 1. 当前状态

- Task 01 已完成。该分支仅新增文档；未改动任何科学数据、坐标、证据类别或来源数量。
- 交付物（均为中文）：
  - `docs/remote-repository-migration-inventory.md`
  - `docs/current-bted-status.md`
  - `docs/github-pages-demo-plan.md`
  - `docs/WORKLOG.md`
- 一处低风险笔误修复：`docs/legacy/original-directories/文献13-PMID38030608/README.md`（"PMID: 38030638" → "PMID: 38030608"）。
- 外部 BTED 工作状态（22 来源注册表、证据分层 SOP、标准化输出、JBrowse 资源、处理记录、回归测试）**无法访问**；交付物中所有相关声明均已标注 `to verify`。

## 2. 待决事项（完整清单见 `docs/current-bted-status.md` 第 3 节）

1. 对齐来源数量口径：13 篇文献 vs 22 条 Table S1 记录 vs 据报 22 个来源的注册表。
2. 固定坐标体系约定（0/1-base、单点 vs 区间、逐来源参考基因组版本）。
3. 在发布任何内容前定义并评审证据分层标签；绝不把仅预测或混合证据的记录标记为实验验证。
4. 决定大型加工资产 / JBrowse track 的托管方式（git/Pages 限制 vs 外部托管）。
5. 仓库清理（**刻意推迟**，不属于 Task 01）：`docs/legacy/original-directories/文献13-PMID38030608/` 下已追踪的约 168 MB read-starts 文件与 `__MACOSX/` 垃圾文件；`README.md` 中悬空的 `archive/` 引用。
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

---

# Task 02 交接补充（2026-08-07）

## 5. Task 02 当前状态

- 静态演示站点骨架已完成，位于 `site/`（index / catalog / methodology / about 四页 + `css/style.css` + `.nojekyll`），验证脚本位于 `scripts/validate-site.py`。
- **分支偏差（已决）：** 任务说明称当前分支为 `agent/github-pages-demo`，实际工作执行于 `agent/reconcile-current-bted-state`（当时约束禁止新建分支）。2026-08-07 经维护者确认，改动直接提交到当前分支，不再移植。
- 本轮未执行 git commit / push / merge / PR 操作；工作区新增文件均未暂存。此前工作区已有的 6 个 docs 修改（OpenAI 审核修订）保持原样，未受影响。
- 目录页刻意排除 3 行基因组序列登录号（GenBank CP027858、CP027859、NC_014500.1），理由：任务要求不展示参考基因组，且版本对齐未定稿。

## 6. Task 02 验证结果

- `python3 scripts/validate-site.py`：PASS（含负向自检）。
- 子路径本地服务（`/<仓库名>/` 前缀）下全部页面与样式 HTTP 200；Playwright 截图确认桌面与移动视口排版正常。
- `git diff --check` 干净。

## 7. Task 02 之后续事项

1. 由维护者决定提交分支（见第 5 节分支偏差），并开启 draft PR 评审骨架。
2. 元数据 schema 与证据分层标准获批前，站点保持骨架阶段；获批后再评估客户端搜索/过滤与记录页模板。
3. 部署时按 `docs/github-pages-demo-plan.md` 第 5 节使用 GitHub Actions 构建专用静态产物，并将 `scripts/validate-site.py` 纳入 CI 检查步骤。
4. 贡献者名单、许可证、反馈渠道目前均为占位，正式发布前需补齐。

---

# Task 03 交接补充（2026-08-07）

## 8. Task 03 当前状态

- 仓库卫生清理方案已完成，交付物为 `docs/cleanup-proposal.md`（问题清单、四选项利弊、风险分析、分阶段推荐、精确命令、回滚方案、事实核查附录）。
- **分支偏差（已决）：** 任务说明称当前分支为自 `main` 新建的 `agent/cleanup-proposal`，实际工作执行于 `agent/reconcile-current-bted-state`（当时约束禁止新建分支）。2026-08-07 经维护者确认，方案文档直接提交到当前分支，不再移植。
- 本轮仅写方案文档：未删除任何文件、未修改 `.gitignore`/`README.md`、未运行任何改写历史的命令、未执行 git commit/push/merge/PR 操作。此前工作区已有内容（6 个 docs 修订、`site/`、`scripts/`）保持原样。
- 本文件第 2 节待决事项第 5 条（仓库清理）现已有对应方案文档，评审后可从"待决"转为"待执行决策"。

## 9. Task 03 推荐方案摘要

- **阶段 A（建议尽快，低风险可逆）：** `git rm --cached` 停止追踪 6 个 read-starts 文件与 `__MACOSX/`，`.gitignore` 追加规则，删除 `README.md:59` 悬空的 `archive/` 行；普通提交 + PR 评审，不改写历史。
- **阶段 B（暂缓，设门槛）：** 仅当 PR #1 已合并、大型资产托管策略定案为"不入 git 历史"、完成镜像备份与协作冻结、旧 SHA 引用已加注后，才用 `git filter-repo` 做一次性历史重写。BFG 为等价备选；Git LFS 不推荐。

## 10. Task 03 之后续事项

1. 维护者评审 `docs/cleanup-proposal.md`；如批准阶段 A，由维护者自 `main` 创建执行分支（方案建议名 `agent/repo-hygiene`）按第 5 节命令执行并开 PR。
2. 阶段 A 执行前确认工作区无未提交工作（当前含 Task 02 产出与本方案文档，需先由维护者决定提交归属）。
3. 阶段 B 不得单独启动；四道门槛全部满足前保持暂缓。
4. 阶段 A 合并后，提醒所有本地克隆者：6 个 read-starts 文件已转为未追踪文件，`git clean -fdx` 会将其删除（内容可从 PMID 38030608 公开补充材料重新获取）。

---

# 协作入库标准 v0.1 交接补充（2026-08-07）

## 11. 本轮交付（feature/bted-v0.1-standards-and-structure）

- **分支基线：** 基于 `origin/agent/reconcile-current-bted-state`（未合并入 main），Draft PR 基线同此。若 PR #1 先合并，本分支需 rebase 到 main 或改 PR 基线。
- **交付物：** `docs/standards/` 五份标准文档（SOP v0.1、协作者指南、字段字典、证据分层与发布边界、目录与协作规范）；`data/registry/templates/` 两个模板（26/24 列）；`data/registry|public|audit/README.md`；`scripts/validate_bted_templates.py`；重写的 README；扩充的 `.gitignore`；`site/` 两处最小更新。
- **模板修正：** 本地模板表头 `axonomy_id` 系拼写错误，入库版本已更正为 `taxonomy_id`；本地工作树若继续使用旧模板，建议同步修正。
- **刻意未做：** 未迁移任何 BATTER_S1 数据 / JBrowse 资产 / 原始文件；未重排 `文献N-PMID*` 目录；未清理历史大文件；未虚构任何已发布数据。

## 12. 给下一位协作者

1. 接入新文献：按 `docs/standards/协作者_新增文献收集与入库指南.md` 执行，先填来源登记表，核验通过才建端点表；新 `source_id` 序号先查 `data/registry/` 与本 WORKLOG 避免冲突。
2. 提交前运行 `python3 scripts/validate_bted_templates.py`（和改动 site/ 时的 `python3 scripts/validate-site.py`）。
3. PR 保持 Draft，描述写清"做了什么 / 没做什么 / 待确认 / 验证结果"。
4. 任何无法核实的信息标记 `to_review` 或 `blocked`，不要猜测。
