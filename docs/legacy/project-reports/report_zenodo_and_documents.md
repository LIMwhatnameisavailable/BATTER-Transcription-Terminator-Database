# Zenodo 仓库调查与 Table S1 文献数据获取信息报告

**论文**: Jin, Cui, Liu et al. "Conserved 3′ stem-loop structures enable comprehensive analysis of bacterial transcription termination in metagenomes." *Microbiome* (2026). DOI: 10.1186/s40168-026-02454-1

**审查日期**: 2026-07-28

---

## 第一章：Zenodo 仓库内容结构调查

### 1.1 仓库基本信息

Zenodo 仓库目前已发布 3 个版本，基本信息如下：

| 属性 | v2（论文正文引用版本） | v3（当前最新版本） |
|------|------------------------|-------------------|
| **URL** | https://zenodo.org/records/16761763 | https://zenodo.org/records/18863501 |
| **DOI** | 10.5281/zenodo.16761763 | 10.5281/zenodo.18863501 |
| **标题** | BATTER for bacterial transcription terminator analysis | 同上 |
| **作者** | Jin Yunfan | 同上 |
| **创建日期** | 2025-08-14 | 2026-03-04 |
| **许可证** | CC-BY-4.0 | 同上 |
| **资源类型** | Software | 同上 |
| **下载量** | 227次（截至查询时） | — |

### 1.2 v2 ↔ v3 版本对比

#### 文件 MD5 校验码对比

| 文件名 | v2 MD5 | v3 MD5 | 是否变化 |
|--------|--------|--------|----------|
| `BATTER-main.zip` | `62000bbad8b75a41738727e34c8d3b0c` | `055cf591754d825fb6ac40a4a84f4bbe` | **是**（代码已更新） |
| `combined-statistics.txt` | 未变 | 未变 | **否** |
| `terminators.flanked.fa.gz` | 未变 | 未变 | **否** |
| `TES.bed.gz` | 未变 | 未变 | **否** |
| `terminator-prediction-scripts-main.zip` | 未变 | 未变 | **否** |

#### 版本差异分析

- `BATTER-main.zip` 的 MD5 在 v2 和 v3 之间发生变化，说明 **代码在审稿期间被更新**（可能包含 bug 修复或功能改进）
- `combined-statistics.txt`、`terminators.flanked.fa.gz`、`TES.bed.gz` 三个核心数据文件的 MD5 **完全未变**，说明核心数据内容没有变化

#### 版本使用建议

- **获取代码**：建议使用 v3（最新版本，含可能的修复和改进）
- **获取数据文件**：使用 v2 或 v3 链接均可（内容相同）

### 1.3 文件详细清单（v2 版本）

| 文件名 | 大小 | 格式 | 用途简述 |
|--------|------|------|----------|
| `terminators.flanked.fa.gz` | 487 MB | Gzip压缩FASTA | 模型训练数据集（数据增强后的终止子实例序列） |
| `TES.bed.gz` | 1.19 GB | Gzip压缩BED | BATTER对42,905个GEMs细菌基因组的全基因组预测结果 |
| `combined-statistics.txt` | 10.6 MB | 制表符分隔文本 | 预测结果汇总统计 |
| `BATTER-main.zip` | 33.7 MB | ZIP压缩代码包 | BATTER工具源代码（v2版） |
| `terminator-prediction-scripts-main.zip` | 25.6 MB | ZIP压缩代码包 | 模型基准测试和数据分析辅助脚本 |

> **v1 概念版**（DOI: 10.5281/zenodo.16675149）与 v2 内容一致，仅文件大小略有差异。

### 1.4 文件内容分类

| 文件 | 所属类型 | 判断依据 |
|------|----------|----------|
| `terminators.flanked.fa.gz` | **(b) 训练数据** | 论文描述为"dataset for model training"，FASTA格式含序列和侧翼区，无真实物种坐标 |
| `TES.bed.gz` | **(c) 预测结果** | 论文描述为"BATTER's prediction across diverse bacterial lineages"，BED格式含坐标 |
| `combined-statistics.txt` | **(d) 统计汇总** | 论文描述为"relevant statistics of the prediction" |
| `BATTER-main.zip` | **(d) 代码** | BATTER工具源代码 |
| `terminator-prediction-scripts-main.zip` | **(d) 代码** | 辅助分析脚本 |

