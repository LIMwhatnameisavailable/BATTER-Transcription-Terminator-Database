# BATTER_S1_014 — 来源处理记录

## 本仓库迁移状态

| 项目 | 值 |
|---|---|
| 发布判定 | `published_standardized` |
| 公开资产 | `data/public/records/BATTER_S1_014/endpoints.tsv` |
| 记录数 | 1283 |
| 主要证据层 | `author_called_endpoint` |
| 迁移日期 | 2026-08-10 |
| 参考组装 | `GCF_003932715.1` |
| 原始数据入口 | https://www.ebi.ac.uk/ena/browser/view/PRJEB36379 |
| 论文 | PMID [33319794](https://pubmed.ncbi.nlm.nih.gov/33319794/) · DOI [10.1038/s41597-020-00775-w](https://doi.org/10.1038/s41597-020-00775-w) |

## 范围与证据边界

Author-published Term-seq endpoint.

BTED 的公开术语为“实验支持的 3′ end / 端点”；这并不表示每个位置均完成了独立的终止功能实验。预测和作者混合实验/预测结果不进入 `data/public/`。详见 [`证据分层与发布边界`](../../standards/证据分层与发布边界.md)。

## 可复现性材料

- 本来源原始测序与出版商工作簿不随 Git 复制；请通过上表的公共入口获取。
- 标准化输入/输出 SHA-256、行数和坐标检查结果写入本目录的 `manifest.json`。
- 完整本地处理记录已作为 `processing_record.md` 随迁移保留。
- 本次不发布 BigWig、FASTA/GFF 或 JBrowse 资产；它们属于大型衍生文件，后续应以有版本的外部发布物/浏览器包提供。
