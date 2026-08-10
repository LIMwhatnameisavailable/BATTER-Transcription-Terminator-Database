# 批次整合记录：2026-08-09 fuchs-cascino-termite

- 生成日期：2026-08-10
- 批次标识：`2026-08-09_fuchs-cascino-termite`
- 来源范围：`BTED_EXT_2026_101` ~ `BTED_EXT_2026_113`（13 个登记来源，其中 12 个建端点表，105 为排除留痕行）
- 数据来源：Fuchs 2021（dRNA-seq/RNAtag-seq，C. difficile）、Cascino 2026（Rend-seq，S. elongatus PCC 7942，3 个 sheet）、TERMITe 8 个数据集（Term-seq 重分析）
- 状态：`to_review`（端点表已构建并通过结构校验，待维护者复核；TERMITe evidence_class 挂起待字典提案二采纳）

## 一、批次仓库结构（同步至正式路径后）

```
data/
├── registry/submissions/
│   └── 2026-08-09_fuchs-cascino-termite_source_intake.tsv   (13 行 × 26 列)
├── records/                                                 ← 独立轨道（修正一）
│   ├── README.md                                            (目录用途说明)
│   ├── BTED_EXT_2026_101/{_endpoints.tsv, _endpoints.bed}   (1967 行)
│   ├── BTED_EXT_2026_102/{...}                              (474 行)
│   ├── BTED_EXT_2026_103/{...}                              (384 行)
│   ├── BTED_EXT_2026_104/{...}                              (399 行)
│   ├── BTED_EXT_2026_106/{...}                              (630 行)
│   ├── BTED_EXT_2026_107/{...}                              (1153 行)
│   ├── BTED_EXT_2026_108/{...}                              (974 行)
│   ├── BTED_EXT_2026_109/{...}                              (779 行)
│   ├── BTED_EXT_2026_110/{...}                              (860 行)
│   ├── BTED_EXT_2026_111/{...}                              (1198 行)
│   ├── BTED_EXT_2026_112/{...}                              (949 行)
│   └── BTED_EXT_2026_113/{...}                              (686 行)
├── audit/excluded_assets/BTED_EXT_2026_101~113/
│   ├── 每源一个 excluded_assets.json（原始 xlsx/docx/pdf/csv 排除清单）
│   └── BTED_EXT_2026_101/fuchs_2021_unresolved_strand_75rows.tsv (审计留痕)
docs/
├── integration/
│   ├── 2026-08-09_fuchs-cascino-termite.md                  (本文件)
│   └── 2026-08-09_fuchs-cascino-termite_第六步对照报告.md     (第六步对照报告)
└── sources/BTED_EXT_2026_101~113/
    └── 每源一个 README.md（12 端点源 + 105 留痕源）
```

## 二、本次执行的修正（相对原方案）

| 修正 | 内容 | 状态 |
|---|---|---|
| 修正一 | 端点表路径由 `data/public/v0.2.0/records/` 改为 `data/records/`（独立轨道，避免污染 v0.2.0 release_manifest 统计口径）；新增 `data/records/README.md` 说明目录边界 | ✅ 已执行 |
| 修正二 | TERMITe 8 源（106–113）端点表 `evidence_class` 由 `algorithm_called_endpoint` 批量替换为 `NA`；intake 表 processing_status 保持 `to_review`，blocker_or_note 追加"算法重分析端点，evidence_class 暂挂起为 NA，待字典提案二正式采纳后升级" | ✅ 已执行 |
| 修正三 | 重写 12 张端点表 `end_id` 列：① 多 GSM sample_id 段取首个代表性 GSM + note 注明完整列表（101/102）；② 链标记 F/R → `plus`/`minus`（与 BATTER_S1 已发布 22 源 house style 一致，经确认）；③ 序号段保留 | ✅ 已执行 |

## 三、source_id 重编号对照

| 旧编号 | 新编号 | 来源 | 行数 | 端点表 |
|---|---|---|---|---|
| BTED_EXT_2026_001 | BTED_EXT_2026_101 | Fuchs 2021（C. difficile 630） | 1967 | ✅ |
| BTED_EXT_2026_002 | BTED_EXT_2026_102 | Cascino 2026 Syn_WT | 474 | ✅ |
| BTED_EXT_2026_003 | BTED_EXT_2026_103 | Cascino 2026 Syn_Δmfd_rep1 | 384 | ✅ |
| BTED_EXT_2026_004 | BTED_EXT_2026_104 | Cascino 2026 Syn_Δmfd_rep2 | 399 | ✅ |
| BTED_EXT_2026_005 | BTED_EXT_2026_105 | Cascino 2026 Eco/Bsu（重复留痕） | — | ❌ excluded_duplicate |
| BTED_EXT_2026_006 | BTED_EXT_2026_106 | TERMITe B. subtilis a | 630 | ✅ |
| BTED_EXT_2026_007 | BTED_EXT_2026_107 | TERMITe B. subtilis b | 1153 | ✅ |
| BTED_EXT_2026_008 | BTED_EXT_2026_108 | TERMITe B. subtilis c | 974 | ✅ |
| BTED_EXT_2026_009 | BTED_EXT_2026_109 | TERMITe E. faecalis | 779 | ✅ |
| BTED_EXT_2026_010 | BTED_EXT_2026_110 | TERMITe L. monocytogenes | 860 | ✅ |
| BTED_EXT_2026_011 | BTED_EXT_2026_111 | TERMITe B. subtilis d | 1198 | ✅ |
| BTED_EXT_2026_012 | BTED_EXT_2026_112 | TERMITe E. coli b | 949 | ✅ |
| BTED_EXT_2026_013 | BTED_EXT_2026_113 | TERMITe E. coli a | 686 | ✅ |
| **合计** | | | **10453** | 12 端点表 |

