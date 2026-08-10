# 文献3 — PMID 31555254

**The Transcription Unit Architecture of Streptomyces lividans TK24**  
Lee et al. (2019), *Front Microbiol*, 10:2074. DOI: 10.3389/fmicb.2019.02074  
dRNA-seq/Term-seq/RNA-seq/Ribo-seq 数据：ENA PRJEB31507（1,978个TSS，1,640个3'端位置）。

文献核查报告
物种: Streptomyces lividans TK24
期刊/年份: Frontiers in Microbiology / 2019

分类结论: A类
分类依据: 正文明确说明通过Term-Seq鉴定了全基因组范围内1,640个transcript 3'-end positions（TEPs，即终止/转录本3'末端位点），并直接指出这些位点及其分类信息保存在Supplementary Dataset 3中（"a total of 1,640 transcript 3′-end positions (TEP) were identified across the genome (Figure 4A and Supplementary Dataset 3)"）。文中还描述了TEP按照与邻近基因的位置关系被分为P/S/A/C/N五类，这种分类逻辑通常意味着该数据集是逐位点列出基因组坐标及分类标签的结构化表格，可直接用于构建终止子数据库，无需重新处理原始测序数据。

已确认的登录号清单:
- ENA (European Nucleotide Archive): PRJEB31507 - 原始测序数据（dRNA-Seq、Term-Seq、RNA-Seq、Ribo-Seq） - Data Availability声明中提供，为原始reads，非处理后坐标
- 参考基因组: CP009124 - S. lividans TK24基因组序列登录号（用于比对参考，非数据产出）

现成坐标数据线索（如为A类，说明具体线索）:
- 数据位置: Supplementary Dataset 3（对应Figure 4A）
- 数据字段: 正文未逐一列出具体列名，但依据描述可推断至少包含"基因组位置（position）"和"分类标签（P/S/A/C/N，即Primary/Secondary/Antisense/Cis-regulatory/Intergenic）"字段；此外Methods部分提及TEP鉴定基于Term-Seq reads 3'端位置聚类及modified z-score筛选，说明该数据集应为逐位点坐标列表而非汇总统计
- 覆盖范围: S. lividans TK24全基因组，基于4个生长时期（早/中/晚指数期、稳定期）双重生物学重复的Term-Seq数据整合鉴定，共1,640个TEP位点

第三方平台内容判断（如涉及Figshare/Zenodo/GitHub等）:
- 平台: 无（补充材料托管于Frontiers期刊自身网站，非Figshare/Zenodo/GitHub）
- 判断: 不适用
- 依据: 文中链接为Frontiers期刊官方supplementary material页面，文件类型为期刊内部编号的Supplementary Dataset/Table/Figure

待人工确认事项:
- 需下载Supplementary Dataset 3原始文件，确认具体列名是否包含Chromosome/Strand/Position/Start/End等标准坐标字段
- 需确认该数据集是否明确标注了链信息（Strand，+/-），这对构建终止子数据库至关重要
- 需确认TEP坐标是单点位置（如3'-end单一碱基坐标）还是范围区间（Start-End），以匹配后续数据库字段设计
- Supplementary Dataset 1（TSS数据）、Dataset 2（翻译效率TE数据）、Dataset 4（TU数据）虽非终止子核心数据，但若需要交叉验证TU边界，也可一并下载核查

建议后续动作:
- 优先从Frontiers期刊官网（https://www.frontiersin.org/articles/10.3389/fmicb.2019.02074/full#supplementary-material）下载Supplementary Dataset 3，核实字段格式后可直接用于终止子坐标数据库的构建
- 若Dataset 3坐标格式与目标数据库字段不完全匹配，仅需做格式转换（如坐标系统调整、列名映射），无需重新下载FASTQ或重跑Term-Seq分析流程
