# BTED 外部来源端点表构建汇总报告（Fuchs 2021 / Cascino 2026 / TERMITe 8 来源）

生成日期：2026-08-10
范围：外部来源端点级数据表构建全部产物。这是项目最终发布与论文写作的核心产出，端点级容错要求高于此前任何一步。
本文件为本次构建的完整清单、行数核对、排除去向、evidence_class 枚举合规性说明。

---

## 一、文件清单（draft/endpoints_output/ 全部 18 个文件）

### 1. 端点表（12 个，24 列，均符合 external_literature_endpoint_schema.tsv）

| 文件 | source_id | 批次 | 行数 |
|---|---|---|---|
| `BTED_EXT_2026_001_fuchs2021_endpoints.tsv` | BTED_EXT_2026_001 | Fuchs 2021 | 1967 |
| `BTED_EXT_2026_002_cascino_synwt_endpoints.tsv` | BTED_EXT_2026_002 | Cascino 2026 | 474 |
| `BTED_EXT_2026_003_cascino_mfdrep1_endpoints.tsv` | BTED_EXT_2026_003 | Cascino 2026 | 384 |
| `BTED_EXT_2026_004_cascino_mfdrep2_endpoints.tsv` | BTED_EXT_2026_004 | Cascino 2026 | 399 |
| `BTED_EXT_2026_006_termite_bacillus_subtilis_a_endpoints.tsv` | BTED_EXT_2026_006 | TERMITe | 630 |
| `BTED_EXT_2026_007_termite_bacillus_subtilis_b_endpoints.tsv` | BTED_EXT_2026_007 | TERMITe | 1153 |
| `BTED_EXT_2026_008_termite_bacillus_subtilis_c_endpoints.tsv` | BTED_EXT_2026_008 | TERMITe | 974 |
| `BTED_EXT_2026_009_termite_enterococcus_faecalis_endpoints.tsv` | BTED_EXT_2026_009 | TERMITe | 779 |
| `BTED_EXT_2026_010_termite_listeria_monocytogenes_endpoints.tsv` | BTED_EXT_2026_010 | TERMITe | 860 |
| `BTED_EXT_2026_011_termite_bacillus_subtilis_d_endpoints.tsv` | BTED_EXT_2026_011 | TERMITe | 1198 |
| `BTED_EXT_2026_012_termite_escherichia_coli_b_endpoints.tsv` | BTED_EXT_2026_012 | TERMITe | 949 |
| `BTED_EXT_2026_013_termite_escherichia_coli_a_endpoints.tsv` | BTED_EXT_2026_013 | TERMITe | 686 |

### 2. 构建脚本（3 个，可复现）

| 文件 | 批次 |
|---|---|
| `build_fuchs_endpoints.py` | Fuchs 2021 |
| `build_cascino_endpoints.py` | Cascino 2026 |
| `build_termite_endpoints.py` | TERMITe 8 来源 |

### 3. 辅助文件（3 个）

| 文件 | 说明 |
|---|---|
| `fuchs_2021_unresolved_strand_75rows.tsv` | Fuchs 2021 strand 无法确定（75 行），保留 5 列可回溯 |
| `cascino_exclusion_report.txt` | Cascino 2026 每 sheet 排除明细与入表/排除校验 |
| `termite_endpoints_summary.txt` | TERMITe 8 来源每源原始行数 / coord_valid / 最终行数 / POT≠summit |

---

## 二、三批端点表行数核对

### 2.1 各批次总览

| 批次 | source 数 | 原始数据行 | 排除 | 端点表行数 | 排除去向 |
|---|---|---|---|---|---|
| Fuchs 2021 | 1 | 2042 | 75 | **1967** | `fuchs_2021_unresolved_strand_75rows.tsv`（strand 无法确定） |
| Cascino 2026 | 3 | 3797 | 2540 | **1257** | `cascino_exclusion_report.txt`（三档：完全排除 / 次级置信度纳入 / 最高置信度纳入） |
| TERMITe 8 | 8 | 7229 | 0 | **7229** | 无（coord_valid 全 True，无排除） |
| **合计** | **12** | **13068** | **2615** | **10453** | |

### 2.2 Fuchs 2021（BTED_EXT_2026_001）

- 数据来源：`new/PMID 34131082/pnas.2103579118.sd04.xlsx`（Dataset S4, TTSs sheet，2042 行）
- 链向推断：`draft/fuchs_strand_inference_result.tsv`（2042 行，与 S4 逐行关联校验通过）
- 主表：confidence 高(1815) + 低(152) = **1967 行**，链向分布 +969 / −998
- 排除：confidence 无法确定 **75 行** → `fuchs_2021_unresolved_strand_75rows.tsv`（locus_tag / tts_position / gff_matched / confidence / note）
- **校验：1967 + 75 = 2042 ✓**
- 坐标：作者 TTS 为 1-based；biological=tts_position；bed_start=tts−1；bed_end=tts（单碱基 BED）
- signal_or_score=NA：Dataset S4 folding sheet 提供折叠能量(kcal/mol)而非峰信号值，且仅覆盖 2011/2042 个 TTS

