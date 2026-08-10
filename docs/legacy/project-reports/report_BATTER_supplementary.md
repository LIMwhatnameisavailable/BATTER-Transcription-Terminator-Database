# 补充材料审查报告

**论文**: Jin, Cui, Liu et al. "Conserved 3′ stem-loop structures enable comprehensive analysis of bacterial transcription termination in metagenomes." *Microbiome* (2026). DOI: 10.1186/s40168-026-02454-1

**审查日期**: 2026-07-28

---

## 第一部分：MOESM1_ESM.docx 解析

### 文件概况

该文件为论文的 **Supplementary Information (补充信息)**，包含：
- **Supplementary Text** (数据增强管道、BATTER-TPE 实现、BATTER-RUT 实现、性能评估、终止子茎环变异分析等方法的详细说明)
- **Figures S1–S13** (13张补充图)
- **Tables S1–S8** (8张补充表)
- **Dataset S1–S2** (两个补充数据集，以段落形式列举)
- **References** (参考文献列表)

---

### 补充图 (Figures S1–S13)

| 编号 | 标题 | 内容概要 |
|------|------|----------|
| **Figure S1** | — | A. TES（转录终点）与最近上游终止密码子之间的距离分布；B. BCM处理与对照样本的read coverage；C. *fabI*, *kdsB*, *serA* 下游保守茎环的多序列比对 |
| **Figure S2** | — | A. 数据增强管道的示意图；B. 实验支持的主要3'端数量统计；C. 数据增强后假定的茎环关联3'端数量 |
| **Figure S3** | — | A. RUT位点预测算法示意图；B. 保守3' YC二聚体（状态C）与其他非保守YC二聚体之间的可行状态转移；C. 基于YC二聚体间距的打分规则 |
| **Figure S4** | — | 在FPR=0.1/KB条件下，七种方法按主要RIT/RDT/未分类分组的Recall、Precision、F1分数 |
| **Figure S5** | — | 在FPR=0.1/KB条件下，七种方法对非主要RIT/RDT/未分类的Recall、Precision、F1分数 |
| **Figure S6** | — | 以CDS序列为背景，九种方法按主要RIT/RDT/未分类分组的Recall、Precision、F1 |
| **Figure S7** | — | 以rRNA（A）和tRNA（B）为背景，六种方法检测主要3'端的性能 |
| **Figure S8** | — | A. 四种物种中三种RUT位点预测方法在不同FPR阈值下的Recall；B. 四种物种中预测RUT位点近转录本3'端的metagene图 |
| **Figure S9** | — | A. 多种细菌物种中tail-to-tail基因对终止子预测性能比较；B. BATTER独有的两个TSS关联终止子实例 |
| **Figure S10** | — | A. RNA编码器示意图（BERT + triplet loss）；B. holdout RNA家族的t-SNE可视化；C. SAM核糖开关的t-SNE可视化 |
| **Figure S11** | — | A. U-tract中位长度与GC含量的关联；B. 茎长中位值与GC含量的关联；C. *Bartonella* 物种中Rho蛋白R87→Q替换；D. *Bartonella* Rho依赖性评分急降；E–F. Clostridia中RUT与CDS反义/正义链重叠比例 |
| **Figure S12** | — | 蓝细菌支系中保守的Rho样蛋白（注释为"DUF4912结构域蛋白"）的多序列比对 |
| **Figure S13** | — | A. BATTER-TPE训练集中Rfam调控前导区关联终止子与下游CDS起始密码子的距离分布；B. 4个AMR基因家族上游具有显著结构共变的非编码RNA的预测共有RNA二级结构 |

---

### 补充表 (Tables S1–S8)

#### Table S1 — Curated 3' ends mapping data (整理的3'端测序数据)

- **标题**: Curated 3' ends mapping data
- **列数**: 6列
- **行数**: 23行（含表头 + 22行数据）
- **列名**: `Published year | Species | Phylum | Reference genome | PMID | Used for data augmentation`

**内容概要**: 该表汇总了本文从已发表文献中收集的所有**转录组3'端测序数据**（主要来自Term-seq及其他3'端定位技术），共涵盖 **20个物种/菌株** 的22条记录，跨越 **5个门**（Proteobacteria、Firmicutes、Actinobacteria、Cyanobacteria、Spirochaetota）。其中 **19条记录** 被标记为"Used for data augmentation = TRUE"，用于模型训练的数据增强。

