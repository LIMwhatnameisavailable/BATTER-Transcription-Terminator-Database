# 仓库卫生清理方案（Task 03）

> **执行状态（2026-08-10）：** 阶段 A 已完成。根目录旧报告已归档，重复的 `docs/legacy/original-directories/`、6 个 read-starts 文本和 `__MACOSX` 已从当前 Git 树移除并加入忽略规则。未执行 `filter-repo`、BFG、LFS migrate 或任何历史重写；旧对象仍可从旧提交恢复。

**日期：** 2026-08-07
**状态：** 阶段 A 已于 2026-08-10 执行；阶段 B 历史重写未执行。
**分支说明：** 任务说明称当前分支为自 `main` 新建的 `agent/cleanup-proposal`，实际工作执行于 `agent/reconcile-current-bted-state`（本轮约束禁止新建分支）。执行本方案时由维护者另行创建执行分支。
**关联：** `docs/HANDOFF.md` 待决事项第 5 条、第 3 节下一步建议第 3 条；`docs/current-bted-status.md` 第 2 节第 7 条、第 3 节第 5 条；draft PR #1。

---

## 1. 清理前问题清单

| # | 问题 | 位置 | 规模 | 事实依据（只读命令复核） |
|---|------|------|------|--------------------------|
| P1 | 大型 read-starts 数据文件被 git 追踪 | `docs/legacy/original-directories/文献13-PMID38030608/` 下 6 个 `*_read_starts.txt` | 工作区合计 **168.0 MB**（33.8 / 17.1 / 44.8 / 21.4 / 33.9 / 17.0 MB），约 631 万行 | `ls -l` 实测；`git ls-files` 确认已追踪；自初始提交 `b59e72a` 起入库 |
| P2 | macOS 归档垃圾文件被 git 追踪 | `docs/legacy/original-directories/文献13-PMID38030608/__MACOSX/` 下 6 个 `._*` AppleDouble 文件 | 每个约 178 B | `git ls-files` 确认已追踪 |
| P3 | README 中悬空的 `archive/` 引用 | `README.md:59`：`├── archive/   # 历史过程记录（已整合的旧报告）` | 1 行文档错误 | 磁盘无 `archive/` 目录；`git log --all -- archive/` 无输出，即该目录在全部可达历史中从未被追踪 |

补充事实：

- 当前 `.git` 目录 31 MB，其中 pack 为 **30.72 MiB**（`git count-objects -vH`）。read-starts 文件为高压缩率文本，对 pack 的具体贡献未单独核实；工作区 168 MB 不等于克隆体积。
- 单文件最大 44.8 MB，低于 GitHub 100 MB 推送硬限制，因此现状不阻塞推送，但远超仓库其余内容体量（其余被追踪文件均在 KB 量级）。
- read-starts 文件内容来自 PMID 38030608 公开补充材料（MOESM10 Source Data）的原始 read starts 计数，可从公开来源重新获取，非独有数据、非敏感数据。
- `__MACOSX/` 为 macOS 解压 zip 产生的元数据残留，无任何信息价值。
- 大型加工资产的托管策略（仓内 git / Git LFS / 外部托管）在 `docs/HANDOFF.md` 待决事项第 4 条中**尚未定案**，本方案不预设该结论。

## 2. 清理选项分析

### 选项 1：`git rm --cached` 仅停止追踪（历史保留）

**做法：** `.gitignore` 追加忽略规则，然后 `git rm --cached` 将目标文件移出索引；文件保留在磁盘，成为未追踪文件。普通提交推送，不改写历史。

**利：**

- 不改写任何提交，commit hash 全部不变，对协作者与在途 PR **零冲击**。
- 操作完全可逆（文件从未离开磁盘，恢复追踪只需 `git add -f`）。
- 立即解决卫生问题：后续克隆的工作区不再检出 168 MB 数据；`__MACOSX/` 彻底出索引；追踪边界与 `.gitignore` 一致。
- 与现有工作流兼容，可在任意分支作为普通 PR 评审合并。

**弊：**

- 历史中的 blob 保留，克隆体积（pack 约 30.72 MiB）**不下降**；`git clone` 仍下载历史中的数据。
- 文件变为未追踪后失去 git 保护：`git clean -fdx` 可将其误删（内容可从公开来源重新获取，风险可控）。
- 若未来出现"历史内容本身不得存在"的合规要求，本选项不满足（本案例为公开文献数据，无此要求）。

### 选项 2：`git filter-repo` 清除历史

