# BATTER S1_020 Dickeya dadantii 数据标准化记录

## 处理结论

本来源已经入库，但必须保持两个证据层，不能合并成“全部经过实验验证的 terminator”。

1. **实验端点主层**：Supplementary Table S2D，共 1,165 条。作者从 Nanopore native RNA-seq 的 read-end stop density 调用 putative TTS，因此本站标记为 `author_called_nanopore_native_rna_3prime_end`。
2. **作者整合注释层**：Supplementary Table S1C，共 2,021 条。该表综合 RNA-seq、Nanopore 端点以及 intrinsic/Rho-dependent terminator predictions，本站标记为 `author_integrated_mixed_evidence_tts`，并在每行保留警告。

## 来源与参考

| 项目 | 内容 |
|---|---|
| 论文 | Forquet et al., Mapping the Complex Transcriptional Landscape of the Phytopathogenic Bacterium Dickeya dadantii, mBio, 2022 |
| PMID / DOI | 35491820 / 10.1128/mbio.00524-22 |
| 实验数据 | E-MTAB-10482（Nanopore native RNA-seq） |
| 参考组装 | GCF_000147055.1 |
| 参考序列 | NC_014500.1，4,922,802 bp |
| 输入表 | `mbio.00524-22-st002.xlsx` S2D；`mbio.00524-22-st001.xlsx` S1C |

作者的方法说明：Nanopore native RNA 由 3′ 向 5′ 方向直接测序；作者统计每个位点结束的 RNA fragments，在基因 stop codon 下游 100 bp 范围内，以 5 bp 窗口 stop signal 和显著性阈值调用 S2D 端点。S1C 则来自后续跨数据集整合，因此证据性质不同。

## 标准化过程

执行：

```bash
python3 import_dickeya_published_tts.py
python3 build_additional_resources.py
python3 extract_batter_s1_registry.py
python3 build_bted_catalog.py
```

处理器执行以下检查：

- FASTA header 必须为 `NC_014500.1`；
- 所有 position 必须位于 1–4,922,802 且 strand 只能为 `+` 或 `-`；
- 同一证据层不允许重复的 position/strand；
- 生物学坐标保留为 1-based，BED 输出为 `[position-1, position)`；
- ID 包含 source、证据层、contig、strand 和序号；
- S1C 的 confidence、terminator type、relative strength 和 evidence warning 均保留。

## 结果

| 层 | 条目数 | + 链 | − 链 | 含义 |
|---|---:|---:|---:|---|
| Nanopore S2D | 1,165 | 531 | 634 | 作者从 native RNA read ends 调用的实验端点 |
| Integrated S1C | 2,021 | 1,378 | 643 | 作者整合 TTS；含实验信号与预测证据 |

S1C 中 terminator type 为 Intrinsic 555、Rho-dependent 244、Not found 1,222；`+pred` confidence 类别明确提示部分记录包含预测支持。

## 输出

目录：`data/dickeya/processed/BATTER_S1_020/`

- `nanopore_native_rna_3prime_ends.tsv/.bed`：主实验端点层；
- `author_integrated_tts.tsv/.bed`：混合证据注释层；
- `reference.fna/.fai`、`genes.gff3.gz/.tbi`：浏览器参考资产；
- `processing_summary.json`：统计和证据层说明；
- `SHA256SUMS.txt`：派生文件校验值。

## 遇到的问题与解决

- **问题：S1C 数量更多，看起来像更完整的终止位点表。** 但它不是纯实验端点集合。解决：S2D 作为实验主层，S1C 作为独立的 mixed-evidence annotation track。
- **问题：不能把 Nanopore 端点直接称为逐位点功能验证的 terminator。** 解决：使用“作者调用的 Nanopore native RNA 3′ end / putative TTS”，不升级证据措辞。
- **问题：网站原来只能下载一个 TSV。** 解决：详情页新增可选 `extraDownloads`，主下载仍为 S2D，S1C 以明确标签单独下载。

## 待人工复核

- 在 JBrowse 抽查正负链各至少 10 条，确认 strand、上游基因和坐标附近关系；
- 如后续下载 E-MTAB-10482 原始 FASTQ/比对文件重算 stop density，应建立新的“本站重分析”证据层，不覆盖作者 S2D；
- 对 S1C 中 `strong+pred`、`medium+pred` 和无预测三类分别抽样，检查页面标签是否足够清晰。
