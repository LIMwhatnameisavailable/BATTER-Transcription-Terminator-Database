# 第六步：最终对照报告 — 2026-08-09 fuchs-cascino-termite 批次

生成日期：2026-08-10
批次：`2026-08-09_fuchs-cascino-termite`
范围：`BTED_EXT_2026_101` ~ `BTED_EXT_2026_113`（13 登记来源，12 端点表，105 排除留痕）
仓库位置：端点表 `data/records/BTED_EXT_2026_10X/`；源记录 `docs/sources/BTED_EXT_2026_101~113/`；审计 `data/audit/excluded_assets/BTED_EXT_2026_101~113/`；批次整合文档 `docs/integration/2026-08-09_fuchs-cascino-termite.md`
当前阶段：**第六步完成，第七步（同步 + git push）待维护者确认后执行**

---

## 一、结论摘要

| 项目 | 结果 |
|---|---|
| 端点表构建 | ✅ 12 张，共 **10,453** 行 |
| end_id 重写（修正三） | ✅ 全部重编号 + `plus`/`minus` 链标记 + 多 GSM 取首 GSM |
| TERMITe evidence_class 挂起（修正二） | ✅ 106–113 全部 7,229 行 `evidence_class=NA` |
| 路径决策（修正一） | ✅ 端点表走 `data/records/`，新增 `data/records/README.md` |
| 模板校验 `validate_bted_templates.py` | ✅ 13 文件（1 intake + 12 端点）全部 PASS |
| 结构/BED/证据校验 `validate_staging_batch.py` | ✅ 12 表 10,453 行全部 PASS（含 3 行 `to_review`） |
| SHA-256 校验清单 | ✅ 12 个 `SHA256SUMS.txt`，24 条记录全部匹配 |
| v0.2 回归检查 `validate_bted_v0_2.py` | ⚠️ 见第五节（行尾环境差异，内容未改） |
| staging 与 draft 源一致性 | ✅ 12/12 端点表 sha256 一致 |

---

## 二、source_id 重编号对照

| 旧编号 | 新编号 | 来源 | 行数 | 端点表 | 主要证据层 |
|---|---|---|---|---|---|
| BTED_EXT_2026_001 | **BTED_EXT_2026_101** | Fuchs 2021（C. difficile 630） | 1967 | ✅ | `author_called_endpoint` |
| BTED_EXT_2026_002 | **BTED_EXT_2026_102** | Cascino Syn_WT | 474 | ✅ | `author_called_endpoint`(388) + `called_endpoint`(86) |
| BTED_EXT_2026_003 | **BTED_EXT_2026_103** | Cascino Syn_Δmfd_rep1 | 384 | ✅ | `author_called_endpoint`(331) + `called_endpoint`(53) |
| BTED_EXT_2026_004 | **BTED_EXT_2026_104** | Cascino Syn_Δmfd_rep2 | 399 | ✅ | `author_called_endpoint`(342) + `called_endpoint`(57) |
| BTED_EXT_2026_005 | **BTED_EXT_2026_105** | Cascino Eco/Bsu | — | ❌ excluded_duplicate | — |
| BTED_EXT_2026_006 | **BTED_EXT_2026_106** | TERMITe B. subtilis a | 630 | ✅ | `NA`（挂起） |
| BTED_EXT_2026_007 | **BTED_EXT_2026_107** | TERMITe B. subtilis b | 1153 | ✅ | `NA`（挂起） |
| BTED_EXT_2026_008 | **BTED_EXT_2026_108** | TERMITe B. subtilis c | 974 | ✅ | `NA`（挂起） |
| BTED_EXT_2026_009 | **BTED_EXT_2026_109** | TERMITe E. faecalis | 779 | ✅ | `NA`（挂起） |
| BTED_EXT_2026_010 | **BTED_EXT_2026_110** | TERMITe L. monocytogenes | 860 | ✅ | `NA`（挂起） |
| BTED_EXT_2026_011 | **BTED_EXT_2026_111** | TERMITe B. subtilis d | 1198 | ✅ | `NA`（挂起） |
| BTED_EXT_2026_012 | **BTED_EXT_2026_112** | TERMITe E. coli b | 949 | ✅ | `NA`（挂起） |
| BTED_EXT_2026_013 | **BTED_EXT_2026_113** | TERMITe E. coli a | 686 | ✅ | `NA`（挂起） |
| **合计** | | | **10,453** | 12 表 | |

重编号为纯 +100 平移；101–113 经全仓 grep 确认零占用，无冲突；无真实数据以旧编号提交过。

---

## 三、三处修正执行明细

### 修正一：端点表路径 → `data/records/`

