# BATTER_S1_005 标准化处理记录

## 入库结论

本来源以 `GCF_001456255.1` 的两条染色体为一个 assembly 接入。v0.2.0
发布 1,154 条文献整理记录，并提供可切换 `CP009977.1` 与
`CP009978.1` 的 JBrowse 配置。这里的记录类型是 `curated_record`，不改写为
本站重新调用的端点。

| 项目 | 值 |
|---|---|
| 来源 | Lalanne et al. 2018，PMID 29606352 |
| 原始数据 | GEO GSE95211；样本 GSM2971249 |
| 实验方法 | Rend-seq |
| 参考组装 | GCF_001456255.1 |
| contig | CP009977.1（3,248,023 bp）；CP009978.1（1,927,130 bp） |
| 文献表 | Supplementary Table S3，`3_terminators_Vnat` |
| v0.2.0 状态 | `published_standardized`；`external_link_only` 来源特异字段 |

## 原问题及处理

旧处理器假设一个来源只有一个 contig，可能丢失第二条染色体，或把不同 contig
上的同值坐标错误合并。多 contig 处理现按 contig 独立读取正负链信号和参考注释；
稳定 ID 同时保留 source、sample、contig、strand、coordinate 和序号，匹配不得跨
contig。

## v0.2.0 工程核查

- 核心表共 1,154 行：CP009977.1 为 898 行，CP009978.1 为 256 行；
- 正链 576 行，负链 578 行；
- `(contig, coordinate, strand)` 无重复；
- 每行均满足 `bed_start = coordinate - 1`、`bed_end = coordinate`；
- 每个 `end_id` 均包含对应 contig 标识；
- 两个 contig 均存在于 JBrowse assembly 的 FAI；
- 针对每个 contig 和 strand 固定抽取首位、中位、末位记录，核查结果保存在
  `data/audit/v0.2.0/priority_source_audit.json`。

这些检查只确认数据表、坐标和浏览器资源的一致性，不构成新的生物学判定。

## v0.2.0 输出

目录：`data/public/v0.2.0/records/BATTER_S1_005/`

- `endpoints.tsv`：24 列统一核心表；
- `endpoints.bed`：BED6 单碱基坐标；
- `fields.json`：原始字段清单及未复制原因；
- `manifest.json`：来源、参考、证据和发布状态；
- `SHA256SUMS.txt`：目录内发布文件校验和。

Lalanne 文章在许可登记中为 `external_link_only`。因此 v0.2.0 不重复发布完整的
来源特异补充字段，`fields.json` 逐列登记被保留在外部来源的字段；JBrowse 中保留
公开实验信号和本站候选层，但不复制受限制的文献整理 overlay。

## 可复现命令

```bash
python3 scripts/build_v0_2_release.py --input-root /path/to/BGIRNA
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_bted_v0_2.py
python3 scripts/build_jbrowse_release.py --input-root /path/to/BGIRNA
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
```

## 已知限制

- 原始 WIG、出版商工作簿和参考基因组不进入 Git；应从 GEO/论文和 NCBI 获取；
- v0.2.0 的抽查是确定性的数据库工程核查，不替代人工逐位点解释；
- 来源特异字段若未来确认可再发布，应在新的版本中恢复，不能覆盖当前许可记录。