### 2.3 Cascino 2026（BTED_EXT_2026_002/003/004）

- 数据来源：`new/PMID 42148773/msystems.01581-25-s0003.xlsx`（Table S1，三个 Syn sheet）
- **2026-08-10 重分级为两级置信度结构**（依据 s0002.docx P32/P34/P77 作者原文核实，详见 `cascino_reclassification_changelog.md`）：
  - **最高置信度**：`gene_term=="defined end"`（1061 行），evidence_class=`author_called_endpoint`
  - **次级置信度**：`diffuse end (diffuse peak)`（164 行）与 `unclear`（gene_peak_posn 有值的 32 行），共 196 行，evidence_class=`called_endpoint`；坐标同样取 `gene_peak_posn`
  - **完全排除**：`TU` / `diffuse end (no peak found)` / `unclear`（gene_peak_posn 为空的 14 行），共 2540 行
- 坐标：`gene_peak_posn`（CP000100.1 1-based）；bed_start=pos−1；bed_end=pos
- signal_or_score=gene_peak_RT（作者给出的 peak 处 readthrough 分数）；空值按数据字段字典规则填 NA
- 关联基因：从 notes 列解析 locus_tag

| sheet | source_id | 总行数 | 最高置信度(defined end) | 次级置信度(diffuse peak+unclear) | 完全排除 | 端点表 |
|---|---|---|---|---|---|---|
| Syn_WT | 002 | 1295 | 388 | 86（diffuse peak 75 + unclear 11） | 821（TU 544 + 无峰 274 + unclear 3） | 474 |
| Syn_∆mfd_rep1 | 003 | 1238 | 331 | 53（diffuse peak 41 + unclear 12） | 854（TU 582 + 无峰 266 + unclear 6） | 384 |
| Syn_∆mfd_rep2 | 004 | 1264 | 342 | 57（diffuse peak 48 + unclear 9） | 865（TU 572 + 无峰 288 + unclear 5） | 399 |
| 合计 | | 3797 | 1061 | 196 | 2540 | **1257** |

- 每 sheet"最高 + 次级 + 排除 = 总行数"校验通过（1295/1238/1264 ✓）；三档逐类明细见 `cascino_exclusion_report.txt`
- 注意：登记表 002 的 endpoint_source_file 原记录为 s0004 (Table S2)；本次按任务指令用 s0003 Table S1 Syn_WT sheet 建表，已在端点表 note 列标注该来源差异

### 2.4 TERMITe 8 来源（BTED_EXT_2026_006~013）

- 数据来源：`TERMITe/data/termite_parsed.csv`（37 列）；参考序列 chrom 标签取自 `TERMITe/tracks/<dataset>/` BED
- 规则：仅 `coord_valid=True`（全库均 True）；坐标=`summit_coordinate`（1-based）；bed_start=summit−1；bed_end=summit
- signal_or_score=termite_score；author_category="TERMITe intrinsic terminator"；关联基因从 upstream_gene 提取
- 每源"原始行数 = coord_valid=True = 最终端点行数"校验通过（8/8 ✓）

| source_id | dataset_id | 行数 | POT≠summit |
|---|---|---|---|
| 006 | Bacillus_subtilis_a | 630 | 0 |
| 007 | Bacillus_subtilis_b | 1153 | 1 |
| 008 | Bacillus_subtilis_c | 974 | 0 |
| 009 | Enterococcus_faecalis | 779 | 1 |
| 010 | Listeria_monocytogenes | 860 | 1 |
| 011 | Bacillus_subtilis_d | 1198 | 0 |
| 012 | Escherichia_coli_b | 949 | 1 |
| 013 | Escherichia_coli_a | 686 | 0 |
| 合计 | | 7229 | 4 |

- POT≠summit 共 4 行（全为负链，差 1bp）：009 那行（NZ_CP008816.1:1636266-1636270, IDR=0.002）正是登记表 coordinate_convention 已解释的"唯一不一致行，低置信边界峰，不影响坐标归属"；007/010/012 各 1 行 IDR 较低。4 行均按任务规则坐标取 summit_coordinate，note 列逐行标注
- **Listeria (010) 措辞专项检查**：860 行全部为 Group 2（流水线代码推定成立）措辞，无一误用 verified 组 ✓

---

## 三、排除记录去向

| 批次 | 排除行数 | 去向 | 可回溯性 |
|---|---|---|---|
| Fuchs 2021 | 75 | `fuchs_2021_unresolved_strand_75rows.tsv` | 每行含 locus_tag / tts_position / gff_matched / confidence / note |
| Cascino 2026 | 2540 | `cascino_exclusion_report.txt`（三档统计明细） | 排除行未复制原始数据；可在源表 s0003.xlsx 按 sheet + gene_term 列精确复现每行 |
| TERMITe 8 | 0 | 无 | — |

