# 文献9 — PMID 34874777

**Different Regulatory Modes of Synechocystis sp. PCC 6803 in Response to Photosynthesis Inhibitory Conditions**  
Cho et al. (2021), *mSystems*, 6(6):e0094321. DOI: 10.1128/mSystems.00943-21  
RNA-seq/Ribo-seq/Term-seq 数据：BioProject PRJNA666973。

文献核查报告
物种: Synechocystis sp. PCC 6803（蓝藻/集胞藻）
期刊/年份: mSystems / 2021

分类结论: A类
分类依据: 文献补充材料中的 Table S5 明确标注为"List of transcript 3′-end positions (TEPs)"，是Term-seq分析后处理得到的、按P/S/I/A/U五类位置关系分类的3′末端坐标表，属于终止子相关的现成坐标数据，可直接下载复用；同时Table S6提供了配套的转录单元(TU)坐标表。

已确认的登录号清单:
- BioProject: PRJNA666973 - 原始测序reads (RNA-seq/Ribo-seq/Term-seq) - 用于存放raw reads，非坐标表
- GenBank: NC_000911.1 - 参考基因组序列 - 仅为比对参考，非分析结果
- RefSeq: GCF_000009725.1 - 参考基因组assembly - 仅为比对参考，非分析结果

现成坐标数据线索（A类核心证据）:
- 数据位置: Table S5（文件名 msystems.00943-21-st005.xlsx，39.56 KB）
- 数据字段: 文本描述其为"transcript 3′-end positions (TEPs)"列表，并按位置关系分为Primary(P)/Secondary(S)/Intragenic(I)/Antisense(A)/Upstream(U)五类（见Fig 4C及正文"The TEPs were classified into five categories...(Fig. 4C and Table S5)"）。虽未逐字给出列名，但从上下文可推断至少包含：基因/位点ID、TEP基因组坐标、链方向、分类标签(P/S/I/A/U)
- 覆盖范围: 全基因组水平，共识别784个TEP，来自CTRL/HL/LT三种条件下重复间一致检测到的位点
- 补充说明: Table S6（msystems.00943-21-st006.xlsx，24.39 KB）为"List of transcription units (TUs)"，共315个TU，是TSS与P-TEP整合后的转录单元坐标表，可作为终止子坐标的上下文补充（提供每个TU对应的起止边界）

第三方平台内容判断（如涉及Figshare/Zenodo/GitHub等）:
- 平台: Figshare
- 判断: 元数据摘要/中间分析结果，非终止子坐标本身
- 依据: 文本中Figshare链接仅对应Table S2（标准化表达量矩阵，全基因表达值）、Table S3（RPF标准化计数）及Fig S3（GO富集图），均与终止子坐标无关，因此可排除Figshare作为终止子数据来源；真正的终止子坐标（Table S5、S6）是通过ASM官网直接托管的补充文件，不经过Figshare中转

待人工确认事项:
- Table S5的实际列名/字段结构（Chromosome、Strand、Position等具体表头）需打开xlsx原文件核实，正文只描述了内容类型而未逐字列出表头
- 需确认TEP坐标是否为单碱基精度的绝对基因组坐标（即可直接用于构建终止子数据库的标准格式），还是相对坐标（如相对起始密码子的相对位置）

建议后续动作:
- 直接下载 Table S5（msystems.00943-21-st005.xlsx）作为该物种终止子（TEP）坐标的核心数据源，按P/S/I/A/U分类字段进行格式转换即可入库；建议同时下载 Table S6 用于补充TU边界信息，无需重新下载FASTQ或重新跑Term-seq分析流程