**涉及的物种（Species）列表**:
1. *Escherichia coli* str. K-12 substr. MG1655 (2条记录)
2. *Bacillus subtilis* subsp. *subtilis* str. 168
3. *Caulobacter vibrioides* NA1000
4. *Vibrio natriegens* NBRC 15636
5. *Streptococcus pneumoniae* TIGR4
6. *Streptomyces lividans* TK24
7. *Pseudomonas aeruginosa* PAO1
8. *Zymomonas mobilis* subsp. *mobilis* ZM4
9. *Streptomyces avermitilis* MA-4680
10. *Streptomyces griseus* subsp. *griseus* NBRC 13350
11. *Streptomyces coelicolor* A3(2)
12. *Streptomyces tsukubensis*
13. *Streptomyces clavuligerus*
14. *Streptomyces venezuelae*
15. *Synechocystis* sp. PCC 7338
16. *Synechocystis* sp. PCC 6803
17. *Dickeya dadantii* 3937
18. *Borreliella burgdorferi* B31 (未用于数据增强)
19. *Mycobacterium tuberculosis* H37Rv (未用于数据增强)

**涉及的原始文献（按PMID）**:

| PMID | 作者 | 年份 | 期刊 | 数据类型 |
|------|------|------|------|----------|
| 29606352 | Lalanne JB et al. | 2018 | *Cell* | **Term-seq**（多物种3'端定位，含 E. coli, B. subtilis, C. vibrioides, V. natriegens） |
| 30517198 | Warrier I et al. | 2018 | *PLoS Pathog* | **Term-seq**（*S. pneumoniae*） |
| 31555254 | Lee Y et al. | 2019 | *Front Microbiol* | **转录单位架构**（*S. lividans*） |
| 31594819 | Thomason MK et al. | 2019 | *mBio* | **3'端定位**（*P. aeruginosa*） |
| 32694125 | Vera JM et al. | 2020 | *mSystems* | **基因组尺度转录-翻译图谱**（*Z. mobilis*） |
| 33319794 | Lee Y et al. | 2020 | *Sci Data* | **5'和3'边界**（*Streptomyces* 6个物种） |
| 33947798 | Hwang S et al. | 2021 | *mSystems* | **转录终止/加工元件**（*S. clavuligerus*） |
| 34054774 | Jeong Y et al. | 2021 | *Front Microbiol* | **多组学分析**（*Synechocystis* PCC 7338） |
| 34874777 | Cho SH et al. | 2021 | *mSystems* | **3'端定位**（*Synechocystis* PCC 6803） |
| 35491820 | Forquet R et al. | 2022 | *mBio* | **转录组图谱**（*D. dadantii*） |
| 37402717 | Petroni E et al. | 2023 | *Nat Commun* | **RNA终止图谱**（*B. burgdorferi*，未用于增强） |
| 37096044 | D'Halluin A et al. | 2023 | *iScience* | **Rho与uORF介导的转录提前终止**（*M. tuberculosis*，未用于增强） |
| 38030608 | Bar A et al. | 2023 | *Nat Commun* | **TRS方法**（*E. coli*，未用于增强） |

**数据类型总结**: 绝大多数为 **Term-seq** 或类似的高通量3'端定位数据，部分为广义的转录组边界分析数据。

---

#### Table S2 — Considered species in meta-term-seq dataset (meta-term-seq数据集中考量的物种)

- **标题**: Considered species in meta-term-seq dataset
- **列数**: 7列
- **行数**: 29行（含表头 + 28个物种）
- **列名**: `Phylum | Class | Order | Family | Genus | Species | Reference genome used`
- **内容概要**: 列出从人类口腔宏基因组数据（meta-term-seq）中鉴定出的28个物种，涵盖 Firmicutes、Actinobacteria、Proteobacteria、Fusobacteria、Bacteroidota 等门，主要用于评估模型在未培养物种上的性能。

---

#### Table S3 — Curated RNA-seq data with Rho inhibition (Rho抑制处理RNA-seq数据)

