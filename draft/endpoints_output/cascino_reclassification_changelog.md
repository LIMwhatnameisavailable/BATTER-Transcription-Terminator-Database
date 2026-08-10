# Cascino 2026 端点表重分级变更说明（两级置信度）

生成日期：2026-08-10
涉及文件（`draft/endpoints_output/`）：
- `BTED_EXT_2026_002_cascino_synwt_endpoints.tsv`
- `BTED_EXT_2026_003_cascino_mfdrep1_endpoints.tsv`
- `BTED_EXT_2026_004_cascino_mfdrep2_endpoints.tsv`
- `cascino_exclusion_report.txt`
- `build_cascino_endpoints.py`

---

## 一、为什么改：依据 s0002.docx 作者原文定义

作者对相关分类术语的原始定义（`new/PMID 42148773/msystems.01581-25-s0002.docx`，Supplementary Methods）：

**P32（defined / diffuse peak / undetermined 三者核心定义）：**
> "If a candidate defined end was found, a secondary search was performed for any additional 3′ peaks (with any degree of readthrough) between the gene stop codon and candidate defined end. As such additional peaks may represent alternate transcript ends, **the end type was recoded to be a "diffuse peak" if additional 3′ peaks were found.** In Figs. 1, 2, 4, and 5, the diffuse peaks were counted as diffuse ends. If no additional 3′ peaks were found, an end type of "defined" was assigned to the gene. In some cases, transcription of a gene ended with a 3′ peak, but readthrough could not be defined due to a downstream 5′ peak in close proximity. **These genes were classified as having an "undetermined" end type.**"

**P34（diffuse end — 无峰情形）：**
> "If no defined end was found, a diffuse end type was assigned if the read density dropped by at least 3.5-fold between the end of the gene (30-105 bp upstream of the stop codon) and the downstream window. The downstream edge of the window was then recorded as the diffuse end position."

**P77（diffuse peak = 含多个 3′ 峰的 diffuse end）：**
> "**Diffuse ends with multiple 3′ peaks (diffuse peaks, n=75)** were excluded from this analysis."

**作者定义的事实推论：**

| 分类 | 作者定义 | 是否有真实 3′ 峰证据 | 本次处理 |
|---|---|---|---|
| `defined end` | 检测到单个候选 3′ 峰（readthrough < 0.5），无额外峰（P28/P32） | 有（单一峰，无歧义） | **最高置信度纳入**，不变 |
| `diffuse end (diffuse peak)` | 先检测到候选 defined end 峰，又在上游发现额外 3′ 峰，重编码为 diffuse peak（P32/P77） | 有（存在真实离散 3′ 峰观测，仅多个候选位点、归属有歧义） | **次级置信度纳入**（原误排除） |
| `unclear`（=作者 undetermined） | 检测到 3′ 峰，但下游 5′ 峰邻近干扰导致 readthrough 无法计算（P32） | 有（峰位置本身有效） | **次级置信度纳入**（原误排除） |
| `diffuse end (no peak found)` | 无离散 3′ 峰，仅覆盖度下降 ≥3.5 倍（P34） | 无（无峰，证据类型与 defined end 不同） | 完全排除，不变 |
| `TU` | 未检测到转录末端证据（TU-internal，P36） | 无 | 完全排除，不变 |

**关键结论：** `diffuse end (diffuse peak)` 与 `unclear` 两类此前被当作"无峰/非终止信号"完全排除，但作者原文明确这两类**都存在真实的 3′ 峰观测证据**，只是置信度低于单一明确峰位的 `defined end`。为不丢失真实观测数据，本次将二者纳入端点表并标记为**次级置信度**，与最高置信度的 `defined end` 明确区分。

---

## 二、改之前 vs 改之后：三个 sheet 端点表行数对比

| sheet | source_id | 改前端点行数 | 改后端点行数 | 最高置信度（defined end） | 次级置信度 | 完全排除 |
|---|---|---|---|---|---|---|
| Syn_WT | 002 | 388 | **474** | 388 | 86 | 821 |
| Syn_∆mfd_rep1 | 003 | 331 | **384** | 331 | 53 | 854 |
| Syn_∆mfd_rep2 | 004 | 342 | **399** | 342 | 57 | 865 |
| **合计** | | **1061** | **1257** | **1061** | **196** | **2540** |

- 改前 = 仅 `gene_term=="defined end"` 入表（1061 行）。
- 改后 = defined end（1061）+ 次级置信度（196 行，diffuse peak 164 + unclear 有峰 32）= **1257 行**。
- 三档校验：每 sheet 最高 + 次级 + 完全排除 = 该 sheet 总行数（1295 / 1238 / 1264），全部通过；总计 1061 + 196 + 2540 = **3797** = 三 sheet 总行数之和 ✓。

