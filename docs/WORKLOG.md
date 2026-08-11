# 工作日志

## 2026-08-12 —— 按导师意见完成组装中心网站演示版

**分支：** `agent/assembly-track-download-demo`
**范围：** 网站、下载与 JBrowse 共享基础设施；未修改或重新解释已冻结的科学记录。

### 完成内容

1. 将网站主入口由 22 条来源记录改为 20 个精确参考组装；完整 assembly accession 一致的 S1_007/S1_013 与 S1_015/S1_017 分别在同一组装页中显示为两个独立来源 track。
2. 保留 22 个来源详情页用于文献、accession、证据类别和限制追溯；常规坐标换算、许可字段和多份技术文件不再占据主要界面。
3. 新增组装级下载构建器。每个组装公开一份 `metadata.json`；19 个有端点数据的组装另有 `endpoints.bed`。聚合 BED 不去重，稳定 `end_id` 继续保留来源身份；S1_002 只有 metadata。
4. 下载页新增全选、清空、多选统计和无第三方依赖的浏览器端 ZIP 打包。ZIP 以组装分目录，避免不同基因组 contig 混入同一 BED。
5. 新增两套多 track JBrowse 配置。构建时比较共享来源的 FASTA/FAI SHA-256，只有参考内容一致才生成共享视图；默认会话打开即显示基因注释和两个来源 track。
6. 首页、Genomes、Download、组装页、来源页和数据说明页均保持中英文切换，并更新为个人仓库链接。
7. 新增 `docs/demo/BTED_组会展示教程_2026-08-12.md`，包含 5–7 分钟演示顺序、讲稿、问答、故障备份和不得夸大的证据边界。
8. 为个人仓库 Pages 增加 140 KB 的配置覆盖层：部署时复用现有 Release 的 123 个大型资产，只替换 21 个单来源配置、增加 2 个多 track 配置并重算 checksum；无需重复发布 93 MB 压缩包。

### 遇到的问题与解决

- **合并 JBrowse 初次进入只显示 Launch view。** 为多 track 配置增加确定性的默认线性视图，在首条已发布端点附近打开 10 kb 窗口，并自动加载基因与两个来源 track。
- **子目录配置的参考索引返回 404。** 合并配置位于 `jbrowse/assemblies/`，资源 URI 改为 `../assets/`；校验器同时验证相对路径、来源资产范围和 FASTA/FAI hash。
- **跨组装 BED 直接拼接会产生 contig 语义冲突。** 批量下载改为 ZIP，每个 assembly 独立目录；只在同一精确 assembly 内汇集来源 BED。
- **浏览器动态下载是否有效。** 用实际浏览器选择两个组装生成 ZIP，再用 `unzip -t` 核验 4 个文件无错误；metadata 中的来源和记录数与页面一致。

### 验证

- v0.2 数据与站点回归：12/12 unittest PASS；
- 20 个组装页、22 个来源页、19 个组装 BED、20 个 metadata，总记录数 28,399；
- 两个共享组装分别为 2,848 与 2,567 条记录，来源 ID 均保留；
- 21 个来源 JBrowse 配置和 2 个多 track 组装配置通过校验；
- 完整 Pages 产物通过文件、链接、证据标签和资源路径检查；
- Playwright 桌面/移动端、中英文、筛选、多选 ZIP 和 JBrowse 实测；最终 JBrowse 控制台 0 error / 0 warning；
- `git diff --check` 通过。

## 2026-08-10 —— BTED v0.2.0 自有数据公开演示构建

**分支：** `agent/bted-v0.2-public-demo`

**范围：** 只处理 BATTER S1 自有数据与共享基础设施，不合并协作者外部来源。

### 完成内容

