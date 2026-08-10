# BTED 当前交接

**更新：** 2026-08-10

**当前分支：** `agent/bted-v0.2-public-demo`

**当前里程碑：** v0.2.0 数据、网站、JBrowse 和完整验收已完成；开发分支、Draft PR #4 与 GitHub Release 草稿均已建立。

## 已交付

- 22 个来源均有 manifest 和详情页；21 个来源公开标准数据，S1_002 为 `audit_only`。
- 21 个来源共 28,399 条 24 列核心记录；17 个许可允许的来源另有来源特异表。
- 每个公开来源有 BED6、字段清单、manifest 和 checksum。
- 21 套独立 JBrowse 配置；S1_005 的 CP009977.1/CP009978.1 位于同一 assembly。
- 双语静态网站包含首页、筛选目录、下载页、方法页、关于页和 22 个来源页。
- 数据/JBrowse Release 资产、CI、Pages workflow 和本地 Pages staging 已具备。
- S1_005、S1_020、S1_022 的工程审计和处理记录已补齐。
- 外部链接审计已保存为 `data/audit/v0.2.0/external_link_audit.tsv`，无失败或缺失必填入口。
- PR #3 的根目录清理已同步：旧报告和登录号快照归档，重复的 `docs/legacy/original-directories/`、read-starts 与 `__MACOSX` 已退出当前 Git 树；历史未改写。

## 接手前阅读

1. [`docs/releases/v0.2.0.md`](releases/v0.2.0.md)
2. [`docs/standards/BTED_数据入库标准流程_v0.2.md`](standards/BTED_数据入库标准流程_v0.2.md)
3. [`docs/standards/BTED_数据发布接口_v0.2.md`](standards/BTED_数据发布接口_v0.2.md)
4. [`data/public/v0.2.0/release_manifest.json`](../data/public/v0.2.0/release_manifest.json)
5. [`data/registry/batter_s1_publication_status.v0.2.0.tsv`](../data/registry/batter_s1_publication_status.v0.2.0.tsv)

## 重新构建

```bash
python3 scripts/build_v0_2_release.py --input-root /path/to/BGIRNA
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/build_release_archives.py
python3 scripts/build_jbrowse_release.py --input-root /path/to/BGIRNA
python3 scripts/build_v0_2_site.py
python3 scripts/stage_pages.py --jbrowse-dir dist/BTED-v0.2.0-jbrowse --output-dir .pages-preview
```

## 完整验证

```bash
python3 scripts/validate_bted_templates.py
python3 scripts/validate_bted_release.py
python3 scripts/validate_repo_layout.py
python3 scripts/validate_bted_v0_2.py
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
python3 scripts/validate-site.py site
python3 scripts/validate-site.py .pages-preview
python3 -m unittest -v tests/test_bted_ingestion.py tests/test_bted_v0_2.py
git diff --check
```

## 待完成

1. 审阅已同步 PR #3 结构清理的 Draft PR #4，保持串联 PR 的改动范围清晰。
2. 按 #1 → #2 → #3 → #4 顺序处理 PR 基线，避免直接把全部历史一次展开到 `main`。
3. 评审通过后发布 `v0.2.0` Release，再合并包含 Pages workflow 的分支。
4. 在 Settings → Pages 选择 GitHub Actions，运行部署并检查稳定链接。
5. S1_002 只有在未来能可靠拆出纯实验端点时才改变 `audit_only`。

## 远端发布状态

- 实现提交：`142e371 feat: build BTED v0.2 public demo`。
- 分支：`agent/bted-v0.2-public-demo`，已通过 SSH 推送。
- Draft PR：`https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database/pull/4`，CI 已通过。
- PR #3 结构清理提交：`61318db refactor: clean repository root and legacy assets`。
- `v0.2.0` Release 草稿包含四个发布资产；保持草稿，直至评审和 Pages 发布顺序确认。
- Pages workflow 仅允许手动触发；正式发布 Release 且管理员启用 Pages 后再运行，避免合并时产生预期失败。
- HTTPS OAuth 令牌仍缺少 `workflow` scope；继续推送本分支可使用已验证的 SSH 地址，无需重新构建数据。

## 不要做

- 不把协作者外部文献合入本分支；
- 不把混合证据或纯预测放进公开端点表/JBrowse；
- 不把作者预测注释解释为新的实验结果；
- 不把原始测序、出版商工作簿、大型 JBrowse 文件或凭据提交到 Git；
- 不在未确认参考、坐标、contig、strand 或许可时猜测补齐。
