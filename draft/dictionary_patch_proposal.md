# 数据字段字典 v0.1 — 建议修改片段（两份提案合并版）

> 本文档为**建议修改片段**，供团队评审。未经维护者确认**不要**直接改动
> `docs/standards/数据字段字典_v0.1.md` 与 `docs/standards/BTED_数据入库标准流程_v0.1.md`。

本文件合并了两份独立的字典枚举提案：

| 提案 | 目标字段 | 新增枚举值 | 取值含义（一句话） | 触发批次 | 关联行 |
|---|---|---|---|---|---|
| 提案一 | `processing_status` | `excluded_duplicate` | 与本库已有来源实质性重叠，仅溯源留痕，不进入标准化 | Cascino 2026 对 Lalanne 2018 的 Eco/Bsu 重分析 | `BTED_EXT_2026_005` |
| 提案二 | `primary_evidence_class` | `algorithm_called_endpoint` | 端点坐标由已发表的可复现计算流水线从公开信号调用（非作者本人补充表发表） | TERMITe 8 个新来源 | `BTED_EXT_2026_006`–`013` |

两份提案针对**不同字段、不同语义维度**，互不替代，需分别评审。

---

# 提案一：新增 `processing_status` 枚举值 `excluded_duplicate`

## 1. 背景与动机

协作来源登记中出现了与库内已有来源**实质性重叠**的记录（如同一 GEO/SRA accession 的
重新分析，详见 `BTED_EXT_2026_005` 留痕行）。这类记录：

- 不是 `blocked`（不存在"无法安全解释的数据缺失或冲突"，恰恰相反，来源与重叠关系都已确认清楚）；
- 也不是 `curated`/`standardized`（明确不进入端点表，不应经历标准化流程）；
- 需要一种能表达"已识别、已判明、仅溯源留痕"的状态，避免误入后续发布流程，也避免重复劳动。

团队决议：在 `processing_status` 枚举中新增 `excluded_duplicate`。

## 2. 字段归属

- **目标字段**：`processing_status`（来源登记表，必填）
- **修改位置**：`数据字段字典_v0.1.md` 第 1 节 · 来源登记表（`processing_status` 行，约第 41 行）；
  `BTED_数据入库标准流程_v0.1.md` 第 8 节 · 处理状态与发布门槛（状态表末尾 `blocked` 行之后）

**原片段**（字典 `processing_status` 行）：

```
| 处理状态 | processing_status | 登记必填 | 来源表 | to_review / accessible / standardized / curated / published / blocked | 六状态定义见 SOP 第 8 节 |
```

**建议修改为**：

```
| 处理状态 | processing_status | 登记必填 | 来源表 | to_review / accessible / standardized / curated / published / blocked / excluded_duplicate | 七状态定义见 SOP 第 8 节；excluded_duplicate 见本条 |
```

**原片段**（SOP 第 8 节状态表末尾）：

```
| `blocked` | 存在无法安全解释的数据缺失或冲突 | 任一硬性核验项失败 | 停止一切公开；记录恢复条件 |
```

**建议追加一行**：

```
| `excluded_duplicate` | 原始测序数据或终止子判定结果与本库另一条已登记来源存在实质性重叠（如同一 GEO/SRA accession 的重新分析），本行仅作溯源留痕，不进入标准化 | 重叠关系经人工核查确认 | 不进入 standardized/endpoint 表；不入任何发布产物 |
```

## 3. 取值含义（字典与 SOP 共用语义）

> **`excluded_duplicate`** —— 该记录对应的原始测序数据或终止子判定结果，与本数据库中
> 另一条已登记来源存在实质性重叠（如同一 GEO/SRA accession 的重新分析），本行仅作溯源
> 留痕使用，不进入最终 `standardized`/endpoint 表。需在 `blocker_or_note` 中注明所重叠的
> 具体 `source_id`。

## 4. 触发场景与实例

| 触发场景 | 判定依据 | 本次实际例子 |
|---|---|---|
| 同一 GEO/SRA accession 被另一文献重新分析，产物与已登记来源同源 | 原始数据 accession 与 registry 已有行一致，且明确为"重分析"而非新增实验 | `BTED_EXT_2026_005`：Cascino 2026（mSystems）Eco/Bsu sheet 复用 **GSE95211**（Lalanne 2018），与 `BATTER_S1_001`（E. coli）、`BATTER_S1_003`（B. subtilis）同源 |

## 5. 使用约定（写入该状态的记录必须满足）

1. `blocker_or_note` 必须写明所重叠的具体 `source_id`（如 `BATTER_S1_001`）；
2. 原始数据来源（`raw_data_accessions`）应与被重叠记录一致或可明确对应；
3. 该状态记录不参与端点表构建、不进入 `published`、不进入站点目录；
4. 若后续发现被重叠记录自身因故失效，需重新评估此行的收录价值并回退为 `to_review`。

## 6. 影响范围核查

- **校验脚本** `scripts/validate_bted_templates.py`：仅校验表头、列数与规范列名，
  不校验 `processing_status` 枚举值，**无需修改**。