---

## 三、新增的 196 行明细（可在原表精确查回）

新增行全部来自次级置信度层，坐标为 `gene_peak_posn`（原表该列即实际峰位数值，直接复用，无额外计算）。每个 sheet 中可按「sheet 名 + gene_term 取值 + 行数」在原文件 `new/PMID 42148773/msystems.01581-25-s0003.xlsx` 精确复现：

| sheet | 次级置信度来源 | 行数 | 原表定位方式 |
|---|---|---|---|
| Syn_WT | `diffuse end (diffuse peak)` | 75 | sheet Syn_WT，gene_term 列 = `diffuse end (diffuse peak)` |
| Syn_WT | `unclear`（gene_peak_posn 有值） | 11 | sheet Syn_WT，gene_term 列 = `unclear` 且 gene_peak_posn 非空 |
| Syn_∆mfd_rep1 | `diffuse end (diffuse peak)` | 41 | sheet Syn_∆mfd_rep1，gene_term 列 = `diffuse end (diffuse peak)` |
| Syn_∆mfd_rep1 | `unclear`（gene_peak_posn 有值） | 12 | sheet Syn_∆mfd_rep1，gene_term 列 = `unclear` 且 gene_peak_posn 非空 |
| Syn_∆mfd_rep2 | `diffuse end (diffuse peak)` | 48 | sheet Syn_∆mfd_rep2，gene_term 列 = `diffuse end (diffuse peak)` |
| Syn_∆mfd_rep2 | `unclear`（gene_peak_posn 有值） | 9 | sheet Syn_∆mfd_rep2，gene_term 列 = `unclear` 且 gene_peak_posn 非空 |
| **合计** | | **196** | |

> 说明：`unclear` 无 `gene_peak_posn` 的行（Syn_WT 3 / rep1 6 / rep2 5，共 14 行）因无峰位坐标可复用，经 2026-08-10 人工决策**归入完全排除档**（见第四节）。

逐行精确查回：每张端点表 `original_row_reference` 列给出 `msystems.01581-25-s0003.xlsx (Table S1, sheet <sheet>, row <row>)`，`associated_gene_or_locus` 给出 locus_tag，可直接定位到原表对应行。

---

## 四、决策记录

1. **2026-08-10 作者定义核实**：依据 s0002.docx P32/P34/P77 原文，确认 `diffuse end (diffuse peak)` 与 `unclear` 存在真实 3′ 峰证据，此前误排除 → 决定重分级纳入。
2. **2026-08-10 人工决策**：`unclear` 中 `gene_peak_posn` 为空的 14 行（Syn_WT 3 / rep1 6 / rep2 5）无峰位坐标可用，经确认**不纳入端点表**，归入完全排除档（排除报告中对 `unclear` 的计数为 3 / 6 / 5）。
3. **evidence_class 选择**：次级置信度层使用 `called_endpoint`（数据字段字典_v0.1.md 第 54 行端点表枚举 `author_called_endpoint` / `called_endpoint` / `observed_signal` / `curated_record` / `author_integrated_mixed_evidence` / `prediction_only` 中，比最高层 `author_called_endpoint` 低一档的现成枚举；证据分层与发布边界.md 六层定义：`called_endpoint` = 按固定规则从信号调用的候选端点）。**未发明新枚举值。**
4. **signal_or_score 空值**：`diffuse peak` 行中有 2 行 `gene_peak_RT` 为空（Syn_WT：Synpcc7942_0988、Synpcc7942_2264），`unclear` 行 `gene_peak_RT` 全部为空。按数据字段字典_v0.1.md 通用约定（"缺失信息一律填 `NA`，不留空、不编造"）→ 统一填 `NA`。
5. **end_id 序号**：端点表行序按原表数据行顺序排列（defined end 与次级置信度行混合按源表顺序），序号连续，无重复。

---

## 五、未变更部分

- `TU` / `diffuse end (no peak found)`：继续完全排除，不入端点表（无终止信号 / 无离散 3′ 峰）。
- Fuchs 2021、TERMITe 8 来源的所有端点表与脚本：本次未触碰。
- 未执行任何 git 操作。

---

## 六、遗留事项

- `README_endpoints_build.md` 中 Cascino 部分的行数（1061 / 388 / 331 / 342 及 exclusion 描述）基于改动前的单级结构，本次重分级后数字已过时；该文件覆盖 Fuchs/Cascino/TERMITe 全部批次，本次按范围未改动，建议维护者评估是否同步更新。
- 端点表 `note` 列已注明次级置信度行的 author_category（`diffuse end (diffuse peak)` / `undetermined`）与坐标来源（gene_peak_posn），发布文案需按证据分层与发布边界.md 将次级层表述为"候选端点"。
