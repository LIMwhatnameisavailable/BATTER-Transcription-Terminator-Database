# 当前 BTED 状态

**更新时间：** 2026-08-10
**当前候选发布：** v0.2.0 public demo
**详细发布说明：** [`docs/releases/v0.2.0.md`](releases/v0.2.0.md)

## 已完成

| 项目 | 当前状态 | 证据/入口 |
|---|---|---|
| 来源范围 | 13 篇原始研究文献、22 条 BATTER Table S1 来源记录 | `data/registry/batter_s1_source_registry.tsv` |
| 来源 manifest | 22/22 | `data/registry/manifests/` |
| 来源处理说明 | 22/22；S1_005、S1_020、S1_022 已完成重点工程审计 | `docs/sources/`、`data/audit/v0.2.0/priority_source_audit.json` |
| 标准化公开数据 | 21 个来源、28,399 条核心记录 | `data/public/v0.2.0/records/` |
| 仅审计来源 | S1_002 | `data/public/v0.2.0/records/BATTER_S1_002/manifest.json` |
| 统一字段与坐标 | 24 列核心表 + 来源特异附表；1-based biological coordinate + BED6 | `docs/standards/BTED_数据发布接口_v0.2.md` |
| 站点 | 双语静态网站、22 个详情页 | `site/` |
| JBrowse | 21 套独立配置、123 个来源前缀资产 | `dist/BTED-v0.2.0-jbrowse/`（本地构建；Release 草稿托管） |

## 已固定的发布边界

1. 预测位点和无法拆分的混合实验/预测表不进入 `data/public/` 或站点下载；只保留公开 checksum 审计摘要。
2. 作者发表端点、信号调用候选端点和文献整理记录分别保留 evidence class，不以“功能终止子”混称。
3. 坐标、contig、链或参考版本无法核实的来源，不以猜测方式升级为公开数据。
4. 原始 FASTQ/BAM、出版商工作簿、FASTA/GFF、BigWig 和本地浏览器资产不进 Git；只提供公共入口、版本说明和 checksum。

## 当前风险与下一步

1. **S1_002：** 为逐数据集观察补齐作者表行、样本、实验类型和坐标 provenance；只有拆出纯实验端点后才可公开。
2. **评审与发布：** 依次审阅串联 PR #1–#4；发布 `v0.2.0` Release 后再启用依赖其资产的 Pages 工作流。
3. **Pages 权限：** 仓库管理员需在 Settings → Pages 选择 GitHub Actions，并在部署后检查仓库子路径链接。
4. **再分发条件：** 正式长期归档或论文发布前，仍需逐来源复核许可与引用要求；未确认资产不得进入公开包。
5. **仓库卫生：** 约 168 MB read-start 文本、`__MACOSX` 和重复文献原目录已从当前 Git 树移除；未改写历史，旧对象仍可从旧提交恢复。是否进一步清理历史见 `docs/cleanup-proposal.md`。

## 必跑验证

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

2026-08-07 的初始远程仓库盘点和“外部工作树待核实”记录已保留在 `docs/WORKLOG.md` 与 `docs/remote-repository-migration-inventory.md` 作为历史背景；本文件以 v0.2.0 候选发布资产为当前事实来源。
