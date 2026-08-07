# BTED 贡献指南

感谢你对 BTED（Bacterial Transcript 3′ End Database）感兴趣。本文件说明如何安全、可复现地向本仓库贡献内容。

## 1. 项目目标与不可协商的边界

BTED 收集**公开、可追溯、实验支持**的细菌转录 3′ end 数据。以下边界不可突破：

- 严格区分 `observed_signal`、`called_endpoint`、`author_called_endpoint`、`curated_record`、`author_integrated_mixed_evidence`、`prediction_only` 六层证据（详见 `docs/standards/证据分层与发布边界.md`）；
- **不得将预测或混合证据作为实验端点发布**。BATTER、RhoTermPredict、TransTermHP、ARNold 等预测结果只能进入内部审计层；
- “实验支持的 3′ end”不等于“每个位点均独立完成了终止功能验证”。候选端点不是终止子结论；
- 坐标、参考组装、链方向无法核实时，必须标记 `to_review` 或 `blocked`，不能猜测；
- 原始测序文件（FASTQ/BAM/BigWig）、出版商工作簿（xlsx/pdf）、缓存、私有资料、本地绝对路径**不得进入本仓库**。

## 2. 分支命名

| 类型 | 命名 | 示例 |
|------|------|------|
| 新来源接入 | `feature/source-<source_id>` | `feature/source-BTED_EXT_2026_001` |
| 标准/文档改进 | `feature/<主题>` | `feature/bted-v0.1-standards-and-structure` |
| 项目结构/重构 | `refactor/<主题>` | `refactor/project-structure-and-literature-notes-v0.1` |
| 仓库卫生清理 | `agent/<主题>` 或 `chore/<主题>` | `agent/repo-hygiene` |

- 不要直接在 `main` 上提交；
- 不要 force push；
- 基线分支以当前未合并分支中最新的公共点为起点，提交前 `git fetch origin`。

## 3. PR 流程

1. **开 Draft PR**：完成本地工作后push分支，并在 GitHub 上开 **Draft** PR；
2. **填写 PR 模板**：按 `.github/pull_request_template.md` 填写来源 ID、证据类别、参考/坐标、未完成事项、验证命令、禁传文件确认；
3. **评审**：由至少一名项目成员检查证据分层是否正确、坐标规则是否遵守、统计口径是否混写、是否夹带禁传文件；
4. **合并**：评审通过后由维护者合并；数据类 PR 必须逐来源审计后合并，不批量打包；
5. **合并后**：更新 `docs/WORKLOG.md` 与 `docs/HANDOFF.md`。

## 4. 新来源接入流程

详细教程见 `docs/standards/协作者_新增文献收集与入库指南.md`，核心步骤：

1. 判断文献是否适合收录（细菌、实验数据、公开可得）；
2. 填写 `data/registry/templates/external_literature_source_intake.tsv`（26 列）；
3. 核对菌株、参考组装、contig、坐标体系、链方向；
4. 核验通过后才建立 `data/registry/templates/external_literature_endpoint_schema.tsv`（24 列）；
5. 保存原始文件在本地 `raw/`（不进入 git），记录 SHA-256；
6. 在 `docs/sources/<source_id>/README.md` 写处理记录；
7. 运行验证命令，开 Draft PR。

## 5. 验证要求

提交前必须运行：

```bash
python3 scripts/validate_bted_templates.py   # 模板结构
python3 scripts/validate-site.py             # 站点产物（如改 site/）
git diff --check                             # 无空白错误
```

新增 Markdown 文档建议同时检查：

- 内部链接可解析；
- 无 `/Users/`、`/home/` 等本地绝对路径；
- 无 `实验验证` 等未批准证据标签（站点内容受 `validate-site.py` 扫描）。

## 6. 记录与交接

每个任务结束时更新 `docs/WORKLOG.md`；跨人/跨模型交接前更新 `docs/HANDOFF.md`。不要把重要上下文只留在聊天里。

## 7. 有疑问时

- 技术标准：查 `docs/standards/`；
- 字段含义：查 `docs/standards/数据字段字典_v0.1.md` 与 `data/registry/batter_s1_source_registry_dictionary.md`；
- 文献索引：查 `docs/literature/README.md`；
- 项目方向：先在 Issue 中讨论，避免做大量未对齐的工作。
