# Supplementary Data 1–5: 结构核查报告

> **来源论文**: PMID 38030608 (Bar et al., Nature Communications 2023, DOI: 10.1038/s41467-023-43534-2)  
> **核查日期**: 2026-07-29  
> **核查范围**: 5 个 Excel 文件的结构审阅（仅读取，不修改）

---

## 文件 1: `41467_2023_43534_MOESM4_ESM.xlsx`

### Sheet 数量：2

| Sheet 名称 | 行数 | 说明 |
|-----------|------|------|
| **Legends** | 24 行 | 字段说明（标题行 + 字段释义） |
| **Content** | 20 行 | 数据表（含表头行 1 行，数据 19 行） |

### Sheet: `Legends`
- 标题行（Row 0）：`Supplementary Data 1 - Previously published sequencing datasets that were analyzed by TRS`
- 列：`Header` / `Description`
- 逐一解释 Content 表中各列的涵义。

### Sheet: `Content`
**列名（11 列）**：
```
Analysis | Study | Accession | Accession link | Strain | Growth condition/phase | Sequencing methodology | SRA run identifiers | Reference sequence IDs | Annotations | Sheets in Supplementary Data 2
```

**重点标注：数据库登录号索引** ✅  
该表包含 `Accession`（BioProject ID）、`Accession link`（NCBI 超链接）、`SRA run identifiers` 等字段，完整记录了论文复用的所有外部测序数据集。

**内容概要**（19 条数据记录）：
- 记录了 5 条 E. coli RNAtag-seq 数据集（Barsheshet 2022, Melamed 2020, Adams 2021, Goldberger 2021, Kavita 2022）
- 1 条 E. coli Term-seq 数据集（Dar and Sorek 2018）
- 多种其他细菌数据集：*Listeria monocytogenes*（Dar 2016, Avican 2021）、*Klebsiella pneumoniae*、*Salmonella*、*Shigella flexneri*、ETEC、EPEC（LB/DMEM, Mizrahi）
- 每条记录包含 `Reference sequence IDs`（如 NC_000913.3、NZ_CP023861.1 等）
- 通过 `Sheets in Supplementary Data 2` 列指向 MOESM5 中的具体子表

---

## 文件 2: `41467_2023_43534_MOESM5_ESM.xlsx`

### Sheet 数量：17

| Sheet 名称 | 行数 | 说明 |
|-----------|------|------|
| **Legends** | 25 行 | 字段说明 |
| **E. coli - Barsheshet** | 1,487 行 | **数据行：1,486** — 对应论文中 1,486 个 3' 端终止子 |
| **E. coli - Dar and Sorek** | 1,466 行 | 含 Class/Related genes/Related IDs |
| **Listeria - Avican (RNAtag-seq)** | 1,179 行 | |
| **Listeria - Dar (term-seq)** | 1,093 行 | |
| **Shigella - Avican** | 1,676 行 | |
| **Salmonella - Avican** | 1,270 行 | |
| **Klebsiella - Avican** | 1,266 行 | |
| **ETEC - Avican** | 1,066 行 | |
| **EPEC - LB - Mizrahi** | 805 行 | |
| **EPEC - DMEM - Mizrahi** | 2,524 行 | |
| **E. coli - Kavita** | 882 行 | |
| **E. coli - Melamed** | 2,115 行 | |
| **E. coli - Goldberger** | 2,401 行 | |
| **E. coli - Bar** | 1,718 行 | |
| **E. coli - Adams (RNAtag-seq)** | 1,336 行 | |
| **E. coli - Adams (Term-seq)** | 743 行 | |

### Sheet: `Legends`
- 标题行：`Supplementary Data 2 - 3' termini determined by TRS for datasets analyzed in this study`
- 字段说明表（Header / Description）

### 数据表公共列（所有 E. coli 子表）
**列名**：`Chromosome | Strand | Start | End | Dominant | Signal | rep1 | rep2 | rep3`（部分表有额外列）

**重点标注：基因组坐标信息** ✅  
所有数据表均包含完整的基因组坐标字段：
- `Chromosome`：染色体/参考序列 ID（E. coli 为 `chr`，其他菌为具体 RefSeq ID 如 `NZ_CP023861.1`）
- `Strand`：正负链（`+` / `-`）
- `Start` / `End`：峰边界
- `Dominant`：峰内统计值最高的位置
- `Signal`：平均统计值 R_i
- `rep1`, `rep2`, `rep3`：各重复的 Bonferroni 校正 p 值

**部分子表含额外列**：
- `Genomic annotation` / `Class`：注释类型（Primary / Alternative primary / Distant primary / Internal / Antisense / IGR / 5' UTR 等）
- `Related genes`：关联基因名
- `Related IDs`：关联基因 ID（如 EG11277、G0-9561）

