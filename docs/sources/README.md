# docs/sources — 来源级（source-level）处理记录

本目录用于存放每个可独立处理来源的 manifest、处理记录与审计摘要。来源级文档与 `docs/literature/` 下的论文级（paper-level）文档是不同颗粒度的记录。

## source-level vs paper-level

| 维度 | `docs/literature/PMID_XXXXXXXX/` | `docs/sources/<source_id>/` |
|------|----------------------------------|-----------------------------|
| 粒度 | 一篇论文 | 一个可独立处理的来源（可能是一篇论文中的一个物种/菌株/参考版本/实验条件） |
| 内容 | 文献信息、公开数据入口、证据类别、参考/坐标、入库决定、已知问题 | 该来源的完整处理过程、checksum、坐标转换细节、QC 结果、失败/重试记录 |
| 状态 | 静态调研结论 | 随处理状态变化的动态记录 |
| 数量 | 13 篇论文 | 22 个 BATTER_S1 来源 + 未来 BTED_EXT 来源 |

**统计口径**：13 篇论文 ≠ 22 个来源记录。同一论文可贡献多个来源记录，同一来源记录也可能对应多个样本条件。

## 命名模板

每个来源建立独立子目录：

```
docs/sources/BATTER_S1_001/
  README.md                # 处理记录（含 evidence class、reference、coordinate、checksum、QC）
  processing_record.md     # 可选：详细处理记录
docs/sources/BTED_EXT_2026_001/
  README.md
  processing_record.md     # 可选
```

机器可读 manifest 固定存放在 `data/registry/manifests/<source_id>.json`，避免同一来源的 JSON 在文档和数据目录各维护一份。

## 当前范围

v0.1 local snapshot 已为 `BATTER_S1_001` 至 `BATTER_S1_022` 建立来源目录。每个目录均含：

- `README.md`：仓库发布判定、证据边界、公开数据入口和下一步；
- `data/registry/manifests/<source_id>.json` 对应的机器可读来源 manifest；
- 有本地详细处理记录的来源另含 `processing_record.md`。部分来源共享一篇批量处理记录；`BATTER_S1_005` 和 `BATTER_S1_022` 仍需补写独立的详细处理 Markdown，当前不把这一缺口伪装成已完成。

新来源仍按 `docs/standards/协作者_新增文献收集与入库指南.md` 与 `CONTRIBUTING.md` 创建独立目录。不要用新的来源覆盖已有 `source_id`。

## 与 data/registry 的关系

- `data/registry/batter_s1_source_registry.tsv` 是来源级注册表（一行 = 一个来源）；
- `docs/sources/<source_id>/README.md` 是该来源的完整人类可读处理记录；
- 两者由 `source_id` 关联。
