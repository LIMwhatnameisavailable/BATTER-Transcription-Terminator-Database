# 远程仓库迁移盘点

**任务：** 01 — 对照远程仓库与当前 BTED 工作状态
**分支：** `agent/reconcile-current-bted-state`
**日期：** 2026-08-07
**范围：** 仅做盘点与差距映射。本任务未迁移、删除、重命名或重排任何数据。

---

## 1. 当前远程仓库清单（已核实）

通过 `git ls-files` 在分支 `agent/reconcile-current-bted-state`（提交 `6d596a1`）上核实。

### 1.1 项目级文档（中文）

| 文件 | 内容 | 作为以下事项的权威来源 |
|------|------|------------------------|
| `README.md` | 项目背景、Phase 1 完成总结、13 个来源核心数据表、下一步计划 | 项目阶段声明 |
| `PROGRESS.md` | 2026-07-28/29 工作日志：MOESM1–3 审查、Zenodo 调查、A/B/C 分类（13/13 为 A 类）、批量下载、交叉核查 | 过程历史 |
| `data_verification_report.md` | 逐篇核查 README 声明与已下载文件的对应关系；坐标字段与行数 13/13 验证通过 | 坐标数据验证声明 |
| `report_BATTER_supplementary.md` | BATTER 论文 MOESM1–3 审查；Table S1（20 个物种/菌株、22 条记录、13 篇 PMID）为来源清单 | BATTER 补充材料内容 |
| `report_zenodo_and_documents.md` | Zenodo 仓库（DOI: 10.5281/zenodo.16761763）内容；结论：Zenodo 含模型代码/训练数据/预测结果，不含 13 篇文献的实验坐标 | 外部原始数据链接 |
| `accession_list_verified.csv` | 13 篇 PMID 经核实的 GEO/SRA/ENA/ArrayExpress/Figshare/PRIDE/GenBank 登录号 | 登录号元数据 |

### 1.2 逐来源目录（`文献N-PMIDxxxxxxxx/`，N = 1–13）

- 每个目录含一份 `README.md`，即该来源的核查报告：文献引用、A/B/C 分类（全部 A 类）、已确认登录号、坐标数据线索、第三方平台判断、待人工确认事项。
- `文献13-PMID38030608/` 另含：
  - `supplementary_data_1to5_findings.md`（MOESM4–8 结构核查）；
  - 6 个 `*_read_starts.txt` 文件，**合计约 168 MB、约 631 万行，已被 git 追踪**（来自 MOESM10 Source Data 的原始 read starts 计数）；
  - `__MACOSX/` AppleDouble 文件（`._*`），**已被 git 追踪** —— 不应进入仓库的 macOS 归档垃圾文件（标记为后续清理决策，本任务不处理）。

### 1.3 任务计划

- `docs/tasks/README.md`、`docs/tasks/01-reconcile-current-bted-state.md`、`docs/tasks/02-github-pages-demo.md`。

### 1.4 刻意不在仓库中的内容

- `.gitignore` 排除了 `*.xlsx`、`*.pdf`、`*.zip`。`data_verification_report.md` 中描述的核心坐标工作簿（如 `mmc3.xlsx`、`ppat.1007461.s006.xlsx`、MOESM5/6）仅存在于本地工作副本，未进入 git。
- `README.md` 提到的 `archive/` 目录（历史报告）在仓库中**不存在**。其中提到的唯一内容（`supplementary_data1_raw_findings.md`）按 `PROGRESS.md` 已被后续核查取代。
- `.git` 约 31 MB，主要被 `文献13` 已追踪的 read-starts 文本文件占据。

---

## 2. 候选迁移材料

当前 BTED 工作状态位于本仓库**之外**，本任务期间**无法访问**。以下关于其内容的所有描述均来自任务说明，并标注 `to verify`。本任务不迁移以下任何内容。

### 2.1 文档类

| 候选材料 | 权威来源 | 预期大小 | 公开适用性 | 迁移风险 |
|----------|----------|----------|------------|----------|
| 证据分层 SOP | 外部 BTED 工作树（`to verify`） | KB–MB | 审阅后适用 | 技术风险低；**措辞风险高**：不得把仅预测或混合证据的记录重新标记为实验验证 |
| 逐来源处理记录 | 外部 BTED 工作树（`to verify`） | KB–MB | 审阅后适用 | 可能含本地绝对路径、机器相关环境说明或私人备注 —— 需清洗 |

### 2.2 来源元数据

