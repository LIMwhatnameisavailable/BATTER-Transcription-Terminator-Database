# BATTER_S1_004 | Caulobacter vibrioides Rend-seq 标准化处理记录

**状态：已标准化并接入本地 JBrowse；人工核查待完成。**
**最后更新：2026-07-29**

## 1. 来源记录

| 项目 | 内容 |
|---|---|
| 内部来源编号 | `BATTER_S1_004` |
| 物种 | *Caulobacter vibrioides* NA1000（文献旧称 *C. crescentus*） |
| BATTER S1 参考组装 | `GCF_000022005.1` |
| 实验坐标参考序列 | `CP001340.1` |
| 原始研究 | Lalanne JB et al., *Cell* (2018), PMID `29606352`, DOI `10.1016/j.cell.2018.03.007` |
| GEO series | `GSE95211` |
| 选用样本 | `GSM2971251` / `SRX3630288` |
| 方法 | Rend-seq；PYE；30 C；200 rpm；OD590 0.3；25 s fragmentation；pooled |
| 原始文件 | 3′ forward 和 3′ reverse 的 `*_no_shadow.wig.gz` |
| 文献注释 | Supplementary Table S3, `4_terminators_Ccre` |

## 2. 入库决策与坐标依据

选择该来源作为第三个试点，原因是它与前两个 Lalanne 2018 试点具有相同的测序与补充表框架，但物种、基因注释和参考序列不同，适合检验流程是否可迁移。

坐标权威为 `CP001340.1`，依据如下：

1. GEO 样本记录的处理信息明确列出 `CP001340.1`；
2. WIG 文件 `variableStep` 的 chromosome 是 `CP001340.1`；
3. Supplementary Table S3 的说明明确写明 position 基于 `CP001340.1`。

**已发现并保留的问题：** GEO 同一条记录中另有一行写着 `NC_000913.2`，这是 *E. coli* 的参考序列，与样本物种、WIG 和补充表均矛盾，判断为元数据复制遗留。该行未用于分析；这一判断不能删除原始记录，已在 `literature_validation_summary.json` 的 `metadata_conflict` 字段中保存。

## 3. 原始数据与可重复下载

| 数据 | URL |
|---|---|
| GEO 样本页 | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM2971251 |
| GEO series | https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE95211 |
| 3′ forward WIG | https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSM2971251&format=file&file=GSM2971251_Caulobacter_crescentus_Rend_seq_PYE_25s_frag_pooled_3f_no_shadow.wig.gz |
| 3′ reverse WIG | https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSM2971251&format=file&file=GSM2971251_Caulobacter_crescentus_Rend_seq_PYE_25s_frag_pooled_3r_no_shadow.wig.gz |
| 原始论文 | https://doi.org/10.1016/j.cell.2018.03.007 |

原始文件 SHA-256 见 `data/batter_ccre_pilot/logs/raw_sha256.txt`。

## 4. 标准化处理

1. 下载 WIG、FASTA 与 GenBank；以 WIG header、Table S3 和 GEO 的 `CP001340.1` 为一致性检查。
2. 由于环境中无 `samtools`，使用 `make_fasta_index.py` 为未修改的 FASTA 创建标准五列 `.fai` 索引；该替代已记录，不改变序列或坐标。
3. 使用 `process_ecoli_rendseq.py` 的参数化接口：信号支持度 >=10，且在 ±5 nt 内严格局部最大，得到**候选实验 3′ end**。该步骤不把候选峰称为 terminator。
4. 从 GenBank 导出 gene GFF3；为候选峰增加同链上游基因和距离注释。
5. 使用 `validate_ccre_lalanne_s3.py` 读取 S3，按同链最近候选峰比较文献位点；精确、±5 nt、未匹配分别保留。

## 5. 当前结果

| 指标 | forward | reverse |
|---|---:|---:|
| 信号位置数 | 1,357,841 | 1,418,541 |
| 严格局部峰候选数 | 45,689 | 49,602 |
| 最大支持度 | 84,496 | 70,117 |
| 基因注释数 | 4,097 | 4,097 |

文献整理的高置信度内在终止记录共 **337** 条：

| 匹配状态 | 条目数 |
|---|---:|
| 与同链候选峰精确重合 | 306 |
| 最近同链候选峰在 ±5 nt 内 | 28 |
| ±5 nt 内未匹配 | 3 |

## 6. 产物与状态

已完成：

- `processed/experimental_3prime_candidates.*.tsv/.bed`
- `processed/experimental_3prime_geneproximal_candidates.*.bed`
- `processed/literature_curated_terminator_records.ccre.tsv/.bed`
- `processed/literature_validation_summary.json`
- `annotation/CP001340.1.genes.gff3`
- 原始与处理日志、校验和（BigWig 以外）。

浏览器发布修复记录：

- 原有 `wigToBigWig` 二进制因缺少 `a local xz dynamic library` 无法启动；该失败保留在终端日志中。
- 改用现有 `batter-browser` 环境中可用的 `bedGraphToBigWig` 重新生成两条 BigWig，并用 `bigWigInfo` 验证。forward 覆盖 1,357,841 个位置、最大值 84,496；reverse 覆盖 1,418,541 个位置、最大值 70,117。
- 使用同一环境的 `bgzip` 与 `tabix` 创建可索引 GFF3；已接入 `browser/jbrowse2/viewer/ccre.config.json`。

待完成：从精确、邻近、未匹配三类中分层选择 10–20 个位点做人工核查。

## 7. 下一次恢复时的检查顺序

1. 检查坐标 `CP001340.1:5219..5419` 的浏览器轨道；
2. 完成人工核查并将状态改为 `curated`；
3. 继续核查 BATTER S1 的下一个来源。

## 2026-08-14 浏览器展示更新

本次仅更新 JBrowse display layer：正负链 signed-log 信号合并显示，默认区域确定性包含两种 strand，候选以富属性 GFF3 展示并可点击追溯稳定 ID、1-based 坐标、raw support 与 `called_endpoint` 警告。标准 BED、原始 BigWig、参考 `CP001340.1` 和既有 metadata conflict 记录均未改变。显示 BigWig 使用非压缩 v4 格式解决浏览器 range 索引兼容问题。
