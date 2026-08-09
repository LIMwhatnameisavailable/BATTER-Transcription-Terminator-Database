# BATTER_S1_017 | S. clavuligerus 2021 Term-seq TEP 标准化处理记录

## 来源

- 论文：Hwang et al., *Regulatory Elements for Transcription Termination in Streptomyces clavuligerus*（2021）
- PMID：`33947798`
- DOI：`10.1128/mSystems.01013-20`
- 公共数据：GEO `GSE128216`、`GSE138325`
- 作者表：Data Set S1，Sheet1
- 补充材料入口：`https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8269248/supplementaryFiles`
- 工作簿 SHA-256：`8ad63056ee5d9d79018b87bd26930e4e9e5aba7a50397810a62f59ce1dd9f317`

## 独立来源原则

BATTER_S1_017 与 BATTER_S1_015 使用相同菌株和组装，但来自不同论文。S1_017 的作者表包含 TEP ID、abundance、类别、RNA folding free energy 和平均 readthrough fraction；这些字段不能被 2020 汇总表替代。两者使用独立 source ID、目录、下载和 JBrowse 配置。

## 坐标映射

作者表的 `Location` 为 `Chromosome` 或 `Plasmid`：

- Chromosome → `CP027858.1`，6,748,591 bp；
- Plasmid → `CP027859.1`，1,795,495 bp。

`TEP position` 按 1-based 保存，BED 为 `[position-1, position)`。匹配和范围检查不得跨 replicon。

## 结果

- TEP 总数：1,427；
- chromosome：1,271；plasmid：156；
- 正链：695；负链：732；
- 类别：P 928、S 223、Pre 117、N 106、A 53；
- 基因注释：6,897 条；
- 作者原 TEP ID、abundance、category、FFE、readthrough 全部保留。

```bash
python3 \
  import_scla2021_published_teps.py
python build_additional_resources.py
```

产物：`data/scla2021_hwang/processed/BATTER_S1_017/`；网站配置：`browser/jbrowse2/viewer/hwang2021_scla.config.json`。

## 遇到的问题

工作簿的 `max_row` 不能直接当作 TEP 数：Sheet1 同时横向放置 TEP、TU 和 TUC 三类表，后两类的有效行数不同。处理器只读取左侧 TEP 区域，并以 `TEP ID` 非空作为记录条件，因此最终为 1,427 条，而不是工作表总行数 1,650。
