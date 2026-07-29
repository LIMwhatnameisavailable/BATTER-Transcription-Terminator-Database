# 文献6 — PMID 33319794

**Genome-scale determination of 5´ and 3´ boundaries of RNA transcripts in Streptomyces genomes**  
Lee et al. (2020), *Sci Data*, 7(1):436. DOI: 10.1038/s41597-020-00775-w  
7种 Streptomyces 物种的 dRNA-seq/Term-seq/RNA-seq 数据，登录号涵盖 SRA 和 ENA（详见 accession_list_verified.csv）。

文献核查报告
物种: Streptomyces属（7个物种：S. avermitilis, S. clavuligerus, S. coelicolor, S. griseus, S. lividans, S. tsukubaensis, S. venezuelae）
期刊/年份: Scientific Data / 2020

分类结论: A类
分类依据: 正文Data Records部分明确写道"The predicted TSSs and TTSs along with the utilized python scripts were deposited in Figshare"，且Technical Validation部分重复强调"The determined TSS and TTS information and smBGC information are available at Figshare"。TTS（转录终止位点）坐标即为终止子分析所需的核心数据，作者明确说明这是已计算好的位置信息（而非仅代码或原始reads），因此可判定为现成坐标可直接复用。

已确认的登录号清单:
- NCBI SRA: SRP158023 - dRNA-Seq/RNA-Seq原始reads(S. avermitilis) - 仅原始测序数据
- NCBI SRA: SRP188290 - dRNA-Seq/RNA-Seq原始reads(S. clavuligerus) - 仅原始测序数据
- NCBI SRA: SRP103795 - dRNA-Seq/RNA-Seq原始reads(S. tsukubaensis) - 仅原始测序数据
- NCBI SRA: SRP058830 - RNA-Seq原始reads(S. coelicolor) - 仅原始测序数据
- NCBI SRA: SRX6937123 / SRX6937124 - Term-Seq原始reads(S. clavuligerus) - 仅原始测序数据
- ENA: PRJEB40918 - dRNA-Seq原始reads(S. griseus) - 仅原始测序数据
- ENA: PRJEB31507 - dRNA-Seq/RNA-Seq原始reads(S. lividans) - 仅原始测序数据
- ENA: PRJEB36379 - dRNA-Seq/Term-Seq原始reads(S. tsukubaensis, S. venezuelae) - 仅原始测序数据
- ENA: PRJEB34219 - RNA-Seq原始reads(S. venezuelae) - 仅原始测序数据
- Figshare: 10.6084/m9.figshare.13259393 - 机器可读元数据文件(ISA-Tab模板，Scientific Data标准附件) - 元数据摘要
- Figshare: 10.6084/m9.figshare.c.5044730 - 【关键】预测的TSS/TTS坐标数据 + Python分析脚本 + smBGC信息摘要 + anti-rRNA oligo组成 - 这是实际数据载体，非单纯元数据

现成坐标数据线索（如为A类，说明具体线索）:
- 数据位置: Figshare collection (DOI: 10.6084/m9.figshare.c.5044730)，正文引用编号为参考文献[30]
- 数据字段: 原文未逐字列出字段名，但明确说明内容为"predicted TSSs and TTSs"（即转录起始/终止位点坐标），结合Methods中z-score算法描述，推断坐标应包含物种/染色体位置(position)、方向(strand)及z-score值等信息
- 覆盖范围: 7个Streptomyces物种，平均每物种约525个TSS、1285个TTS(注：约7-8%位于smBGC区域内)；每物种四个生长阶段(E/T/L/S)生物学重复数据汇总后的终点位置

第三方平台内容判断（如涉及Figshare/Zenodo/GitHub等）:
- 平台: Figshare（两个不同DOI）
- 判断: 
  1) 10.6084/m9.figshare.13259393 → 元数据摘要（Scientific Data期刊标准的"machine-accessible metadata file"模板，通常仅含描述性元数据，不含具体坐标）
  2) 10.6084/m9.figshare.c.5044730 → 真实坐标数据（正文明确指出此处包含predicted TSS/TTS position数据本体，以及配套Python脚本、smBGC摘要表、oligo序列表）
- 依据: 正文两次重复强调"TSS and TTS information...available at Figshare"，且该表述独立于对python脚本的描述（"along with the utilized python scripts"），说明TSS/TTS坐标是与脚本并列的、明确存在的实体文件，而非脚本的运行结果占位说明

待人工确认事项:
- 需下载Figshare collection (10.6084/m9.figshare.c.5044730) 中的具体文件，确认TSS/TTS坐标表的准确字段名（是否含Chromosome/Strand/Position/Species/GrowthPhase等）以及文件格式（CSV/TXT/Excel等）
- 需确认TTS坐标是否已包含"z-score"筛选后的最终结果，还是原始候选位点列表（需要进一步筛选转录终止子的严格定义，如是否为rho-independent终止子的具体序列范围，还是仅为3'端断点position）
- 需确认该坐标表是否已按不同物种、不同生长阶段分别列出，便于后续按物种拆分构建终止子数据库

建议后续动作:
- 优先下载Figshare collection (10.6084/m9.figshare.c.5044730) 中的TSS/TTS坐标文件，若字段完整（含物种、染色体位置、链方向），可直接提取TTS部分用于构建终止子数据库，无需重新下载FASTQ或重跑pipeline
- 若Figshare文件中TTS仅为单碱基断点位置而非完整终止子区域，需结合原文Methods中z-score方法说明，自行定义上下游延伸窗口以匹配目标数据库对"终止子坐标"的格式要求
