# BATTER S1_009 Zymomonas mobilis Term-seq 处理记录

## 结论

Data Set S3 的 2,091 条最终 TTS 已标准化。作者并非只看到 3′ end 就称为终止：他们结合 TSS-seq 的 5′-monophosphoryl sites，将存在相邻下游 5′ 端或与 tRNA 重叠的端点归为 RNA processing sites，再从最终 TTS 集合中移除。

## 多 replicon

| 参考序列 | 类型 | TTS 数 |
|---|---|---:|
| CP023715.1 | chromosome | 2,040 |
| CP023716.1 | pZM32 | 20 |
| CP023717.1 | pZM33 | 20 |
| CP023718.1 | pZM36 | 10 |
| CP023719.1 | pZM39 | 1 |

五条参考序列均属于 GCF_003054575.1，并在同一个 JBrowse assembly 内发布。作者 legend 明确声明坐标为 1-based；BED 使用 `[position-1, position)`。

## 预测分离与问题

- `TTS_list` 是实验端点经过 processing-site 排除后的结果；
- `ttHP_predicted_terminators` 的 1,746 条纯 TransTermHP 预测没有作为实验轨道导入；
- TTS 表中的 `PreTerm` 仅作为“是否匹配预测”的属性保留；
- 正文称 617/2,040 个染色体 TTS 匹配 predicted terminator，而 `TTS_list` 的 PreTerm 列实际标记 616 条。本站采用逐行表格值，并记录这 1 条差异。

输出位于 `data/zmobilis/processed/BATTER_S1_009/`，包含标准 TSV/BED、五 replicon FASTA/FAI、gene GFF3/tabix、摘要和 SHA-256。执行脚本为 `import_zmobilis_termseq_tts.py`。
