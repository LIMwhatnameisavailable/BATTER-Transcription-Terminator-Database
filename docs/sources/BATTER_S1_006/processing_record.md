# BATTER S1_006 Streptococcus pneumoniae Term-seq 标准化处理记录

## 结论

Warrier et al. 2018 的 Supplementary Table S2 已导入，共 1,864 条作者从 pooled Term-seq（3′-end sequencing）数据调用的高置信 TTS，参考序列为 `NC_003028.3`。

论文给出的调用门槛是 coverage ≥10 且相对背景富集 ≥2 倍。表内 1,864 条记录全部满足该门槛，并通过参考范围和 BED 坐标转换检查。它们对应 1,811 个唯一 position/strand：52 个端点关联多个 locus，共产生 53 条额外表行。本站保留作者的 1,864 行关系，同时增加 `genomic_site_id`，没有静默去重。

## 来源与处理

| 字段 | 内容 |
|---|---|
| PMID / DOI | 30517198 / 10.1371/journal.ppat.1007461 |
| 公共数据 | SRP136114 |
| 参考组装 | GCF_000006885.1 |
| 参考序列 | NC_003028.3，2,160,842 bp |
| 输入 | `ppat.1007461.s006.xlsx`，sheet `TTS.10.1` |
| 执行 | `import_spneumoniae_termseq_tts.py` |

保留字段包括 locus、TTS、strand、coverage、enrichment、3′ UTR length、上下游序列、作者预测的 fold 和 MFE。结构字段作为附加注释保存；不能据此把每条记录表述为逐位点功能实验验证。

输出目录：`data/spneumoniae/processed/BATTER_S1_006/`。其中包含标准 TSV/BED、参考 FASTA/FAI、gene GFF3/tabix、处理摘要和 SHA-256。

## 问题记录

- S1 只给 assembly，作者表不重复写 contig。根据 TIGR4 组装和论文参考，统一映射至 `NC_003028.3`；FASTA、GFF 与全部坐标范围一致。
- 表中含 predicted fold/MFE，但 TTS 本身来自 Term-seq 富集阈值。网站将端点证据与结构预测措辞分开。
- 当前发布作者的端点表，没有从 SRP136114 原始 reads 重算信号；以后重分析必须作为单独版本，不能覆盖作者条目。
- 初次自动检查曾要求 position/strand 全部唯一，因此被 52 个多 locus 关联端点拦截。检查作者行后确认它们不是坐标错误；处理器改为同时保存唯一 `end_id`（每个作者表行）和可重复的 `genomic_site_id`（同一物理端点）。原失败原因和修复均保留在本记录中。