| 候选材料 | 权威来源 | 预期大小 | 公开适用性 | 迁移风险 |
|----------|----------|----------|------------|----------|
| 22 来源注册表 | 外部 BTED 工作树（`to verify`） | KB | 审阅后适用 | **必须解释数量口径差异**：本仓库核实了 13 篇文献；外部注册表据报覆盖 22 条记录（与 BATTER Table S1 的 22 条记录 / 13 篇 PMID 一致，`to verify`）。多出的 9 条记录的出处与证据类别未核实 |
| 来源清单（manifest：逐来源文件列表、校验和、版本） | 外部 BTED 工作树（`to verify`） | KB–MB | 审阅后适用 | 校验和与参考基因组版本必须与一手来源一致；存在传播未核实坐标声明的风险 |

### 2.3 代码

| 候选材料 | 权威来源 | 预期大小 | 公开适用性 | 迁移风险 |
|----------|----------|----------|------------|----------|
| 标准化/格式转换流水线脚本 | 外部 BTED 工作树（`to verify`） | KB–MB | 审阅后适用 | 必须检查是否硬编码了凭据、API key、本地绝对路径 |
| 回归测试 | 外部 BTED 工作树（`to verify`） | KB–MB | 审阅后适用 | 测试夹具可能内嵌原始数据或未核实的预期值；夹具来源必须记录 |

### 2.4 加工后 / 公开资产

| 候选材料 | 权威来源 | 预期大小 | 公开适用性 | 迁移风险 |
|----------|----------|----------|------------|----------|
| 标准化坐标输出（BED/GFF 或等价格式） | 外部 BTED 工作树（`to verify`） | MB–数十 MB | 可能适用 | **科学风险最高**：坐标体系（0/1-base）、参考基因组版本对齐、证据类别标签均未核实。任何导入前必须通过 `docs/current-bted-status.md` 中的验收门槛 |
| JBrowse 资源（配置、track 文件） | 外部 BTED 工作树（`to verify`） | MB–数百 MB | 部分适用（受 GitHub Pages 大小限制） | 大型 track 文件可能超出 Pages/git 实际限制；可能需要外部托管或降采样 |

### 2.5 原始输入

| 候选材料 | 权威来源 | 预期大小 | 公开适用性 | 迁移风险 |
|----------|----------|----------|------------|----------|
| 出版商补充材料工作簿（`*.xlsx`，13 个来源） | 出版商 / 本地工作副本（本仓库 `.gitignore` 已排除） | 每个 KB–MB | **不要复制进 git**；通过引用 DOI/登录号再分发 | 出版商再分发条款；与一手来源重复 |
| 原始测序 reads（FASTQ） | GEO/SRA/ENA/ArrayExpress（见 `accession_list_verified.csv`） | GB–TB | **绝不复制**；仅链接 | 体积；重复；无附加价值 |
| BATTER Zenodo 产物（`TES.bed.gz` 1.19 GB、`terminators.flanked.fa.gz` 487 MB） | Zenodo DOI: 10.5281/zenodo.16761763（见 `report_zenodo_and_documents.md`） | GB | **绝不复制**；仅链接 | 纯预测数据 —— 绝不可作为实验证据展示 |

### 2.6 临时产物

| 候选材料 | 权威来源 | 预期大小 | 公开适用性 | 迁移风险 |
|----------|----------|----------|------------|----------|
| 缓存、中间转换输出、日志 | 外部 BTED 工作树 / 本地（`to verify`） | 不定 | 不适用 | 可再生成；无归档价值 |
| `__MACOSX/` AppleDouble 文件 | 本仓库（`文献13-PMID38030608/__MACOSX/`，已追踪） | KB | 不适用 | 已被提交；是否删除是独立决策，不在 Task 01 范围内 |

---

## 3. 禁止复制到 GitHub 的内容

- 凭据、API key、令牌、`.env` 文件、SSH 密钥，或任何含密钥的配置。
- 私有或未发表的数据；个人数据；文档或代码中内嵌的本地用户路径。
- 原始测序文件（FASTQ/FASTQ.gz）及任何数 GB 级的原始压缩包。
- 已有公开 DOI/登录号托管的重复原始数据（Zenodo、GEO、SRA、ENA、ArrayExpress、Figshare、PRIDE）—— 只链接，不复制。
- 缓存、临时输出、编辑器/操作系统产物（`.DS_Store`、`__MACOSX/`、`._*`）。
- `文献13` 的大型 read-starts 文本文件**已被追踪**（约 168 MB）；不得再添加同类文件。是否从 git 历史中清除是记录在 `docs/current-bted-status.md` 中的待决事项。

---

## 4. 本任务未改动的内容

- 未修改、删除、重命名或移动任何现有文件。
- 未导入任何外部 BTED 材料。
- 未改动任何科学声明、坐标、证据类别或来源数量。
