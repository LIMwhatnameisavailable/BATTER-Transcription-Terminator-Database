# 项目工作日志 (PROGRESS.md)

## 项目当前状态

已完成对 BATTER 论文（Table S1）全部 13 篇原始文献的完整筛查与数据验证。所有 13 篇文献的补充材料均包含可直接复用的终止子/TTS/TEP 基因组坐标表（A 类判定），相关 xlsx 文件已批量下载并完成内容交叉核查，13/13 验证通过。项目已从"信息核查阶段"进入**"数据格式标准化与数据库构建阶段"**。下一步工作：统一坐标体系（0-base/1-base、参考基因组版本对齐），制定字段命名规范，逐篇文献格式转换并入库。

---

## 2026-07-28

### MOESM1–3 补充材料解析
- 审查了 Jin et al. (Microbiome, 2026) 论文配套的 3 个补充材料文件：
  - **MOESM1_ESM.docx**（Supplementary Information）：解析了 Figures S1–S13 和 Tables S1–S8，确认 Table S1 为"Curated 3' ends mapping data"，涵盖 20 个物种/菌株的 22 条数据记录，来自 13 篇原始文献。该表是 BATTER 模型训练数据的基础起点。
  - **MOESM2_ESM.xlsx**（Dataset S1）：数据增强所用的基因簇（115 个）和 Rfam 家族（121 个）列表。
  - **MOESM3_ESM.xlsx**（Dataset S2）：BATTER 对 42,905 个 GEMs 细菌基因组的终止子预测结果汇总统计。
- 产出：`report_supplementary_review.md`

### Zenodo 仓库调查与 Table S1 文献数据获取信息报告
- 调查了 Zenodo 仓库（DOI: 10.5281/zenodo.16761763）内容，确认其包含：
  - BATTER 模型代码（v2→v3 有更新）
  - 模型训练数据（FASTA 序列）
  - 42,905 个基因组的预测结果（BED 坐标）
  - **不包含** 13 篇原始文献的实验验证终止子坐标数据
- 对 13 篇原始文献的 PubMed Data Availability 声明逐篇人工核查，整理出经核实的数据库登录号清单
- 发现并修正了此前 AI 生成报告中的多处编造错误（PMID 32694125、33947798、35491820、37402717 等登录号错误）
- 详见 `archive/supplementary_data1_raw_findings.md`（该步骤被后续核查更正，详见下文 2026-07-29 条目）
- 产出：`report_zenodo_and_sources.md`、`accession_list_verified.csv`

## 2026-07-29

### PMID 38030608 Supplementary Data 文件核查
- 最初下载并核查了 MOESM10 文件（`41467_2023_43534_MOESM10_ESM.zip`），发现该文件仅为论文图表源数据（Source Data.xlsx + 6 个 read start 文本文件），并非论文提到的"Supplementary Data 1 登录号清单"。
- 核实后更正为：论文的 Supplementary Data 1–5 对应 MOESM4–8 五个文件，而非 MOESM10。
- 旧报告（`supplementary_data1_raw_findings.md`）已移入 `archive/` 保留。

### 对 MOESM4–8 五个文件进行结构核查
- **MOESM4 (Supplementary Data 1)**：19 条外部复用文献登录号索引，涵盖 Listeria/Klebsiella/Salmonella/Shigella/ETEC/EPEC 等方法学验证数据，与 Table S1 的 13 篇文献无重叠。
- **MOESM5 (Supplementary Data 2)**：17 个子表，包含各物种/数据集的 3' 端终止子坐标数据。E. coli - Barsheshet 表恰好 1,486 行数据，对应论文声称的 1,486 个终止子。所有数据表均含 Chromosome/Strand/Start/End/Dominant/Signal 等完整坐标字段。
- **MOESM6 (Supplementary Data 3)**：LB/EG 条件下 RNAtag-seq 和 Term-seq 四组数据集的终止子鉴定结果，额外包含 RNA 二级结构自由能预测和 U-tract 序列信息。Summary 表（3,125 行）汇总了四组数据集的交集分析。
- **MOESM7 (Supplementary Data 4)**：3' UTR–CDS 表达分析，888 行数据，含异常值标记（Is outlier）和附近 TSS 位置。
- **MOESM8 (Supplementary Data 5)**：133 个 EPEC 条件特异性终止子候选（LB vs DMEM），含通读差异值。
- 产出：`supplementary_data_1to5_findings.md`

### 更新 accession_list_verified.csv 为清洁最终版
- 移除了所有修正痕迹标记，替换为对使用者有实际科学价值的 Notes 说明
- 更新了 PMID 33319794 Figshare 条目的 Notes（已确认为元数据摘要，非真实坐标数据）
- 更新了 PMID 38030608 相关行（E-MTAB-12429 添加 Notes，GitHub 行去除待核查标记）
- 新增一行记录 Supplementary Data 1（MOESM4）的核查结论

### 文件结构整理
- 将已被取代的 `supplementary_data1_raw_findings.md` 移入 `archive/`
- 从 `report_zenodo_and_sources.md` 中移除"版本与勘误说明"章节（内容已整合至本 PROGRESS.md）
- 更新 `README.md`，移除已解决的待办事项，补充最新进展
- 建立本工作日志 PROGRESS.md

### 13篇文献逐一分类核查（A/B/C判定）
- 针对全部13篇文献，采用"每篇文献单独开一个LLM对话，人工粘贴文献正文内容"的方式，判断产出数据类别：
  - **A类**（现成坐标可直接复用）：补充材料中直接提供处理好的终止子/TTS/TEP坐标表
  - **B类**（仅原始测序数据，需重新分析）
  - **C类**（信息不足）
- **判定结果：13/13 均为 A 类**，各篇补充材料均明确包含可下载的基因组坐标表
- 涉及 PMID：29606352、30517198、31555254、31594819、32694125、33319794、33947798、34054774、34874777、35491820、37402717、37096044、38030608

### 批量下载核心数据文件
- 针对13篇文献，逐一下载了 README 标注的核心补充材料数据文件（xlsx为主，部分含pdf说明文档）
- 建立"文献N-PMIDxxxxxxxx"格式的 13 个子目录，每个含 README.md + 对应数据文件

### README声明与实际下载文件交叉核查
- 用自动脚本 + 人工复核方式，对 13 个文献目录逐一核查"README 声明的完整文件清单"与"实际下载文件"的对应关系
- 逐一打开每个已下载的 xlsx 文件验证：
  - (a) 是否存在真实的基因组坐标字段（Position/Start-End/TSS/TTS等）
  - (b) 实际数据行数是否与论文正文声称的终止子/TTS/TEP 数量一致
- **核查结论：13/13 篇文献的核心坐标数据文件均验证通过**，字段完整、数量匹配
- 详见 `data_verification_report.md`