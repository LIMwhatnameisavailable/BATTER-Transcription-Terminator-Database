# data/registry/templates — 协作入库模板

本目录包含两个核心 TSV 模板，用于向 BTED 贡献新来源和端点记录。

| 文件 | 用途 | 列数 |
|------|------|------|
| `external_literature_source_intake.tsv` | 来源级登记表：一行代表一个可独立处理的来源 | 26 |
| `external_literature_endpoint_schema.tsv` | 端点级登记表：一行代表一个端点或作者表中的一个可追溯观测 | 24 |

## 使用方式

1. 在本地复制模板，为每篇新文献/每个新来源填写一行；
2. 同一论文若包含多个物种、菌株或参考版本，应拆分为多行；
3. 填写完成后运行 `python3 scripts/validate_bted_templates.py` 校验表头与必填列；
4. 不要在本目录中直接修改两个模板文件的列名或列顺序。

## 字段说明

详见 [`docs/standards/数据字段字典_v0.1.md`](../../../docs/standards/数据字段字典_v0.1.md)。