**关键结论**: Zenodo仓库中 **不包含** 类型(a)的数据（即Table S1所列13篇原始论文中提取/标准化的实验3'端终止子坐标数据）。它只包含：
- BATTER模型代码
- 增强后的训练数据（FASTA序列）
- 42,905个基因组的 **预测** 结果（BED坐标）
- 统计汇总

---

## 第二章：Table S1 原始文献数据获取信息

### 查询方法说明

本表数据来源于对每篇原始文献 PubMed 摘要页 Data Availability 声明的 **逐字人工核查**，并对所有登录号进行了交叉验证。部分文献的登录号在 PubMed 摘要页不直接显示，需进入 PMC 全文或期刊网页获取。以下为核查确认后的权威数据汇总。

### Table S1 文献数据获取信息汇总表

| PMID | 物种 | 期刊/年份 | 数据库登录号 | 数据类型 | 备注 |
|------|------|-----------|-------------|----------|------|
| **29606352** | *E. coli* MG1655, *B. subtilis* 168, *V. natriegens*, *C. vibrioides* NA1000（即 *C. crescentus*） | *Cell* 2018, Lalanne et al. | **GEO SuperSeries**: GSE95211（21个samples：18个Rend-seq + 3个ribosome profiling）<br>**GitHub**: https://github.com/jblalanne/Rend_seq_core_scripts<br>**Mendeley**: 10.17632/ncm3s3pk2t.1 | 原始测序reads + 核心分析脚本 + 补充验证数据 | GSE95211页面Organisms字段确认覆盖这4个物种，与Table S1完全吻合 |
| **30517198** | *S. pneumoniae* TIGR4 | *PLoS Pathog* 2018, Warrier et al. | **SRA**: SRP136114 | 原始测序reads（RNA-seq, term-seq, 5' end-seq） | 无更多细节 |
| **31555254** | *S. lividans* TK24 | *Front Microbiol* 2019, Lee et al. | **ENA**: PRJEB31507 | 原始测序reads（dRNA-seq, Term-seq, RNA-seq, Ribo-Seq） | 原文措辞"RNA-Seq, Term-Seq, RNA-Seq, and Ribo-Seq"存在重复笔误，推测第一个应为dRNA-seq |
| **31594819** | *P. aeruginosa* PAO1 | *mBio* 2019, Thomason et al. | **ENA**: PRJEB31965 | 原始测序reads（RNA-seq, term-seq） | 与文献#11（PMID 37402717）复用的数据一致 |
| **32694125** | *Z. mobilis* ZM4 | *mSystems* 2020, Vera et al. | **GEO**: GSE139939（RNA-seq/TSS-seq/term-seq/ribo-seq）<br>**PRIDE**: PXD016962（蛋白质组）<br>**GitHub**: https://github.com/jmvera255/Vera_2020_mSystems | 原始测序reads（多组学）+ 蛋白质组数据 + 分析代码 | ⚠️ **重要修正**：此前版本错误标注为PRJNA587699/SRP228586，已更正为GSE139939 |
| **33319794** | 7种 *Streptomyces*（详见下方分物种明细表） | *Sci Data* 2020, Lee et al. | 见下方"PMID 33319794 分物种登录号明细表"<br>**Figshare**: https://doi.org/10.6084/m9.figshare.13259393 | 原始测序reads（dRNA-seq, Term-seq, RNA-seq）+ 处理后的TSS/TTS坐标文件 | ⚠️ Figshare链接需下载后确认：该页面描述为"human readable CSV + machine readable JSON metadata"，可能只是期刊要求的标准化元数据摘要，不一定包含真实的TSS/TTS坐标数据 |
| **33947798** | *S. clavuligerus* | *mSystems* 2021, Hwang et al. | **GenBank基因组**: CP027858, CP027859<br>**GEO**: GSE128216（RNA-seq/dRNA-seq/ribo-seq）<br>**GEO**: GSE138325（term-seq） | 基因组序列 + 原始测序reads | ⚠️ **重要修正**：此前版本错误标注为SRP223981/PRJNA575515，已更正为GSE128216 + GSE138325 |
| **34054774** | *Synechocystis* sp. PCC 7338 | *Front Microbiol* 2021, Jeong et al. | **BioProject**: PRJNA629670 | 原始测序reads（genome-seq, RNA-seq, dRNA-seq, Term-seq） | 已确认无误 |
| **34874777** | *Synechocystis* sp. PCC 6803 | *mSystems* 2021, Cho et al. | **BioProject**: PRJNA666973 | 原始测序reads（RNA-seq, Ribo-seq, Term-seq） | 已确认无误 |
| **35491820** | *D. dadantii* 3937 | *mBio* 2022, Forquet et al. | **Genome**: NC_014500.1<br>**ArrayExpress**: E-MTAB-7650（RNA-seq）<br>**ArrayExpress**: E-MTAB-541（in vitro microarray）<br>**ArrayExpress**: E-MTAB-10482（Nanopore）<br>**ArrayExpress**: E-MTAB-9075（dRNA-seq）<br>**GEO**: GSE94713（in planta microarray） | 基因组参考序列 + 原始测序reads + 微阵列数据 | ⚠️ **重要修正**：此前版本遗漏了E-MTAB-541（in vitro microarray数据集），共5个数据集而非4个 |
| **37402717** | *B. burgdorferi* B31 | *Nat Commun* 2023, Petroni et al. | **GEO SuperSeries**: GSE222088（包含4个SubSeries）<br>  ├── GSE222084: bulk RNA-seq<br>  ├── **GSE222085**: BCM RNA-seq（对应Table S3的Rho抑制数据）<br>  ├── GSE222086: SPD RNA-seq<br>  └── **GSE222087**: 3'RNA-seq/Term-seq（对应Table S1的常规3'端数据）<br>**复用的外部数据**：*E. coli* PRJNA640168, *P. aeruginosa* ERR3258013-15（PRJEB31965）, *B. subtilis* ERS1048762/ERS1051962/ERS1051954/ERS1051963（PRJEB12568）<br>**Figshare原始图片**: 10.6084/m9.figshare.22569205 | 原始测序reads + 处理后轨道数据 | 请在引用时注意区分：Table S1应引用GSE222087，Table S3应引用GSE222085；处理后轨道数据存放于NICHD自建基因组浏览器（4个独立URL，见原文） |
| **37096044** | *M. tuberculosis* H37Rv | *iScience* 2023, D'Halluin et al. | **ArrayExpress**: E-MTAB-11753<br>**GitHub**: https://github.com/ppolg/Mtb_termseq | 原始测序reads（RNA-seq）+ 分析代码 | 已确认无误 |
| **38030608** | *E. coli* str. K-12 MG1655 | *Nat Commun* 2023, Bar et al. | **ArrayExpress**: E-MTAB-12429<br>**GitHub**: https://github.com/amirbarHUJI/TRS | 原始测序reads（RNAtag-seq, term-seq）+ 算法实现 | 论文提到"Supplementary Data 1"中列出了本研究复用的其他外部文献登录号清单，该补充材料文件体积较大，**本轮暂未核查，留待后续处理** |

