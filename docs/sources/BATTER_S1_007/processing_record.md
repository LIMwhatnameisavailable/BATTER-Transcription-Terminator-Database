# BATTER_S1_007 | S. lividans 2019 Term-seq TEP 标准化处理记录

## 来源

- 论文：Lee et al., *The Transcription Unit Architecture of Streptomyces lividans TK24*（2019）
- PMID：`31555254`
- DOI：`10.3389/fmicb.2019.02074`
- 原始测序：ENA `PRJEB31507`
- 作者端点表：Supplementary Dataset 3，`Table_6.XLSX`
- 许可：论文与补充材料为 CC BY
- 补充材料下载：`https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6742748/supplementaryFiles`
- 工作簿 SHA-256：`4dc71204ce32f16044204ace7b659abaafb2068d39be0c61f9f0c8340d852956`

## 为什么必须与 BATTER_S1_013 分开

BATTER_S1_007 和 BATTER_S1_013 都是 *S. lividans* TK24，也都使用 `GCF_000739105.1 / CP009124.1`，但它们来自不同论文和端点表。S1_007 是 2019 原论文的 1,640 个 TEP；S1_013 是 2020 Scientific Data 汇总表中的 1,208 个作者 TTS。本站使用独立 source ID、record ID、目录、TSV 和 JBrowse 配置，禁止相互覆盖。

## 数据含义

作者明确说明 Term-seq 缺少可区分“转录终止”与“转录后加工”的对照，因此这些记录是 transcript 3′-end positions（TEP），不是全部都可称为已验证 terminator。BTED 证据类别为 `author_called_termseq_tep`。

## 坐标与标准化

作者表字段为 `Position / Intensity / Strand / Category / Associated gene`。Position 按 `CP009124.1` 的 1-based 坐标保存；BED 转换为 `[Position-1, Position)`。每条 ID 包含 source、sample、contig、strand 和序号。

```bash
python3 \
  import_sliv2019_published_teps.py
```

## 结果

- TEP 总数：1,640；
- 正链：811；负链：829；
- 分类：P 1,200；S 115；N 89；A 100；C 136；
- 参考序列：CP009124.1，8,345,283 bp；
- 基因注释：7,425 条；
- 所有坐标范围、链、BED 转换和唯一 ID 检查通过。

产物目录：`data/sliv2019_lee/processed/BATTER_S1_007/`。网站资产使用 `lee2019_sliv` 前缀，配置为 `browser/jbrowse2/viewer/lee2019_sliv.config.json`。

## 遇到的问题

PMC 直接点击补充表会返回 “Preparing to download” HTML，不能当作 XLSX 读取；OA tar 链接也返回 404。最终通过 Europe PMC `supplementaryFiles` API 下载 ZIP，并核对内部 `Table_6.XLSX` 文件类型和工作簿结构。失败入口与下载文件保存在 `data/source_audit/BATTER_S1_007/`。
