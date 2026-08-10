# BTED_EXT_2026_101 — 来源处理记录

## 本仓库迁移状态

| 项目 | 值 |
|---|---|
| 发布判定 | `to_review` |
| 公开资产 | `data/records/BTED_EXT_2026_101/`（24 列端点表 + BED6） |
| 记录数 | 见端点表行数（`BTED_EXT_2026_101_endpoints.tsv`） |
| 主要证据层 | `author_called_endpoint` |
| 迁移日期 | 2026-08-10 |
| 参考组装 | `GCF_000932055.2` |
| 参考序列 | `CP010905.2` |
| 原始数据入口 | GSE155167; PRJNA648911; SRP273712 |
| 论文 | PMID [34131082](https://pubmed.ncbi.nlm.nih.gov/34131082/) · DOI [10.1073/pnas.2103579118](https://doi.org/10.1073/pnas.2103579118) |

## 范围与证据边界

作者直接发表的端点（`author_called_endpoint`）。链向推断自 GFF 特征交叉验证（confidence 高/低），详见 `draft/fuchs_strand_inference_result.tsv`；strand 无法确定的 75 行未入表，审计留痕见 `data/audit/excluded_assets/BTED_EXT_2026_101/fuchs_2021_unresolved_strand_75rows.tsv`（并登记于同目录 `excluded_assets.json`）。

BTED 的公开术语为“实验支持的 3′ end / 端点”；这并不表示每个位置均完成了独立的终止功能实验。证据分层定义见 [`证据分层与发布边界`](../../standards/证据分层与发布边界.md)。

## 坐标体系

- 端点坐标：`1-based (dnaA Start=1, 无 Start=0; 已与 GCF_000932055.2/NZ_CP010905.2 GFF 交叉验证, 10 基因坐标抽查 9/10 完全一致; 注: 论文表标注基因组 4,274,806 bp, 但 CP010905.2 实际为 4,274,782 bp (NCBI 核实), 论文标注基因组长度4,274,806 bp与当前RefSeq记录CP010905.2实际长度4,274,782…`
- `end_id` 格式：`<source_id>_<sample_id>_<reference_name>_<plus|minus>_<序号>`；链标记用 `plus`/`minus` 全词，与 BATTER_S1 已发布 22 源一致
- BED6 转换：`reference_name`、`position-1`、`position`、`end_id`、`0`、`strand`

## 可复现性材料

- 本来源原始数据（补充表/PDF/parsed.csv）不随 Git 复制；请通过上表公共入口获取。
- 标准化端点表 SHA-256 见本目录 `SHA256SUMS.txt`。
- 端点表构建脚本：`draft/endpoints_output/build_*.py`；排除记录见 `draft/endpoints_output/*_exclusion_report.txt`。
- 本次不发布 BigWig、FASTA/GFF 或 JBrowse 资产；大型衍生文件应以外部发布物/浏览器包提供。
