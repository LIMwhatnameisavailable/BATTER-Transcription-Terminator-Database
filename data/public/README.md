# data/public —— 可公开标准化数据

这里存放体积适合 Git 托管、可追溯到公开来源的 BTED 标准化小型数据。原始测序文件、出版商工作簿、参考 FASTA/GFF、BigWig 与完整 JBrowse 包不进入本目录；它们应通过原始公共数据库或后续有版本的外部发布物获取。

## 当前发布：v0.2.0（2026-08-10）

- 22 个 BATTER Table S1 来源均有来源 manifest 与人类可读处理记录；
- 21 个来源发布了标准化核心 TSV/BED，共 **28,399** 条记录；
- 17 个来源为作者发表的实验 3′ end 表；4 个 Lalanne 2018 来源为 `curated_record`；
- 17 个来源在许可允许时提供 `source_annotations.tsv`；4 个 Lalanne 来源的完整来源字段为 `external_link_only`；
- 21 个来源均有版本化 JBrowse 配置，大型资产通过 GitHub Release 提供；
- `BATTER_S1_002` 只发布审计说明，不发布端点表：其本地结果包含作者整合的多技术证据，尚未能按公开端点 schema 拆分；
- `BATTER_S1_020` 的作者混合证据表、`BATTER_S1_022` 的纯预测 RUT 表均只有 checksum 审计记录，未复制到本目录。

机器可读总清单见 [`v0.2.0/release_manifest.json`](v0.2.0/release_manifest.json)，22 来源发布判定见 [`../registry/batter_s1_publication_status.v0.2.0.tsv`](../registry/batter_s1_publication_status.v0.2.0.tsv)。每个来源位于 `v0.2.0/records/<source_id>/`。

## 进入本目录的条件

1. 来源、参考组装、contig、链方向与坐标规则已完成核查，并写入来源处理记录；
2. 内容属于 `observed_signal`、`called_endpoint`、`author_called_endpoint` 或 `curated_record`，且字段和用词符合其证据层；
3. 不含 `author_integrated_mixed_evidence` 或 `prediction_only`；
4. 标准 TSV 符合 24 列 schema；单碱基坐标满足 `BED start = position - 1`、`BED end = position`；
5. 每个已发布文件有 SHA-256，并能通过 `python3 scripts/validate_bted_v0_2.py`；
6. 单文件体积适合 Git 托管。大文件改用 Zenodo、Figshare 或版本化浏览器包，本目录只放指针与 checksum。

## 文件命名

- `records/<source_id>/endpoints.tsv`：作者发表或按公开规则调用的实验端点；
- `records/<source_id>/endpoints.bed`：对应实验端点的 BED6；
- `v0.2.0/records/<source_id>/source_annotations.tsv`：来源特异字段；
- `v0.2.0/records/<source_id>/fields.json`：字段清单与证据属性；
- `v0.2.0/release_manifest.json`：发布级计数、来源决策和文件 checksum；
- `../audit/excluded_assets/<source_id>/excluded_assets.json`：不进入公开端点层的本地资产的可复核摘要。
