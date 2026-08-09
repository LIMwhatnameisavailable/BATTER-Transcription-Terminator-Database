# BATTER_S1_010–016 | Lee 2020 Streptomyces Term-seq 批量处理记录

## 数据来源与处理边界

论文：Lee et al., *Genome-scale determination of 5′ and 3′ boundaries in Streptomyces genomes*, Scientific Data (2020)，PMID `33319794`，DOI `10.1038/s41597-020-00775-w`。

作者端点表：Figshare `Dataset 2. The predicted transcription termination sites of Term-Seq`，DOI `10.6084/m9.figshare.13251158.v1`，文件 `Dataset_figshare_2.xlsx`，许可 `CC0`。

- 下载 URL：`https://ndownloader.figshare.com/files/25517291`
- MD5：`ddb9c64604d288e1eea4e11385dc2ebf`（与 Figshare 元数据一致）
- SHA-256：`b5be27485e99d838f90bea1909ba54d959c66fe877a912576a6d368ad8ba12b9`

本批次直接导入作者发表的 `Reference genome / Strand / Position / z-score`，不从原始 reads 重新调用峰。证据类别统一为 `author_called_termseq_tts`。

## 坐标判断

作者表给出单碱基 genomic Position。BTED 将其作为 1-based 生物学坐标保存，并导出 BED `[Position-1, Position)`。所有位置均通过参考序列长度检查。标准 TSV 同时保存作者未带版本的 accession 和 NCBI 版本化 reference name。

## 已完成的七个来源

| source_id | 物种 | 参考 contig | 端点数 | + / − | 基因注释 |
|---|---|---|---:|---:|---:|
| BATTER_S1_010 | *S. avermitilis* | BA000030.4 | 1,159 | 619 / 540 | 7,676 |
| BATTER_S1_011 | *S. griseus* | NC_010572.1 | 2,024 | 1,003 / 1,021 | 7,119 |
| BATTER_S1_012 | *S. coelicolor* | NC_003888.3 | 1,308 | 658 / 650 | 7,680 |
| BATTER_S1_013 | *S. lividans* | CP009124.1 | 1,208 | 572 / 636 | 7,425 |
| BATTER_S1_014 | *S. tsukubensis* | CP020700.1 | 1,283 | 659 / 624 | 6,469 |
| BATTER_S1_015 | *S. clavuligerus* | CP027858.1、CP027859.1 | 1,140 | 564 / 576 | 6,897 |
| BATTER_S1_016 | ATCC 15439（论文/ATCC：*S. venezuelae*；NCBI CP059991.1：*S. gardneri*） | CP059991.1 | 870 | 448 / 422 | 8,122 |

合计 8,992 条作者端点。每个来源输出 `published_termseq_endpoints.tsv/.bed`、参考 FASTA/FAI、gene GFF3/tabix、`processing_summary.json` 和 `SHA256SUMS.txt`，并使用独立来源前缀接入 JBrowse。

`BA000030.4` 是作者表使用的 GenBank accession；S1 写的是 RefSeq assembly `GCF_000009765.2`。自动比较确认 BA000030.4 与该组装 chromosome `NC_003155.5` 序列长度均为 9,025,608 bp，序列 SHA-256 完全一致，因此基因注释 seqid 可有证据地映射到 BA000030.4。

## BATTER_S1_016 分类名称冲突及解决

S1、论文、ENA 样本和 ATCC 把生物材料写作 *Streptomyces venezuelae* ATCC 15439，同时论文明确说明 reads 映射到 `CP059991`。NCBI assembly report 和 FASTA header 则把 `GCF_015710995.1 / CP059991.1` 标为 *Streptomyces gardneri* ATCC 15439。CP059991 的提交记录来自论文同一团队，标题仍写作 *S. venezuelae* ATCC 15439，并说明它以另一条 *S. venezuelae* ATCC 15439 序列 `CP013129` 做 reference-guided assembly。

处理决定：坐标证据链能够闭合，因为论文、作者表和参考序列均明确指向 CP059991.1；因此解除坐标阻塞并接入端点轨道。分类学标签不强行二选一：详情页与 TSV 使用双标签，注册表标为 `verified_with_taxonomy_conflict`，并永久保留 ATCC/ENA 与 NCBI 的差异。该处理解决的是“能否按 CP059991 展示坐标”，不是宣称已经解决菌株分类学争议。

## 执行过程与遇到的问题

```bash
python3 \
  import_lee2020_published_endpoints.py
python -m unittest -v tests/test_bted_ingestion.py
```

- NCBI EUtils 下载 GenBank 时发生过 `LibreSSL SSL_ERROR_SYSCALL`，并出现未完整结束的记录。处理时保留问题，改用 NCBI assembly GFF 下载；发布前用 tabix 列出 contig 检查索引。
- 最新的 `NC_003888`、`NC_010572` GenBank 记录为 CON 形式，单一 flatfile 不适合作为完整基因注释来源。改用对应 GCF assembly 的 `genomic.gff.gz`。
- `S. clavuligerus` 作者表含 chromosome 与 plasmid 两个 replicon；按多 contig 规则在同一 assembly 中发布，未丢弃 plasmid。

软件：Python 3.13.9；openpyxl 3.1.5；bgzip/tabix 1.24。处理摘要位于 `data/streptomyces_lee2020/logs/import_summary.json`。
