# BTED 科学边界与未完成工作

## 1. 数据库回答什么问题

BTED 把分散在论文、补充材料和公共测序库中的细菌转录 3′ 端数据，整理成可追溯、可下载、
可在 JBrowse 中核对的资源。当前 canonical release 是 `v0.2.0`：

- 13 篇论文、22 个 source records；
- 21 个 `published_standardized` source，1 个 `audit_only` source（`BATTER_S1_002`）；
- 20 个 assembly records、19 个去重可浏览 assembly；
- 28,399 条 endpoint，其中 24,887 条 `author_called_endpoint`、3,512 条
  `curated_record`。

记录数描述的是当前 BTED 发布内容，不代表 GTDB 的物种规模，也不代表所有记录都经过独立功能验证。

## 2. 不可混合的证据类型

| 类型 | 含义 | 可否计入实验端点 |
|---|---|---|
| `observed_signal` | 测序处理得到的连续链特异信号，如 Rend-seq BigWig | 否；信号不是单碱基端点 |
| `called_endpoint` | BTED 或明确流程从信号调用出的候选端点 | 视来源和验证状态单独发布 |
| `author_called_endpoint` | 原论文作者报告的端点 | 是，但仍不等于逐条功能验证 |
| `curated_record` | 从论文/补充表整理的记录 | 是，必须保留原始定义与限制 |
| `model_prediction` | 模型输出的候选区间 | 否；必须标 `experimental=false` |

生物学坐标统一为 1-based；单碱基 BED 使用 `start=position-1`、`end=position`。任何匹配、
去重或上下文关联都不得跨 contig；source、sample、contig、strand 和 sequence identity
不能静默合并。

## 3. S1_003 本地证据试点

对象为 *Bacillus subtilis* 168、`BATTER_S1_003`、`GCF_000009045.1` /
`NC_000964.3`，浏览区间为 18,000–28,000。

- 测量信号：Rend-seq 正/负链 raw BigWig，当前不归一化。
- 整理端点：Lalanne Table S3 的 1,414 条 `curated_record`。
- 训练扩增：BATTER 训练序列存在，但没有可直接投影到本 assembly 的可靠坐标轨道。
- 模型输出：BATTER-TPE regional compatibility pilot，11 条区间（7 + / 4 −）；
  `model_prediction`、`experimental=false`，不进入 canonical endpoint 数量。

信号、端点和预测在空间上邻近只适合辅助浏览，不能自动解释为实验验证、因果关系或同一个终止事件。

## 4. C 类训练扩增数据：已有证据与真正缺口

官方来源是 BATTER Zenodo record（论文引用版本
`https://zenodo.org/records/16761763`，后续 record `18863501`）。其中
`terminators.flanked.fa.gz` 是扩增后的模型训练序列，不是 FASTQ，也不是当前 BTED 实验端点表。

此前本地核查记录为：

- 文件 487,584,624 bytes，MD5 `643c53efed144376b2ad14f5d341c4a5`，gzip 完整；
- 2,532,438 条序列：1,263,651 条正链、1,268,787 条负链；
- 5,626 条 header 含多个局部 span；
- 42,690 个唯一 FASTA OTU，其中 42,662 个可在 `combined-statistics.txt` 找到，
  28 个未匹配；
- header 保存 OTU/contig/window/strand 和窗口内 terminator span，BATTER 代码按
  0-based half-open 的局部 `[start,end)` 使用；
- 当前 S1_003 的 `GCF_000009045.1` / `NC_000964.3` 未发现直接对应；
  例如此前找到的 *B. subtilis* `OTU-8254` 对应
  `GCF_003665195.1` / `NZ_CP032852.1`，是不同 assembly。

以上数字来自此前完成的文件级核查；2026-09-06 临时文件已不存在，且本轮访问 Zenodo/HF 的网络
不可用，因此没有再次下载复算。接手人重新确认时，应把文件放在 `/private/tmp`，核对 MD5、
gzip、FASTA header 计数、strand 计数、OTU 集合及统计表 join；只把结果和来源写入 Git。

因此准确结论不是“C 完全没有数据”，而是：

1. 可以做不依赖基因组位置的序列级数据集介绍或分布统计；
2. 不能把局部窗口坐标直接画到 S1_003；
3. 若要成为 JBrowse 轨道，需要获得相同 reference 的 contig identity，或建立并验证
   sequence-to-reference alignment / cross-assembly liftover；
4. 映射产物必须记录目标 assembly、contig、strand、唯一/多重匹配、坐标换算和失败原因。

不能利用附近的 Rend-seq signal、B 类端点或 D 类预测来反推 C 的坐标。

## 5. 信号显示优化

保留现有 raw BigWig 为科学真源。未来可新增派生显示：

```text
plus display  = +log10(1 + raw_plus)
minus display = -log10(1 + raw_minus)
```

派生轨道只能用于压缩动态范围和镜像链方向，不能覆盖 raw 文件。验收要求是：

- 页面和 track metadata 清楚标记变换公式；
- 用户仍能查看/下载 raw BigWig 和原始数值；
- 正负链使用一致变换和明确零点；
- 不把独立自动缩放后的视觉高度当成跨轨道定量比较；
- 若 JBrowse 默认 tooltip 不能同时显示 raw 与 transformed value，采用派生显示轨道与 raw
  轨道并存，不伪装成同一数值。

## 6. GTDB 扩展路线

当前 BTED 的 19 个可浏览 assembly 是“有实验来源且参考版本可核实”的集合。GTDB 是覆盖大量
细菌/古菌基因组的分类框架，扩展不应理解为把 GTDB 所有 genome 自动标为实验终止子。

推荐分阶段推进：

1. 建立 GTDB release、species cluster、representative genome 与 NCBI assembly 的版本化映射。
2. 优先扩展已有实验研究涉及的物种/菌株，保证 source manifest、reference、contig 和许可完整。
3. 对无实验数据的 GTDB genome，只发布明确标注的模型预测层，绝不进入实验 endpoint 统计。
4. 以 species cluster/representative genome 做批次试点，测量映射成功率、资产体积、预测量和成本，
   再决定扩大范围。
5. 每次扩展产生新 release version；不改写 `v0.2.0`。

## 7. 优先待办

1. 由维护者评审并决定是否部署本交接分支中的 S1_003 仪表盘、D pilot 和本地 proxy 修复。
2. 重新下载并复核 C 数据，产出序列级 catalogue；坐标映射另立可审计任务。
3. 设计 signed-log 派生信号资产及 raw-value 用户入口。
4. 定义 `endpoint_gene_context` 算法；目前仍为零，不得误报已计算。
5. 在隔离环境做 PostgreSQL/FastAPI 真实 smoke，或明确归档该备选路线。
6. 决定 preview 是否升级为 production/custom domain；正式发布前重新核对许可、线上版本和回滚方案。
