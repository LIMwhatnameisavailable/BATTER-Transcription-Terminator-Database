# docs/legacy — 历史资料留档

本目录保存项目早期的探索性记录、初步文献核查笔记与未核实的推断，仅供溯源，不作为当前 BTED 标准结论或入库依据。

## 内容

- `literature-initial-review/` — 2026 年 7 月对 BATTER Table S1 13 篇论文的初评 README（原 `文献N-PMID*/README.md` 的逐份副本）。这些笔记包含 A/B/C 分类、坐标数据线索、第三方平台判断、待人工确认事项和后续动作建议，其中部分内容为推断或待核实，已在正式文献调研 README 中被重新校验并标注。
- 各篇论文的当前正式结论请见 `docs/literature/PMID_XXXXXXXX/README.md`。

## 使用原则

1. 本目录内容只读、不用于自动化构建；
2. 正式文档与历史文档冲突时，以 `docs/standards/` 和 `docs/literature/` 的当前版本为准；
3. 历史笔记中提到的下载链接、登录号、文件名等仍可作为线索，但需重新核验。

## 后续清理

仓库中已追踪的 `文献13-PMID38030608/` 下约 168 MB read-starts 文本文件与 `__MACOSX/` AppleDouble 垃圾文件的清理方案，见根目录 `docs/cleanup-proposal.md`。本目录不处理这些大文件。