- 端点表由 `data/public/v0.2.0/records/` 改为 `data/records/<source_id>/`（独立轨道）。
- 原因：`validate_bted_v0_2.py` 硬编码 `EXPECTED_SOURCES=BATTER_S1_001~022`，新源放入 v0.2.0 层既不覆盖校验、也污染 release_manifest 统计口径。
- 新增 `data/records/README.md`：说明目录用途，与 `data/public/v0.2.0/`（BATTER_S1_001-022 专属发布层）相互独立。

### 修正二：TERMITe 8 源 evidence_class → NA

- 106–113 端点表 `evidence_class`：`algorithm_called_endpoint` → `NA`（7,229 行）。
- intake 表 processing_status 保持 `to_review`，blocker_or_note 追加：`算法重分析端点, evidence_class 暂挂起为 NA, 待字典提案二(algorithm_called_endpoint)正式采纳后升级`。
- docs/sources/README.md 措辞同步：挂起期间不称"原作者直接发表的端点"，也不称"预测"。
- 101–104 证据层不变（`author_called_endpoint` / `called_endpoint`）。

### 修正三：end_id 格式重写

经你确认的两个决策：**链标记用 `plus`/`minus`**（与已发布 22 源 house style 一致）、**多 GSM 取首个代表性 GSM + note 注明完整列表**。

| 来源 | 改前示例 | 改后示例 |
|---|---|---|
| 101 | `BTED_EXT_2026_001_GSM4696498;GSM4696499;GSM4696500_CP010905.2_F_000001` | `BTED_EXT_2026_101_GSM4696498_CP010905.2_plus_000001` |
| 102 | `BTED_EXT_2026_002_GSM9264033;GSM9264034_CP000100.1_R_000003` | `BTED_EXT_2026_102_GSM9264033_CP000100.1_minus_000003` |
| 106 | `BTED_EXT_2026_006_SRR17335818-829_NC_000964.3_F_000001` | `BTED_EXT_2026_106_SRR17335818-829_NC_000964.3_plus_000001` |

- 101/102 多 GSM 行 note 追加 `完整GSM列表=...（end_id 取首个代表性GSM）`；101 覆盖 1967 行、102 覆盖 474 行（含次级置信度 86 行）。
- 全部 10,453 行 end_id 唯一；改前备份保留为 `*.pre_rewrite.tsv`（draft/endpoints_output/）。

---

## 四、校验结果

### 4.1 `validate_bted_templates.py`（通用模板校验）

| 检查对象 | 结果 |
|---|---|
| 来源登记模板（26 列） | ✅ PASS |
| 端点标准模板（24 列） | ✅ PASS |
| staging intake（13 行 × 26 列） | ✅ PASS |
| 12 张 staging 端点表（24 列） | ✅ 全部 PASS |

### 4.2 `validate_staging_batch.py`（本批专项结构校验）

- 24 列 schema 顺序一致、行数>0、end_id 唯一、source_id 与目录一致
- BED6 逐行换算 `[ref, pos-1, pos, end_id, "0", strand]` 全部正确
- strand 取值 `{+, -}`
- qc_status：10,450 行 `pass` + **3 行 `to_review`**（见 4.2.1）
- 证据层合规：106–113 全 `NA`，101–104 仅 `author_called_endpoint`/`called_endpoint`，无禁用证据类
- intake：13 行 26 列、101–113 有序、TERMITe 行带挂起 blocker note
- **结论：PASS（0 problem）**

#### 4.2.1 已知 `to_review` 行（3 行，POT≠summit 差 1bp）

| end_id | 来源 | 坐标 | 说明 |
|---|---|---|---|
| `BTED_EXT_2026_107_SRR12232093-300_NC_000964.3_minus_001105` | 107 (B. subtilis b) | 4023498 | POT(4023499)≠summit(4023498)，数据集未做四项独立验证 |
| `BTED_EXT_2026_110_ERR1248436-460_NC_003210.1_minus_000176` | 110 (L. monocytogenes) | 657294 | POT(657295)≠summit(657294)，数据集未做四项独立验证 |
| `BTED_EXT_2026_112_ERR8194521-523_NC_000913.3_minus_000711` | 112 (E. coli b) | 3476569 | POT(3476570)≠summit(3476569)，数据集未做四项独立验证 |

坐标已按任务规则取 `summit_coordinate`，但所在数据集不在四项独立验证覆盖内（仅 E. coli a / E. faecalis 两个代表数据集验证），1 bp 归属未实证 → **qc_status=`to_review`**，note 写明原因与恢复条件（对 POT/summit 区间做 U-tract 比对与 T-run 富集确认后改回 `pass`）。第 109 源同类行（E. faecalis `NZ_CP008816.1:1636268`）属代表数据集内已验证的低置信边界峰，已在 intake 登记表解释，保持 `pass`。

