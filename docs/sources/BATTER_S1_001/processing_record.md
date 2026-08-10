# BATTER S1 试点：*E. coli* MG1655 Rend-seq 3′ end 数据处理记录

## 1. 目的与范围

本记录跑通 BATTER 补充表 S1 的第一个数据源，从公共数据库的处理后 3′ end 信号开始，产出可用于 genome browser 的基因组、基因注释、信号轨道与候选 3′ end 位点表。

本轮产物是 **实验观察到的 3′ end 候选峰**，不是最终的 terminator 注释。任何 RIT/RDT 机制标签、BATTER 预测支持或“主要终止位点”判定，都必须作为后续独立注释层加入。

## 2. 数据源与固定身份

| 项目 | 内容 |
|---|---|
| BATTER S1 ID | `BATTER_S1_001` |
| 物种 | *Escherichia coli* str. K-12 substr. MG1655 |
| BATTER S1 参考组装 | `GCF_000005845.1` |
| 实验使用的核酸序列 accession | `NC_000913.2` |
| 论文 | Lalanne JB et al. *Cell* (2018), PMID: 29606352, DOI: [10.1016/j.cell.2018.03.007](https://doi.org/10.1016/j.cell.2018.03.007) |
| 方法 | Rend-seq（end-enriched RNA-seq） |
| GEO | [GSE95211](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE95211) |
| BioProject / SRA study | `PRJNA376419` / `SRP100536` |
| 本轮样本 | `GSM2500131` / `SRX2582347` |
| 条件 | WT；MOPS complete；37 C、180 rpm；至 OD590 = 0.3；25 s RNA fragmentation；pooled |

### 关键决定：使用 `NC_000913.2`

GEO 的样本元数据明确写明 reads 使用 Bowtie v1.0.1 比对至 `NC_000913.2`；原 WIG 中的染色体名为 `NC_000913_2`。因此本项目的试点主坐标体系固定为：

```text
biological / GFF coordinate: NC_000913.2, 1-based inclusive
browser BED / bedGraph:     NC_000913.2, 0-based half-open
```

不得直接改用 `NC_000913.3`。若未来必须整合到 `.3`，须做并记录 lift-over / 序列差异核查。

## 3. 输入与目录结构

```text
data/batter_ecoli_pilot/
├── raw/
│   ├── GSM2500131_3f_no_shadow.wig.gz
│   └── GSM2500131_3r_no_shadow.wig.gz
├── reference/
│   ├── NC_000913.2.fna
│   ├── NC_000913.2.gb
│   └── NC_000913.2.chrom.sizes
├── annotation/
│   └── NC_000913.2.genes.gff3
├── processed/
│   ├── experimental_3prime_signal.forward.bedGraph
│   ├── experimental_3prime_signal.reverse.bedGraph
│   ├── experimental_3prime_signal.forward.bw
│   ├── experimental_3prime_signal.reverse.bw
│   ├── experimental_3prime_candidates.forward.bed/.tsv
│   ├── experimental_3prime_candidates.reverse.bed/.tsv
│   └── processing_summary.json
└── logs/
    ├── raw_sha256.txt
    ├── derived_sha256.txt
    └── processing_summary.stdout.txt
```

两个原始 WIG 均选择 `no_shadow` 版本，避免保留作者定义的 peak shadow。`3f`、`3r` 分别作为正链、负链 RNA 的 3′ end 信号；请在未来引用原研究 methods 时再次核验其 strand 命名含义。

## 4. 已执行流程

### Step 1. 获取并核对样本元数据

下载 GEO SOFT 元数据并检查 `GSM2500131`：

```bash
curl -L -s 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE95nnn/GSE95211/soft/GSE95211_family.soft.gz' \
  -o /tmp/GSE95211_family.soft.gz
gzip -cd /tmp/GSE95211_family.soft.gz | sed -n '440,490p'
```

确认了培养条件、读段处理流程、`NC_000913.2` 组装、以及 3′ 端 WIG 文件的来源。

### Step 2. 下载处理后 3′ end 信号

优先使用 GEO 的 HTTPS 下载端点，而不是 FTP 静态链接：

```bash
curl -L -o data/batter_ecoli_pilot/raw/GSM2500131_3f_no_shadow.wig.gz \
  'https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSM2500131&format=file&file=GSM2500131_Escherichia_coli_WT_Rend_seq_MOPS_comp_25s_frag_pooled_3f_no_shadow.wig.gz'
curl -L -o data/batter_ecoli_pilot/raw/GSM2500131_3r_no_shadow.wig.gz \
  'https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSM2500131&format=file&file=GSM2500131_Escherichia_coli_WT_Rend_seq_MOPS_comp_25s_frag_pooled_3r_no_shadow.wig.gz'
shasum -a 256 data/batter_ecoli_pilot/raw/*.wig.gz > data/batter_ecoli_pilot/logs/raw_sha256.txt
```

WIG 文件是 `variableStep` 格式，示例为 `chrom=NC_000913_2`，随后每行依次为 1-based 位置和该位置的 reads 数。

### Step 3. 获取匹配的参考序列与基因注释

从 NCBI E-utilities 使用历史 accession 直接获取 FASTA 与完整 GenBank record：

```bash
curl -L -o data/batter_ecoli_pilot/reference/NC_000913.2.fna \
  'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=NC_000913.2&rettype=fasta&retmode=text'
curl -L -o data/batter_ecoli_pilot/reference/NC_000913.2.gb \
  'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=NC_000913.2&rettype=gbwithparts&retmode=text'
```

### Step 4. 生成轨道和候选峰

运行可审计脚本：

```bash
python3 process_ecoli_rendseq.py
```

脚本执行内容：

1. 把 WIG 的 contig 名 `NC_000913_2` 标准化为 `NC_000913.2`；
2. 将每个观测位置输出为一碱基 bedGraph interval：`[position-1, position)`；
3. 从 GenBank 的 `gene` feature 导出 4,497 个基因到 GFF3；
4. 以“read support ≥ 10 且在 ±5 nt 内为严格局部最大值”为**候选 end**规则；
5. 为每个候选点记录链、支持度、邻近同链基因、到该基因 3′ 端的距离与来源 accession；
6. 输出 BED（浏览器轨道）和 TSV（数据库主表的初始层）。

## 5. 结果与质控

| 项目 | 正链 | 负链 |
|---|---:|---:|
| 有信号的位置数 | 1,184,107 | 1,239,375 |
| 候选 3′ end 峰 | 25,872 | 30,004 |
| 最大 read support | 256,681 | 367,957 |
| 位于同链基因内部的候选峰 | 22,201 | 26,392 |
| 位于同链基因后 0–128 nt 的候选峰 | 2,174 | 2,235 |

已检查：

- 两条 BED 均按坐标升序排列；
- 所有 BED interval 均为一个碱基，且符合 0-based half-open 规则；
- 所有输出文件的 SHA-256 已写入 `logs/`；
- 基因组长度固定为 4,639,675 bp。

### Step 5. 生成 BigWig 并配置本地 JBrowse 2

使用 conda 环境 `Conda environment `batter-browser`` 中的 UCSC 工具，将排序后的 bedGraph 转为 BigWig；随后用 `bigWigInfo` 核对结果。两个 BigWig 分别覆盖 1,184,107（正链）和 1,239,375（负链）个基因组位置，与输入信号一致。

本地浏览器目录为 `browser/jbrowse2/`，组装固定为 `NC_000913.2`。当前仅发布五条**实验数据轨道**：基因注释、正/负链 3′ end 信号 BigWig、正/负链候选峰 BED。未加入 BATTER 预测轨道，避免将预测与实验观察混为同一证据层。

可本地启动并在浏览器打开：

```bash
python3 -m http.server 8000 --directory browser/jbrowse2
# 浏览器打开 http://localhost:8000
```

### 结果应如何解释

共得到 55,876 个“高信号局部峰”，绝不能直接称为 55,876 个 terminators。大量峰落在基因内部，可能来自 RNA 加工、降解、中间转录本或真实的内部终止。初步更适合作为候选主要 3′ end 的是同链基因下游 0–128 nt 的 4,409 个峰；这仍只是位置和信号筛选，尚未整合重复、操纵子、茎环、Rho 扰动或原文的终止验证。

### Step 6. 用原始论文 Supplementary Table S3 进行坐标验证

从 Lalanne et al. (2018) 的 `NIHMS964513-supplement-Table_S3.xlsx` 提取：

- `2_terminators_Ecol`：599 条高置信度、基于 Rend-seq 3′ 峰和序列特征筛选的 *E. coli* putative intrinsic terminator；
- `6_tuned_term_Ecol`：127 条具有 read-through 下游表达信息的记录；以“下游基因 mRNA 中 read-through 来源比例 >50%”作为透明的二次计算标准，得到 89 条满足该阈值的记录。

两张表均明确使用 `NC_000913.2`，因此无需 lift-over。用相同链方向匹配本试点的严格局部最大候选峰：599 条高置信度记录与 read-through 表合并后共 607 个坐标-链记录，其中 576 条精确命中、13 条在 5 nt 内命中、18 条在 5 nt 内无候选局部峰。后者不否定文献证据，可能受培养条件、测序深度、峰调用阈值或局部最大值规则影响。

输出：

```text
processed/literature_curated_terminator_records.ecoli.tsv
processed/literature_curated_terminator_records.ecoli.bed
processed/literature_validation_summary.json
```

这些记录的原文类别、序列、结构、U-tract、read-through 等字段被保留；资源中应表述为“文献整理的实验/序列支持内在终止子记录”，不能将其误写为我们本次重新实验验证的结果。

### 浏览器默认候选轨道的可读性筛选

原始局部峰规则产生正链 25,872、负链 30,004 个候选，适合保存和审计，但在浏览器小窗口中会过于密集。额外输出 `experimental_3prime_geneproximal_candidates.*`，仅保留同链基因下游 0–128 nt 的候选：正链 2,174、负链 2,235。该轨道用于浏览器默认展示，完整候选仍保留为独立轨道和 TSV。

这只是**基因组语境筛选**，不是新的 terminator 判定。它能减少与转录结束无关的内部峰干扰，但也会漏掉操纵子内部、非编码 RNA 或复杂基因边界附近的真实终止事件；因此文献支持轨道仍须独立保留。

为使人工质控可重复，已从精确命中的记录中按正/负链、read-through 高低和是否影响下游表达分层选择 10 个位点；核查步骤与双语说明见 `docs/Ecoli_Lalanne2018_10个终止位点人工核查教程.md`。

## 6. 遇到的问题与解决/待解决项

| 问题 | 原因或现象 | 处理 | 对标准流程的要求 |
|---|---|---|---|
| S1 assembly 与常用 E. coli 版本不一致 | S1 是 `GCF_000005845.1`，GEO 明确为 `NC_000913.2`，而较新资料常使用 `.3` | 固定本试点为 `.2` | 每个数据集必须以实验 metadata 的 assembly 为准；不可静默替换版本 |
| 旧 RefSeq assembly 的 FTP 目录没有 FASTA/GFF | `ASM584v1` 当前 FTP 目录仅返回 metadata | 从 E-utilities 用 `NC_000913.2` 获取 FASTA 和 GenBank | 保存实际使用的 sequence accession、下载 URL、日期与 checksum |
| 直接访问 `ftp.ncbi.nlm.nih.gov` 的 HTTPS SSL 失败 | 环境报 `SSL_ERROR_SYSCALL` | 改用 GEO 的 `geo/download` HTTPS 接口成功 | 下载脚本应保留备用 URL；记录访问失败而不是更换数据源不留痕迹 |
| 初始 UCSC BigWig 工具无法运行 | 下载的 x86_64 `wigToBigWig` 在 arm64 macOS 上缺少 `a local xz dynamic library` | 改用 conda 的原生 `ucsc-bedgraphtobigwig`，已成功输出并用 `bigWigInfo` 验证 | 标准流程优先使用可复现的 conda 环境；转换前先检查 chromosome sizes 与排序 |
| 单一样本没有生物学重复 | `GSM2500131` 为 pooled 样本 | 本轮仅标为 single-sample evidence | 资源数据库必须有 `replicate_support` 与 `evidence_level` 字段；本数据不可声称跨重复稳定 |
| 3′ end 峰不等于 terminator | 大量候选峰位于基因内部 | 输出名使用 `candidates`，未给 RIT/RDT 标签 | 机制与 terminator 状态必须单独注释，不能从峰信号直接推断 |
| JBrowse 提示 `Could not resolve identifiers` | 浏览器缓存了旧 `config.json`，而入口 URL 已引用新版轨道 ID | 在 `config=` URL 参数中加入资源配置版本；刷新后重新读取配置 | 每次变更 trackId 时同步更新门户配置版本，并用一键链接实测 |
| 候选峰轨道标签过密 | BED 第 4 列为完整 `end_id`，在小窗口中遮挡信号 | 保留含 ID 的主 BED/TSV；另生成第 4 列为 `.` 的 browser BED | 浏览器展示文件与数据库主表可以分离；保证浏览清晰但不丢失可追溯 ID |

## 7. 对资源标准化的可复制 SOP

对于 S1 的每个新数据源，按以下顺序执行：

1. **建立 source record**：论文、PMID/DOI、method、sample、公共 accession、许可证、下载日期。
2. **锁定原始坐标体系**：记录作者使用的 assembly/contig 名和 WIG/BED/GFF 坐标规则。
3. **下载两类输入**：优先作者处理后 end signal/peak；保留 raw FASTQ/SRA accession 供未来重分析。
4. **验证文件**：解压测试、记录 SHA-256、核对 contig 和基因组长度。
5. **转换为标准轨道**：FASTA、GFF3、signal（BigWig 优先；不可用时 bedGraph/WIG）、candidate end BED。
6. **生成主表初始字段**：`end_id, source_id, sample_id, assembly, chrom, coordinate, strand, read_support, assay, evidence_type`。
7. **基因组语境注释**：同链基因、到 CDS/gene 3′ 端距离、intragenic/intergenic、operon 信息（若有）。
8. **机制与预测注释**：结构、Rho 证据、BATTER-TPE/RUT 结果必须分轨、分字段记录。
9. **质量控制**：坐标排序、越界检查、抽查至少 10 个 locus、记录阈值和软件版本。
10. **发布前证据分级**：区分“实验 peak”“候选主要 end”“文献验证 terminator”“RIT/RDT-supported”“BATTER prediction”。

## 8. 下一轮工作

1. 整合原文 Supplementary Table S3 的 intrinsic terminators/read-through fraction，先核对坐标体系；
2. 以 Table S3 为金标准，匹配当前候选峰，产生“文献支持的实验 terminator”独立轨道和主表字段；
3. 从匹配成功的位点中选择 10 个，进行人工 browser 核查；
4. 将 0–128 nt 下游候选进一步与操纵子、茎环、Rho 机制证据整合，形成“主要 transcription end”层；
5. BATTER 预测可以在后续作为可开关的比较轨道，但不纳入本资源第一版的实验主数据。