- **标题**: Curated RNA-seq data with Rho inhibition
- **列数**: 7列
- **行数**: 5行（含表头 + 4条记录）
- **列名**: `Published year | Species | GC content | Phylum | Reference genome | Accession | PMID`
- **内容概要**: 收录了4个物种（*E. coli*, *B. burgdorferi*, *B. subtilis*, *M. tuberculosis*）在用Rho抑制处理（BCM处理）条件下的RNA-seq数据，用于验证Rho依赖性终止。

| PMID | 作者 | 年份 | 期刊 | 物种 |
|------|------|------|------|------|
| 23207917 | (未查) | 2012 | — | *E. coli* (GSE41939) |
| 37402717 | Petroni E et al. | 2023 | *Nat Commun* | *B. burgdorferi* (GSE222085) |
| 36735730 | (未查) | 2023 | — | *B. subtilis* (GSE195579) |
| 37096044 | D'Halluin A et al. | 2023 | *iScience* | *M. tuberculosis* (E-MTAB-11753) |

---

#### Table S4 — Recombinant plasmids constructed for RUT test with the fluorescence reporter assay (荧光报告实验构建的重组质粒)

- **列数**: 3列
- **行数**: 18行（含表头 + 17个质粒）
- **列名**: `Plasmids | Putative RUTs | Putative RUT sequences (5'→3')`
- **内容概要**: 列出用于RUT功能验证的17个重组质粒，包括来自 *Nostoc* sp. PCC 7120（固氮基因簇）和 *Chlorogloeopsis fritschii* PCC 6912（FaRLiP/LoLiP基因簇）的预测RUT序列。

---

#### Table S5 — Primers used in this study (本研究所用引物)

- **列数**: 2列
- **行数**: 33行（含表头 + 32条引物）
- **列名**: `Primer | Sequence (5'→3')`
- **内容概要**: 列出用于构建重组质粒的所有PCR引物序列。

---

#### Table S6 — dRNA-seq datasets curated in this study (整理的dRNA-seq数据集)

- **标题**: dRNA-seq datasets curated in this study
- **列数**: 5列
- **行数**: 15行（含表头 + 14条记录）
- **列名**: `Published year | Species | Phylum | Reference genome | PMID`
- **内容概要**: 收录了14个物种的dRNA-seq（差异RNA-seq）数据集，用于转录起始位点（TSS）鉴定。涵盖 *Xanthomonas campestris*、*Listeria monocytogenes*、*Salmonella* Typhimurium、*Corynebacterium glutamicum*、*Campylobacter jejuni*、*Caulobacter crescentus*、*Borrelia burgdorferi*、*Synechococcus elongatus*、*Bacteroides thetaiotaomicron*、*Enterococcus faecalis*、*Flavobacterium psychrophilum*、*Nostoc punctiforme*、*Clostridioides difficile*、*Fusobacterium nucleatum*。

---

#### Table S7 — Benchmark Time and Resources Usage (基准测试时间和资源消耗)

- **列数**: 4列
- **行数**: 6行（含表头 + 5种方法）
- **列名**: `Method | Time (min) | Memory usage (Gb) | Disk usage (Gb)`
- **内容概要**: 比较5种方法在 *E. coli* 基因组上的运行时间和资源消耗：BATTER-TPE仅需 ~3分钟，快于 BacTermFinder (~121分钟) 和 termNN (~120分钟)。

| 方法 | 时间 (min) | 内存 (Gb) | 磁盘 (Gb) |
|------|-----------|-----------|-----------|
| RNIE | 44.8 | 0.08 | 0.001 |
| BacTermFinder | 120.8 | 6.52 | 99.79 |
| termNN | 119.9 | 25.16 | 132.38 |
| **BATTER-TPE** | **3.03** | **3.28** | **0.003** |
| transterm | 0.54 | 0.03 | 0.006 |

---

#### Table S8 — Curated Cyanobacteria traits (整理的蓝细菌性状)

- **列数**: 8列
- **行数**: 69行（含表头 + 68个蓝细菌基因组）
- **列名**: `refseq id | species | unicellular | marine | nitrogen fixation | FaRLiP | LoLiP | RDT fraction`
- **内容概要**: 列出68个蓝细菌基因组的分类学信息和生物学性状（单细胞/多细胞、海洋/非海洋、固氮能力、FaRLiP/LoLiP基因簇存在与否），以及BATTER预测的RDT（Rho依赖性终止子）比例。

