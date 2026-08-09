# docs/legacy — 历史资料留档

本目录保存项目早期的探索性记录、初步文献核查笔记与未核实的推断，仅供溯源，不作为当前 BTED 标准结论或入库依据。

## 内容

- `literature-initial-review/` — 2026 年 7 月对 BATTER Table S1 13 篇论文的初评 README（原 `文献N-PMID*/README.md` 的逐份副本）。这些笔记包含 A/B/C 分类、坐标数据线索、第三方平台判断、待人工确认事项和后续动作建议，其中部分内容为推断或待核实，已在正式文献调研 README 中被重新校验并标注。
- `project-reports/` — 项目早期的补充材料核查、BATTER/Zenodo 审查和过程日志；它们用于追溯历史判断，不是当前发布接口。
- 各篇论文的当前正式结论请见 `docs/literature/PMID_XXXXXXXX/README.md`。

## 使用原则

1. 本目录内容只读、不用于自动化构建；
2. 正式文档与历史文档冲突时，以 `docs/standards/` 和 `docs/literature/` 的当前版本为准；
3. 历史笔记中提到的下载链接、登录号、文件名等仍可作为线索，但需重新核验。

## 已完成的目录清理

2026-08-10 已从当前 Git 树移除重复的 `original-directories/`、约 168 MB read-starts 文本和 `__MACOSX` 文件；正式文献说明保留在 `docs/literature/`，早期 README 保留在 `literature-initial-review/`。这次操作没有改写 Git 历史，旧文件仍可从旧提交恢复。执行与后续历史清理边界见 [`docs/cleanup-proposal.md`](../cleanup-proposal.md)。