**做法：** 在全新镜像克隆上运行 `git filter-repo --invert-paths --path ... --path-glob ...`，将目标路径从全部历史中抹除，然后 force-push 覆盖远端全部分支与标签。

**利：**

- 历史真正缩小：pack 中相关 blob 被移除，克隆体积下降。
- 路径级精确（精确路径 + glob），不误伤其他内容；速度快；是 git 官方推荐的 filter-branch 继任者，维护状态好。
- 一次性彻底解决问题，且可同时清理 `__MACOSX/`。

**弊：**

- **全量改写历史**：目标文件自初始提交 `b59e72a` 即入库，因此其后的每一个 commit hash 都会改变。
- 所有协作者必须重新克隆或 `fetch` + `reset --hard`；在旧克隆上 `git pull` 会产生混乱的合并历史。
- 未合并的 draft PR #1 将失效，需基于新历史重建；任何引用旧 SHA 的文档（`docs/WORKLOG.md`、`docs/HANDOFF.md` 中引用了 `43fcc5f`、`85776aa`、`ee039bb`、`f5868ae`、`6d596a1`）全部悬空。
- GitHub 服务端会保留旧对象（缓存、PR ref、fork 网络），彻底移除需联系 GitHub Support。
- 需要冻结窗口、完整镜像备份与协作通知，组织协调成本高。

### 选项 3：BFG Repo-Cleaner

**做法：** `java -jar bfg.jar --delete-folders __MACOSX --delete-files '*_read_starts.txt' <镜像克隆>`，然后 `git reflog expire` + `git gc --prune=now`，再 force-push。

**利：**

- 为大文件/目录删除场景优化，语法简单，速度快（对本仓库体量与 filter-repo 差异无感）。
- 与选项 2 一样能使历史真正缩小。

**弊：**

- 需要 Java 运行环境（额外依赖）。
- **默认保护 HEAD**：当前 HEAD 仍含这些文件，必须先用选项 1 的方式提交一次删除，再运行 BFG，流程多一步且易被忽略导致"跑了但没清掉"。
- 路径匹配精度与灵活性不如 filter-repo；项目维护活跃度低于 filter-repo。
- 协作冲击与选项 2 **完全相同**（同样是全量改写历史 + force-push）。

### 选项 4：Git LFS

**做法：** `git lfs track "docs/legacy/original-directories/文献13-PMID38030608/*_read_starts.txt"`，并用 `git lfs migrate import --everything` 将历史中的文件改写为 LFS 指针，大对象存入 LFS 存储。

**利：**

- 文件保持版本化管理，克隆默认只拉取指针（可按需 `git lfs pull`）。
- GitHub 原生支持，适合"必须在仓内版本化的大资产"。

**弊：**

- `git lfs migrate import` **同样全量改写历史**，协作冲击与选项 2/3 相同（若不做 migrate 只做 track，则等同选项 1 且历史不缩小）。
- GitHub LFS 免费额度仅 1 GiB 存储 / 1 GiB 月带宽：168 MB 的对象集被克隆数次即可耗尽当月带宽，产生费用或拉取失败。
- 增加所有克隆者的工作流复杂度（必须安装 git-lfs）；GitHub Pages、源码归档（zip 下载）拿到的是指针而非内容。
- **预设了"这批文件必须在仓内版本化"的结论**，而托管策略（HANDOFF 待决事项第 4 条）尚未定案；这批文件可从公开来源重新获取，仓内版本化的必要性存疑。

## 3. 风险分析

### 3.1 历史重写的共性风险（选项 2、3 及选项 4 的 migrate 模式）

1. **协作者同步断裂**：所有 commit hash 改变后，每个持有克隆的人都必须重新克隆或硬重置；任何基于旧历史的本地分支、stash、标签全部失效。
2. **在途工作损失**：本仓库当前有未合并的 draft PR #1，以及工作区中未提交的 Task 02 产出（`site/`、`scripts/`）与 6 个 docs 修订。改写前若不先提交/导出，这些工作的评审上下文（PR 评论、提交链）将不可恢复地断裂。
3. **引用悬空**：项目文档（WORKLOG/HANDOFF）与外部讨论中引用的旧 SHA 全部失效，可追溯性受损。
4. **服务端残留**：GitHub 的 PR ref、fork 网络与对象缓存会保留旧数据；force-push 不等于服务端彻底删除，需联系 GitHub Support，且周期不可控。
5. **不可逆性**：无完整镜像备份时，改写错误（路径写错、误伤其他文件）不可恢复。

### 3.2 本仓库的特有加剧因素

