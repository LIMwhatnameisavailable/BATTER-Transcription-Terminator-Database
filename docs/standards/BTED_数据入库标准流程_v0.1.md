# BTED 数据入库标准流程（SOP v0.1，协作版）

本文件是 BTED 的数据入库规范，面向所有通过 GitHub 协作的贡献者。它以项目本地工作树中的 SOP v0.2 为科学和数据规范基础整理而成，去除了单机环境与本地路径相关内容；涉及的具体处理脚本随后续逐来源数据迁移任务、按 `docs/current-bted-status.md` 的验收门槛进入本仓库。

协作者上手请先读 [协作者_新增文献收集与入库指南](协作者_新增文献收集与入库指南.md)；字段含义查 [数据字段字典](数据字段字典_v0.1.md)；发布边界查 [证据分层与发布边界](证据分层与发布边界.md)。

## 1. 目标与证据边界

将公开的细菌转录 3′ end 实验数据转化为可追溯、可下载、可在基因组浏览器核查的标准资源。以下数据层必须严格分开保存、分开命名、分开发布：

1. `observed_signal`：WIG、bedGraph、BAM 等实验信号；
2. `called_endpoint`：按公开规则从信号调用的候选端点；
3. `author_called_endpoint`：作者在补充表中发表的实验端点坐标；
4. `curated_record`：人工整理、文献关联与核查记录；
5. `author_integrated_mixed_evidence`：作者整合实验与预测得到的混合结果，仅内部审计，不公开发布；
6. `prediction_only`：纯计算预测（BATTER、RhoTermPredict、TransTermHP、ARNold 等），不作为实验端点发布。

两条不可逾越的边界：

- “实验支持的 3′ end”不等于“每个位点均独立完成了终止功能验证”。`author_called_endpoint` 表示实验信号支持的作者调用结果，不表示逐位点的遗传学功能验证。
- 预测结果不能伪装成实验端点。BATTER 等预测即使发表在实验论文的补充表中，也只能进入内部审计层。

## 2. 目录与唯一标识

每个来源先获得来源级 ID。同一物种的不同论文、样本或参考版本不得共用输出目录与 ID。

端点 ID 必须包含以下要素，保证跨来源唯一且可回溯：

`source_id + sample_id + contig + strand + sequence_number`

示例：`BATTER_S1_010_LEE2020_TERMSEQ_BA000030_4_F_000001`

新外部来源的 `source_id` 使用 `BTED_EXT_年份_三位序号`（例如 `BTED_EXT_2026_001`）；既有 `BATTER_S1_NNN` 编号保持不变。`dataset_id` 使用小写英文短横线 slug（例如 `ecoli-termseq-author-2024`）。

## 3. 来源登记：来源表与端点表分离

新文献一律先登记为来源级记录。不能把论文信息、样本信息和数千个端点坐标混在同一张表里。

- 来源登记表（`data/registry/templates/external_literature_source_intake.tsv`，26 列）：一行代表一个可独立处理的来源。同一论文中的不同物种、菌株、实验体系或参考版本，必要时应拆成多行。
- 端点表（`data/registry/templates/external_literature_endpoint_schema.tsv`，24 列）：一行代表一个端点或作者表中一个可追溯的观测。

来源登记至少记录：论文题目、PMID、DOI、全文链接、物种、菌株、实验方法、证据类别、样本 accession、原始下载地址、端点来源文件、参考组装、contig、坐标体系、链方向、许可、处理状态和问题说明。

作者原始表必须原样冻结保存；标准化端点表只做明确的坐标转换和 schema 映射，不能覆盖或删除作者原有字段。

## 4. 坐标与参考版本核查

依次比对：论文正文 / 补充表、数据可用性声明、GEO/SRA/ENA 元数据、WIG/BAM header、参考 FASTA header、NCBI assembly report。必须明确：

- 作者坐标是否为 1-based；
- BED 是否使用 0-based、半开区间；
- contig 名称是否带版本号（如 `NC_000964.3`），与 FASTA header 是否逐字符一致；
- 多 contig（染色体 + 质粒）是否全部存在；
- 物种、菌株、assembly 与 sequence accession 是否一致。

坐标规则（不可协商）：

- BTED 生物学坐标统一使用 1-based；
- 单碱基 BED 必须使用 `start = position - 1`、`end = position`；
- 不允许跨 contig 匹配；
- 参考 assembly、FASTA contig 名称、BED chrom、GFF3 seqid 必须一致；
- 无法确认参考版本、contig、坐标体系或链方向时，标记为 `to_review` 或 `blocked`，不能猜测。

## 5. 两类输入的处理方式

### 5.1 原始信号型（WIG / bedGraph / BAM）

1. 冻结原始文件并保存 SHA-256；
2. 每个 contig 单独验证 header、长度和链；
3. WIG/bedGraph 转 BigWig；BAM 先检查 reference dictionary；
4. 按来源 manifest 中固定的公开规则调用候选端点（例如 Rend-seq 当前规则：信号 ≥10 且在 ±5 nt 内为严格局部极大值）；
5. 输出信号 BigWig、候选 TSV/BED、基因 GFF3、处理摘要；
6. 与文献端点比对时只在相同 contig 和 strand 内匹配。

