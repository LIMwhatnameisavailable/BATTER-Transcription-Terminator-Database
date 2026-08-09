# BATTER_S1_018–019 | Synechocystis Term-seq TEP 标准化处理记录

## BATTER_S1_018：PCC 7338

- 论文：*Multi-Omic Analyses of Synechocystis sp. PCC 7338*；PMID `34054774`；
- 原始项目：`PRJNA629670`；
- 作者表：Supplementary Data S2；
- 结果：487 条 TEP，正链 259、负链 228；
- replicon：CP054306.1 478 条，CP054307.1/CP054308.1/CP054309.1 各 3 条；
- 类别：P 327、S 25、A 42、I 35、N 28、U 30。

作者表明确给出 Locus，因此四个 replicon 分别映射，不把质粒坐标并入染色体。

## BATTER_S1_019：PCC 6803

- 论文：*Regulatory Modes of Synechocystis sp. PCC 6803*；PMID `34874777`；
- 原始项目：`PRJNA666973`；
- 作者表：Table S5；
- 参考：论文方法明确为 `NC_000911.1`；
- 结果：784 条 TEP，正链 383、负链 401；
- 类别：P 496、S 57、A 66、I 103、U 62。

作者说明 P/S TEP 经 RNA-seq profile 人工整理，I/A/U 也通过 profile 人工识别；本站保留为 `author_called_termseq_tep`，不进一步宣称逐位点独立验证。

## 标准化过程

```bash
python3 \
  import_synechocystis_published_teps.py
python build_additional_resources.py
```

两套数据均保存作者 TEP ID、category、associated gene、1-based 坐标和规范 BED；生成独立 FASTA/FAI、gene GFF3/tabix、摘要、checksum、下载与 JBrowse 配置。

产物：`data/synechocystis/processed/BATTER_S1_018/` 和 `BATTER_S1_019/`。

## 遇到的问题

首次批量下载命令在 zsh 中把“来源编号 + PMC 编号”当作一个未拆分字符串，产生了两个带空格的空目录并导致 URL 404。空目录已删除，随后使用明确的来源目录和 URL 分别下载。此问题说明批量 shell 循环不能依赖隐式分词，后续应优先使用 manifest 或 Python 列表。
