# BATTER S1_008 Pseudomonas aeruginosa PAO1 Term-seq 处理记录

## 结论

本来源分成两个作者数据层：Table S1B 的 1,965 个 reproducible Term-seq 3′ sites 为实验端点主层；Table S1A 的 gene-associated TTS 为作者解释层。两层只有 460 个 position/strand 重合，不能强行合并。

参考组装为 GCF_000006765.1，序列 `NC_002516.2`，长度 6,264,404 bp。原始项目为 PRJEB31965。

## 数量冲突

论文正文称鉴定 804 个与基因或操纵子相关的 TTS，但补充表 S1A 实际包含 805 条非 NA 记录，且对应 805 个唯一 position/strand。未找到越界、重复或非法 strand，因此本站不擅自删除其中一条：保留全部 805 行，并在输出每行加入 `count_discrepancy_warning`。

## 输出与证据边界

- `reproducible_termseq_3prime_sites.tsv/.bed`：1,965 个可重复实验 3′ 位点；
- `gene_associated_tts.tsv`：805 条作者基因关联解释；
- 两层分别显示在 JBrowse；
- Term-seq 3′ end 不自动升级为逐位点功能验证 terminator；
- 参考、gene GFF3、处理摘要和 SHA-256 位于 `data/paeruginosa/processed/BATTER_S1_008/`。

执行：`import_paeruginosa_termseq_sites.py`。初始核查中发现“正文 804 / 表格 805”和两层交集较低，这些不是静默修正项，已作为数据版本问题保留。
