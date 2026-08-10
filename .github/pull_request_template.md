## 本 PR 接入/修改的 source_id

<!-- 例如：BTED_EXT_2026_001；如涉及多个请逐项列出 -->

## 数据证据类别

<!-- 从以下类别选择：observed_signal / called_endpoint / author_called_endpoint / curated_record / author_integrated_mixed_evidence / prediction_only -->

## 参考序列与坐标体系

<!-- 必填：参考组装（GCF/GCA 号）、contig 名称约定、坐标 1-based/0-based、链方向定义 -->

## 未完成事项

<!-- 例如：某条件数据未下载、某 contig 坐标待核对、许可证待确认等 -->

## 验证命令

<!-- 列出已运行的命令与结果 -->

```bash
python3 scripts/validate_bted_templates.py
python3 scripts/validate-site.py
git diff --check
```

## 确认框

- [ ] 本 PR 未包含原始测序文件（FASTQ/FASTQ.gz/FQ/BAM/CRAM/BigWig 等）
- [ ] 本 PR 未包含出版商工作簿（xlsx/pdf/zip）
- [ ] 本 PR 未包含大文件（>1 MiB 的二进制或原始数据）
- [ ] 本 PR 未包含私有资料、凭据、API key、本地绝对路径
- [ ] 本 PR 未将预测或混合证据作为实验端点发布
- [ ] 已按 `CONTRIBUTING.md` 运行验证命令且通过

## 其他说明

<!-- 评审人需要知道的补充信息 -->
