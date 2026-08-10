# BTED 数据入库标准流程 v0.2

本 SOP 面向数据库整理，不要求接入者重新解释论文结果。所有判断必须能回到论文、补充表、公共 accession 和参考序列。

## 1. 来源登记

1. 分配唯一 `source_id`；同物种、不同论文或参考版本不能复用 ID。
2. 填写论文、物种/菌株、方法、样本 accession、参考版本和数据入口。
3. 确认来源类型：`raw_signal` 或 `published_endpoint_table`。
4. 登记许可为 `verified_redistributable`、`external_link_only` 或 `to_review`。

完成标准：来源 manifest 可独立说明数据来自哪里；缺失项写明原因，不猜测。

## 2. 原始输入审计

### 2.1 原始信号型

- 保存远程 URL、accession、文件名、大小和 SHA-256；
- 核对样本、链特异性、contig 名称和参考版本；
- WIG/bedGraph/BAM 转为浏览器信号时保留转换命令和工具版本；
- 本站调用的峰只能标为 `called_endpoint`/candidate，不能冒充作者端点。

### 2.2 作者端点表型

- 保存表名、sheet、表头、行数和 workbook checksum；
- 明确坐标是 0-based/1-based、点坐标/区间、正负链规则；
- 直接保留作者端点定义，不用统一算法重新解释；
- 混合实验/预测表必须拆层；不能可靠拆分则保持 `audit_only`。

## 3. 参考与坐标

1. 固定 assembly accession、contig accession 和 FASTA header。
2. 核对坐标范围和 strand 合法值。
3. BTED 核心表使用 1-based；BED6 使用 0-based half-open。
4. 多 contig 分别验证；任何匹配不得跨 contig。
5. 作者参考与浏览器参考不同时，必须记录序列一致性或正式 liftover 依据。

## 4. 两层标准化

1. 生成固定 24 列 `endpoints.tsv`。
2. 生成 `source_annotations.tsv`，通过稳定 `end_id` 关联作者原始字段。
3. 为每个原列指定字段属性、数据类型、单位、原列名和发布状态。
4. 无法放入主/附表的字段必须在 `fields.json` 说明舍弃或暂不发布原因。
5. 生成 BED、manifest 和 checksum。

## 5. 证据与发布门槛

始终分开：

- `observed_signal`
- `called_endpoint`
- `author_called_endpoint`
- `curated_record`
- `author_integrated_mixed_evidence`
- `prediction_only`

只有证据类别、参考、坐标、contig、strand 和来源均可核实的端点才能进入公开核心表。预测可作为附加注释，但不能改变证据类别。

## 6. JBrowse

1. 生成来源独立配置和带 source 前缀的资产。
2. 核对 FASTA/FAI、GFF/TBI、BED/BigWig 与配置引用。
3. 多 contig 必须在同一视图内可切换。
4. 未通过发布门槛的来源不显示 “Open JBrowse”。
5. 大型资产打包到 GitHub Release；Git 仅保存配置生成器、标准、小表和文档。

## 7. 网站

详情页至少显示来源、论文、数据 accession、assembly、坐标规则、证据类别、状态、记录数、限制、下载和浏览器入口。网页由 release manifest/registry 自动生成，禁止手工复制维护 22 份状态数据。

## 8. 质量控制与状态推进

推荐状态：`to_review → accessible → standardized → curated → published`；无法继续时为 `blocked`，并记录恢复条件。

发布前执行：

```bash
python3 scripts/validate_bted_templates.py
python3 scripts/validate_bted_v0_2.py
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
python3 scripts/validate-site.py site
python3 -m unittest -v tests/test_bted_ingestion.py tests/test_bted_v0_2.py
git diff --check
```

## 9. 问题记录

每个来源的 `processing_record.md` 必须保留：原问题、尝试过程、最终处理、仍未解决的风险和恢复条件。问题解决后不得删除原记录。共享代码或发布修改还需更新 `docs/WORKLOG.md` 与 `docs/HANDOFF.md`。

## 10. 流程图

可编辑流程图位于 [`docs/diagrams/BTED_v0.2_数据入库与发布流程.drawio`](../diagrams/BTED_v0.2_数据入库与发布流程.drawio)。