1. 保持 v0.1 的 24 列核心接口，新增来源特异 `source_annotations.tsv`、逐字段 `fields.json`、逐来源 manifest/BED/checksum 和少数一对多附表。
2. 冻结 22 个来源：21 个公开标准化来源、1 个 `audit_only`（S1_002），共 28,399 条核心记录。
3. 建立许可登记。17 个来源发布来源特异表；4 个 Lalanne 来源标为 `external_link_only`，逐字段登记但不复制完整补充字段。
4. 生成 21 套来源独立 JBrowse 配置、123 个带来源前缀的引用资产；S1_002 无配置。Lalanne 公开配置移除受限制的文献整理 overlay。
5. 完成 S1_005、S1_020、S1_022 的确定性数据库工程审计：双 contig、BED 转换、唯一键、证据层和参考映射检查结果写入 `data/audit/v0.2.0/priority_source_audit.json`。
6. 重构双语静态网站：英文默认/中文切换、22 个来源详情页、筛选目录、下载、原始数据入口和 21 个 JBrowse 链接。
7. 生成数据与 JBrowse Release 压缩包；增加 GitHub Actions CI 与 Pages 工作流，Pages 在部署时下载固定版本 JBrowse 资产。
8. 新增 v0.2 SOP、发布接口、版本说明、来源处理记录和可编辑 draw.io 流程图。
9. 联网审计 88 条逐来源链接（61 个唯一 URL）：83 条正常可达，5 条返回访问限制状态；无 404/410、网络失败或缺失必填入口。S1_015 的 SRA 入口已补齐。

### 遇到的问题与解决

- **作者原字段在 v0.1 核心表中会丢失。** v0.2 增加来源特异表和逐列字段清单，要求每个原列被发布、映射或明确说明未发布原因。
- **JBrowse 官方压缩代码触发站点凭据/路径扫描误报。** 供应商 runtime 改为由 JBrowse package checksum 验证；BTED 自有 HTML、JS、配置和目录数据继续严格扫描。
- **S1_008 基因关联表不是全部可一对一连接。** 805 条记录全部保留，460 条连接到稳定 `end_id`，345 条明确标记 `unlinked_author_annotation`，不强配、不丢弃。
- **S1_020 混合层容易被误用。** v0.2 公开数据和 JBrowse 只保留 S2D 的 1,165 条端点，S1C 仅在内部审计和处理记录中出现。
- **合并时 Pages 会在尚未启用且 Release 仍为草稿的状态下自动失败。** 最终审阅将 Pages workflow 收窄为 `workflow_dispatch` 手动触发；正式发布 Release、管理员启用 Pages 后再部署。

### 已完成验证

- `validate_bted_templates.py`、v0.1 compatibility validator、v0.2 validator；
- S1_005/020/022 priority audit；
- 21 配置 JBrowse package validator；
- source-only 和完整 Pages artifact validator；
- v0.1 + v0.2 共 11 项 unittest；
- `validate_bted_templates.py`：PASS；
- `validate_bted_release.py`：PASS（v0.1 回归不变）；
- `audit_v0_2_priority_sources.py` / `validate_bted_v0_2.py`：PASS；
- `validate_jbrowse_release.py`：PASS（21 配置、123 个来源前缀资产）；
- `validate-site.py site` 与完整 `.pages-preview`：PASS（完整产物 1,150 个文件）；
- `tests/test_bted_ingestion.py` + `tests/test_bted_v0_2.py`：11/11 PASS；
- draw.io XML、GitHub Actions YAML、Python syntax 和 `git diff --check`：PASS。

### 发布状态

本地数据、站点、JBrowse 和 Release 资产已构建。GitHub 推送、Release 和 Pages 激活需要有效的 GitHub CLI 登录及维护者评审；不在本地构建阶段猜测或绕过认证。

## 2026-08-10 —— PR #3 仓库根目录与 legacy 向前清理

**来源提交：** `61318db` | **状态：** 已同步进 v0.2 分支，未改写历史

### 完成内容

1. 将根目录旧报告归入 `docs/legacy/project-reports/`，将登录号快照归入 `data/audit/legacy/`。
2. 从当前 Git 树移除重复的 `docs/legacy/original-directories/`、约 168 MB read-starts 文本和 `__MACOSX`；独立调研记录已保留到项目报告目录。
3. 新增 `scripts/validate_repo_layout.py`，并更新 README、目录规范、历史索引、迁移记录和 `.gitignore`。
4. 清理是普通可逆提交，没有删除标准化公开数据，也没有执行 `git filter-repo` 或 force push。

