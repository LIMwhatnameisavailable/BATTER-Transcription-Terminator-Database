# 文献12 — PMID 37096044

**Premature termination of transcription is shaped by Rho and translated uORFS in Mycobacterium tuberculosis**  
D'Halluin et al. (2023), *iScience*, 26(4):106465. DOI: 10.1016/j.isci.2023.106465  
RNA-seq 数据：ArrayExpress E-MTAB-11753；分析代码：GitHub ppolg/Mtb_termseq。

文献核查报告
物种: Mycobacterium tuberculosis (M.TB, H37Rv)
期刊/年份: iScience, Volume 26, Issue 4, 2023

分类结论: A类

分类依据: 补充材料中明确提供了Table S3（Transcription Termination Sites, TTS），标注为"identified as a TTS"的基因组坐标结果表，且正文Methods部分详细描述了TTS的坐标提取流程（基于Bedtools/termseq_peaks输出的CPM峰值位置），该表可直接用于构建终止子数据库，无需重新下载FASTQ或重跑pipeline。

已确认的登录号清单:
- ArrayExpress: E-MTAB-11753 - RNA-seq/Term-seq/tagRNA-seq原始测序数据 - 用于生成本文所有坐标表的原始reads，Key Resources Table中列出
- GitHub: https://github.com/ppolg/Mtb_termseq - 分析代码（非数据本体）- 包含TTS/PS/uORF等坐标提取所用的R脚本

现成坐标数据线索（如为A类，说明具体线索）:
- 数据位置: Table S3（Transcription Termination Sites, TTS；见Figure 3和STAR Methods），另有Table S1（New TSS）、Table S2（Extracted PS, Processing Sites）、Table S4（RD TTS, TTS scores, RT scores）、Table S5（Conditional TTS/5' leaders）
- 数据字段: 正文明确提及这些表包含基因组位置信息（"genomic positions"）、TTS分类（Internal/Antisense/Final/Orphan）、CPM覆盖度、TTS score、RT score等；Table S3标题直接标注为"Transcription termination sites (TTS)"，为终止子核心坐标表
- 覆盖范围: M. tuberculosis H37Rv全基因组，log期生长条件，三次生物学重复（Term-seq/tagRNA-seq），共鉴定2567个TTS（经50nt processing site过滤后的最终终止位点集合），另有RhoTermPredict计算预测的29096个RDTS也列于Table S3

第三方平台内容判断（如涉及Figshare/Zenodo/GitHub等）:
- 平台: GitHub (ppolg/Mtb_termseq)
- 判断: 代码
- 依据: Key Resources Table与Data and Code Availability部分均明确表述为"Customized code for analysing data"/"All original codes used to generate results and corresponding figures"，正文多处引用该仓库中的具体R脚本文件名（如Mtb_peaksfrequency.R、Mtb_PS_distance.R等），确认其内容为分析脚本而非坐标数据本体

待人工确认事项:
- 需下载Table S3原始Excel/CSV文件，确认其列结构是否包含标准字段（如Chromosome/Strand/Start/End或Position），以确定与目标终止子数据库schema的兼容性和是否需要额外格式转换
- 需确认Table S3中2567个TTS坐标与29096个RhoTermPredict预测RDTS坐标是否在同一表格内分列存放，或是否需要分别提取
- PMID号未在提供文本片段中出现，需另行核实

建议后续动作:
- 可直接下载Supplementary Table S3（及可能需要的Table S4/S5作为补充置信度信息）用于坐标提取和格式转换，无需重新下载ArrayExpress原始测序数据或重跑Term-seq分析流程
