# 文献5 — PMID 32694125

**Genome-Scale Transcription-Translation Mapping Reveals Features of Zymomonas mobilis Transcription Units and Promoters**  
Vera et al. (2020), *mSystems*, 5(4):e00250-20. DOI: 10.1128/mSystems.00250-20  
多组学数据：GEO GSE139939（RNA-seq/TSS-seq/term-seq/ribo-seq）；蛋白质组：PRIDE PXD016962。

文献核查报告
物种: Zymomonas mobilis ZM4
期刊/年份: mSystems / 2020

分类结论: A类

分类依据: 文献在Data Availability中虽仅给出GEO原始测序数据登录号，但正文明确说明经统计分析（Poisson检验+TSS-seq整合去除processing sites）得到的2,091个转录终止位点（TTS）及TransTermHP预测的1,746个内源终止子，已直接存放于补充材料Data Set S3（xlsx表格，389.89 KB），可直接下载使用，无需重跑pipeline。

已确认的登录号清单:
- GEO: GSE139939 - RNA-seq/TSS-seq/term-seq/ribo-seq原始及processed reads - 用于生成TTS坐标的原始测序数据来源，非终止子坐标本身
- ProteomeXchange/PRIDE: PXD016962 - 蛋白质质谱数据 - 与终止子无关
- GitHub: https://github.com/jmvera255/Vera_2020_mSystems - σ70/σA启动子建模脚本代码 - 与终止子坐标无关，仅为启动子分析代码

现成坐标数据线索（如为A类，说明具体线索）:
- 数据位置: Supplementary Data Set S3（文件名 msystems.00250-20-sd003.xlsx，389.89 KB）
- 数据字段: 
  - Sheet 1: 列名说明（column legends），适用于Sheet 2-4
  - Sheet 2: RNA processing sites（RNA加工位点，非终止子但同一表内含坐标）
  - Sheet 3: Transcription termination sites (TTSs) —— 核心终止子坐标数据，共2,091个候选TTS（正文Table 2列出各条件下具体数量）
  - Sheet 4: TTS与TransTermHP预测终止子的匹配结果（249个匹配的intrinsic terminator，563个映射的TTS，含"r"标记的反向补充终止子）
  - Sheet 5: TransTermHP预测的全部转录终止子列表（1,746个，genome-wide，与基因注释无关，独立预测）
- 覆盖范围: Z. mobilis ZM4染色体+4个质粒，6种生长条件（MMG/RMG ± O2，mid-glucose/stationary两个时间点），2,091个TTS，1,746个预测intrinsic terminator，249个经实验验证匹配的terminator

第三方平台内容判断（如涉及Figshare/Zenodo/GitHub等）:
- 平台: GitHub (jmvera255/Vera_2020_mSystems)
- 判断: 代码
- 依据: 正文明确表述为"σA/σ70 promoter model pipeline and all associated scripts"，仅为启动子分析用的Python/Perl脚本，不含终止子坐标数据

待人工确认事项:
- Data Set S3中Sheet 1的具体列名（如Chromosome/Strand/Position/Start/End等字段名称）未在正文中逐字列出，仅描述了各Sheet的内容类别，建议下载xlsx原文确认字段结构以便直接映射进终止子数据库
- Sheet 4中"r"标记的反向补充终止子（54个）的具体坐标表示方式需核对原表

建议后续动作:
- 可直接下载补充材料Data Set S3 (msystems.00250-20-sd003.xlsx)，重点使用Sheet 3（TTS坐标）和Sheet 5（TransTermHP预测的intrinsic terminator坐标），无需重新下载GSE139939 FASTQ或重跑pipeline