### 验证

- 仓库布局、模板、v0.1 发布、站点和 4 项 v0.1 unittest 全部通过；
- 同步至 v0.2 后重新执行 v0.1/v0.2/JBrowse/站点完整回归。

## 2026-08-10 —— v0.1 local snapshot：本地 BTED 结果首次进入 Git

**分支：** `refactor/project-structure-and-literature-notes-v0.1`
**状态：** 已完成构建、校验与文档更新；待提交并推送。

### 完成内容

1. 审计本地 BGIRNA 工作树的 22 个 `BATTER_S1` 来源、处理记录与证据边界；将 13 篇论文与 22 个来源的统计口径明确分开。
2. 新增 `scripts/build_local_snapshot_release.py`：将本地已整理的小型结果迁入正式目录，统一为 24 列 TSV；实验端点另生成 BED6；不复制原始测序、出版商工作簿、FASTA/GFF、BigWig 或 JBrowse 包。
3. 新增 `scripts/validate_bted_release.py`：检查 22 来源齐全、来源 README/manifest、公开 evidence class、1-based→BED、链、ID、文件行数及 SHA-256。
4. 生成 `data/public/records/`：21 个 `published_standardized` 来源、28,399 条记录；17 个作者发表端点来源有 TSV+BED，4 个 Lalanne 2018 来源以 `curated_record` TSV 发布。
5. `BATTER_S1_002` 标为 `audit_only`。其作者整合 TRS 表与数据集级观察表不复制到公开端点层；`BATTER_S1_020` 的混合表和 `BATTER_S1_022` 的纯预测表也只保留公开的 checksum 审计摘要。
6. 新增 22 个 `data/registry/manifests/BATTER_S1_*.json`、22 个 `docs/sources/<source_id>/README.md`、可用的详细处理记录副本，以及发布状态表 `data/registry/batter_s1_publication_status.tsv`。
7. 更新 `README.md`、贡献指南、`data/public`/`data/audit`/`data/registry` 说明、来源索引、GitHub Pages 来源目录和方法页面；新增发布说明 `docs/releases/v0.1-local-snapshot.md`。

### 关键判断

- 本地工作不是“没做”，而是此前没有被 Git 追踪、没有统一公共 schema，也没有跨来源自动校验。
- 本版没有把 BATTER、RhoTermPredict、TransTermHP 等预测结果伪装为实验端点。
- `curated_record` 与 `author_called_endpoint` 同样可追溯，但不可使用同一种“终止子功能”措辞；浏览器发布留待下一版本。

### 验证

- `python3 scripts/build_local_snapshot_release.py --input-root /path/to/BGIRNA`：PASS（21 来源 / 28,399 条记录；实际本地快照路径未写入 Git）。
- `python3 scripts/validate_bted_release.py`：PASS（22 来源、24 列 schema、证据边界、坐标、BED、SHA-256）。
- `python3 scripts/validate_bted_templates.py`：PASS。
- `python3 scripts/build_sources_page.py`：PASS（22 来源、21 个已发布来源、28,399 条记录）。
- `python3 scripts/validate-site.py`：PASS。
- `git diff --check`：PASS。

### 后续优先级

1. 提交并推送本次 v0.1 local snapshot；开 Draft PR 前由项目成员复核许可/再分发条件。
2. 为 `BATTER_S1_002` 建立逐观测 provenance 表，判断能否拆成纯实验端点。
3. 补写 `BATTER_S1_005`、`BATTER_S1_022` 的独立详细处理记录。
4. 将本地 JBrowse 以独立、版本化、可校验的浏览器发布物部署；不能把未审计的大轨道直接塞入 Git。

## 2026-08-09 —— 外部来源正式整合入库要求 v0.1

**分支：** `refactor/project-structure-and-literature-notes-v0.1` | **状态：** 已完成文档与目录入口建设，未接收任何外部端点数据

### 完成内容

