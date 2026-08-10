# data/registry —— 来源级注册表与模板

本目录是 BTED 协作入库的登记入口，存放来源级（source-level）注册信息与表结构规范。

## 内容

- `batter_s1_source_registry.tsv` —— BATTER Table S1 的 22 个来源登记；
- `batter_s1_publication_status.tsv` —— v0.1 release 对每个来源的公开发布判定、主资产、记录数与证据层；
- `manifests/BATTER_S1_*.json` —— 22 个来源的机器可读 manifest，包含可复现性链接与仓库发布信息；
- `templates/external_literature_source_intake.tsv` —— 外部文献来源登记模板（26 列）。一行代表一个可独立处理的来源；同一论文中的不同物种、菌株、实验体系或参考版本应拆成多行。
- `templates/external_literature_endpoint_schema.tsv` —— 端点标准表头（24 列）。一行代表一个端点或作者表中一个可追溯的观测；只有通过坐标核验的来源才建立端点表。

两个表必须分离填写：论文信息、样本信息和端点坐标不能混在同一张表里。

## 使用方式

1. 按 [协作者指南](../../docs/standards/协作者_新增文献收集与入库指南.md) 复制模板到自己的来源目录并填写；
2. 字段含义、必填级别与合法值见 [数据字段字典](../../docs/standards/数据字段字典_v0.1.md)；
3. 提交 PR 前运行结构校验：

   ```bash
   python3 scripts/validate_bted_templates.py
   ```

## 编号规则

- 新外部来源的 `source_id`：`BTED_EXT_年份_三位序号`（例如 `BTED_EXT_2026_001`），序号先到 `data/registry/` 与 `docs/WORKLOG.md` 确认未被占用；
- BATTER Table S1 既有来源沿用 `BATTER_S1_NNN` 编号，协作中不修改；
- `dataset_id` 使用小写英文短横线 slug（例如 `ecoli-termseq-author-2024`）。

## 边界

- 本目录只放登记表、schema 与小型元数据；端点级数据文件在逐来源审计通过前不进入本目录；
- 作者原始补充表必须原样冻结保存在提交者本地，登记其文件名与 SHA-256，不复制进 git；
- 本地 `raw/`、下载缓存与临时文件不进 GitHub（见根目录 `.gitignore`）。
