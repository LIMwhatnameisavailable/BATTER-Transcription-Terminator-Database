# BATTER_S1_002 — 来源处理记录

## 本仓库迁移状态

| 项目 | 值 |
|---|---|
| 发布判定 | `audit_only` |
| 公开资产 | `无（仅审计）` |
| 记录数 | 0 |
| 主要证据层 | `NA` |
| 迁移日期 | 2026-08-10 |
| 参考组装 | `GCF_000005845.2` |
| 原始数据入口 | https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-12429 |
| 论文 | PMID [38030608](https://pubmed.ncbi.nlm.nih.gov/38030608/) · DOI [10.1038/s41467-023-43534-2](https://doi.org/10.1038/s41467-023-43534-2) |

## 范围与证据边界

No public endpoint table is emitted in this release. The local derived assets are described in an exclusion manifest until their evidence/provenance can be reconciled to the public schema.

BTED 的公开术语为“实验支持的 3′ end / 端点”；这并不表示每个位置均完成了独立的终止功能实验。预测和作者混合实验/预测结果不进入 `data/public/`。详见 [`证据分层与发布边界`](../../standards/证据分层与发布边界.md)。

## 可复现性材料

- 本来源原始测序与出版商工作簿不随 Git 复制；请通过上表的公共入口获取。
- 标准化输入/输出 SHA-256、行数和坐标检查结果写入本目录的 `manifest.json`。
- 完整本地处理记录已作为 `processing_record.md` 随迁移保留。
- 本次不发布 BigWig、FASTA/GFF 或 JBrowse 资产；它们属于大型衍生文件，后续应以有版本的外部发布物/浏览器包提供。
