# 文献7 — PMID 33947798

**Elucidating the Regulatory Elements for Transcription Termination and Posttranscriptional Processing in the Streptomyces clavuligerus Genome**  
Hwang et al. (2021), *mSystems*, 6(3):e01013-20. DOI: 10.1128/mSystems.01013-20  
基因组：GenBank CP027858/CP027859；RNA-seq/dRNA-seq/ribo-seq：GEO GSE128216；term-seq：GEO GSE138325。

文献核查报告
物种: Streptomyces clavuligerus ATCC 27064
期刊/年份: mSystems, 2021 (Vol. 6, No. 3)

分类结论: A类
分类依据: 文献补充材料 Data Set S1 Sheet 1 明确提供了"List of all transcript 3′ end sites (TEPs), transcription units (TUs), and transcription unit clusters (TUCs)"的完整坐标表，包含TEP类别、折叠自由能、readthrough fraction、TU/TUC分类等字段，属于可直接复用的处理后坐标数据，无需重新下载FASTQ跑pipeline

已确认的登录号清单:
- GenBank: CP027858, CP027859 - 全基因组序列及注释 - 参考基因组，非终止子坐标本身
- GEO: GSE128216 - RNA-seq/dRNA-seq/ribosome profiling原始测序数据 - 用于TSS和转录组整合分析的原始reads
- GEO: GSE138325 - Term-seq原始测序数据 - 用于识别TEP（转录3'端位点）的原始reads，即终止子相关原始数据源

现成坐标数据线索（A类核心证据）:
- 数据位置: Supplemental Material "DATA SET S1"（文件名 msystems.01013-20-sd001.xlsx），Sheet 1
- 数据字段: 包含TEP位置分类（P/S/Pre/A/N五类）、Folding free energy (kcal/mol)、Avg. readthrough fraction、TU类别（Mono/Poly/Pre/Inter）、RPF_cut、ORF frame、TSS_Cat、TEP_Cat、Nc_TU_Cat等字段，且明确说明"Folding free energy of the RNA structure is calculated from the sequence at −40 bp upstream to 0 bp from TEP"——具备明确的基因组坐标计算基准，可用于反推TEP在基因组上的具体位置
- 覆盖范围: 全基因组共1,427个TEP位点、1,648个TU、610个TUC，物种为S. clavuligerus ATCC 27064，覆盖early/transition/late-exponential/stationary四个生长时期的数据整合结果
- 补充说明: Sheet 2 另外提供了24组XRE-DUF397基因对及其双向TEP（Bi-TEP）信息，属于该坐标表的功能注释延伸部分，不影响Sheet 1作为主坐标表的A类判定

第三方平台内容判断:
- 平台: http://cholab.or.kr（正文Materials and Methods中提及）
- 判断: 代码/元数据摘要，非坐标数据本体
- 依据: 原文明确说明该网址托管的是"The python script and KNN machine classifiers used (pickled python objects)"，即TEP识别所用的机器学习脚本与分类器模型文件，而非终止子坐标表本身，坐标数据已完整收录于Data Set S1中 

待人工确认事项:
- 建议下载 msystems.01013-20-sd001.xlsx 原始文件，核实Sheet 1中是否包含明确的Chromosome/Strand/Start-End或Position列（文本描述中提到的是"TEP position"及分类字段，未逐一列出原始列名，需打开表格确认具体列结构是否可直接映射为标准基因组坐标格式）
- 需确认该文件是否区分了正负链（Strand）标注方式，以便格式转换时正确处理链方向

建议后续动作:
- 可直接下载并解析 Supplemental Data Set S1 (Sheet 1) 用于构建终止子数据库，仅需做字段名称到标准坐标格式的映射转换，无需重新下载GSE138325的term-seq原始FASTQ数据重新跑pipeline 
- 若需要验证或扩展分析（如不同生长阶段差异TEP），GSE128216与GSE138325可作为原始数据备用来源
