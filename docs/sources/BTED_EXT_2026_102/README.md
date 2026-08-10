# BTED_EXT_2026_102 — 来源处理记录

## 本仓库迁移状态

| 项目 | 值 |
|---|---|
| 发布判定 | `to_review` |
| 公开资产 | `data/records/BTED_EXT_2026_102/`（24 列端点表 + BED6） |
| 记录数 | 见端点表行数（`BTED_EXT_2026_102_endpoints.tsv`） |
| 主要证据层 | `author_called_endpoint` |
| 迁移日期 | 2026-08-10 |
| 参考组装 | `GCF_000012525.1` |
| 参考序列 | `CP000100.1 (RefSeq 等价 NC_007604.1)` |
| 原始数据入口 | GSE309256 |
| 论文 | PMID [42148773](https://pubmed.ncbi.nlm.nih.gov/42148773/) · DOI [10.1128/msystems.01581-25](https://doi.org/10.1128/msystems.01581-25) |

## 范围与证据边界

作者直接发表的端点（`author_called_endpoint`，最高置信度 `defined end` 层）与次级置信度端点（`called_endpoint`，`diffuse peak`/`unclear` 有峰层，依据 s0002.docx P32/P34/P77 作者原文重分级，详见 `cascino_reclassification_changelog.md`）混合。坐标统一取 `gene_peak_posn`（CP000100.1 1-based 单碱基）。

BTED 的公开术语为“实验支持的 3′ end / 端点”；这并不表示每个位置均完成了独立的终止功能实验。证据分层定义见 [`证据分层与发布边界`](../../standards/证据分层与发布边界.md)。

## 坐标体系

- 端点坐标：`1-based 单碱基位点 (2026-08-09 实证确认): peak_position 为 CP000100.1 1-based 坐标上的单个基因组碱基; U_tract 列=峰前含峰位的 8nt 窗口, 用 s0004 全 388 行(225 U-tract+163 No U-tract, 含 - 链 195 行) 对 CP000100.1 序列验证 100% 吻合(+ 链=正链 [peak-7,peak], - 链=正链 [p…`
- `end_id` 格式：`<source_id>_<sample_id>_<reference_name>_<plus|minus>_<序号>`；链标记用 `plus`/`minus` 全词，与 BATTER_S1 已发布 22 源一致
- BED6 转换：`reference_name`、`position-1`、`position`、`end_id`、`0`、`strand`

## 可复现性材料

- 本来源原始数据（补充表/PDF/parsed.csv）不随 Git 复制；请通过上表公共入口获取。
- 标准化端点表 SHA-256 见本目录 `SHA256SUMS.txt`。
- 端点表构建脚本：`draft/endpoints_output/build_*.py`；排除记录见 `draft/endpoints_output/*_exclusion_report.txt`。
- 本次不发布 BigWig、FASTA/GFF 或 JBrowse 资产；大型衍生文件应以外部发布物/浏览器包提供。
