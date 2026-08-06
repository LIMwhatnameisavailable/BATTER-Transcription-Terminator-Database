# 文献13 — PMID 38030608

**TRS: a method for determining transcript termini from RNAtag-seq sequencing data**  
Bar et al. (2023), *Nat Commun*, 14(1):7843. DOI: 10.1038/s41467-023-43534-2  
自产 RNAtag-seq/term-seq 数据：ArrayExpress E-MTAB-12429；算法实现：GitHub amirbarHUJI/TRS；Supplementary Data 1–5 见本文件夹。

文献核查报告
PMID: 38030608（Nature Communications 2023, 14:7843）
物种: 主要为 Escherichia coli K-12 MG1655（另涉及EPEC、ETEC、Salmonella enterica、Klebsiella pneumoniae、Shigella flexneri、Listeria monocytogenes等多种细菌的公开数据再分析）
期刊/年份: Nature Communications, 2023

分类结论: A类
分类依据: 正文明确指出"we identified a total of 1486 3' termini (Supplementary Data 1-2)"，说明Supplementary Data 2中已包含TRS流程处理后得到的3'末端（终止子）基因组坐标列表；同时Supplementary Data 3被明确关联到"3' termini positions were determined by applying TRS... (Methods, Supplementary Table 1, Supplementary Data 3)"，同样是处理后的坐标表，覆盖LB/EG两种培养条件下RNAtag-seq与term-seq四组数据集的终止子位点

已确认的登录号清单:
- ArrayExpress: E-MTAB-12429 - 原始测序reads(RNAtag-seq + term-seq, E. coli K-12 MG1655, LB/EG两种培养基各三个重复) - 本研究新产生的原始数据
- 其他公开数据集登录号 - 未在提供文本中直接列出具体编号，仅说明"All referenced sequencing libraries accession codes... are listed in Supplementary Data 1"，即Data 1本身是一个"登录号索引表"，汇总了论文中复用的所有外部RNAtag-seq/term-seq数据集（涉及E. coli、EPEC、ETEC、Salmonella、Klebsiella、Shigella flexneri、Listeria等）的原始来源

现成坐标数据线索（A类核心证据）:
- 数据位置: Supplementary Data 2（对应E. coli K-12 MG1655 LB指数期RNAtag-seq数据鉴定出的1486个3'末端坐标）；Supplementary Data 3（对应LB/EG条件下RNAtag-seq与term-seq四个数据集鉴定出的3'末端坐标，涉及1814/1984个位点等）
- 数据字段: 正文未逐字列出列名，但Methods部分详细描述了终止子的分类体系（Primary/Distant Primary/Alternative Primary/Premature/Orphan等八类），推断坐标表至少包含基因组位置(position)、所属基因/操纵子归属、分类标签(primary/premature/orphan等)字段；具体列名建议下载XLSX原文确认
- 覆盖范围: E. coli K-12 MG1655，指数生长期，LB与EG（基本培养基+葡萄糖）两种条件，各3个生物学重复，RNAtag-seq与term-seq两种测序方法交叉验证

另外两个补充数据集（Supplementary Data 4、5）虽同样是"处理后结果"，但内容不是终止子坐标本体，而是衍生分析结果：
- Supplementary Data 4: 3'UTR-CDS表达量回归分析中识别出的38个异常值(outlier)基因列表，非直接终止子坐标表
- Supplementary Data 5: EPEC中条件特异性终止/加工位点的候选基因列表（133个候选，经统计筛选），属于衍生的候选清单而非完整坐标数据库

第三方平台内容判断（如涉及Figshare/Zenodo/GitHub等）:
- 平台: GitHub（https://github.com/amirbarHUJI/TRS）
- 判断: 代码（Code Availability部分明确说明这是TRS算法的Python包实现，仅为流程代码，不含数据本体）
- 依据: 原文Code availability章节原话为"The implementation of the TRS algorithm is available as a python package in the Python Package Index and GitHub"，未提及托管坐标数据

待人工确认事项:
- 需下载Supplementary Data 2与Data 3的XLSX原文，逐一核实列名（是否包含Chromosome/Strand/Start/End或Position字段），以及坐标是基于何种参考基因组版本（正文提及使用NC_000913.3作为E. coli K-12 MG1655参考基因组）
- 需确认Supplementary Data 1中列出的其他细菌（EPEC/ETEC/Salmonella/Klebsiella/Shigella/Listeria）数据仅为"外部原始测序登录号索引"，还是也包含这些细菌重新分析后的终止子坐标（正文Fig.9部分提到对这些菌种应用TRS后得到了保守终止子位置，但未明确说明这些跨物种结果坐标是否也收录进了某个Supplementary Data文件，还是仅以图形展示）
- 需确认Data 4、Data 5是否附带坐标列（如position/start/end），还是仅为基因名+统计值列表

建议后续动作:
- 对E. coli K-12 MG1655（核心物种）而言，可直接下载Supplementary Data 2（LB指数期基线数据集）与Supplementary Data 3（LB/EG四组交叉验证数据集）用于格式转换，构建终止子数据库，无需重新跑pipeline
- 对论文中提及的其他5种细菌（EPEC、ETEC、Salmonella、Klebsiella、Shigella flexneri）及Listeria monocytogenes，建议先查阅Supplementary Data 1索引及正文Supplementary Information部分，确认这些跨物种分析结果是否也已整理为坐标表并公开，若未公开则需按登录号下载FASTQ后使用作者提供的TRS开源代码重新跑分析