---

### 补充数据集 (Datasets)

- **Dataset S1**: 用于数据增强的蛋白质编码基因簇（115个）和Rfam家族列表 → 内容对应 **MOESM2_ESM.xlsx**
- **Dataset S2**: 跨细菌谱系的终止子茎环性质 → 内容对应 **MOESM3_ESM.xlsx**

---

## 第二部分：MOESM2_ESM.xlsx 解析

### 文件概况

- **工作表数量**: 2个
- **文件大小**: ~36 KB

### Sheet 1: `gene clusters for augmentation`

| 属性 | 内容 |
|------|------|
| **行数** | 116行（含表头 + 115个基因簇） |
| **列数** | 3列 |
| **列名** | `Cluster id | Gene name | Pfam id` |
| **数据类型** | 聚类编号（0000–0114）、基因名称、Pfam结构域ID列表 |

**内容概要**: 该表对应 **Dataset S1** 中"蛋白质编码基因簇"部分，列出115个用于数据增强的蛋白质编码基因簇。每个基因簇包含一个或多个Pfam结构域。这些基因簇来源于具有至少3个细菌门Term-seq支持的基因，经过序列聚类（40% identity）和Pfam注释后得到。

**示例数据**:
- 0000: DNA-directed RNA polymerase subunit beta' (含 PF00623, PF04983, PF04997 等7个Pfam域)
- 0001: DNA-directed RNA polymerase subunit beta (含 PF00562, PF04560 等6个Pfam域)
- 0002: pyruvate carboxylase (含 PF00289, PF02222 等8个Pfam域)

### Sheet 2: `Rfam families for augmentation`

| 属性 | 内容 |
|------|------|
| **行数** | 929行（含表头，实际非空数据121行，末尾有空行） |
| **列数** | 4列 |
| **列名** | `Rfam id | Name | Description | Category` |
| **数据类型** | Rfam家族ID、简称、描述、分类（sRNA/attenuator/riboswitch等） |

**内容概要**: 该表对应 **Dataset S1** 中"Rfam家族"部分，列出121个用于ncRNA终止子数据增强的细菌Rfam家族，主要包括sRNA（如6S RNA、CsrB、Spot 42、GcvB、MicF等）、attenuator和riboswitch。

**数据判断**: MOESM2_ESM.xlsx 是 **Dataset S1** 的电子表格版，内容为"数据增强所用的基因簇和Rfam家族列表"，属于**训练数据元信息**，而非训练数据本身或预测结果。

---

## 第三部分：MOESM3_ESM.xlsx 解析

### 文件概况

- **工作表数量**: 2个
- **文件大小**: ~1.6 MB

### Sheet 1: `stem loop properties`

| 属性 | 内容 |
|------|------|
| **行数** | 2049行（含表头 + 2048个OTU数据行） |
| **列数** | 14列 |
| **列名** | `OTU id | GC content | stem length | length of U-rich sequence | # of prediction / CDS | # of prediction / KB in IGR | gene length | loop length | gene number | genome size | igr length | # downstream | # threeprime | Taxonomy` |

**内容概要**: 该表对应 **Dataset S2**，包含BATTER-TPE在 **42,905个GEMs细菌基因组** 上预测的终止子茎环性质汇总（按OTU级别聚合）。每行代表一个OTU（物种级操作分类单元），记录了该物种中终止子的平均/中位茎长、环长、U-tract长度、GC含量、预测密度等统计信息，以及完整的GTDB分类学注释。

**代表性数据行**:
- `OTU-10019` | GC=55.7% | 茎长=11 | U-tract=4 | 预测数/CDS=0.113 | 预测数/KB(IGR)=1.509 | 基因数=2875 | 基因组大小=3.28Mb | 分类: Acidobacteriota→UBA890

### Sheet 2: `rho dependency`

| 属性 | 内容 |
|------|------|
| **行数** | 15749行（含表头 + 15,748个OTU） |
| **列数** | 13列（前8列有实际数据，后5列为空） |
| **列名（有效列）** | `OTU id | GC content | Rho scores | Rho homolog | length of U-rich sequence | Completeness | Contamination | Taxonomy` |

