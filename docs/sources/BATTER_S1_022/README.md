# BATTER_S1_022 — 来源处理记录

## 本仓库迁移状态

| 项目 | 值 |
|---|---|
| 发布判定 | `published_standardized` |
| 公开资产 | `data/public/v0.2.0/records/BATTER_S1_022/endpoints.tsv` |
| 记录数 | 2567 |
| 主要证据层 | `author_called_endpoint` |
| 版本 / 日期 | `v0.2.0` / 2026-08-10 |
| 参考组装 | `GCF_000195955.2` |
| 原始数据入口 | https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-11753 |
| 论文 | PMID [37096044](https://pubmed.ncbi.nlm.nih.gov/37096044/) · DOI [10.1016/j.isci.2023.106465](https://doi.org/10.1016/j.isci.2023.106465) |

## 范围与证据边界

Author-called Term-seq TTS. Prediction-support columns are retained only as author annotations; prediction-only RUT records are excluded.

BTED 的公开术语为“实验支持的 3′ end / 端点”；这并不表示每个位置均完成了独立的终止功能实验。预测和作者混合实验/预测结果不进入 `data/public/`。详见 [`证据分层与发布边界`](../../standards/证据分层与发布边界.md)。

## 可复现性材料

- 本来源原始测序与出版商工作簿不随 Git 复制；请通过上表的公共入口获取。
- 标准化输入/输出 SHA-256、行数和坐标检查结果写入本目录的 `manifest.json`。
- 详细坐标映射、预测层隔离和工程核查见 [`processing_record.md`](processing_record.md)。
- JBrowse 资产进入 `BTED-v0.2.0-jbrowse-assets.tar.gz`，不直接提交 Git。
