# BATTER_S1_005 — 来源处理记录

## 本仓库迁移状态

| 项目 | 值 |
|---|---|
| 发布判定 | `published_standardized` |
| 公开资产 | `data/public/v0.2.0/records/BATTER_S1_005/endpoints.tsv` |
| 记录数 | 1154 |
| 主要证据层 | `curated_record` |
| 版本 / 日期 | `v0.2.0` / 2026-08-10 |
| 参考组装 | `GCF_001456255.1` |
| 原始数据入口 | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE95211 |
| 论文 | PMID [29606352](https://pubmed.ncbi.nlm.nih.gov/29606352/) · DOI [10.1016/j.cell.2018.03.007](https://doi.org/10.1016/j.cell.2018.03.007) |

## 范围与证据边界

Literature-curated record on the two-contig reference; manual review status remains documented in the source manifest.

BTED 的公开术语为“实验支持的 3′ end / 端点”；这并不表示每个位置均完成了独立的终止功能实验。预测和作者混合实验/预测结果不进入 `data/public/`。详见 [`证据分层与发布边界`](../../standards/证据分层与发布边界.md)。

## 可复现性材料

- 本来源原始测序与出版商工作簿不随 Git 复制；请通过上表的公共入口获取。
- 标准化输入/输出 SHA-256、行数和坐标检查结果写入本目录的 `manifest.json`。
- 详细过程、双染色体核查和许可边界见 [`processing_record.md`](processing_record.md)。
- JBrowse 资产进入 `BTED-v0.2.0-jbrowse-assets.tar.gz`，不直接提交 Git。
