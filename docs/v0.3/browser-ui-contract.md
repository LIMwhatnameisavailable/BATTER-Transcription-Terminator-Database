# BTED v0.3 浏览器与首页 UI 契约

**状态：** 已批准的产品/可视化契约；v0.3 前端已实现目录、详情与查询入口，JBrowse
仍使用登记 config/asset contract，不改变 canonical release
**适用范围：** v0.3 API/浏览器实现；不改变 canonical release、24 列 endpoint 或证据边界

## 1. 首页入口

首页首屏把两个科研任务并排呈现，视觉权重相同：

1. **Search by accession**：输入带版本的 assembly accession，进入 assembly/source
   详情、筛选 endpoints、打开 JBrowse 或下载 canonical 文件；不接受不带版本 accession
   作为唯一定位键。
2. **Data augmentation**：进入 `/api/v1/augmentation` 的来源级登记页。第一版只
   展示 Table S1 `used_for_batter_augmentation = TRUE` 的 19 个来源、publication、
   assembly、evidence 和记录数；文案必须写明这是 source-level eligibility，不宣称
   19 个来源的每条 endpoint 已进入训练，也不显示 gene clusters、Rfam、训练 split 或
   预测位点。

两入口都显示当前 `release_version` 和 provenance 入口。首页不把 13 篇论文、22 个
来源和 endpoint 数量混成一个无单位的“数据集数”。

基因目录入口为 `/genes`，调用 `GET /api/v1/genes`，支持 assembly、contig、locus tag、
stable gene ID、feature type 和 1-based start 区间过滤。列表显示 gene/locus、assembly/
contig、坐标和 strand；每行可进入 gene detail 或 assembly context。Assembly list/detail
显示同一 release 的 `gene_count`，并链接到 `/genes?assembly_accession=...`。该入口只呈现
GFF-derived annotation，不计算或解释 `endpoint_gene_context`。

## 2. 可点击信息与右侧详情

论文、accession 和 BTED 记录在轨道/表格中都必须是可点击元素；点击后打开右侧详情
面板或等价的 detail route，不丢失当前 assembly/contig/strand/location。最少包括：

| 页面对象 | 可点击字段 | 右侧详情必须显示 |
| --- | --- | --- |
| publication | paper title、PMID、DOI、PMC | 题目、journal/year、PMID/DOI/PMC 链接、source 列表、release provenance |
| raw data | GEO、SRA、ENA/BioProject/BioStudies accession | repository、完整 accession、外部 URL、所属 source、许可/再分发状态 |
| BTED record | `end_id`、作者 endpoint ID、下载表行 | 24 列 endpoint 值、source/sample/contig、1-based/BED 坐标、strand、evidence、原始表/行引用、source manifest |
| assembly/contig | versioned assembly accession、contig accession | strain/物种、contig 长度、reference/GFF3 asset checksum、独立 source tracks |

右侧详情必须保留 source → publication → raw accession 的链接链。`BATTER_S1_002`
可以打开 source/audit 详情并显示 publication、raw accession 和限制，但没有 endpoint
record、endpoint download 或 JBrowse deep link；不能用“暂无数据”的空卡片伪造这些入口。

### 2.1 Public browser entry

The public catalogue links to a lightweight `browser.html` wrapper. It displays the
organism/strain, versioned assembly, selected source, publication/raw-accession links,
BED download and dataset details above the embedded JBrowse application. The bundled
`jbrowse/index.html` remains an internal iframe entry and is not modified by the wrapper.
When several sources share one assembly, the wrapper offers an “All source tracks” view
and a source selector; source tracks remain independent. `loc`, `session`, `tracks`,
`highlight` and `assembly` query state is forwarded to the iframe so shared deep links do
not lose their position or view state. S1_002 stays outside this entry because it is
metadata/audit-only.

## 3. 基因轨道的缩放语义

基因显示随视窗从远到近按确定性层级切换，不在远景绘制不可读的长标签：

| 缩放层级 | 表现 | 允许的信息 |
| --- | --- | --- |
| 远景（far） | 固定颜色的 gene feature 色块 | feature 存在、方向/大致长度；不显示拥挤文字 |
| 中景（mid） | 基因重复/方向使用紧凑 `›` / `‹` 方向符号 | strand、相邻 feature 的边界；标签仍按拥挤阈值隐藏 |
| 近景（near） | 展开 gene/locus 标签 | 稳定 gene ID、locus tag、feature type、release/GFF3 provenance |

`›`/`‹` 只表达基因 feature 的方向，不表达终止功能或 endpoint 证据。不同 contig
永远分开渲染；跨 contig 的“最近基因”或合并标签不允许。gene clusters、Rfam 不是
本契约的轨道。

## 4. Endpoint explorer 的交互契约