- 目标文件自**初始提交**即入库，改写意味着仓库历史上的**每一个**提交哈希都会变化，无任何"部分保留"的折中。
- 路径含非 ASCII 字符（`docs/legacy/original-directories/文献13-PMID38030608/`），命令行与工具链中需注意引号与 `core.quotepath` 转义，误写路径会导致清错或清不掉。
- 当前分支结构简单（main + 1 个在途分支），是重写代价相对最低的窗口之一；但该窗口随 PR #1 评审推进与 Task 02 提交而随时变化。

### 3.3 选项 1 的特有风险

- 文件未追踪后被 `git clean -fdx` 或手工清理误删（缓解：内容可从公开来源重新获取；在执行步骤中明确提示）。
- 误以为"停止追踪 = 历史清除"：后续若因体积原因必须重写历史，仍需走选项 2/3 的完整流程。

### 3.4 降低紧迫性的事实

- read-starts 数据为公开文献补充材料，无敏感信息，历史残留不构成安全或合规风险。
- pack 仅约 30.72 MiB，克隆体积问题并不紧急；真正紧急的是卫生问题（垃圾文件、悬空引用、追踪边界不清）。

## 4. 推荐方案及理由

**推荐分阶段执行：阶段 A 立即做（选项 1 + README 修复），阶段 B 设门槛暂缓（选项 2）。**

- **阶段 A（已于 2026-08-10 执行）：** 当前 Git 树停止保留重复原目录、6 个 read-starts 文件与 `__MACOSX/`，`.gitignore` 增加整目录规则；根目录历史报告同时归档。以普通提交进入 PR #3，不改写历史。
- **阶段 B（暂缓，满足全部门槛后再决策）：** 若届时托管策略定案为"彻底移出仓库历史"，用 **选项 2（git filter-repo）** 做一次性协调重写。门槛：
  1. draft PR #1 已合并，无其他在途分支（或已全部导出 patch）；
  2. 大型资产托管策略（HANDOFF 待决事项第 4 条）已定案，且结论为"不入 git 历史"；
  3. 已完成完整镜像备份并通知全部协作者冻结推送；
  4. 文档中的旧 SHA 引用已评估并加注。
- **不推荐选项 3（BFG）作为首选：** 与 filter-repo 冲击相同，但多一步 HEAD 保护前置、路径精度较低、维护状态较弱。仅作为 filter-repo 不可用时的等价替代。
- **不推荐选项 4（Git LFS）：** 预设了未定的托管结论；免费额度与 168 MB 对象集不匹配；若要历史缩小同样必须改写历史，不省任何协作成本。

**理由：** 当前 pack 仅约 30.72 MiB，体积收益小；而历史重写的协作冲击（PR #1 失效、文档 SHA 悬空、全员重新克隆）确定且大。阶段 A 以零协作冲击解决全部三项卫生问题中"向前看"的部分；把不可逆操作推迟到托管策略定案、在途工作清零之后，收益不变而风险最低。`archive/` 引用的修复选择"删除该行"而非"补建目录"：该目录在全部历史中从未存在，无内容可恢复，保留引用只会继续误导读者。

## 5. 精确执行步骤（命令）

> 以下命令保留为最初方案记录。阶段 A 已按上方执行状态完成，**不要重复执行**；实际范围还包括移除重复的 `original-directories/` 和整理根目录旧报告。阶段 B 仍未执行。

### 阶段 A：停止追踪 + 文档修复（普通提交，可逆）

```bash
# 0. 维护者自最新 main 创建执行分支（本方案不创建分支）
git switch main && git pull
git switch -c agent/repo-hygiene

# 1. .gitignore 追加规则（保留文件原有 BOM 与内容，仅追加）
cat >> .gitignore <<'EOF'

# macOS 归档垃圾
__MACOSX/
.DS_Store

# 大型 read-starts 数据（PMID 38030608 公开补充材料，可从来源重新获取）：
# 停止追踪，本地文件保留
docs/legacy/original-directories/文献13-PMID38030608/*_read_starts.txt
EOF

# 2. 停止追踪（--cached：文件保留在磁盘）
git rm -r --cached --quiet "docs/legacy/original-directories/文献13-PMID38030608/__MACOSX"
git rm --cached --quiet docs/legacy/original-directories/文献13-PMID38030608/*_read_starts.txt

# 3. 手工编辑 README.md：删除第 59 行
#    "├── archive/                   # 历史过程记录（已整合的旧报告）"

# 4. 验证
git ls-files | grep -E "__MACOSX|read_starts" && echo "FAIL: 仍在追踪" || echo "OK: 已全部停止追踪"
ls -lh docs/legacy/original-directories/文献13-PMID38030608/*_read_starts.txt   # 确认 6 个文件仍在磁盘（合计约 168 MB）
git status -sb                                  # 确认仅有预期改动
git diff --check

# 5. 提交、推送、开 draft PR（维护者执行）
git add .gitignore README.md
git commit -m "chore: stop tracking read-starts data and __MACOSX junk; drop dangling archive/ ref"
git push -u origin agent/repo-hygiene
```

