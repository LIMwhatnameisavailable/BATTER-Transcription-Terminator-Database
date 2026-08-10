# 文献1 — PMID 29606352

**Evolutionary Convergence of Pathway-Specific Enzyme Expression Stoichiometry**  
Lalanne et al. (2018), *Cell*, 173(3):749-761.e38. DOI: 10.1016/j.cell.2018.03.007  
Rend-seq 数据：GEO GSE95211（4物种，18个Rend-seq + 3个ribosome profiling样本）；核心脚本：GitHub jblalanne/Rend_seq_core_scripts。

文献核查报告
物种: Bacillus subtilis、Escherichia coli、Vibrio natriegens、Caulobacter crescentus（四种细菌，另含酵母Saccharomyces cerevisiae作为对比但非终止子分析对象）
期刊/年份: Cell, 2018年4月19日, Volume 173, Issue 3

分类结论: A类
分类依据: 正文STAR Methods明确指出"final list of intrinsic terminators for the four species considered can be found in Table S3, with measured readthrough in wild-types and in the various mutants...as well as terminator properties"；Supplementary Table S3标题即为"Intrinsic Terminators and Readthrough Fractions Determined by Rend-Seq"，包含8个分表，分别对应4个物种的全部终止子列表和"tuned terminators"子集，属于已处理完成、可直接复用的终止子坐标/属性表。

已确认的登录号清单:
- GEO: GSE95211 - 原始测序reads及Rend-seq/核糖体图谱的pile-up wig文件 - 这是原始数据，非终止子坐标表本身
- Mendeley Data (DOI): 10.17632/ncm3s3pk2t.1 - Rend-seq验证数据、mRNA丰度、翻译效率、Northern blot原始图像 - 主要为验证性/元数据，非终止子坐标主表
- GitHub: https://github.com/jblalanne/Rend_seq_core_scripts - Rend-seq核心分析脚本（代码，非数据）

现成坐标数据线索（A类核心证据）:
- 数据位置: Supplementary Table S3（"Intrinsic Terminators and Readthrough Fractions Determined by Rend-Seq, Related to Figures 4 and S3"），文件为Spreadsheet格式（507.67 KB）
- 数据结构: 共8个Sheet
  - Sheet 1: B. subtilis鉴定出的全部终止子（依据文本，共1486个高置信度内源终止子，其中1414个可定量readthrough）
  - Sheet 2: E. coli终止子（630个高置信度，599个可定量readthrough）
  - Sheet 3: V. natriegens终止子（1257个通过标准，1154个可定量）
  - Sheet 4: C. crescentus终止子（374个通过标准，338个可定量）
  - Sheet 5-8: 上述四物种对应的"tuned terminators"子集（B. subtilis 167个，E. coli 88个，V. natriegens 140个，C. crescentus 47个）
- 数据字段: 文本明确提及包含"测定的readthrough（野生型及各突变株）"及"terminator properties"（发夹自由能ΔG、U-tract长度、loop大小、stem长度等，见Determinants of readthrough fraction一节），推断表中应包含末端位置坐标（因terminator鉴定基于genomic position的peak z-score方法）、readthrough分数、序列/结构特征参数
- 覆盖范围: 4个细菌物种，B. subtilis为最主要研究对象（含野生型及rho/pnpA/rnr/rph/yhaM等多个核酸酶敲除突变株的对照数据）

第三方平台内容判断:
- 平台1: GitHub (jblalanne/Rend_seq_core_scripts)
  判断: 代码
  依据: 明确标注为"Core Rend-seq data analysis scripts"，用于处理原始Rend-seq数据的pipeline代码，非坐标数据本体
- 平台2: Mendeley Data (10.17632/ncm3s3pk2t.1)
  判断: 元数据摘要/验证性图表，非终止子坐标主表
  依据: 文本反复描述该处存放的是"Northern blots raw data""Rend-seq validation data""mRNA abundances""translation efficiency"，用于文献比对验证（如5'RACE测序结果、既往文献3'端比对），而非系统性终止子坐标列表；真正的终止子坐标列表明确指向Table S3

待人工确认事项:
- Table S3实际列名（是否包含Chromosome/Strand/Start/End或等效的Position字段）需下载原始xlsx文件核实，本文本仅描述其内容类别（终止子编号、readthrough分数、结构参数），未逐字列出列名
- 需确认Table S3中终止子位置坐标的具体表示方式（是单一Position列，还是Start/End范围，或是相对于上下游基因的相对位置）
- Data S1（PDF格式，7.75MB）虽标注含"Chromosomal Positions"，但主要用于展示保守基因簇的转录本结构重塑示例（图5、S4配套数据），并非独立的终止子坐标数据库，建议区分使用用途

建议后续动作:
- 可直接下载Table S3（Spreadsheet, 507.67 KB）用于构建四物种终止子坐标数据库，重点提取B. subtilis和E. coli的高置信度终止子及tuned terminator子集
- 若需要Rend-seq峰值的原始wig文件做进一步验证或重新计算readthrough，可从GEO: GSE95211下载pile-up wig文件辅助交叉核对Table S3坐标
- 建议下载后检查Table S3列名格式，如坐标体系与目标数据库要求不一致，可能需要简单的格式转换（而非重新跑分析pipeline）
