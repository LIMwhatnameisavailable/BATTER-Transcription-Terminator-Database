# BATTER 原始文献数据溯源与整理

## 任务背景

Jin, Cui, Liu et al. (Microbiome, 2026) 发表的 BATTER 工具用于预测细菌转录终止位点，其
Table S1 列出了 13 篇提供真实实验（Term-seq/Rend-seq/dRNA-seq等）验证数据的原始文献。
论文配套的 Zenodo 仓库（DOI: 10.5281/zenodo.16761763）仅包含模型代码、训练数据和预测
结果，不含这 13 篇文献的原始实验坐标数据。

## 任务目标

构建一个基于真实实验验证的细菌转录终止子数据库（及配套可视化网站），而非依赖模型预测
结果。

## 已完成工作

### Phase 1: 信息核查与数据获取（已完成 ✅）

- 排查 Zenodo 仓库内容，确认其数据类型（训练数据/预测结果），不可直接作为实验数据库来源
- 逐篇人工核查 13 篇原始文献的 PubMed Data Availability 声明，整理出经核实的数据库登录号清单（GEO/SRA/ENA/ArrayExpress等），产出 `accession_list_verified.csv`
- 核查 PMID 38030608 (Bar et al. 2023) 的 5 个 Supplementary Data 文件（MOESM4–8），确认结构
- 对 13 篇文献逐一做 A/B/C 分类判断（基于论文正文+补充材料文本），**全部 13/13 确认为 A 类**
- 批量下载核心数据文件，建立"文献N-PMIDxxxxxxxx"格式的 13 个子目录
- 完成 README 声明与实际文件的交叉核查，逐文件验证坐标字段与数据量，**13/13 验证通过**
- 产出文件：`data_verification_report.md`（完整核查报告）

## 当前状态

**项目已从信息核查阶段进入数据格式标准化与数据库构建阶段。**

所有 13 篇原始文献的终止子/TTS/TEP 坐标数据均已下载并完成内容验证，确认包含完整的基因组坐标字段（Position/Strand/Start-End等），可直接用于数据库构建，无需重新下载 FASTQ 或重跑分析 pipeline。

## 已验证的核心数据源

| PMID | 物种 | 核心坐标文件 | 数据规模 |
|------|------|-------------|----------|
| 29606352 | 4种细菌(Bsub/Ecol/Vnat/Ccre) | mmc3.xlsx | ~3500个终止子(4物种合计) |
| 30517198 | S. pneumoniae | ppat.1007461.s006.xlsx | ~1864个TTS |
| 31555254 | S. lividans | Table 6.XLSX | ~1640个TEP |
| 31594819 | P. aeruginosa | mbio.02253-19-st001.xlsx | ~804个关联TTS |
| 32694125 | Z. mobilis | msystems.00250-20-sd003.xlsx | ~2091个TTS |
| 33319794 | 7种Streptomyces | Dataset_figshare_2.xlsx | ~2027个TTS |
| 33947798 | S. clavuligerus | msystems.01013-20-sd001.xlsx | ~1427个TEP |
| 34054774 | Synechocystis PCC 7338 | Data Sheet 2.XLSX | ~487个TEP |
| 34874777 | Synechocystis PCC 6803 | msystems.00943-21-st005.xlsx | ~784个TEP |
| 35491820 | D. dadantii | mbio.00524-22-st002.xlsx | 3564+5851+1165个TTS(三套体系) |
| 37402717 | B. burgdorferi | MOESM4_ESM.xlsx | 1333+944个3'末端 |
| 37096044 | M. tuberculosis | mmc4.xlsx | ~2567个TTS |
| 38030608 | E. coli+6种病原菌 | MOESM5+MOESM6 | 多物种合计数千个终止子 |

## 目录结构

```
BATTER数据整理/
├── 文献1-PMID29606352/        # 数据目录（含 README.md + 核心xlsx文件）
├── 文献2-PMID30517198/
├── 文献3-PMID31555254/
│   ...                        # 其他文献目录结构相同
├── 文献13-PMID38030608/
├── archive/                   # 历史过程记录（已整合的旧报告）
├── accession_list_verified.csv # 经核实的登录号总表
├── data_verification_report.md # 13篇文献交叉核查报告
├── PROGRESS.md                # 工作日志
└── README.md                  # 本文件
```

## 下一步计划

1. **制定统一数据标准**: 确定坐标体系（0-base/1-base）、参考基因组版本对齐策略、字段命名规范
2. **逐篇格式转换**: 将 13 篇文献的原始 xlsx 数据逐篇转换为统一格式（BED/GFF），保留并标准化元数据（物种、实验条件、置信度、终止子类型等）
3. **构建结构化数据库**: 整合全部转换后的数据，建立索引（按物种、PMID、终止子类型等）
4. **搭建可视化/检索网站**: 基于数据库开发可检索的 Web 界面
