# BTED 当前交接

**更新：** 2026-08-10
**当前分支：** `refactor/project-structure-and-literature-notes-v0.1`
**当前里程碑：** v0.1 local snapshot 已构建并通过校验；PR #3 根目录和 legacy 当前树清理已完成，待推送并同步到 PR #4。

## 已交付

- 22 个 BATTER S1 来源均有 `data/registry/manifests/BATTER_S1_*.json` 和 `docs/sources/<source_id>/README.md`。
- 21 个来源、28,399 条记录已发布为 Git 可追踪的标准化 TSV；17 个作者发表端点来源有 BED6。
- 4 个 Lalanne 2018 来源按 `curated_record` 发布，不与从本地信号调用的候选峰混写。
- `BATTER_S1_002` 维持 `audit_only`；混合证据和预测资产只保存公开 checksum 审计摘要。
- 构建器：`scripts/build_local_snapshot_release.py`；发布校验器：`scripts/validate_bted_release.py`。
- 页面 `site/sources.html` 已改为 v0.1 发布索引；站点不提供 JBrowse/BigWig。
- 根目录只保留正式项目入口；早期报告归入 `docs/legacy/project-reports/`，登录号快照归入 `data/audit/legacy/`。
- 重复 `docs/legacy/original-directories/`、read-starts 和 `__MACOSX` 已从当前 Git 树移除；未改写历史。

## 接手前先读

1. [`docs/releases/v0.1-local-snapshot.md`](releases/v0.1-local-snapshot.md)
2. [`docs/standards/证据分层与发布边界.md`](standards/证据分层与发布边界.md)
3. [`data/registry/batter_s1_publication_status.tsv`](../data/registry/batter_s1_publication_status.tsv)
4. 要处理的 `data/registry/manifests/BATTER_S1_NNN.json` 与 `docs/sources/BATTER_S1_NNN/README.md`

## 验证命令

```bash
python3 scripts/validate_bted_templates.py
python3 scripts/validate_bted_release.py
python3 scripts/build_sources_page.py
python3 scripts/validate_repo_layout.py
python3 scripts/validate-site.py
git diff --check
```

## 下一步（按优先级）

1. 将本次结构清理推送到 PR #3 的远端分支并确认 diff。
2. 将 PR #3 更新合并到 PR #4，保留 v0.2 WORKLOG/HANDOFF 与网站内容。
3. 按 #1 → #2 → #3 → #4 的顺序处理串联 PR；不要在下游 PR 改 base 前删除上游分支。
4. 许可/再分发条件仍由项目维护者复核；S1_002 只有拆出纯实验端点后才允许发布。
5. 历史重写不是本次任务；若未来执行，必须先完成镜像备份与协作冻结。

## 不要做

- 不把 `author_integrated_mixed_evidence` 或 `prediction_only` 放进 `data/public/`；
- 不把 1-based 坐标直接当 BED start；
- 不让同物种、不同论文或不同参考版本的条目共用 source ID；
- 不复制 FASTQ/BAM/BigWig、出版商工作簿或本机绝对路径到仓库。