说明：Cascino 排除行未单独落文件保存原始行，因源表结构简单（gene_term 列即分类依据），exclusion report 已给出每 sheet 三档计数（最高置信度 / 次级置信度 / 完全排除）及完全排除的类别明细，排除行可在源文件按 sheet + gene_term 完全复现。若需逐行保留，可后续补充。

---

## 四、evidence_class 使用情况与字典枚举合规性

### 4.1 端点表 evidence_class 实际取值

| evidence_class | 使用 source | 行数 | 是否在字典端点表枚举 |
|---|---|---|---|
| `author_called_endpoint` | 001, 002, 003, 004 | 3028 | ✅ 在（字典：`author_called_endpoint`） |
| `called_endpoint` | 002, 003, 004 | 196 | ✅ 在（字典：`called_endpoint`；Cascino 次级置信度层使用） |
| `algorithm_called_endpoint` | 006–013 | 7229 | ⚠️ **不在**当前枚举，属待确认提案 |

注：`called_endpoint` 是数据字段字典_v0.1.md 端点表 `evidence_class` 枚举中**已有的现成枚举值**，非新提案；由 Cascino 2026 次级置信度层（196 行）新增使用，与 006–013 使用的 `algorithm_called_endpoint`（提案二待确认状态）性质不同。

### 4.2 algorithm_called_endpoint 的字典状态

- 当前字典（`数据字段字典_v0.1.md`）端点表 `evidence_class` 枚举：`author_called_endpoint` / `called_endpoint` / `observed_signal` / `curated_record` / `author_integrated_mixed_evidence` / `prediction_only`（后两类仅内部审计）
- 来源登记表 `primary_evidence_class` 枚举：`author_called_endpoint` / `called_endpoint` / `observed_signal`
- **`algorithm_called_endpoint` 均不在二者当前枚举中**，但：
  - `draft/dictionary_patch_proposal.md` **提案二** 建议来源表 `primary_evidence_class` 新增 `algorithm_called_endpoint`（TERMITe 8 新来源触发）；
  - 提案二第 4 节明确建议端点表 `evidence_class` **同步新增**同一值，理由："否则来源表标 algorithm_called_endpoint、端点表无对应枚举会产生口径断裂"。
- 本次端点表按提案二建议使用 `algorithm_called_endpoint`，**待维护者确认**后方可视为正式枚举值。发布前需在文档中落实提案二（来源表 + 端点表 + 证据分层文档同步），或回退为 `called_endpoint` 并在 note 说明。

### 4.3 关联的字典提案

- `dictionary_patch_proposal.md` 提案一：来源表 `processing_status` 新增 `excluded_duplicate`（用于 BTED_EXT_2026_005 重复留痕行）。本次端点表构建不涉及 005，不受影响。
- 提案二：`primary_evidence_class`（来源表）与 `evidence_class`（端点表）新增 `algorithm_called_endpoint`。本次 TERMITe 8 来源端点表依赖此提案。

---

## 五、质控与坐标体系说明

### 5.1 qc_status

- 全部 10453 条端点 qc_status = `pass`（字典枚举：pass / to_review / blocked）
- Fuchs low-confidence 行（152）与 Cascino/TERMITe 各来源均按坐标级校验通过，链向来源与坐标来源已在 note 注明

### 5.2 坐标体系

| 批次 | 作者坐标 | biological_coordinate_1based | bed_start | bed_end | 验证 |
|---|---|---|---|---|---|
| Fuchs | TTS 1-based (dnaA Start=1) | TTS 位点 | TTS−1 | TTS | 坐标直接取自 S4 TTS 列 |
| Cascino | gene_peak_posn 1-based | gene_peak_posn | pos−1 | pos | 与 Table S2(s0004) 已序列实证坐标交叉验证（Syn_WT 386/386 精确一致等） |
| TERMITe | summit 1-based | summit_coordinate | summit−1 | summit | 四项独立验证（009/013）或流水线推定（其余 6 源）；BED tracks chrom 标签与实际 accession 一致 |

### 5.3 三批端点表列数与 BED 换算

- 12 个端点表均 24 列、列顺序与 schema 一致
- BED 换算错误行：Fuchs 0 / Cascino 0 / TERMITe 0
- strand 取值：全部 {+, −}

---

## 六、待处理/遗留事项

1. **字典提案确认**：`algorithm_called_endpoint`（提案二）需维护者确认，并同步更新字典、证据分层文档、SOP（见提案二第 8 节）。确认前 TERMITe 端点表 evidence_class 视为"提案中"状态。
2. **Fuchs unresolved 75 行**：strand 无法确定，已单独留存待人工核查（可结合 GFF 特征补链向）。
3. **Cascino 排除行未逐行落文件**：如需逐行可回溯的排除记录，可补充生成（见第三节说明）。
4. **TERMITe 4 行 POT≠summit**：坐标已按规则取 summit_coordinate 并在 note 标注；009 行为登记表已解释的低置信边界峰，其余 3 行建议后续人工复核。
5. **source 级状态**：12 个 source 在来源登记表中均仍为 `to_review`，待端点表发布流程完成后更新。
