# 文献10 — PMID 35491820

**Mapping the Complex Transcriptional Landscape of the Phytopathogenic Bacterium Dickeya dadantii**  
Forquet et al. (2022), *mBio*, 13(3):e0052422. DOI: 10.1128/mbio.00524-22  
5个数据集：RNA-seq E-MTAB-7650、microarray E-MTAB-541、Nanopore E-MTAB-10482、dRNA-seq E-MTAB-9075、in planta microarray GSE94713。

文献核查报告
物种: Dickeya dadantii（植物病原细菌）
期刊/年份: mBio, 2022 (Vol. 13, No. 3)

分类结论: A类

分类依据: 文中明确说明终止子（TTS）的基因组坐标已整理进可下载的Supplementary Table S2（XLSX文件），并在正文多处直接引用"provided in Table S2B and S2C"、"Table S2D"等措辞，字段包含"Genomic position"及"secondary structure"，可直接用于构建终止子数据库，无需重新下载FASTQ跑pipeline。

已确认的登录号清单:
- ArrayExpress: E-MTAB-7650 - RNA-seq原始数据（data set 1，用于TU/TSS/TTS初步定量信号）- 原始reads，非坐标表
- ArrayExpress: E-MTAB-541 - DNA microarray原始数据（data set 2，用于共表达验证）- 原始信号数据，非终止子坐标
- ArrayExpress: E-MTAB-10482 - Nanopore native RNA-seq原始数据（data set 3，用于TTS验证）- 原始reads，非坐标表
- ArrayExpress: E-MTAB-9075 - dRNA-seq (TEX处理)原始数据（data set 4，用于TSS鉴定）- 原始reads，非坐标表
- GEO: GSE94713 - in planta DNA microarray原始数据（data set 5，用于验证）- 原始信号数据，非坐标表
- NCBI: NC_014500.1 - D. dadantii 3937基因组序列与注释文件（参考基因组，非终止子数据本身）

现成坐标数据线索（A类核心证据）:
- 数据位置: Supplementary Table S2（XLSX文件，约0.6MB），子表B/C/D
- 数据字段（正文明确提及）:
  - Table S2B: "Genomic position and secondary structure of putative TTSs: intrinsic terminators predicted by ARNold"（3,564个rho-independent终止子坐标+结构）
  - Table S2C: "Genomic position of putative TTSs: rho-dependent terminators predicted by RhoTermPredict"（5,851个rho-dependent终止子坐标）
  - Table S2D: "Putative TTSs identified by Nanopore native RNA-seq"（1,165个实验验证TTS坐标）
  - Table S2A（作为对照）: dRNA-seq识别的9,288个TSS坐标
- 另有Table S1（A-D）：包含2,028个TU的坐标、TSS/TTS在TU中的分布、未注释基因坐标等，同样是处理好的坐标表
- 覆盖范围: 全基因组尺度，D. dadantii strain 3937，整合了intrinsic + rho-dependent预测终止子及Nanopore实验验证终止子三套坐标体系

第三方平台内容判断:
- 平台: 无涉及Figshare/Zenodo/GitHub，补充材料直接以ASM期刊官方Supplemental Material形式提供（PDF图+XLSX表格），非第三方托管

待人工确认事项:
- 需下载正文提供的实际XLSX文件（mbio.00524-22-st002.xlsx，对应Table S2）核实具体列名（如是否为Chromosome/Strand/Start/End或类似坐标字段格式），确认字段是否可直接映射到目标数据库schema
- 需确认PMID（正文未直接给出，建议通过DOI https://doi.org/10.1128/mbio.00524-22 反查）
- 注意该文提供了三套不同来源终止子坐标（ARNold预测、RhoTermPredict预测、Nanopore实验验证），使用时需明确标注数据来源/置信度层级，避免混淆预测与实验数据

建议后续动作:
- 可直接下载Supplementary Table S2（st002.xlsx）中B/C/D三个子表，提取终止子基因组坐标用于数据库构建；建议同时下载Table S1（st001.xlsx）获取TU坐标及TSS/TTS在TU中的上下文信息，便于后续注释与筛选（如区分internal vs. primary TTS、并保留置信度/support evidence字段）