### 重点：E. coli - Barsheshet 表
- 1,486 行数据（不含表头），对应论文所述 **"E. coli K-12 MG1655 (LB, exponential phase) 鉴定出的 1,486 个 3' 端终止子坐标"**
- 列：`Chromosome | Strand | Start | End | Dominant | Signal | rep1 | rep2 | rep3`
- 无 `Genomic annotation` 列（与其他 E. coli 子表不同）

### 其他子表差异
- **E. coli - Dar and Sorek**：含 `Class` 列，`Related genes` 和 `Related IDs` 列
- **E. coli - Kavita / Adams**：仅 2 个重复列（`rep1`, `rep2`），无 `rep3`
- **非 E. coli 子表**：染色体列使用具体 RefSeq ID（如 `NZ_CP023861.1`、`NC_016810.1` 等）

---

## 文件 3: `41467_2023_43534_MOESM6_ESM.xlsx`

### Sheet 数量：6

| Sheet 名称 | 行数 | 说明 |
|-----------|------|------|
| **Legend** | 28 行 | 字段说明 |
| **LB RNAtag-seq** | 2,055 行 | LB 条件下 RNAtag-seq 鉴定的终止子 |
| **LB Term-seq** | 1,985 行 | LB 条件下 Term-seq 鉴定的终止子 |
| **EG RNAtag-seq** | 1,811 行 | EG（指数生长）条件下 RNAtag-seq |
| **EG Term-seq** | 1,886 行 | EG 条件下 Term-seq |
| **Summary** | 3,126 行 | 四组数据集的交集汇总 |

### Sheet: `Legend`
- 标题行：`Supplementary Data 3 - 3' termini identified by applying TRS to RNAtag-seq and term-seq data of the same RNA samples`
- 说明：该文件包含对同一 RNA 样本同时应用 RNAtag-seq 和 term-seq 后，由 TRS 鉴定的 3' 端终止子列表

### 四组数据表（LB RNAtag-seq / LB Term-seq / EG RNAtag-seq / EG Term-seq）
**列名（19 列）**：
```
Chromosome | Strand | Start | End | Dominant | Signal | Rank | [LB_1/LB_2/LB_3 或 EG_1/EG_2/EG_3] | Related IDs | Related genes | Genomic annotation | Fold seq | Fold | Free energy | U-tract seq | Max U-tract | Max nonconsecutive U-tract
```

**重点标注：基因组坐标 + 结构信息** ✅
- 与前两个文件一致的基因组坐标字段（Chromosome, Strand, Start, End, Dominant）
- 额外包含 **RNA 二级结构预测** 相关信息：
  - `Fold seq`：折叠序列
  - `Fold`：点括号结构注释
  - `Free energy`：自由能（kcal/mol，如 -13.2, -23.4 等）
  - `U-tract seq`：U 序列
  - `Max U-tract`：最大连续 U 长度（如 9, 6, 7 等）
  - `Max nonconsecutive U-tract`：最大非连续 U 长度

### Sheet: `Summary`
**列名（12 列）**：
```
Chromosome | Strand | Dominant | Genomic annotation | Related genes | Related IDs | Number of datasets | Identified in LB RNAtag-seq | Identified in EG RNAtag-seq | Identified in LB Term-seq | Identified in EG Term-seq | Annotated in EcoCyc
```

- 3,125 行数据（不含表头）
- 汇总每个终止子在四组数据集中是否被鉴定到（1/0 标记）
- `Annotated in EcoCyc`：是否已在 EcoCyc 数据库中注释（1/0）
- `Number of datasets`：在几组数据集中被鉴定（值范围 1–4）

---

## 文件 4: `41467_2023_43534_MOESM7_ESM.xlsx`

### Sheet 数量：2

| Sheet 名称 | 行数 | 说明 |
|-----------|------|------|
| **Legend** | 20 行 | 字段说明 |
| **Data** | 889 行 | 3' UTR–CDS 表达分析数据 |

### Sheet: `Legend`
- 标题行：`Supplementary Data 4 - 3' UTR – CDS expression analysis`
- 说明：该文件包含 3' UTR 与 CDS 表达水平的比较分析

### Sheet: `Data`
**列名（20 列）**：
```
Chromosome | Strand | Start | End | Dominant | Gene name | Genomic annotation of 3' terminus | CDS length | 3' UTR length | CDS library 1 | CDS library 2 | CDS rlibrary 3 | 3' UTR library 1 | 3' UTR librray 2 2 | 3' UTR library 3 | Is outlier library 1 | Is outlier librray 2 | Is outlier librray 3 | # of libs as outlier | Neraby TSS
```

**重点标注：基因组坐标 + 异常值标记** ✅
- 基因组坐标：`Chromosome | Strand | Start | End | Dominant`
- 基因信息：`Gene name`（基因名）、`CDS length`（CDS 长度）、`3' UTR length`（3' UTR 长度）
- 表达量：3 个重复的 CDS 和 3' UTR 文库 read 计数（`CDS library 1/2/3`, `3' UTR library 1/2/3`）
- **异常值标记**：`Is outlier library 1/2/3`（True/False）、`# of libs as outlier`（在几个文库中被标记为异常值）
- 前 12 行样例显示所有记录的 `# of libs as outlier` 均为 3（三个文库全部标记为异常值）
- `Neraby TSS`（附近转录起始位点，部分为 None 或分号分隔的多个位置）

