# data/public —— 可公开标准化数据

这里存放体积适合 Git 托管、可追溯到公开来源的 BTED 标准化小型数据。原始测序文件、出版商工作簿、参考 FASTA/GFF、BigWig 与完整 JBrowse 包不进入本目录；它们应通过原始公共数据库或后续有版本的外部发布物获取。

## 当前发布：v0.1 local snapshot（2026-08-10）

- 22 个 BATTER Table S1 来源均有来源 manifest 与人类可读处理记录；
- 21 个来源发布了标准化 TSV，共 **28,399** 条记录；
- 其中 17 个来源为作者发表的实验 3′ end 表，并提供规范 BED；4 个 Lalanne 2018 来源为 `curated_record`，仅发布带坐标的文献整理 TSV，不发布 BED/JBrowse；
- `BATTER_S1_002` 只发布审计说明，不发布端点表：其本地结果包含作者整合的多技术证据，尚未能按公开端点 schema 拆分；
- `BATTER_S1_020` 的作者混合证据表、`BATTER_S1_022` 的纯预测 RUT 表均只有 checksum 审计记录，未复制到本目录。

机器可读总清单见 [`release_manifest.v0.1-local-snapshot.json`](release_manifest.v0.1-local-snapshot.json)，22 来源发布判定见 [`../registry/batter_s1_publication_status.tsv`](../registry/batter_s1_publication_status.tsv)。每个来源位于 `records/<source_id>/`。

## 进入本目录的条件

1. 来源、参考组装、contig、链方向与坐标规则已完成核查，并写入来源处理记录；
2. 内容属于 `observed_signal`、`called_endpoint`、`author_called_endpoint` 或 `curated_record`，且字段和用词符合其证据层；
3. 不含 `author_integrated_mixed_evidence` 或 `prediction_only`；
4. 标准 TSV 符合 24 列 schema；单碱基坐标满足 `BED start = position - 1`、`BED end = position`；
5. 每个已发布文件有 SHA-256，并能通过 `python3 scripts/validate_bted_release.py`；
6. 单文件体积适合 Git 托管。大文件改用 Zenodo、Figshare 或版本化浏览器包，本目录只放指针与 checksum。

## 文件命名

- `records/<source_id>/endpoints.tsv`：作者发表或按公开规则调用的实验端点；
- `records/<source_id>/endpoints.bed`：对应实验端点的 BED6；
- `records/<source_id>/curated_records.tsv`：文献整理记录，不等同于本库从信号重新调用的端点，故不提供 BED；
- `release_manifest...json`：发布级计数、来源决策、输入/输出 checksum；
- `../audit/excluded_assets/<source_id>/excluded_assets.json`：不进入公开端点层的本地资产的可复核摘要。
