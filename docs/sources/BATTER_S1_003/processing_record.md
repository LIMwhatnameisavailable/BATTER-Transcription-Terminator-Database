# BATTER S1 试点：*Bacillus subtilis* 168 Rend-seq 3′ end 数据处理记录

## 固定身份

| 项目 | 内容 |
|---|---|
| BATTER S1 ID | `BATTER_S1_003` |
| 物种 | *Bacillus subtilis* subsp. subtilis str. 168 |
| S1 assembly | `GCF_000009045.1` |
| 实验/reference accession | `NC_000964.3` |
| 论文 | Lalanne et al. 2018, PMID 29606352, DOI `10.1016/j.cell.2018.03.007` |
| 样本 | `GSM2500127` / `SRX2582343` |
| 条件 | WT；LB；37°C、180 rpm；OD590 0.3；25 s fragmentation；pooled |
| 3′ end 输入 | `3f_no_shadow`、`3r_no_shadow` WIG |

GEO 元数据与 Lalanne Table S3 都明确使用 `NC_000964.3`；WIG contig 也是 `NC_000964.3`，所以无 contig 名转换或 lift-over。

## 运行流程与结果

使用参数化的 `process_ecoli_rendseq.py`，并设置本物种的目录、contig、长度、source/sample ID 和 WIG 文件名。统一峰规则：read support ≥10，且在 ±5 nt 内为严格局部最大值。

| 项目 | 正链 | 负链 |
|---|---:|---:|
| 有信号位置 | 1,319,436 | 1,334,281 |
| 宽松局部峰 | 43,351 | 44,724 |
| 同链基因下游 0–128 nt 候选 | 2,174 | 2,235 |
| 最大 support | 638,747 | 71,213 |

从 Table S3 的 `1_terminators_Bsub` 读取 1,414 条高置信度内在终止子记录；同链匹配当前候选峰后，1,311 条精确匹配、82 条在 5 nt 内、21 条未在 5 nt 内匹配。

## 产物

```text
data/batter_bsub_pilot/
├── raw/                     # GEO no_shadow WIG 与 checksum
├── reference/               # NC_000964.3 FASTA/GenBank/FAI/chrom.sizes
├── annotation/              # 基因 GFF3 + tabix
├── processed/               # bedGraph、BigWig、候选 BED/TSV、文献匹配表
└── literature/              # Lalanne Supplementary Table S3
```

浏览器配置为 `browser/jbrowse2/viewer/bsub.config.json`；门户的第二个资源条目在 `browser/jbrowse2/portal-data.js`。

## 新发现的标准化要求

多物种共用同一个 JBrowse 静态目录时，不能让不同物种使用同名资源文件（如 `experimental_3prime_signal.forward.bw`），否则后复制的文件会覆盖先前物种，产生 BigWig 解析错误。B. subtilis 在 viewer 中统一使用 `bsub_` 前缀；以后每个物种都必须使用稳定的物种/assembly 前缀。

## 人工核查与状态升级（2026-08-06）

**决定：`standardized` → `curated`。** 依据任务看板 P0 卡，对发布资产做只读独立重算，全部通过后升级；非因自动测试通过而改状态。

### 核查证据

1. 原始完整性：2 个 raw WIG.gz 的 SHA-256 与 `logs/raw_sha256.txt` 一致。
2. 派生完整性：21 个派生文件的 SHA-256 与 `logs/derived_sha256.txt` 一致；重跑 `validate_bsub_lalanne_s3.py` 后输出字节一致，冻结校验和仍有效。
3. 参考一致性：WIG header 唯一 contig 为 `NC_000964.3`；FAI 与 chrom.sizes 均为 4,215,606 nt；与 GEO 元数据、Table S3 使用的 accession 一致，无 lift-over。
4. 候选集独立重导：从原始 WIG 全精度信号按公开规则（read support ≥10 且 ±5 nt 严格局部极大）重算，正链 43,351、负链 44,724，与发布 TSV 逐位点完全相等；无重复位点、无越界坐标（均在 `[1, 4215606]`）。
5. 坐标与字段：TSV `read_support` 与原始 WIG 值逐一精确相等；BED 全部满足 `start = position − 1`、`end = position`；strand 仅 `+`/`-`；`end_id` 前缀规范（`BATTER_S1_003_GSM2500127_F|R_NNNNNN`）。
6. 信号轨道精度：bedGraph/BigWig 为 WIG 值的 6 位有效数字舍入（`process_ecoli_rendseq.py` 中 `{value:g}`），全基因组最大相对偏差 4.94e-06（理论上限 5e-06）；TSV 保留全精度。属既定管线行为，非数据缺陷。
7. 文献匹配复核：1,414 条 Table S3 记录的同链匹配全部重算（`signal_at_published_coordinate`、最近候选距离、`match_status`），计数 1,311 精确 / 82 条 ≤5 nt / 21 条未匹配，与 `literature_validation_summary.json` 一致。
8. JBrowse 资源：`bsub_` 前缀资产齐备（信号 BigWig ×2、gene-proximal BED ×2、文献 BED、参考 FASTA/FAI/GFF3/tabix），`bsub.config.json` 与 portal 条目存在，无跨物种同名覆盖。

### 代表位点

| 位点 | 坐标 | 证据 |
|---|---|---|
| `BATTER_S1_003_GSM2500127_F_001183` | 22,384 + | 全基因组最大 support 638,747（trnSL-Ser1 区内），重算复现 |
| `BATTER_S1_003_GSM2500127_R_027733` | 3,173,404 − | 负链最大 support 71,213（trnB-Leu1 区内），重算复现 |
| `LALANNE2018_BSUB_IT_0001`（dnaA） | 1,839 + | 文献首条，精确命中候选峰 `F_000123`，信号 464 |
| `LALANNE2018_BSUB_IT_0014`（ksgA） | 51,532 + | 邻近命中例，距最近候选 1 nt |
| `LALANNE2018_BSUB_IT_0066`（ycdG） | 308,181 + | 未匹配例：信号 13，最近候选在 220 nt 外，按原始状态保留 |

### ID 约定说明

单 contig 来源的 `end_id` 不嵌入 contig 名（与已 `curated` 的 S1_001、S1_004 相同）；contig 身份由 `chrom` 列、manifest 与单 contig 参考唯一确定。多 contig 来源（如 S1_005）才在 ID 中嵌入 contig。本来源遵循该既定约定。

### 剩余风险

- 候选峰是信号峰，不是终止子结论；门户与文档已注明，发布时不得改述为 terminator。
- 21 条文献记录在 ±5 nt 内无候选峰：作者调用基于汇总/多条件证据，本库仅 WT 单样本信号，可能无合格峰；记录按原始状态保留，未删除。
- `portal-data.js` 中 `试点 · 已标准化` 为展示层文案约定，四个 Rend-seq 试点（含已 `curated` 的 S1_001/004/005）一致，本次未改动；如需展示层与注册表状态对齐，应四来源统一处理。

### 验证命令与结果（2026-08-06）

- 独立重算脚本（只读，未入库）：WIG→候选集全量重导、文献表全量复核、BED/TSV/信号一致性 —— 全部通过。
- `validate_bsub_lalanne_s3.py`（bundled Python）：输出与冻结校验和字节一致。
- `python -m unittest -v tests/test_bted_ingestion.py`：16 项全部通过。
- `node --check` × 6（portal-data、streptomyces-resources、source-catalog、portal、catalog-ui、record）：全部通过。
- 状态变更经 `extract_batter_s1_registry.py` + `build_bted_catalog.py` 重新生成，diff 确认仅 S1_003 行变化。