**注意**：列名中存在拼写不一致：
- `CDS rlibrary 3`（应为 `CDS library 3`）
- `3' UTR librray 2 2`（应为 `3' UTR library 2`）
- `Is outlier librray 2`（应为 `Is outlier library 2`）
- `Neraby TSS`（应为 `Nearby TSS`）

888 行数据（不含表头），对应论文所述 **"38 个 3' UTR 来源转录本异常值候选"** 的扩展分析数据集。

---

## 文件 5: `41467_2023_43534_MOESM8_ESM.xlsx`

### Sheet 数量：2

| Sheet 名称 | 行数 | 说明 |
|-----------|------|------|
| **Legend** | 14 行 | 字段说明 |
| **Data** | 134 行 | EPEC 条件特异性终止子候选 |

### Sheet: `Legend`
- 标题行：`Supplementary Data 5 - EPEC condition-dependent changes in 3' termini`
- 说明：EPEC（肠致病性大肠杆菌）在不同生长条件下（LB vs DMEM）的 3' 端终止子变化

### Sheet: `Data`
**列名（9 列）**：
```
Chromosome | Strand | Position in LB | Position in DMEM | Readthrough difference | Absolute readthrough difference | Related genes | Genomic annotation | Notes
```

**重点标注：基因组坐标 + 条件特异性** ✅
- `Chromosome`：参考序列（样品为 `NC_011601`）
- `Strand`：正负链
- `Position in LB` / `Position in DMEM`：LB 和 DMEM 条件下的基因组位置
- `Readthrough difference`：通读差异值（范围约 -0.60 至 +0.72）
- `Absolute readthrough difference`：绝对差异值
- `Related genes`：关联基因名
- `Genomic annotation`：注释类型（`Internal` 或 `5' UTR`）
- `Notes`：附注（如 `"Perssumably ibpA 3' UTR"`，其中 `Perssumably` 疑为拼写错误）

133 行数据（不含表头），对应论文所述 **"EPEC 条件特异性终止子候选，133 个"** ✅

---

## 汇总对照表

| 文件 | 对应论文描述 | Sheet 数 | 数据行数 | 关键字段 |
|------|------------|---------|---------|---------|
| MOESM4 | Data 1: 外部数据库登录号清单 | 2 | 19 行 | Accession, Study, SRA, Strain |
| MOESM5 | Data 1-2: 1,486 个 E. coli 终止子 + 多物种终止子 | 17 | 最大 2,401 行 | Chromosome, Strand, Start, End, Dominant, Signal |
| MOESM6 | Data 3: 四组数据集（LB/EG, RNAtag-seq/term-seq） | 6 | 最大 3,125 行 | 同上 + Fold seq, Free energy, U-tract 等结构信息 |
| MOESM7 | Data 4: 3' UTR 异常值候选 | 2 | 888 行 | CDS/3' UTR 长度, 表达量, Is outlier 标记 |
| MOESM8 | Data 5: 133 个 EPEC 条件特异性终止子 | 2 | 133 行 | Position in LB/DMEM, Readthrough difference |

---

## 特别发现

### 1. 拼写/命名不一致（MOESM7）
- `CDS rlibrary 3` → 应为 `CDS library 3`
- `3' UTR librray 2 2` → 应为 `3' UTR library 2`
- `Is outlier librray 2` → 应为 `Is outlier library 2`
- `Neraby TSS` → 应为 `Nearby TSS`

### 2. 拼写不一致（MOESM8）
- Legend 中 `Readtrhough difference` → 应为 `Readthrough difference`（但 Data 表头正确）
- Legend 中 `Genomic annoation` → 应为 `Genomic annotation`（但 Data 表头正确）

### 3. 坐标字段全覆盖
5 个文件均包含可映射到基因组的坐标字段（Chromosome, Strand, Start/End 或 Position），可直接用于后续数据库导入。

### 4. 参考基因组对照
- E. coli 数据统一使用 `chr` 表示（对应 NC_000913.3）
- 其他菌种使用具体的 RefSeq ID（如 NZ_CP023861.1, NC_016810.1 等）
- EPEC 数据使用 `NC_011601`

### 5. 论文声称的 1,486 个终止子已确认
MOESM5 中 `E. coli - Barsheshet` 表恰好 1,486 行数据（不含表头），匹配论文正文描述。

### 6. EPEC 条件特异性 133 个终止子已确认
MOESM8 的 Data 表恰好 133 行数据（不含表头），匹配论文正文描述。

---

*报告结束。所有文件仅进行了结构审阅，未做数据清洗或修改。*