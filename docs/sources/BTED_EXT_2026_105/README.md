# BTED_EXT_2026_105 — 来源处理记录

## 本仓库迁移状态

| 项目 | 值 |
|---|---|
| 发布判定 | `excluded_duplicate` |
| 公开资产 | `data/records/BTED_EXT_2026_105/`（24 列端点表 + BED6） |
| 记录数 | 见端点表行数（`BTED_EXT_2026_105_endpoints.tsv`） |
| 主要证据层 | `NA` |
| 迁移日期 | 2026-08-10 |
| 参考组装 | `GCF_000005845.1;GCF_000009045.1` |
| 参考序列 | `NC_000913.3;NC_000964.3` |
| 原始数据入口 | GSE95211 |
| 论文 | PMID [42148773](https://pubmed.ncbi.nlm.nih.gov/42148773/) · DOI [10.1128/msystems.01581-25](https://doi.org/10.1128/msystems.01581-25) |

## 范围与证据边界

**排除重复（excluded_duplicate）**：本来源为对 Lalanne et al. 2018 已发表 Rend-seq 数据（GSE95211）的重新分析（Eco/Bsu sheet），与 BATTER_S1_001（E. coli）和 BATTER_S1_003（B. subtilis）同源，非新增贡献，不重复收录。留痕行仅登记，不建端点表。详见 intake 表 blocker_or_note 与 `data/audit/excluded_assets/105/excluded_assets.json`。

BTED 的公开术语为“实验支持的 3′ end / 端点”；这并不表示每个位置均完成了独立的终止功能实验。证据分层定义见 [`证据分层与发布边界`](../../standards/证据分层与发布边界.md)。

## 坐标体系

- 端点坐标：`NA…`
- `end_id` 格式：`<source_id>_<sample_id>_<reference_name>_<plus|minus>_<序号>`；链标记用 `plus`/`minus` 全词，与 BATTER_S1 已发布 22 源一致
- BED6 转换：`reference_name`、`position-1`、`position`、`end_id`、`0`、`strand`

## 可复现性材料

- 本来源原始数据（补充表/PDF/parsed.csv）不随 Git 复制；请通过上表公共入口获取。
- 标准化端点表 SHA-256 见本目录 `SHA256SUMS.txt`。
- 端点表构建脚本：`draft/endpoints_output/build_*.py`；排除记录见 `draft/endpoints_output/*_exclusion_report.txt`。
- 本次不发布 BigWig、FASTA/GFF 或 JBrowse 资产；大型衍生文件应以外部发布物/浏览器包提供。
