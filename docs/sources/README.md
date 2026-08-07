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
  manifest.json            # 文件清单与校验和（迁移时创建）
docs/sources/BTED_EXT_2026_001/
  README.md
  manifest.json
```

## 本轮范围

本分支只建立本目录说明与命名模板，不批量复制或伪造 22 份处理记录。未来每接入一个新来源，由协作者按 `docs/standards/协作者_新增文献收集与入库指南.md` 与 `CONTRIBUTING.md` 创建对应目录。

## 与 data/registry 的关系

- `data/registry/batter_s1_source_registry.tsv` 是来源级注册表（一行 = 一个来源）；
- `docs/sources/<source_id>/README.md` 是该来源的完整人类可读处理记录；
- 两者由 `source_id` 关联。
