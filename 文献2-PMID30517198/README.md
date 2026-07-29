# 文献2 — PMID 30517198

**The Transcriptional landscape of Streptococcus pneumoniae TIGR4 reveals a complex operon architecture and abundant riboregulation**  
Warrier et al. (2018), *PLoS Pathog*, 14(12):e1007461. DOI: 10.1371/journal.ppat.1007461  
Term-seq 数据：SRA SRP136114（1,864个高置信度TTS，790个高置信度TSS）。

文献核查报告
物种: Streptococcus pneumoniae TIGR4
期刊/年份: PLoS Pathogens / 2018

分类结论: A类
分类依据: 正文Supporting Information部分明确说明S2 Table为"List of all the transcription termination sites (TTSs) identified from term-seq"，包含1864个TTS的position（坐标）、coverage、3'-UTR长度、茎环结构预测及上游uridine数量等已处理字段，属于可直接复用的现成终止子坐标表，无需重新下载FASTQ跑pipeline。

已确认的登录号清单:
- SRA: SRP136114 - 原始测序reads（RNA-Seq、term-seq、5'end-Seq） - Data Availability声明中提供，为原始数据登录号，非坐标表
- GenBank: NC_003028.3 - 参考基因组序列（TIGR4） - 用于比对的参考基因组，非实验产出坐标

现成坐标数据线索（如为A类，说明具体线索）:
- 数据位置: Supplementary S2 Table（TTS坐标表，最相关）；同时S1 Table为TSS坐标表，S4 Table为5'-UTR候选调控元件（含early TTS）坐标表
- 数据字段: 明确提及的字段包括——position（位点坐标）、coverage（覆盖度）、3'-UTR length（3'非翻译区长度）、predicted stem-loop structure（茎环结构预测）、number of uridines upstream（上游尿苷数）。S1 Table还包含Processed/unprocessed ratio、5'-UTR length、intergenic/CDS-internal标注
- 覆盖范围: S. pneumoniae TIGR4单一菌株，term-seq数据来自early-log/mid-log期、±万古霉素处理条件下的合并（pooled）样本，共识别1864个高置信度TTS

第三方平台内容判断（如涉及Figshare/Zenodo/GitHub等）:
- 平台: GitHub (https://github.com/nikhilram/T4pipeline)
- 判断: 代码（附带track文件用于可视化）
- 依据: 原文明确描述为"modified perl scripts, sample input files, and the track files for visualization"，属于分析流程代码与可视化辅助文件，并非终止子坐标的主要来源；坐标数据的权威来源仍是Supplementary S2 Table

待人工确认事项:
- 需下载S2 Table（XLSX格式）原文件，核实具体列名、坐标是基于哪个坐标系（1-based/0-based）、以及Chromosome/Strand字段是否显式列出（正文描述中未明确提及是否有单独的Strand列，但因为TIGR4为单染色体基因组且term-seq方法通常按链区分，需核对原表格式细节）
- GitHub仓库中的track文件是否也包含可直接使用的坐标（BED/GFF格式），可作为S2 Table之外的备选/交叉验证来源

建议后续动作:
- 可直接下载Supplementary S2 Table（TIF/XLSX），核对字段名后进行格式转换（如统一为Chromosome/Strand/Start/End标准格式）即可纳入终止子数据库构建流程；SRP136114中的原始reads仅作为潜在的重新验证或跨条件分析的补充数据源，非本次数据库构建所必需。
