# BATTER_S1_022 标准化处理记录

## 入库结论

作者 Supplementary Table S3 的 2,567 条 Term-seq TTS 已作为
`author_called_endpoint` 接入。表内的结构或预测软件列只保存在
`source_annotations.tsv` 中，不能改变核心端点的证据类别。单独的
RhoTermPredict RUT 预测表共 29,096 条，不进入公开端点表和 JBrowse。

| 项目 | 值 |
|---|---|
| 论文 | Premature termination of transcription in *Mycobacterium tuberculosis* |
| PMID / DOI | 37096044 / 10.1016/j.isci.2023.106465 |
| 原始数据 | E-MTAB-11753 |
| 实验方法 | Term-seq |
| 作者坐标参考 | AL123456.3 |
| BTED assembly / contig | GCF_000195955.2 / NC_000962.3 |
| 输入表 | `mmc4.xlsx`，Table S3 “Classification of TTS” |

## 参考坐标核验

来源快照分别保存了 AL123456.3 与 NC_000962.3 的参考序列。处理摘要记录两条序列
完全一致，长度均为 4,411,532 bp，因此作者表的 1-based 坐标可直接对应到
GCF_000195955.2 / NC_000962.3，不进行 liftover 或位置偏移。公开表同时保留
`published_reference_accession=AL123456.3` 和 `reference_name=NC_000962.3`，避免隐藏
该映射决策。

## v0.2.0 工程核查

- 记录数 2,567；正链 1,269，负链 1,298；
- 所有记录均来自 `Table S3 / mmc4.xlsx, Classification of TTS`；
- `(contig, coordinate, strand)` 无重复；
- 每行均满足 1-based 到 BED 0-based half-open 的转换规则；
- 所有核心记录均为 `author_called_endpoint`，不存在 `prediction_only` 行；
- 预测支持字段被标记为 `prediction_annotation`，只存在于来源特异表；
- 确定性首位、中位、末位抽查见
  `data/audit/v0.2.0/priority_source_audit.json`。

以上检查属于文件与坐标一致性验证，不重新评估作者的 TTS 分类。

## v0.2.0 输出

目录：`data/public/v0.2.0/records/BATTER_S1_022/`

- `endpoints.tsv`：24 列核心端点表；
- `source_annotations.tsv`：作者 ID、分类、分值及预测支持等 29 个来源字段；
- `endpoints.bed`：BED6；
- `fields.json`：逐字段类型、单位、原列名和证据属性；
- `manifest.json`：论文、数据入口、参考、决策和限制；
- `SHA256SUMS.txt`：发布文件校验和。

## 可复现命令

```bash
python3 scripts/build_v0_2_release.py --input-root /path/to/BGIRNA
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_bted_v0_2.py
python3 scripts/build_jbrowse_release.py --input-root /path/to/BGIRNA
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
```

## 已知限制

- 原始工作簿、FASTQ 和参考序列不提交 Git，详情页链接到论文与 E-MTAB-11753；
- 直接坐标对应依赖已记录的序列一致性核验；若以后更换 assembly，必须重新核对；
- 预测列是作者附加注释，不可筛选后另称为实验端点集合。
