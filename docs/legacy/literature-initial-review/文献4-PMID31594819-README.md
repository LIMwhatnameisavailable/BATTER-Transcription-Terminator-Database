# 文献4 — PMID 31594819

**A rhlI 5' UTR-Derived sRNA Regulates RhlR-Dependent Quorum Sensing in Pseudomonas aeruginosa**  
Thomason et al. (2019), *mBio*, 10(5):e02253-19. DOI: 10.1128/mBio.02253-19  
RNA-seq 和 term-seq 数据：ENA PRJEB31965。

文献核查报告
物种: Pseudomonas aeruginosa (PAO1)
期刊/年份: mBio / 2019

分类结论: A类
分类依据: 正文明确说明"We identified a total of 804 TTSs associated with annotated P. aeruginosa genes or operons (see Table S1, tab A)"，即补充材料Table S1的Tab A是一份已经处理好的、覆盖全基因组的转录终止位点(TTS)坐标表，可直接复用；同时正文Table 1也直接列出了7个AHL调控sRNA的具体3'端基因组坐标(position)，进一步印证存在现成坐标数据。

已确认的登录号清单:
- ENA: PRJEB31965 - 原始测序数据(RNA-seq + term-seq reads) - 用于产生Table S1数据的原始reads，本身不是坐标表，但已有对应的处理结果可直接使用，无需重新分析

现成坐标数据线索（A类核心证据）:
- 数据位置: Table S1 (supplemental material, xlsx文件, mbio.02253-19-st001.xlsx), Tab A
- 数据字段: 文本描述为"Transcription termination sites (TTS) associated with P. aeruginosa PAO1 genes"，正文Table 1中展示的字段示例包括：sRNA name / Flanking genes (5′/3′) / 3′ end position / sRNA strand / Fold change / Comments，可推断Tab A至少含有基因名、TTS基因组坐标(position)、链方向等字段
- 覆盖范围: PAO1菌株，全基因组范围内共804个与已注释基因/操纵子关联的TTS；另有独立的Tab B为21个AHL差异调控位点的差异表达分析(DESeq2结果，非坐标本身，但同样来自term-seq定量分析)

Table S1其他Tab内容判断:
- Tab A: 804个TTS坐标列表 → 判断为"真实坐标数据"，是构建终止子数据库的核心可用材料
- Tab B: term-seq位点差异表达分析(DESeq2 base mean/fold change/P value) → 判断为差异表达统计结果，非坐标本身，但可作为Tab A坐标的功能注释补充
- Tab C: TargetRNA2预测的RhlS靶点列表 → 判断为下游功能预测结果，与终止子坐标无关
- Tab D: 菌株/质粒/引物信息 → 实验材料清单，非坐标数据

第三方平台内容判断:
- 平台: 无涉及Figshare/Zenodo/GitHub，仅使用ASM期刊自带supplemental material机制(PDF+XLSX)托管Table S1
- 判断: 不适用（未使用第三方平台）
- 依据: 文献仅通过期刊官方补充材料系统提供Text S1、Fig S1-S7及Table S1(xlsx)，测序原始数据单独存放于ENA

待人工确认事项:
- 需下载mbio.02253-19-st001.xlsx原文件，确认Tab A实际列名是否包含Chromosome/Strand/Start/End或类似标准坐标字段格式，以及804条记录的具体数据结构（是否已可直接映射到基因组版本、是否需要额外的坐标系转换）
- 确认Tab A的804个TTS是否覆盖全部检测条件（+AHL和-AHL两种条件是否分别列出，还是合并的代表性位点）

建议后续动作:
- 可直接下载Supplementary Table S1 (mbio.02253-19-st001.xlsx) 的Tab A，提取804条TTS坐标用于终止子数据库构建，无需重新下载ENA PRJEB31965的FASTQ原始数据重新跑term-seq分析流程
