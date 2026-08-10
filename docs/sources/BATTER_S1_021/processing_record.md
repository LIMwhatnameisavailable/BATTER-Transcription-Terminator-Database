# BATTER S1_021 Borreliella burgdorferi 3′RNA-seq 处理记录

## 结论

Supplementary Data 1 已导入。log sheet 有 1,333 条观察，transition/stationary sheet 有 944 条观察；两者共享 372 个 reference/position/strand 位点，合并后为 1,905 个唯一 3′ end sites。

本站同时发布：

- `unique_3prime_end_sites.tsv`：1,905 个物理端点，适合检索与 JBrowse；
- `published_3prime_end_observations.tsv`：2,277 条样本观察，保留条件特异 read count 和注释。

## 多 replicon 与坐标

作者 Supplementary Data 3 明确给出 replicon label 到 NCBI accession 的映射。GCF_000008685.2 包含染色体和21个质粒，共22个参考序列；端点实际覆盖其中20个，cp9 和 lp5 没有作者端点记录。全部参考仍保留在 JBrowse assembly 中。

作者坐标按 1-based 生物学位置保存，BED 使用 `[position-1, position)`。22条 FASTA header、GFF seqid 与端点范围均已自动核对。

## 证据边界与问题

- 条目称为 `3′RNA-seq end`，不把全部端点自动表述成 terminator；
- terminator score、Kinefold structure 和 A-tract 是附属预测/结构注释；
- 372 个共有端点中有14个的基因说明、classification 或结构注释在两个条件间不完全相同。两个条件的原值分别保留，并设置 `metadata_conflict_between_conditions`；
- 本来源 `Used for BATTER augmentation = FALSE`，但属于公开实验数据，故仍进入 BTED 独立目录。

输出目录：`data/bburgdorferi/processed/BATTER_S1_021/`。执行脚本：`import_bburgdorferi_3prime_ends.py`。