注意：执行后本地 6 个 read-starts 文件成为未追踪文件，`git clean -fdx` 会将其删除；其内容可从 PMID 38030608 公开补充材料重新获取，如需本地留存请自行备份。

### 阶段 B：filter-repo 历史重写（仅在第 4 节全部门槛满足后执行）

```bash
# 0. 前置检查：PR #1 已合并；无在途分支（或已 git format-patch 导出）；已通知协作者冻结

# 1. 完整镜像备份（保留至全部协作者确认迁移完成后再归档冷存储）
git clone --mirror https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database.git bted-backup-YYYYMMDD.git

# 2. 在全新镜像克隆上执行改写（filter-repo 官方要求；不要在日常使用的工作树上运行）
pip install git-filter-repo    # 或 brew install git-filter-repo
git clone --mirror https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database.git bted-clean.git
cd bted-clean.git
git filter-repo --invert-paths \
  --path "docs/legacy/original-directories/文献13-PMID38030608/__MACOSX" \
  --path-glob "docs/legacy/original-directories/文献13-PMID38030608/*_read_starts.txt"

# 3. 验证
git log --all --oneline -- "*read_starts.txt" "__MACOSX"   # 应无输出
git count-objects -vH                                       # pack 应显著缩小

# 4. 重新挂接远端并强制推送（filter-repo 默认移除原 remote）
git remote add origin https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database.git
git push --force --all origin
git push --force --tags origin

# 5. 善后
#    - 全部协作者重新克隆（禁止在旧克隆上 pull）
#    - 重建受影响的 PR；在 WORKLOG/HANDOFF 中为新历史基线加注
#    - 如需清除 GitHub 服务端缓存对象，联系 GitHub Support
```

## 6. 回滚方案

### 阶段 A 回滚

- 提交未推送：`git reset --hard HEAD~1`（在执行分支上）。
- 提交已推送/已合并：`git revert <阶段A提交>`。
- 恢复追踪（如需）：`git add -f docs/legacy/original-directories/文献13-PMID38030608/*_read_starts.txt`（`-f` 因为已被 `.gitignore` 忽略），并移除 `.gitignore` 追加行。
- 数据安全性：阶段 A 全程不删除磁盘文件，回滚零数据丢失风险。

### 阶段 B 回滚（force-push 之后）

```bash
# 用阶段 B 第 1 步的镜像备份整体覆盖回远端
cd bted-backup-YYYYMMDD.git
git remote add origin https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database.git
git push --force --all origin
git push --force --tags origin
```

- 全部协作者需再次重新克隆。
- 限制：GitHub 的 PR ref 不接受推送，已失效的 PR 只能重建不能恢复；回滚期间基于新历史产生的提交需人工 cherry-pick 或放弃。
- 备份保留策略：镜像备份至少保留到全部协作者书面确认迁移完成、且经过一个完整工作迭代后，再转冷存储归档；在此之前禁止删除。

---

## 附录 A：事实核查记录（2026-08-07，只读命令）

| 命令 | 结果 |
|------|------|
| `ls -l docs/legacy/original-directories/文献13-PMID38030608/*_read_starts.txt` | 6 个文件：33.8 / 17.1 / 44.8 / 21.4 / 33.9 / 17.0 MB，合计 168.0 MB |
| `git ls-files docs/legacy/original-directories/文献13-PMID38030608/` | 6 个 read-starts 文件与 6 个 `__MACOSX/._*` 文件均已追踪 |
| `git log --all --oneline --diff-filter=A -- "*read_starts.txt"` | 初始提交 `b59e72a` 引入 |
| `git count-objects -vH` / `du -sh .git` | size-pack 30.72 MiB；`.git` 合计 31 MB |
| `ls -d archive` | No such file or directory |
| `git log --all --oneline -- archive/` | 无输出（该路径在全部可达历史中从未被追踪） |
| `grep -n archive README.md` | 第 59 行：`├── archive/   # 历史过程记录（已整合的旧报告）` |
| `ls -la docs/legacy/original-directories/文献13-PMID38030608/__MACOSX/` | 6 个 `._*` 文件，每个约 178 B |