1. 新增 `docs/standards/外部来源正式整合入库要求_v0.1.md`，明确“来源搜集 ≠ 已入库”、四类来源的处置边界、批次交接包、逐来源标准化门槛、选择性合并原则和 PR 检查清单。
2. 新增 `docs/integration/README.md` 与 `data/registry/submissions/README.md`，分别作为批次整合决定与协作者来源登记快照的固定入口。
3. 在根目录 `README.md` 和 `CONTRIBUTING.md` 加入正式入口；更新目录规范中已过时的历史目录说明和 `data/audit` 的公开审计摘要定位。
4. 本轮只建立协作规范：未复制任何原始文件、未接收或发布 Fuchs / Cascino / TERMITe 的端点记录、未改动证据字段字典的正式枚举。

### 验证

- `python3 scripts/validate_bted_templates.py`：PASS。
- `python3 scripts/validate-site.py`：PASS。
- `git diff --check`：PASS。

### 待后续团队确认

- 是否正式采用 `algorithm_called_endpoint` 与 `excluded_duplicate` 两个枚举值；确认前，相关外部来源保持 `to_review` / `NA`，不得作为已标准化数据发布。
- 选择性接收协作者外部来源登记快照和核验材料时，须另开整合分支和 Draft PR，不直接合并资料搜集分支。

## 2026-08-07 —— Task 01：对照远程仓库与当前 BTED 工作状态