#### 4.2.2 Fuchs 75 行（strand 无法确定）审计留痕

- 构建脚本 `draft/endpoints_output/build_fuchs_endpoints.py`：主表仅收录 confidence=`高`(1815) + `低`(152) = **1967 行**；`无法确定`(75) 从一开始就路由至独立文件，**从未计入 1967**。全量交叉验证：主表 1967 行 ∩ 75 行文件 = **0 重叠**。
- 75 行文件已复制至审计区随批次入库：`data/audit/excluded_assets/BTED_EXT_2026_101/fuchs_2021_unresolved_strand_75rows.tsv`（76 行 = 表头 + 75），并在同目录 `excluded_assets.json` 登记（`evidence_class=curation_exclusion`，`public_repository_copy=true`，sha256=`814dc45b…725fef`）。

### 4.3 SHA-256

- 12 个 `data/records/<sid>/SHA256SUMS.txt`，每条覆盖 `_endpoints.tsv` + `_endpoints.bed`，共 24 条记录，重算 **全部匹配**。

### 4.4 staging 与源一致性

- 12 张 staging 端点表与 `draft/endpoints_output/` 源 sha256 **12/12 一致**。
- intake 行数 13 = draft 源 13。

---

## 五、⚠️ v0.2 回归检查说明（重要，请知悉）

运行 `python scripts/validate_bted_v0_2.py` 输出 **106 处 checksum mismatch（exit 1）**。经诊断：

- 本仓库 `core.autocrlf=true`（Windows 检出），工作树文件为 **CRLF** 行尾；
- 发布者在 LF 环境计算 `SHA256SUMS.txt`；
- 对工作树文件做 **LF 归一化后重算**：**106/106 全部匹配**，包括全部 22 源 + release_manifest。

**结论**：现有 22 个 BATTER_S1 来源**内容未被误改**，v0.2 回归 FAIL 纯属 Windows 行尾环境差异，非数据问题。如 CI/后续发布在 LF 环境运行，该脚本将 PASS。**建议**：若需要本机以 LF 检出运行此校验，可临时 `git config core.autocrlf input` 后重新检出，或改用 LF 归一化校验脚本。

同时按预期：该脚本**不校验新来源**（硬编码 22 源），新源走 `data/records/` 独立轨道，由 `validate_staging_batch.py` 覆盖。

---

## 六、批次仓库结构（同步至正式路径后）

```
data/
├── registry/submissions/2026-08-09_fuchs-cascino-termite_source_intake.tsv        (13×26)
├── records/
│   ├── README.md
│   └── BTED_EXT_2026_10X/{BTED_EXT_2026_10X_endpoints.tsv, .bed, SHA256SUMS.txt}   (12 源)
└── audit/excluded_assets/BTED_EXT_2026_101~113/excluded_assets.json               (13 个)
    └── BTED_EXT_2026_101/fuchs_2021_unresolved_strand_75rows.tsv                   (审计留痕, 76 行)
docs/
├── integration/2026-08-09_fuchs-cascino-termite.md
├── integration/2026-08-09_fuchs-cascino-termite_第六步对照报告.md                   (本报告)
└── sources/BTED_EXT_2026_101~113/README.md                                        (13 个)
```

---

## 七、待维护者决策事项

1. **第七步是否执行**：同步 `staging/` 到仓库对应路径 + `git add/commit/push main`。本报告确认无误后方可执行。
2. **字典提案二确认**：`algorithm_called_endpoint` 正式采纳后，将 106–113 `evidence_class` 从 `NA` 升级（端点表 + 字典 + 证据分层文档 + SOP 同步）。
3. **v0.2 行尾问题**：是否调整本机 `core.autocrlf` 以便后续本机运行 v0.2 校验。
4. **Cascino 排除行**：如需逐行可回溯的排除记录，可补充生成（当前 exclusion_report 为三档计数，源表可按 sheet+gene_term 复现）。
5. **Fuchs unresolved 75 行**：strand 无法确定的 75 条 TTS 从未计入主表（1967 行不含），已随批次复制至 `data/audit/excluded_assets/BTED_EXT_2026_101/fuchs_2021_unresolved_strand_75rows.tsv` 供审计追溯，并在 `excluded_assets.json` 登记；其余 TTS 待人工核查。**不阻塞发布**（主表只含 confidence 高/低行）。
6. **TERMITe POT≠summit 行**：4 行中 109（E. faecalis）为代表数据集内已验证的低置信边界峰，intake 已解释，保持 `pass`；其余 3 行（107/110/112）已标记 `qc_status=to_review`，note 写明原因与恢复条件，**恢复条件达成前不得改回 `pass`**。