`/explore` 是 client-side filter view：source、assembly、contig、gene/locus、strand、
evidence 和 1-based position filters 在页面内请求 `GET /api/v1/endpoints` 更新结果，当前
过滤条件和 page 保留在 URL query 中，可直接分享或用浏览器前进/后退恢复。列表必须清楚
显示 loading、error、empty states；分页只更新当前 view，不整页导航。`Download current
results` 必须将当前过滤条件传给 `/api/v1/downloads/endpoints`，分别提供 TSV 与 BED6；BED6
仍为 `position - 1` 到 `position` 的坐标投影。Explore 表的 context 链接只标为 `View record`
或 `Assembly details`；实际带 `loc=contig:(position-500)-(position+500)` 的 JBrowse deep link
由 endpoint detail 在 assembly browser 可用时生成，否则明确显示 `JBrowse unavailable`。

## 5. Endpoint 轨道的缩放语义

端点从远到近按以下顺序表达，避免在全基因组视图堆叠几万条文字：

| 缩放层级 | 表现 | 允许的信息 |
| --- | --- | --- |
| 远景 | 端点密度/数量色带或密度图 | 该窗口有多少公开 endpoint；不能暗示新证据或训练权重 |
| 中景 | 固定像素宽度的棒棒糖/针形标记，链方向用 `▲` / `▼`（或等价方向箭头） | `end_id` 的短标记、strand、evidence class；像素宽度不随 score 夸大 |
| 近景/点击 | 展开详情面板 | 全部 24 列、source/sample/contig、作者 ID、坐标换算、原始行、QC、注释与下载/浏览链接 |

`▲`/`▼` 表达 strand/端点方向，不等于“终止子功能验证”。密度聚合必须只在同一
release、assembly、contig、strand 和 evidence 过滤条件内计算；不得跨 contig 去重。

## 6. Raw plus/minus BigWig

- raw plus/minus BigWig 轨道保留实验信号的正值；正负链由独立 track、颜色或上下布局
  表达，**不得为了镜像显示而把 raw signal 归一化、取负或改写文件**；
- 默认显示模式为 `linear`，与 asset 中的 raw 数值一致；`log`/`autoscale` 只能是
  display-only 变换，必须在图例、tooltip 或详情中明确，不能把变换后的数值导出为
  raw signal；
- 只有作者明确提供的 `signal_or_score`/author score 才能称为 author score。不能把
  author score、显示高度或候选峰高改称 `raw coverage`；没有 coverage 证据时必须写
  “score”或“signal”；
- track 名称和详情显示 `observed_signal`、`called_endpoint`、
  `author_called_endpoint`、`curated_record` 的证据层，不显示 prediction-only 或不可
  拆分 mixed-evidence 轨道。

## 7. Reference/GFF3 资产

浏览器配置同时区分并可追溯：

1. **Original NCBI GFF3**：原始/参考注释资产，保留来源 URL、assembly/contig、版本、
   byte size 和 SHA-256；
2. **BTED subset GFF3 + TBI**：由已登记 assembly/release 生成的浏览器子集，GFF3 与
   TBI 各自登记 asset ID、checksum、release 和生成器版本；subset 不能覆盖 original
   资产，也不能跨 release 复用未核验的索引；
3. 两者均通过同源 `/api/v1/assets/{asset_id}` 提供 Range；partial request 按 API 契约
   校验 allowlist、登记 byte size、Content-Range 和返回长度，完整 SHA-256 在导入/资产
   登记时完成。

轨道点击后的 feature detail 必须能回到 GFF3/TBI asset provenance。S1_002 不创建公开
   endpoint 或浏览器轨道；audit metadata 仍可在 source detail 显示。

## 8. 与证据边界的关系

UI 是查询层的呈现，不是新的生物学推断层：

- 不把 3′ end 信号改称逐位点功能验证 terminator；
- 不把模型预测或作者整合 mixed-evidence 写进公开 endpoint 轨道；
- 不在页面上把 augmentation 来源级 TRUE 改写为逐端点训练事实；
- 点击、缩放、密度聚合和 display transform 都必须保留 release、source、sample、
  contig、strand、evidence 和 provenance。

## 9. 验收清单

实现浏览器/UI 时至少验证：

- 首页两个入口并排且均返回 release/provenance；augmentation 显示恰好 19 个来源级 TRUE；
- title/PMID/DOI/GEO/SRA/ENA/BTED record 均能打开右侧详情并回到原视图；
- gene 的 far/mid/near 为色块 → `›`/`‹` → 标签；endpoint 为密度 → 固定像素棒棒糖/`▲`/`▼` → 详情；
- raw plus/minus BigWig 默认 linear、保持正值，log/autoscale 标记为 display-only；
- original NCBI GFF3 与 BTED subset GFF3/TBI 可区分、可点击、checksum/Range 通过登记；
- S1_002 无 endpoint/JBrowse；预测/mixed 证据和跨 contig 聚合不出现在公开 UI。
