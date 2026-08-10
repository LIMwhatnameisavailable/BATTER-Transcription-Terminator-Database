# 文献11 — PMID 37402717

**Extensive diversity in RNA termination and regulation revealed by transcriptome mapping for the Lyme pathogen Borrelia burgdorferi**  
Petroni et al. (2023), *Nat Commun*, 14(1):3931. DOI: 10.1038/s41467-023-39576-1  
GEO SuperSeries GSE222088（含GSE222084-87四个SubSeries）；复用外部数据：E. coli/P. aeruginosa/B. subtilis。

文献核查报告
物种: Borrelia burgdorferi（莱姆病螺旋体）
期刊/年份: Nature Communications, 2023

分类结论: A类

分类依据: 正文明确说明已将统计学显著的RNA 3'末端（含终止子评分）整理成表格并作为Supplementary Data 1提供，同时Rho依赖性终止区域整理在Supplementary Data 4中；这些文件包含可直接使用的基因组坐标及配套的终止子强度评分，无需重新下载FASTQ、重新跑分析流程即可用于构建终止子数据库。

已确认的登录号清单:
- GEO: GSE222088（SuperSeries，总入口） - 原始测序数据 - 包含4个SubSeries
- GEO: GSE222084 - 原始测序数据（bulk RNA-seq） - 用于总RNA-seq分析
- GEO: GSE222085 - 原始测序数据（BCM RNA-seq） - 用于Rho终止分析（±BCM处理）
- GEO: GSE222086 - 原始测序数据（SPD RNA-seq） - 用于精胺处理差异表达分析
- GEO: GSE222087 - 原始测序数据（3'RNA-seq/Term-seq） - 用于3'末端/终止子鉴定的核心原始数据
- SRA/BioProject（他人已发表数据，本文重新分析用于跨物种比较）: PRJNA640168（E. coli）、ERR3258013-ERR3258015 / PRJEB31965（P. aeruginosa）、ERS1048762,ERS1051962,ERS1051954,ERS1051963 / PRJEB12568（B. subtilis） - 原始测序数据 - 这些是作者重新下载并用自建pipeline重新分析生成对比用终止子数据，本文未提供这三个物种的终止子坐标表原始来源，如果目标是其他物种的终止子坐标则需按B类处理

现成坐标数据线索（本文为B. burgdorferi的A类核心证据）:
- 数据位置: Supplementary Data 1（3'末端坐标+intrinsic termination score）；Supplementary Data 4（Rho termination regions坐标，按基因分类的tab）；同时Supplementary Data 2（sRNA 5'/3'边界坐标）、Supplementary Data 3（转录组注释文件，含ORF/UTR/tRNA/rRNA/sRNA边界）、Supplementary Data 5（上游/ORF内3'末端坐标+spermidine-dependent score）
- 数据字段: 明确提及的字段包括——3' end基因组坐标（单碱基精度peak坐标）、strand、分类（Primary/Antisense/Internal/Orphan）、intrinsic termination score（KineFold模型评分，阈值≥3.0）、Rho score（R(BCM/untreated)比值及Fisher检验p值）、spermidine-dependent score（R(untreated/spermidine)比值及p值）、关联基因/ORF信息
- 覆盖范围: B. burgdorferi B31菌株（PA003），对数期(log)和温度诱导稳定期(TS-stationary)两种生长条件下的全基因组3'端图谱；3次生物学重复；共1333个（log期）和944个（TS-stationary期）3'末端

第三方平台内容判断:
- 平台: Figshare (https://doi.org/10.6084/m9.figshare.22569205)
- 判断: 非坐标数据，为Source Data（原始未裁剪的Northern blot/免疫印迹扫描图及分子量标记）
- 依据: 正文明确说明"Source data for this paper have been submitted to Figshare...includes all uncropped and unprocessed scans with molecular weight markers labeled"，与终止子坐标无关

- 平台: GitHub (https://github.com/NICHD-BSPC/termseq-peaks 和 https://github.com/lcdb/lcdb-wf)
- 判断: 代码
- 依据: 明确说明为peak-calling流程代码及数据处理pipeline代码，用于复现分析而非存储坐标数据本身

- 平台: UCSC Genome Browser track hub链接（NICHD Bioinformatics Core托管）
- 判断: 可视化轨道数据（bigwig等），非表格化坐标清单
- 依据: 描述为"processed RNA-seq data...available online via UCSC genome browser"，提供的是测序覆盖度轨道，用于浏览而非直接的终止子坐标表；如需坐标仍应以Supplementary Data 1/4/5为准

待人工确认事项:
- 建议下载Supplementary Data 1、4、5的XLSX原文，确认字段命名与Chromosome/Start/End/Strand是否直接对应，以及是否需要额外的坐标系转换（1-based vs 0-based）
- 确认Supplementary Data 1中log期与TS-stationary期数据是否在同一表格的不同sheet中区分，便于按条件筛选

建议后续动作:
- 可直接下载Supplementary Data 1（3'末端坐标+intrinsic terminator score）和Supplementary Data 4（Rho termination regions坐标）用于B. burgdorferi终止子数据库构建，仅需做格式转换（如列名标准化、坐标系核对），无需重新下载FASTQ或重新跑pipeline
- 若还需要E. coli/P. aeruginosa/B. subtilis的终止子坐标用于跨物种比较，则这部分需按B类处理，即根据文中给出的SRA/BioProject登录号重新下载原始数据并按本文描述的pipeline（lcdb-wf + termseq-peaks）重新分析