### PMID 33319794 分物种登录号明细表

以下为 Lee et al. 2020 (*Sci Data*) 中7种 *Streptomyces* 物种的分物种登录号明细：

| 物种 | dRNA-seq | Term-seq | RNA-seq |
|------|----------|---------|---------|
| *S. avermitilis* | SRP158023 | 同dRNA-seq（SRP158023） | SRP158023 |
| *S. clavuligerus* | SRP188290 | **SRX6937123, SRX6937124**（独立登录号） | SRP188290 |
| *S. tsukubaensis* | SRP103795 | PRJEB36379（与 *S. venezuelae* 共用） | SRP103795 |
| *S. coelicolor* | 未单独说明 | 同 *S. griseus* 的 PRJEB40918 | SRP058830 |
| *S. griseus* | PRJEB40918 | 同 dRNA-seq（PRJEB40918） | 同 dRNA-seq（PRJEB40918） |
| *S. lividans* | PRJEB31507 | 同 dRNA-seq（PRJEB31507） | PRJEB31507 |
| *S. venezuelae* | PRJEB36379 | PRJEB36379 | PRJEB34219 |

### 数据获取模式统计

| 模式 | 涉及文献数 | 说明 |
|------|-----------|------|
| **GEO / GEO SuperSeries** | 5/13（38%） | PMID 29606352（GSE95211）, 32694125（GSE139939）, 33947798（GSE128216 + GSE138325）, 35491820（GSE94713）, 37402717（GSE222088） |
| **ENA（European Nucleotide Archive）** | 3/13（23%） | PMID 31555254（PRJEB31507）, 31594819（PRJEB31965）, 33319794（部分物种） |
| **ArrayExpress** | 3/13（23%） | PMID 35491820（E-MTAB-7650/541/10482/9075）, 37096044（E-MTAB-11753）, 38030608（E-MTAB-12429） |
| **NCBI SRA / BioProject** | 3/13（23%） | PMID 30517198（SRP136114）, 34054774（PRJNA629670）, 34874777（PRJNA666973） |
| **Figshare** | 2/13（15%） | PMID 33319794（13259393）, 37402717（22569205） |
| **PRIDE（蛋白质组）** | 1/13（8%） | PMID 32694125（PXD016962） |
| **GenBank（基因组）** | 1/13（8%） |PMID 33947798（CP027858/CP027859） |

