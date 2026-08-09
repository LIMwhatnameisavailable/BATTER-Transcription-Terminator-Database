# 当前 BTED 状态

**更新时间：** 2026-08-10
**当前发布：** v0.1 local snapshot
**详细发布说明：** [`docs/releases/v0.1-local-snapshot.md`](releases/v0.1-local-snapshot.md)

## 已完成

| 项目 | 当前状态 | 证据/入口 |
|---|---|---|
| 来源范围 | 13 篇原始研究文献、22 条 BATTER Table S1 来源记录 | `data/registry/batter_s1_source_registry.tsv` |
| 来源 manifest | 22/22 | `data/registry/manifests/` |
| 来源处理说明 | 22/22 有 README；S1_005、S1_022 待补独立详细记录 | `docs/sources/` |
| 标准化公开数据 | 21 个来源、28,399 条记录 | `data/public/records/` |
| 仅审计来源 | S1_002 | `data/audit/excluded_assets/BATTER_S1_002/` |
| 统一字段与坐标 | 24 列 schema；1-based biological coordinate + BED6 | `data/registry/templates/`、`scripts/validate_bted_release.py` |
| 站点 | 静态发布索引已更新 | `site/` |
| JBrowse/BigWig | 未随 Git release 发布 | 后续独立版本化浏览器包 |

## 已固定的发布边界

1. 预测位点和无法拆分的混合实验/预测表不进入 `data/public/` 或站点下载；只保留公开 checksum 审计摘要。
2. 作者发表端点、信号调用候选端点和文献整理记录分别保留 evidence class，不以“功能终止子”混称。
3. 坐标、contig、链或参考版本无法核实的来源，不以猜测方式升级为公开数据。
4. 原始 FASTQ/BAM、出版商工作簿、FASTA/GFF、BigWig 和本地浏览器资产不进 Git；只提供公共入口、版本说明和 checksum。

## 当前风险与下一步

1. **S1_002：** 为逐数据集观察补齐作者表行、样本、实验类型和坐标 provenance；只有拆出纯实验端点后才可公开。
2. **来源文档：** 补写 S1_005、S1_022 的独立详细处理记录。
3. **浏览器：** 从本地已核查 JBrowse 建立独立发布包，清单中必须有版本、checksum、参考序列与资产托管位置。
4. **再分发条件：** 正式外部发布到 Zenodo/生产网站前，逐来源复核派生 TSV/BED 的许可与引用要求。
5. **仓库卫生：** 历史追踪的大型 read-start 文本和 `__MACOSX` 仍需按 `docs/cleanup-proposal.md` 的单独决策处理；本版未删除任何历史文件。

## 必跑验证

```bash
python3 scripts/validate_bted_templates.py
python3 scripts/validate_bted_release.py
python3 scripts/build_sources_page.py
python3 scripts/validate-site.py
python -m unittest -v tests/test_bted_ingestion.py
git diff --check
```

2026-08-07 的初始远程仓库盘点和“外部工作树待核实”记录已保留在 `docs/WORKLOG.md` 与 `docs/remote-repository-migration-inventory.md` 作为历史背景；本文件以 v0.1 已实际迁入的资产为当前事实来源。
