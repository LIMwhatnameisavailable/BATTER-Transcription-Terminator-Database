# BTED_EXT_2026_112 — 来源处理记录

## 本仓库迁移状态

| 项目 | 值 |
|---|---|
| 发布判定 | `to_review` |
| 公开资产 | `data/records/BTED_EXT_2026_112/`（24 列端点表 + BED6） |
| 记录数 | 见端点表行数（`BTED_EXT_2026_112_endpoints.tsv`） |
| 主要证据层 | `NA`（挂起，原 `algorithm_called_endpoint`，待字典提案二正式采纳后升级） |
| 迁移日期 | 2026-08-10 |
| 参考组装 | `GCF_000005845.1 (ASM584v1)` |
| 参考序列 | `NC_000913.3` |
| 原始数据入口 | PRJEB36932 (ERP120199; ERR8194521-523) |
| 论文 | PMID [35357499](https://pubmed.ncbi.nlm.nih.gov/35357499/) · DOI [10.1093/nar/gkac206](https://doi.org/10.1093/nar/gkac206) |

## 范围与证据边界

算法重分析端点（TERMITe 流水线代码调用）。**evidence_class 暂挂起为 `NA`**，待字典提案二（`algorithm_called_endpoint`）正式采纳后升级；在团队正式采纳前不得称为原作者直接发表的端点，也不得称为预测。端点来源为 TERMITe 对原始 Term-seq 数据的重分析，而非论文补充表原文。

⚠️ **本源有 1 行 `qc_status=to_review`**：POT 与 summit 相差 1 bp（坐标已按规则取 summit），所在数据集不在四项独立验证覆盖内，1 bp 归属未实证。恢复条件见该行 note（对 POT/summit 区间做 U-tract 比对与 T-run 富集确认后改回 `pass`）。

BTED 的公开术语为“实验支持的 3′ end / 端点”；这并不表示每个位置均完成了独立的终止功能实验。证据分层定义见 [`证据分层与发布边界`](../../standards/证据分层与发布边界.md)。

## 坐标体系

- 端点坐标：`parsed.csv 坐标 1-based 单碱基(2026-08-09 实证, 验证代表性数据集=E.coli a PRJNA906280 686行单染色体 + E.faecalis PRJEB12568 779行含3个复制子): 1) summit_coordinate==POT 全部一致(E.coli_a 686/686, E.faecalis 778/779; 唯一不一致行NZ_CP008816.1:1636266-163627…`
- `end_id` 格式：`<source_id>_<sample_id>_<reference_name>_<plus|minus>_<序号>`；链标记用 `plus`/`minus` 全词，与 BATTER_S1 已发布 22 源一致
- BED6 转换：`reference_name`、`position-1`、`position`、`end_id`、`0`、`strand`

## 可复现性材料

- 本来源原始数据（补充表/PDF/parsed.csv）不随 Git 复制；请通过上表公共入口获取。
- 标准化端点表 SHA-256 见本目录 `SHA256SUMS.txt`。
- 端点表构建脚本：`draft/endpoints_output/build_*.py`；排除记录见 `draft/endpoints_output/*_exclusion_report.txt`。
- 本次不发布 BigWig、FASTA/GFF 或 JBrowse 资产；大型衍生文件应以外部发布物/浏览器包提供。
