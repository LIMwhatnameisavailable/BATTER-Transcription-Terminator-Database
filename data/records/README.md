# data/records/ — BTED_EXT_* 外部来源端点表专用目录

本目录用于存放 **BTED_EXT_\*** 外部来源的标准化端点表，与 `data/public/v0.2.0/`（BATTER_S1_001–022 专属发布层）**相互独立**。

## 目录边界

| 目录 | 用途 | 来源编号 |
|---|---|---|
| `data/public/v0.2.0/records/` | BATTER_S1_001–022 的 v0.2.0 两层发布层（release_manifest 校验，22 源硬编码） | `BATTER_S1_001` ~ `BATTER_S1_022` |
| `data/records/`（本目录） | 外部文献来源的标准化端点表（本批次 BTED_EXT_2026_101–113 及其后续批次） | `BTED_EXT_2026_101` ~ `BTED_EXT_2026_113` |

## 结构约定

每个来源一个子目录，命名 `<source_id>/`，内含：

- `<source_id>_endpoints.tsv` — 24 列端点表（列定义见 `data/registry/templates/external_literature_endpoint_schema.tsv`）
- `<source_id>_endpoints.bed` — 对应 BED6 转换（`reference_name`、`pos-1`、`pos`、`end_id`、`0`、`strand`）

## 为什么独立于 data/public/v0.2.0/

`scripts/validate_bted_v0_2.py` 将 `EXPECTED_SOURCES` 硬编码为 `BATTER_S1_001`~`BATTER_S1_022`，且发布门禁校验 (21 public, 1 audit-only, 28,399 records, 21 JBrowse) 只对既有 22 源成立。外部来源若写入 v0.2.0 发布层，既无法被该校验器覆盖，也会污染已发布的 release_manifest 统计口径。因此外部来源端点表走本独立轨道，遵循《外部来源正式整合入库要求 v0.1》的 `data/records/<source_id>/` 路径约定。

## 批次索引

| 批次 | 目录 | 来源 |
|---|---|---|
| 2026-08-09 | `staging/2026-08-09_fuchs-cascino-termite/data/records/` | BTED_EXT_2026_101–113（Fuchs 2021 / Cascino 2026 / TERMITe 8 源） |