**分支：** `agent/reconcile-current-bted-state` | **Draft PR：** [#1](https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database/pull/1) | **状态：** 已完成第一轮并按 OpenAI 审核意见完成文档修订；修订尚未提交，待用户提交推送后最终评审

### 完成内容

1. 读取了仓库现状文档：`README.md`、`PROGRESS.md`、`data_verification_report.md`、`report_BATTER_supplementary.md`、`report_zenodo_and_documents.md`、`accession_list_verified.csv`，以及全部 13 份逐来源 README（`文献1`–`文献13`）。
2. 通过 `git ls-files` 核实了被追踪文件清单（外部 BTED 工作树无法访问；所有外部声明均标注 `to verify`）。
3. 分支相对 origin/main 的净变更为**新增 8 个 Markdown 文件，不修改任何现有文件**：
   - `docs/remote-repository-migration-inventory.md` —— 已核实的远程清单；候选材料分组（文档 / 来源元数据 / 代码 / 加工后公开资产 / 原始输入 / 临时产物），含权威来源、预期大小、公开适用性、迁移风险；禁止复制清单。
   - `docs/current-bted-status.md` —— 仓库已核实现状 vs 据报告的外部 BTED 状态（全部 `to verify`）；7 项待决事项；后续数据迁移的 8 条验收门槛。
   - `docs/github-pages-demo-plan.md` —— 静态站点范围、页面地图、公开资产、外部原始数据链接（只链接不复制）、Pages 部署与验证方案；明确 Pages 无服务端数据库或私有数据访问。
   - `docs/WORKLOG.md`、`docs/HANDOFF.md` —— 工作日志与交接说明。
   - `docs/tasks/README.md`、`docs/tasks/01-reconcile-current-bted-state.md`、`docs/tasks/02-github-pages-demo.md` —— 分支任务计划（来自本分支较早提交 `6d596a1`）。
4. 推送了提交 `f5868ae`（任务文档）与后续收尾提交（`ee039bb`、`85776aa`）；将已存在的 draft PR #1 的标题与描述更新为 Task 01 交付内容。revert 提交 `43fcc5f` 目前仅在本地，尚未推送。
5. 收尾提交后，应要求将 Task 01 的全部文档改写为中文（任务计划文件 `docs/tasks/` 为流程定义，保持英文）。

### 记录备查、本任务未处理的发现

- `docs/legacy/original-directories/文献13-PMID38030608/` 下追踪了约 168 MB 的 read-starts 文本文件与 `__MACOSX/` AppleDouble 垃圾文件。
- `README.md` 引用的 `archive/` 目录在仓库中不存在。
- 来源数量口径：13 篇 PMID（本仓库核实）vs BATTER Table S1 在这 13 篇 PMID 下列出的 22 条记录 vs 外部工作树据报的 22 来源注册表；外部注册表与 Table S1 的 22 条记录是否一一对应尚未核实。

### 收尾提交与范围修正

- 新增 `docs/WORKLOG.md`（本文件）与 `docs/HANDOFF.md`（提交 `ee039bb`）。
- `docs/legacy/original-directories/文献13-PMID38030608/README.md` 的 PMID 笔误修复（"PMID: 38030638" → "PMID: 38030608"）曾包含在提交 `ee039bb` 中，已经 revert 提交 `43fcc5f` **移出 Task 01 范围**，留待后续单独处理；Task 01 不再包含、也不再声称该修复。

## 2026-08-07 —— OpenAI 审核修订（10 项）

按 OpenAI 审核意见对 Task 01 文档完成以下修订（仅改动 `docs/` 下的文件）：

1. 纠正分支范围声明：相对 origin/main 为新增 8 个 Markdown 文件、无现有文件被修改（分支历史曾含 1 处 README 笔误修复，已 revert 移出）；不再声称"只新增 3 个文件"。
2. PMID 笔误修复已移出 Task 01，WORKLOG/HANDOFF 不再声称 Task 01 修复了它。
3. 收敛"13/13 验证通过"表述：改为"13/13 来源均确认存在包含坐标字段的核心补充表；行数核对总体相符，但部分来源存在筛选口径、混合表内容或小幅行数差异，尚不能据此将表内每条记录统一视为实验验证终点"。
4. 收敛 A 类表述：A 类补充表"可作为后续标准化和逐记录证据审核的候选输入"，不暗示可直接用于数据库构建。
5. 澄清"22"的口径：区分 13 篇 PMID、Table S1 的 22 条记录、外部工作树据报的 22 来源注册表；注明外部注册表与 Table S1 是否一一对应尚未核实。
6. 修正仓库体积描述：当前 git pack 约 30.72 MiB；read-starts 文件对压缩后 pack 大小的具体贡献未单独核实。
7. 修正 Task 02 启动条件：Task 02 先实现静态骨架；元数据 schema 与证据口径获批前不生成带科学结论的完整目录。
8. 保持 Pages 硬边界：确认 Task 02 不包含 FASTQ、出版商工作簿、私有数据、坐标数据集、JBrowse、服务端代码。
9. 使 WORKLOG、HANDOFF 内容一致；draft PR #1 的标题与描述需按修订后的文档同步更新（PR 操作需用户执行）。
10. 重新验证：以下五条命令已于本轮修订后运行，结果见下节。

### 验证（本轮修订后）

- `git diff --check`：干净（无输出，退出码 0）。
- `git status -sb`：分支 `agent/reconcile-current-bted-state` 领先 origin 1 个提交（revert `43fcc5f` 未推送）；工作区含 6 个已修改的 docs 文档（本轮修订，未提交）。
- `git diff origin/main...HEAD --name-status`：8 个新增 Markdown，无修改、无删除。
- `git diff origin/main...HEAD --stat`：8 个文件，+468 行。
- `git log --oneline -5`：`43fcc5f`（revert 笔误修复）、`85776aa`（中文化）、`ee039bb`（收尾）、`f5868ae`（任务文档）、`6d596a1`（任务计划）。

## 2026-08-07 —— Task 02：GitHub Pages 静态演示站点骨架

**分支：** 实际执行于 `agent/reconcile-current-bted-state`（任务说明称当前分支为 `agent/github-pages-demo`，与实际不符；按约束未新建分支、未执行任何 git 提交/推送/PR 操作） | **状态：** 骨架已完成并通过本地验证，待提交与评审

### 完成内容

1. 读取任务上下文：`docs/tasks/02-github-pages-demo.md`、`docs/github-pages-demo-plan.md`、`docs/current-bted-status.md`、`README.md`、`accession_list_verified.csv`。
2. 新增静态站点骨架（纯 HTML + CSS，无构建工具链、无 JavaScript、无服务端代码）：
   - `site/index.html` —— 项目目的、证据边界、范围说明（13 篇 PMID / Table S1 22 条记录 / 外部据报 22 来源注册表三口径区分）、数据来源声明、局限性。
   - `site/catalog.html` —— 书目级元数据表（45 行），由 `accession_list_verified.csv` 派生；仅 PMID、物种/菌株、期刊年份、数据库名称、登录号/DOI、数据类型六列；刻意排除 3 行基因组序列登录号（GenBank CP027858、CP027859、NC_014500.1，因参考基因组版本对齐未完成）；不含坐标、证据类别、参考基因组、记录级状态；登录号链接至 GEO/SRA/ENA/ArrayExpress/BioProject/PRIDE/DOI/GitHub 等外部公开页面。
   - `site/methodology.html` —— 数据来自公开文献补充材料（只链接不复制）、当前处于标准化阶段（坐标体系/参考基因组/证据分层 SOP/schema 均未定稿）、外部 BTED 状态全部待核实且不入站、排除项清单、可复现性说明。
   - `site/about.html` —— 项目信息、贡献者（占位）、许可证（占位，明确发布前需完成许可证/再分发检查）、反馈渠道（占位）。
   - `site/css/style.css` —— 基础样式（响应式、表格横向滚动、无外部资源引用）。
   - `site/.nojekyll` —— 令 GitHub Pages 跳过 Jekyll 处理。
3. 新增 `scripts/validate-site.py`：检查必需文件存在；产物中无 FASTQ/xlsx/zip/BED/GFF 等原始数据或坐标文件、单文件 ≤1 MiB；无根相对链接与本地绝对路径；无 API key/密码/令牌等凭据字样；无未批准证据标签（"experimentally validated"、"实验验证" 等，含否定语境一律禁止）；HTML 内部相对链接全部可解析。
4. 全部内部链接使用相对路径（如 `catalog.html`、`css/style.css`），兼容 GitHub Pages 项目子路径 `/<仓库名>/` 部署。

### 骨架阶段刻意未做的内容

- 不含任何坐标数据、记录级条目、证据类别标签、JBrowse 配置或链接。
- 不含客户端搜索/过滤（纯 HTML + CSS 约束；待元数据 schema 获批后再评估引入少量 vanilla JS）。
- 未导入外部 BTED 工作树的任何内容；未执行 git commit/push/PR 操作；未删除任何文件；未改动科学数据。

### 验证（本轮）

- `python3 scripts/validate-site.py`：PASS（6 个文件，33,127 字节，全部检查通过）。
- 负向自检：构造含 FASTQ、根相对链接、本地绝对路径、`api_key` 字样、"experimentally validated" 字样的临时目录，脚本正确报告 13 个问题并以退出码 1 结束。
- 子路径冒烟测试：以符号链接构造 `/BATTER-Transcription-Terminator-Database/` 路径前缀，`python3 -m http.server` 下 index/catalog/methodology/about/css/.nojekyll 及目录索引全部返回 HTTP 200。
- 渲染检查：Playwright 截图确认桌面（1280px）与移动（390px）视口下四页排版正常，表格横向滚动，无重叠（截图存于 /tmp，未入库）。
- `git diff --check`：干净。

## 2026-08-07 —— Task 03：仓库卫生清理方案（仅文档，未执行清理）

**分支：** 实际执行于 `agent/reconcile-current-bted-state`（任务说明称当前分支为自 `main` 新建的 `agent/cleanup-proposal`，与实际不符；按约束未新建分支、未执行任何 git 提交/推送/合并/PR 操作） | **状态：** 方案文档已完成，待评审与维护者决策

### 完成内容

1. 只读事实核查（全部命令与结果记录在 `docs/cleanup-proposal.md` 附录 A）：
   - `docs/legacy/original-directories/文献13-PMID38030608/` 下 6 个 `*_read_starts.txt` 已追踪，工作区合计 168.0 MB（33.8 / 17.1 / 44.8 / 21.4 / 33.9 / 17.0 MB），自初始提交 `b59e72a` 起入库；当前 git pack 30.72 MiB。
   - `docs/legacy/original-directories/文献13-PMID38030608/__MACOSX/` 下 6 个 `._*` AppleDouble 文件已追踪（每个约 178 B）。
   - `README.md:59` 引用的 `archive/` 目录在磁盘与全部可达历史中均不存在（`git log --all -- archive/` 无输出）。
2. 新增 `docs/cleanup-proposal.md`，包含：当前问题清单；四个清理选项（`git rm --cached` 停止追踪 / `git filter-repo` 清除历史 / BFG Repo-Cleaner / Git LFS）的逐项利弊；风险分析（历史重写对协作者、draft PR #1、文档 SHA 引用的影响）；分阶段推荐方案；精确执行命令；回滚方案。
3. 推荐结论（详见方案文档第 4 节）：**阶段 A** 立即以 `git rm --cached` + `.gitignore` + 删除 README 悬空行解决卫生问题（普通提交、零协作冲击、完全可逆）；**阶段 B** 的 filter-repo 历史重写设四道门槛暂缓（PR #1 合并、托管策略定案、镜像备份与协作冻结、SHA 引用加注）。

### 本任务刻意未做

- 未删除任何文件；未运行 `git rm`；未修改 `.gitignore`、`README.md` 或任何科学数据。
- 未运行任何改写 git 历史的命令（filter-repo / BFG / LFS migrate 均未触碰）。
- 未执行 git commit / push / merge / PR 操作；未创建分支。
- 此前工作区已有内容（OpenAI 审核修订的 6 个 docs、Task 02 的 `site/` 与 `scripts/`）保持原样，未受影响。

### 验证（本轮）

- `git diff --check`：干净。
- 方案文档中的全部事实声明均以只读命令复核（见附录 A）；未运行任何写操作。

## 2026-08-07 —— 提交与推送

经维护者确认，Task 02/03 产出直接提交到 `agent/reconcile-current-bted-state`（不再移植到独立分支）。本轮提交：

- `b453404` —— Task 01 交付文档与 Task 02 计划的评审修订（4 个 docs）。
- `7e48745` —— Task 02 静态站点骨架（`site/`）与验证脚本（`scripts/validate-site.py`）。
- `1c16af3` —— Task 03 仓库卫生清理方案（`docs/cleanup-proposal.md`，仅文档）。
- 本提交 —— WORKLOG/HANDOFF 收尾记录。

上述提交连同此前未推送的 revert `43fcc5f` 一并推送至 origin；draft PR #1 现涵盖 Task 01–03，标题与描述已同步更新，仍待最终评审。

## 2026-08-07 —— 协作入库标准 v0.1（feature/bted-v0.1-standards-and-structure）

**分支：** `feature/bted-v0.1-standards-and-structure`（基于 `origin/agent/reconcile-current-bted-state`，因后者尚未合并入 main） | **PR 基线：** `agent/reconcile-current-bted-state` | **状态：** 完成并推送，Draft PR 待评审

### 完成内容

1. 只读核查：确认 `agent/reconcile-current-bted-state` 未合并入 main、工作区干净、存在未合并 Draft PR #1；完整阅读本地 BTED 工作树的 AGENTS.md、SOP v0.2、WORKLOG、HANDOFF 与两个外部文献模板，以及本仓库 README、Pages 计划、迁移盘点、状态文档。
2. 新增 `docs/standards/` 五份标准文档：SOP v0.1（以本地 SOP v0.2 为科学基础，剔除本地路径与单机脚本）、协作者新增文献收集与入库指南、数据字段字典 v0.1（覆盖两个模板全部 50 列）、证据分层与发布边界、项目目录与协作规范。
3. 迁移两个模板至 `data/registry/templates/`（来源表 26 列 / 端点表 24 列；修正本地模板表头拼写 `axonomy_id` → `taxonomy_id`）；新增 `data/registry`、`data/public`、`data/audit` 三个 README 说明用途与边界。
4. 新增 `scripts/validate_bted_templates.py`（无第三方依赖）：检查表头存在、列数 26/24、重复列名、必备核心列、规范列名与顺序，输出 PASS/FAIL。
5. 重写 README：确立正式名称 BTED（Bacterial Transcript 3′ End Database）、协作与可复现性主仓库定位、收/不收边界、统计口径（13 篇论文 vs 22 条来源记录不混写）、协作者入口与校验命令；移除"补充表坐标可直接用于数据库构建"的旧表述。
6. 更新 `.gitignore`：追加 .DS_Store、`__MACOSX/`、`._*`、`data/local/`、`raw/`、FASTQ/BAM/CRAM/BigWig 等原始数据类型、缓存/临时/本地环境文件；未删除任何已追踪文件、未改写历史（清理建议见 `docs/cleanup-proposal.md` 与 `docs/standards/项目目录与协作规范.md`）。
7. `site/` 最小改动：methodology.html 增加"入库标准与证据边界"一节（链接 GitHub 文档）、更新外部工作树状态描述；about.html 更正项目英文名；保持 demo/骨架性质，未加 JBrowse、未加坐标数据、未加记录级条目。
8. 本轮未做：完整数据迁移、JBrowse 发布、原始数据上传、`文献N-PMID*` 目录重排、历史大文件清理。

### 验证

- `git diff --check`：干净。
- `python3 scripts/validate_bted_templates.py`：PASS（来源表 26 列、端点表 24 列）。
- `python3 scripts/validate-site.py`：PASS。
- 全仓库新增/修改文档无 `/Users/` 本地绝对路径；无新增 xlsx/pdf/zip/FASTQ/BAM/BigWig 文件。

### 遗留

- 22 个 BATTER_S1 来源的数据迁移尚未开始，须按 `docs/current-bted-status.md` 验收门槛逐来源审计。
- `文献13` 已追踪大文件与 `__MACOSX/` 的清理仍待维护者按 `docs/cleanup-proposal.md` 决策。
- `docs/standards/` 五份文档为 v0.1，接入首批真实外部文献后应回顾修订。

## 2026-08-10 —— BTED 自有数据 v0.2.0 本地交付

**分支：** `agent/bted-v0.2-public-demo` | **实现提交：** `142e371` | **状态：** 已推送，Draft PR #4 与 v0.2.0 Release 草稿已建立

### 完成内容

1. 22 个 BATTER S1 来源均生成 v0.2 manifest 和网站详情页；21 个来源发布 28,399 条统一端点记录，S1_002 保持 `audit_only`。
2. 建立核心端点表、来源特异附表、字段清单、BED6、manifest 和 SHA-256 的两层发布接口；混合证据与预测注释不进入实验端点层。
3. 完成 S1_005 双 contig、S1_020 分层和 S1_022 参考版本的重点工程审计。
4. 生成 21 套独立 JBrowse 配置、双语静态网站、22 个来源页、CI/Pages 工作流、Release 压缩包和 draw.io 流程图。
5. 完整本地验收通过：模板/v0.1/v0.2/JBrowse/网站/Pages/坐标/checksum/11 项单元测试均通过；外部链接审计无失败和必填缺失。

### GitHub 上传问题与解决

- 已创建本地提交 `142e371 feat: build BTED v0.2 public demo`，工作树干净。
- 2026-08-10 先后使用默认 HTTP、HTTP/1.1、HTTP/1.1 + 500 MiB `http.postBuffer` 推送，均未改变数据或提交。
- 失败信息包括 `Could not resolve host`、`Failed to connect to github.com port 443` 和 `HTTP2 framing layer`；随后 `curl -I --connect-timeout 15 https://github.com` 同样超时。
- 网络恢复后，HTTPS 推送因当前 OAuth 令牌缺少修改 `.github/workflows/` 所需的 `workflow` scope 被拒绝；该拒绝与数据内容无关。
- `ssh -T git@github.com` 确认本机 SSH 身份有效，随后通过 SSH 成功推送完整分支，保留 CI 与 Pages workflow。
- 已创建 Draft PR #4：`https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database/pull/4`，基线为 PR #3 的 `refactor/project-structure-and-literature-notes-v0.1`；CI `BTED validation` 通过。
- 已创建 `v0.2.0` GitHub Release 草稿并上传数据包、JBrowse 包及两个 SHA-256 文件。Release 尚未发布，Pages workflow 尚未触发。
