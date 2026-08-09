## 概述
本次提交新增 13 条外部文献来源登记（26 列 intake 模板），覆盖三批数据：

| 来源 | 行数 | PMID/DOI | 核心验证内容 |
|---|---|---|---|
| Fuchs 2021 | 1 | PMID 34131082 | 全量链方向推断验证（2042 个位点） |
| Cascino 2026 | 4 | PMID 42148773 | Eco/Bsu 坐标版本核实，1 行标记重复排除 |
| TERMITe (Kosiński 2025) | 8 | NAR 2025 | 8 个 registry 外全新来源，坐标体系经 U-tract 序列实证 |

## 关键发现
- **Fuchs**：链方向字段缺失，已通过基因组注释交叉比对完整推断补全，全量位点验证通过。
- **Cascino**：新旧坐标版本存在偏移，已用序列级证据锁定归属版本；第 5 行为 Lalanne 2018 数据重分析，标记为重复排除（`processing_status=excluded_duplicate`），其 `primary_evidence_class` 按字典规则填 `NA`。
- **TERMITe**：与 registry 现有条目比对后，确认 9 个数据集重叠、8 个为全新来源；坐标体系（1-based，BED offset=-1）已用 E. coli（单染色体）与 E. faecalis（3 复制子）两个代表性数据集做 U-tract 序列级验证，其余 6 个基于同一流水线代码推定。

## 字典变更提案（需讨论）
本次提交同时提出 2 个新枚举值（详见 `draft/dictionary_patch_proposal.md`），尚未合入正式字典，请团队确认后再落地：
- `processing_status = excluded_duplicate`：标记与 registry 已有记录重复、不重复收录的来源
- `primary_evidence_class = algorithm_called_endpoint`：标记端点坐标来自已发表算法重分析（而非原作者手动标注）的来源

## 变更文件
- `draft/external_literature_source_intake_final.tsv`：最终合并的 13 行登记表
- `draft/dictionary_patch_proposal.md`：字典枚举变更提案
- `draft/fuchs_strand_inference_result.tsv`：Fuchs 链方向推断的完整验证结果
- `draft/termite_coord_validation.md`：TERMITe 坐标体系验证证据