**内容概要**: 该表同样对应 **Dataset S2**，记录了BATTER-RUT预测的Rho依赖性评分。每个OTU的Rho依赖性评分是该物种所有主要3'端上游RUT位点评分的平均值。还包含Rho同源物存在与否（1/0）、基因组完整度、污染率等信息。

**代表性数据行**:
- `OTU-39820` | GC=58.8% | Rho评分=3.30 | 有Rho同源物=1 | U-tract=4 | 完整度=100% | 污染=0% | 分类: Acidobacteriota

**数据判断**: MOESM3_ESM.xlsx 是 **Dataset S2** 的电子表格版，内容为"BATTER对42,905个GEMs细菌基因组的全基因组预测结果汇总"，包括茎环性质统计和Rho依赖性评分。**它并非模型训练数据，而是大规模预测结果产出。**

---

## 第四部分：交叉核对（PDF正文 vs 数据文件）

### Code & Data Availability（来自PDF正文）

PDF正文第17页的 **Code availability** 部分明确指出：

> **Codes of BATTER** are available at https://github.com/xu-research-lab/BATTER
> 
> **Scripts for model benchmarking and data analysis** are available at https://github.com/uaauaguga/terminator-prediction-scripts
> 
> **Data for model training, and predicted transcript 3' ends in GEMs genomes** are available in Zenodo (https://zenodo.org/records/16761763)

### 对应关系核查

| 数据来源 | 内容 | 对应文件 |
|----------|------|----------|
| **GitHub (xu-research-lab/BATTER)** | BATTER工具代码 | 不在本目录中 |
| **GitHub (uaauaguga/terminator-prediction-scripts)** | 模型基准测试和数据分析脚本 | 不在本目录中 |
| **Zenodo (16761763)** | 模型训练数据 + 42,905个GEMs基因组的预测转录3'端 | 不在本目录中 |
| **MOESM1_ESM.docx** | 补充信息（Figures S1–S13, Tables S1–S8, Dataset S1–S2文本） | 本目录 |
| **MOESM2_ESM.xlsx** | **Dataset S1** — 数据增强用基因簇（115个）和Rfam家族（121个） | 本目录 |
| **MOESM3_ESM.xlsx** | **Dataset S2** — 终止子茎环性质和Rho依赖性评分（跨42,905基因组） | 本目录 |

### 补充说明

1. **MOESM2_ESM.xlsx** 对应的是 **Dataset S1**（数据增强的"种子"信息），**不是**原始的模型训练数据（训练数据本身在Zenodo上）。
2. **MOESM3_ESM.xlsx** 对应的是 **Dataset S2**（预测结果汇总统计），**不是**42,905个基因组的原始预测结果（原始预测结果在Zenodo上）。
3. 真正的 **模型训练数据**（~250万个增强的终止子实例）和 **42,905个基因组的全基因组预测结果**（每个基因组的详细终止子位置）均存放于 **Zenodo (https://zenodo.org/records/16761763)**，因文件过大未包含在补充材料中。

---

## 第五部分：关键结论

### 哪个表格/文件是"可以作为后续数据库建设起点的原始研究列表"？

**→ Table S1（在 MOESM1_ESM.docx 中）** 是您所说的"**S1表**"。

**Table S1 — "Curated 3' ends mapping data"** 汇总了所有从已发表文献中收集的转录组3'端测序数据，包含：
- **20个物种/菌株** 的22条数据记录
- **13篇原始文献**（2018–2023年）
- 详细标注了 **PMID、物种、门类、参考基因组、是否用于数据增强**
- 数据来源包括 **Term-seq、dRNA-seq、转录组边界分析** 等多种实验技术

这个表是全文所有分析的基础起点：BATTER模型从这些实验数据中提取3'端关联的茎环结构，通过数据增强管道扩展到~250万个实例，最终完成对42,905个细菌基因组的全面预测。

**如果要构建一个"细菌转录终止子数据库"，Table S1 中的原始文献列表是必须收录的核心数据来源**，同时可以补充：
- Table S6（dRNA-seq数据集，用于TSS鉴定）
- MOESM2（Dataset S1：增强用的基因簇和Rfam家族）
- MOESM3（Dataset S2：42,905基因组的预测结果汇总，可作为数据库内容的直接参考）

---

*报告完*