- **端点标准表**（24 列）无此枚举（其 `evidence_class` 枚举不受影响）。
- **site/** 静态站点：不展示记录级状态，**无影响**。

## 7. 首个应用实例

| source_id | 重叠对象 | 说明 |
|-----------|----------|------|
| `BTED_EXT_2026_005` | `BATTER_S1_001`（E. coli）、`BATTER_S1_003`（B. subtilis） | Cascino 2026 对 Lalanne 2018（GSE95211）的重分析，非新增贡献 |

---

# 提案二：新增 `primary_evidence_class` 枚举值 `algorithm_called_endpoint`

## 1. 背景与动机

TERMITe（Kosiński et al., NAR 2025）是整合型终止子数据库，对公开 Term-seq 数据做统一重分析。
协作登记本轮引入 8 个全新来源（`BTED_EXT_2026_006`–`013`，B. subtilis a–d、E. coli a/b、
E. faecalis、L. monocytogenes），其端点坐标**全部来自 TERMITe 流水线的重分析产物**
（`data/termite_parsed.csv` + `tracks/*.bed`），而非各原始论文作者在补充表中发表的坐标。

这引出字典未覆盖的情形：端点是"**算法调用**"的，且该算法已发表在同行评审论文中、规则公开可复现，
但它**不是作者本人在原始文献补充表中发表的实验端点**。现有三个枚举值均无法准确描述：

- `author_called_endpoint`——坐标由作者在补充表发表，TERMITe 来源不满足；
- `called_endpoint`——本库"按公开规则从信号调用"的**候选**端点（未发表、标注"候选"），
  TERMITe 端点是已随算法论文公开发布的结果，且经 TERMITe 内部 TranstermHP/RNAfold 双算法交叉，
  语义高于裸"候选"；
- `observed_signal`——原始信号层，不是端点坐标层。

团队决议：在 `primary_evidence_class` 枚举中新增 `algorithm_called_endpoint`。

## 2. 字段归属

- **目标字段**：`primary_evidence_class`（来源登记表，可暂缓、标准化前必填）
- **修改位置**：`数据字段字典_v0.1.md` 第 1 节 · 来源登记表（`primary_evidence_class` 行，约第 30 行）
- **联动位置**：`数据字段字典_v0.1.md` 第 2 节 · 端点表（`evidence_class` 行，约第 54 行，
  建议同步加入，理由见第 7 节）；`证据分层与发布边界.md` 六层表与 SOP 第 1 节六层列表
  （若采纳，建议在 `author_called_endpoint` 旁并列或紧邻新增一层，见第 7 节）

**原片段**（字典来源表 `primary_evidence_class` 行）：

```
| 主要证据类别 | primary_evidence_class | 可暂缓（标准化前必填） | 来源表 | author_called_endpoint / called_endpoint / observed_signal | 六层定义见证据分层文档；判不出填 NA 并标记 to_review |
```

**建议修改为**：

```
| 主要证据类别 | primary_evidence_class | 可暂缓（标准化前必填） | 来源表 | author_called_endpoint / algorithm_called_endpoint / called_endpoint / observed_signal | 六层定义见证据分层文档；判不出填 NA 并标记 to_review；algorithm_called_endpoint 见本条 |
```

## 3. 取值含义（字典与 SOP 共用语义）

> **`algorithm_called_endpoint`** —— 端点坐标由**已发表的、规则公开且可复现的计算流水线**
> 从公开实验信号统一调用，随该算法论文一并发布；坐标**非**原始文献作者本人在补充表中发表，
> 但算法及其参数、输入数据均可溯源。可用于整合型数据库/重分析批次（如 TERMITe）的端点登记。

## 4. 与 `author_called_endpoint` 的区别

| 维度 | `author_called_endpoint` | `algorithm_called_endpoint`（新增） |
|---|---|---|
| 调用者 | 原始文献作者本人 | 已发表的第三方/独立计算流水线 |
| 坐标出处 | 原始论文补充表 | 重分析流水线输出（随算法论文发布） |
| 原始数据 | 本文实验数据 | 常为多篇已公开文献的数据（重分析） |
| 证据强度 | 作者对自身信号的直接解读 | 算法对公开信号的统一重解读；依赖算法可信度（须已发表、可复现） |
| 可追溯性 | 回溯到作者表行号 | 回溯到算法版本 + 输入数据 accession + 参数 |
| 本次例子 | `BTED_EXT_2026_001`–`004`（Fuchs/Cascino 作者端点） | `BTED_EXT_2026_006`–`013`（TERMITe 重分析/自有数据） |

**发布边界**：两者均属"实验支持的端点"层，可公开；但公开文案须区分"作者发表的端点"与
"算法重分析的端点"，不得混用术语（见 `证据分层与发布边界.md` 第 3 节用词边界）。

## 5. 为何不能复用 `excluded_duplicate` 的逻辑

TERMITe 这 8 行**不是重复数据**，因此 `excluded_duplicate`（提案一）**不适用**：

| 维度 | `excluded_duplicate` 适用情形 | TERMITe 8 行实际情况 |
|---|---|---|
| 与 registry 关系 | 与已登记来源**实质性重叠**（同 accession/同源重分析） | 经逐项实证**确认全新**：B. subtilis a–d 与 `BATTER_S1_003` 同参考基因组但**不同 BioProject/不同数据**（PRJNA792588/646522/278818/PRJEB12568 vs GSE95211）；E. coli b/a 同参考但不同数据；E. faecalis、L. monocytogenes 为 registry **无此物种记录** |
| 处置方向 | 不进入标准化、仅留痕 | **需要进入端点表**（8 行各数百~上千条端点，是本次登记的实质贡献） |
| 判定字段 | `processing_status`（这行还收不收） | `primary_evidence_class`（端点证据怎么标注）——**不同字段、不同问题** |
| 语义后果 | 标成它=排除出库 | 标成它=错误排除 8 个新来源，登记意图落空 |

一句话：`excluded_duplicate` 回答"**是否收录**"，`algorithm_called_endpoint` 回答"**端点如何定性**"；
前者针对重复来源，后者针对全新来源的判定方式，二者不可互相替代。

## 6. 触发场景与实例

| 触发场景 | 判定依据 | 本次实际例子 |
|---|---|---|
| 端点来自整合型数据库/重分析流水线的统一调用 | `endpoint_source_file` 指向重分析输出（如 `TERMITe data/termite_parsed.csv`），而非原文补充表；算法论文已发表 | `BTED_EXT_2026_006`–`012`（TERMITe 对 Chabbra 2022 / Mandell 2021 / Dar 2016 / Mondal 2016 / Choe 2022 公开 Term-seq 的重分析） |
| 算法论文自带新实验数据，端点为流水线直接产出 | 无上游论文，数据为算法论文本研究产出 | `BTED_EXT_2026_013`（E. coli a，PRJNA906280，TERMITe 自有新数据，坐标同样由 TERMITe 流水线调用） |

## 7. 使用约定（写入该状态的记录必须满足）

1. `endpoint_source_file` 必须指向重分析流水线输出文件（而非原文补充表），写明 dataset_id 与行数；
2. `coordinate_convention` / `strand_definition` 须按流水线自身规范实证（TERMITe 已按
   `draft/termite_coord_validation.md` 实证为 1-based、BED offset=−1）；
3. `blocker_or_note` 注明"端点数据源=重分析流水线"，并与原始论文文献信息（PMID/DOI/BioProject）
   一并登记，保证重分析↔原始数据双向可溯源；
4. 端点表 `evidence_class` 建议**同步新增** `algorithm_called_endpoint`，使端点级记录与来源级
   定性一致（否则来源表标 algorithm_called_endpoint、端点表无对应枚举会产生口径断裂）；
5. 公开文案用词：写"TERMITe 算法重分析端点"，不写"作者发表的终止子"。

## 8. 影响范围核查

- **校验脚本** `scripts/validate_bted_templates.py`：仅校验表头、列数与规范列名，
  不校验 `primary_evidence_class` 枚举值，**无需修改**（沿用提案一结论）。
- **证据分层与发布边界.md**：六层表中 `author_called_endpoint` 旁新增一层
  `algorithm_called_endpoint`（定义、典型载体、公开/JBrowse/审计三栏均"可以"），需团队确认后同步；
- **BTED_数据入库标准流程_v0.1.md** 第 1 节六层列表：同证据分层文档，建议同步新增一行。
- **site/** 静态站点：不展示来源级枚举，**无影响**。

## 9. 应用实例（8 行）

| source_id | 原始文献 | 重分析数据集 | endpoint_source_file |
|---|---|---|---|
| `BTED_EXT_2026_006` | Chabbra 2022（PRJNA792588） | Bacillus_subtilis_a（630 行） | TERMITe `data/termite_parsed.csv` |
| `BTED_EXT_2026_007` | Mandell 2021（PRJNA646522） | Bacillus_subtilis_b（1153 行） | 同上 |
| `BTED_EXT_2026_008` | Dar 2016（PRJEB12568） | Bacillus_subtilis_c（974 行） | 同上 |
| `BTED_EXT_2026_009` | Dar 2016（PRJEB12568） | Enterococcus_faecalis（779 行，3 复制子） | 同上 |
| `BTED_EXT_2026_010` | Dar 2016（PRJEB12568） | Listeria_monocytogenes（860 行） | 同上 |
| `BTED_EXT_2026_011` | Mondal 2016（PRJNA278818） | Bacillus_subtilis_d（1198 行） | 同上 |
| `BTED_EXT_2026_012` | Choe 2022（PRJEB36932） | Escherichia_coli_b（949 行） | 同上 |
| `BTED_EXT_2026_013` | TERMITe 自有（PRJNA906280） | Escherichia_coli_a（686 行） | 同上（自有产出） |

8 行已全部按 `algorithm_called_endpoint` 填写于 `draft/termite_new_sources.tsv`。

---

*提案日期：2026-08-09 · 提案人：BTED 协作者 · 状态：待维护者确认*