候选峰是信号峰，不是终止子结论，发布文案不得改述。

### 5.2 作者端点表型（补充表坐标）

1. 保存作者原始表，不修改任何单元格；
2. 记录表格名称、文件 DOI/URL、许可和 SHA-256；
3. 原样保留作者的 accession、strand、position、score 等字段；
4. 只做明确的坐标转换和 schema 映射，不以统一峰算法重算作者结果；
5. 自动检查参考序列范围、contig、链和重复 ID；
6. 输出标准 TSV/BED、摘要和 checksum。

### 5.3 同一来源含多种证据时

不能因为多个表都叫 TTS / terminator 就直接合并。先为每张表判断 `evidence_class`：

- 测序 read-end、作者明确的实验端点调用：进入实验端点层；
- RNA-seq、端点测序与序列预测共同整合的表：进入 `author_integrated_mixed_evidence` 内部审计层，不对公开数据库发布；
- 纯序列预测：进入 `prediction_only` 内部排除层，不生成公开下载或基因组浏览器轨道；
- 无法判断形成过程：暂停发布并记录为 `blocked`。

不同证据层使用不同的 TSV/BED 文件和明确的警告字段。公开网站只接入实验端点层。

## 6. 多 contig 规则

- 一个数据集可包含多个 chromosome / plasmid；
- FASTA、FAI、GFF3、BED 中的 contig 名称必须完全一致；
- 端点 ID 必须含 contig；
- 最近峰查找不得跨 contig；
- 基因组浏览器使用一个 assembly，同时列出全部 replicon；
- 验收时逐个 contig 检查至少一条记录。

## 7. 输出 schema 与自动质控

每条端点至少包含：`end_id`、`source_id`、`sample_id`、`reference_name`、`biological_coordinate_1based`、`bed_start_0based`、`bed_end_0based`、`strand`、`assay`、`evidence_class` 和来源回溯字段（完整定义见端点模板与字段字典）。

自动质控项：

- 坐标在 `[1, contig_length]` 区间内；
- BED 转换满足 `start = position - 1`；
- strand 只能为 `+` 或 `-`；
- FASTA header、GFF3 seqid、BED chrom 一致；
- 同物种不同 source 的输出不互相覆盖；
- 发布资产存在且 checksum 可复算；
- `blocked` / `to_review` 来源没有公开浏览器入口。

## 8. 处理状态与发布门槛

统一使用以下六个状态：

| 状态 | 含义 | 进入条件 | 发布限制 |
|------|------|----------|----------|
| `to_review` | 尚未确认样本文件、参考版本或坐标 | 来源登记完成即默认进入 | 不得发布任何端点数据或轨道 |
| `accessible` | 已定位公开数据，尚未标准化 | 原始数据 / 补充表链接与登录号核实 | 同上 |
| `standardized` | 已输出统一格式文件 | 通过第 4 节坐标核验与第 7 节质控 | 人工核查与发布评审未完成前不公开 |
| `curated` | 坐标与文献整理、人工核查完成 | 处理记录写清证据与剩余风险 | 可进入发布候选 |
| `published` | 下载、详情、浏览器、版本与校验齐全 | 发布评审通过 | 公开；后续修改须留版本记录 |
| `blocked` | 存在无法安全解释的数据缺失或冲突 | 任一硬性核验项失败 | 停止一切公开；记录恢复条件 |

只有公开实验数据、参考版本和坐标均核实的来源，才可以提供公开下载与基因组浏览器视图。原始大文件优先链接公共数据库，公开渠道只发布标准派生文件。

## 9. 问题记录原则

问题解决后不删除原问题。记录“发现方式 — 影响 — 处理决定 — 解决证据 — 剩余风险”。下载中断、工具缺失、元数据复制错误、taxonomy/assembly 冲突都必须进入处理记录与 `data/audit/` 留档。

## 10. 外部文献协同登记（新来源）

### 10.1 最小登记门槛

找文献阶段至少填写：`source_id`、`dataset_id`、`paper_title`、`pmid` 或 `doi`、`species`、`strain`、`assay`、`raw_or_supplement_url`、`endpoint_source_file`、`processing_status`、`blocker_or_note`。信息暂缺时填 `NA`，并在 `blocker_or_note` 写明缺失原因；不得根据物种名推测参考版本或坐标规则。

### 10.2 进入标准化的硬性门槛

以下信息均核实后，来源才可由 `to_review` / `accessible` 进入 `standardized`：

1. 实验方法和 `evidence_class`；
2. 菌株、参考 assembly、实际 FASTA contig 名称及长度；
3. 作者端点表或原始实验信号的可追溯入口；
4. 坐标体系、链方向及单碱基端点的解释；
5. 原始文件 / 补充表名称与 SHA-256；
6. 原始数据、论文和补充材料的永久链接。

任何一项不能核实：保留来源登记并标记 `to_review` 或 `blocked`，不生成公开端点下载或浏览器轨道。

### 10.3 固定字段与作者特异字段

标准端点表的核心列不随论文改变；作者特有的 score、coverage、TTS class、结构预测或基因关联信息追加在核心列之后。原始作者表必须原样冻结保存，不能为适配模板而覆盖或删除作者原有列。
