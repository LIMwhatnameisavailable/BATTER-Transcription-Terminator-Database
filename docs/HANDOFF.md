# BTED 当前交接

**更新：** 2026-08-10
**当前分支：** `refactor/project-structure-and-literature-notes-v0.1`
**当前里程碑：** v0.1 local snapshot 已构建并通过校验，待提交/推送。

## 已交付

- 22 个 BATTER S1 来源均有 `data/registry/manifests/BATTER_S1_*.json` 和 `docs/sources/<source_id>/README.md`。
- 21 个来源、28,399 条记录已发布为 Git 可追踪的标准化 TSV；17 个作者发表端点来源有 BED6。
- 4 个 Lalanne 2018 来源按 `curated_record` 发布，不与从本地信号调用的候选峰混写。
- `BATTER_S1_002` 维持 `audit_only`；混合证据和预测资产只保存公开 checksum 审计摘要。
- 构建器：`scripts/build_local_snapshot_release.py`；发布校验器：`scripts/validate_bted_release.py`。
- 页面 `site/sources.html` 已改为 v0.1 发布索引；站点不提供 JBrowse/BigWig。

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
python3 scripts/validate-site.py
git diff --check
```

## 下一步（按优先级）

1. 提交、推送并开 Draft PR；许可/再分发条件由项目维护者复核。
2. 为 `BATTER_S1_002` 补逐观测的作者表行、样本、实验类型与坐标 provenance；能够拆出纯实验端点后才允许发布。
3. 补写 `BATTER_S1_005` 和 `BATTER_S1_022` 的详细处理记录。
4. 制定独立 JBrowse 发布包（资产清单、版本、checksum、外部托管位置）；不要直接把原始/大轨道提交到 Git。
5. 后续接入新来源继续使用 26 列 source intake 与 24 列 endpoint schema，并保留一个来源一个 PR 的审计粒度。

## 不要做

- 不把 `author_integrated_mixed_evidence` 或 `prediction_only` 放进 `data/public/`；
- 不把 1-based 坐标直接当 BED start；
- 不让同物种、不同论文或不同参考版本的条目共用 source ID；
- 不复制 FASTQ/BAM/BigWig、出版商工作簿或本机绝对路径到仓库。