### 数据处理流程建议

从原始文献到可用数据库的标准步骤：
1. **下载原始reads** → 通过上表中的GEO/SRA/ENA/ArrayExpress登录号获取FASTQ
2. **重新分析3'端** → 使用原文献或BATTER论文的pipeline处理reads，鉴定转录终点
3. **标准化格式** → 统一为BED/GFF格式的坐标文件，包含物种、染色体、位置、链、终止子类型等信息
4. **整理元数据** → 关联文献信息、实验条件、置信度等

---

## 最终结论

### 能否直接复用Zenodo数据作为数据库起点？

**直接复用的限制**：
- Zenodo中的 `TES.bed.gz` 是 **BATTER模型的预测结果**（类型c），**不是** 从Table S1文献中提取的实验验证数据（类型a）
- 对于构建"实验验证的细菌转录终止子数据库"，我们需要的核心数据是：
  - 从13篇文献中提取的 **实验支持的3'端坐标**（Term-seq/Rend-seq/dRNA-seq检测到的真实终止位点）
  - 这些数据不在Zenodo上，需要 **逐篇回到原始文献** 去下载原始测序reads并重新分析

**可以部分复用Zenodo数据的场景**：
- 如果目标是构建"BATTER预测的终止子数据库"（而非实验验证数据库），可以直接使用 `TES.bed.gz`
- `terminators.flanked.fa.gz` 中的增强训练数据可用于了解模型的训练数据分布
- `combined-statistics.txt` 中的统计信息可作为数据库的元数据参考

### 判断总结

> **不可直接复用Zenodo数据作为实验验证终止子数据库的起点。**
>
> 必须逐篇回到Table S1中的13篇原始文献，从上表所列的GEO/SRA/ENA/ArrayExpress登录号下载原始测序reads，然后通过标准化的3'端鉴定pipeline重新处理，才能获得可用的实验验证终止子坐标数据。Zenodo中的数据（尤其是`TES.bed.gz`）可作为下游比较和补充的参考，但不能替代从原始实验数据中提取的金标准终止子信息。

---

*报告完*