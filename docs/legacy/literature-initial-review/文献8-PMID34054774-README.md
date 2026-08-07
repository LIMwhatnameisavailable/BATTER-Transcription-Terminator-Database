# 文献8 — PMID 34054774

**Multi-Omic Analyses Reveal Habitat Adaptation of Marine Cyanobacterium Synechocystis sp. PCC 7338**  
Jeong et al. (2021), *Front Microbiol*, 12:667450. DOI: 10.3389/fmicb.2021.667450  
全基因组测序/dRNA-seq/Term-seq/RNA-seq 数据：BioProject PRJNA629670。

文献核查报告
物种: Synechocystis sp. PCC 7338（海洋蓝细菌）；比较物种为淡水 Synechocystis sp. PCC 6803
期刊/年份: Frontiers in Microbiology, 2021

分类结论: A类
分类依据: 正文明确指出通过 Term-seq 鉴定获得了 487 个 TEP（transcript 3′-end position，即终止子相关的转录本3′末端位点），并按照与邻近基因的相对位置进行了分类（P/S/U/I/A/N 六类），该结果直接对应存放于 Supplementary Data 2 中（"a total of 487 TEPs were identified and categorized based on their relative positions to the adjacent genes ... (Figure 2H and Supplementary Data 2)"）。这是一份已经处理完成的基因组坐标/位点列表，可直接用于构建终止子数据库，无需重新下载FASTQ或重跑pipeline。

已确认的登录号清单:
- NCBI BioProject: PRJNA629670 - 原始测序数据（genome-seq, RNA-seq, dRNA-seq, Term-seq） - 本研究自产数据，Data Availability Statement中明确列出
- NCBI SRA: SRR12763770, SRR12763771 - Term-seq原始reads（Synechocystis sp. PCC 6803对照物种） - 引自Cho and Jeong 2020，用于比较分析，非本文一手产出，且仅为原始reads

现成坐标数据线索（A类核心证据）:
- 数据位置: Supplementary Data 2（TEP列表，对应Figure 2H）
- 数据字段: 文本未逐字列出表头，但根据Methods部分描述可推断至少包含——TEP基因组位置（5′端位置，链方向经过reverse处理）、TEP分类标签（P-TEP主要位点/S-TEP次要位点/U-TEP 5'UTR内/I-TEP基因内部/A-TEP反义链/N-TEP基因间区）、可能还包含L-shaped/I-shaped终止子形状分类（文中提及此分类但未指明具体存放位置，需核实是否也在Data 2或另有Supplementary Table）
- 覆盖范围: Synechocystis sp. PCC 7338全基因组，共487个TEP（329个P-TEP + 25个S-TEP + 其余为U/I/A/N类），基于Term-seq三次生物学重复数据经机器学习（KNN分类器）鉴定

补充说明（其他相关Supplementary编号，非终止子坐标本体）:
- Supplementary Data 1: TSS列表（897个TSS及分类），用于启动子/5'UTR分析，非终止子数据
- Supplementary Data 3: 启动子区域和终止子区域在两物种间的保守性比较分类（conserved/mismatched/orphan/specific），这是下游比较分析结果，不是原始终止子坐标表本身
- Supplementary Data 4: 差异表达基因（DEG）列表，与终止子无关

第三方平台内容判断:
- 平台: 无（本文未提及Figshare/Zenodo/GitHub存放数据；提到了一个实验室网站 http://cholab.or.kr 用于分享自研Python脚本）
- 判断: 代码（非坐标数据）
- 依据: 原文明确说明"The Python script is available at http://cholab.or.kr"，用于说明TEP鉴定所用的KNN分类脚本，属于代码工具而非数据本体

待人工确认事项:
- 需下载Frontiers官网的Supplementary Material原始文件（页面提示有5个"Download source data"链接但未展示文件名），逐一确认哪个文件对应"Supplementary Data 2"，并核实其具体字段名（是否含Chromosome/Strand/Position等标准列名）
- 需确认Supplementary Data 2中是否同时包含L-shaped/I-shaped终止子形状分类信息，或该信息存放于Supplementary Figure 2F/G对应的另一份数据文件中
- 需确认Supplementary Table 2-6等表格是否与终止子数据有交叉引用（例如Supplementary Table 6提及NDH-1基因表达）

建议后续动作:
- 直接下载该文献Frontiers网站的Supplementary Data 2文件，核对字段格式后即可用于终止子数据库构建，无需下载PRJNA629670下的FASTQ重新跑pipeline
- 若需要与淡水种PCC 6803的终止子坐标进行比较，则该部分数据未见现成坐标表，需按登录号SRR12763770/71下载原始reads自行分析（此部分归为B类）