重编号为纯 +100 平移，13 个新编号（101–113）经全仓 grep 确认零占用，无冲突；无真实数据以旧编号（001–013）提交过。

## 四、evidence_class 使用与字典合规性

| evidence_class | 使用来源 | 行数 | 字典状态 |
|---|---|---|---|
| `author_called_endpoint` | 101（全部）、102–104（最高置信度层） | 3028 | ✅ 现成枚举 |
| `called_endpoint` | 102–104（次级置信度层） | 196 | ✅ 现成枚举 |
| `NA`（挂起） | 106–113（原 `algorithm_called_endpoint`） | 7229 | ⚠️ 待提案二确认后升级 |

- TERMITe 8 源按《外部来源正式整合入库要求 v0.1》第 2 节规则：团队正式采纳 `algorithm_called_endpoint` 前，端点表 `evidence_class` 暂填 `NA`，`processing_status` 保持 `to_review`；不得称为原作者直接发表的端点，也不得称为预测。
- `NA` 为数据字段字典通用缺省值，不落入 v0.2.0 禁用证据集（`author_integrated_mixed_evidence` / `prediction_only`），但新源不走 v0.2.0 校验器（见第五节）。

## 五、路径决策与校验器边界

- `scripts/validate_bted_v0_2.py` 将 `EXPECTED_SOURCES` 硬编码为 `BATTER_S1_001`~`S1_022`，只校验 `data/public/v0.2.0/records/`。新源放入该层既不被覆盖校验，也会污染已发布 release_manifest 统计口径 → 新源端点表改走 `data/records/`（与 v0.2.0 完全独立轨道）。
- 本批次**不修改** `manifest.json` / `release_manifest.json`（发布阶段产物，不在本批次范围）。
- 通用模板校验 `scripts/validate_bted_templates.py`（不涉及硬编码来源列表）适用于新来源；`validate_bted_v0_2.py` 仅作为回归检查确认既有 22 源未被误改。

## 六、坐标体系与 end_id

- 坐标：Fuchs TTS 1-based、Cascino `gene_peak_posn` 1-based 单碱基、TERMITe `summit_coordinate` 1-based 单碱基；BED6 一律 `[reference_name, pos-1, pos, end_id, "0", strand]`。
- `end_id` 格式：`<source_id>_<sample_id>_<reference_name>_<plus|minus>_<序号>`，链标记用 `plus`/`minus` 全词（与已发布 22 源一致）；101/102 多 GSM 源 end_id 取首个代表性 GSM，完整列表写入 note 列。
- 全部 10453 行 end_id 唯一、24 列列名与 `external_literature_endpoint_schema.tsv` 一致、strand 取值 `{+, -}`、BED 换算错误 0 行。

## 七、排除记录

| 来源 | 排除内容 | 去向 |
|---|---|---|
| 105 | 整源 excluded_duplicate（Eco/Bsu 为 Lalanne 2018 数据重分析） | intake 留痕行 + excluded_assets.json |
| Fuchs 75 行 | strand 无法确定的 TTS（confidence=无法确定，从未计入主表 1967 行） | `data/audit/excluded_assets/BTED_EXT_2026_101/fuchs_2021_unresolved_strand_75rows.tsv`（随批次入库，登记于 excluded_assets.json，sha256=`814dc45b…725fef`） |
| Cascino 2540 行 | TU / diffuse end (no peak) / unclear 无峰 | `cascino_exclusion_report.txt` |
| TERMITe 3 行 | POT≠summit 差 1bp，数据集未做四项独立验证（107/110/112） | 端点表 `qc_status=to_review`，note 写明原因与恢复条件 |

## 八、待办事项

1. 字典提案二（`algorithm_called_endpoint`）正式采纳后，将 106–113 端点表 `evidence_class` 由 `NA` 升级；同步字典、证据分层文档、SOP。
2. 12 个来源在来源登记表中状态仍为 `to_review`，待端点表发布流程完成。
3. TERMITe 3 行 `to_review`（107/110/112 POT≠summit）：恢复条件为对 POT/summit 区间做 U-tract 序列比对与 T-run 富集确认终止子边界，达成后改回 `pass` 并删除 note 说明。
4. 第四步 SHA-256 校验清单与第六步最终对照报告已生成（SHA-256 清单 24/24 匹配；报告见 `docs/integration/2026-08-09_fuchs-cascino-termite_第六步对照报告.md`）。
5. 第七步（同步 + git 提交/push）暂缓，待维护者审阅对照报告后另行指示。
