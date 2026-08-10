# BATTER_S1_002 | E. coli TRS 3′ termini 标准化处理记录

## 来源

- 论文：Bar et al. 2023, TRS: a method for determining transcript termini from RNAtag-seq sequencing data
- PMID / DOI：38030608 / 10.1038/s41467-023-43534-2
- 物种：Escherichia coli str. K-12 substr. MG1655
- 参考：GCF_000005845.2 / NC_000913.3
- 原始数据 accession：E-MTAB-12429
- 主输入：Supplementary Data 3 (`41467_2023_43534_MOESM6_ESM_Supplementary_Data_3.xlsx`)
- 元数据输入：Supplementary Data 1 (`41467_2023_43534_MOESM4_ESM_Supplementary_Data_1.xlsx`)

## 处理决定

- 该来源为作者发表端点表型数据，本轮不重新从 raw reads 调用峰。
- 主表使用 Supplementary Data 3 的 `Summary` sheet。
- `Dominant` 解释为作者定义的代表性 3′ terminus 1-based 坐标。
- 四个实验 sheet（LB/EG RNAtag-seq 与 LB/EG Term-seq）保留为数据集级 observation 表。
- BATTER 预测不纳入该实验数据层。

## 输出

- 标准主表：`data/trs_ecoli_2023/processed/BATTER_S1_002/author_integrated_trs_3prime_termini.tsv`
- 数据集级观察：`data/trs_ecoli_2023/processed/BATTER_S1_002/dataset_level_trs_3prime_observations.tsv`
- BED：`data/trs_ecoli_2023/processed/BATTER_S1_002/author_integrated_trs_3prime_termini.bed`
- JBrowse 配置：`browser/jbrowse2/viewer/bar2023_ecoli_trs.config.json`
- 网站资源片段：`data/web_resources/BATTER_S1_002.json`

## 统计

- 非冗余端点数：3,125
- 数据集级观察数：7,493
- 参考序列：NC_000913.3（4,641,652 bp）
- 链分布：+ 1,518；− 1,607
- 支持数据集数量分布：{"1": 1024, "2": 776, "3": 395, "4": 930}
- 基因注释数：4,506

## 遇到的问题与解决

- 早先下载的 EuropePMC supplementary archive 不完整，未作为正式输入。
- Nature 附件说明 PDF 不是数据本体；根据说明选择 Supplementary Data 3 作为主数据。
- 既有 E. coli pilot 使用 NC_000913.2；本来源使用 NC_000913.3，因此单独下载 GCF_000005845.2 / ASM584v2 参考，不复用旧参考。

## 校验

- `chromosome + strand + Dominant` 唯一性通过。
- Dominant 坐标范围检查通过。
- `Number of datasets` 与四个 `Identified in ...` 字段一致。
- TSV、BED、FASTA、GFF、JBrowse asset 均已生成 SHA-256。
