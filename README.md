# BTED —— Bacterial Transcript 3′ End Database

BTED（Bacterial Transcript 3′ End Database，细菌转录 3′ end 数据库）是一个面向**公开、可追溯、实验支持**的细菌转录 3′ end 数据的标准化数据库项目。

本仓库是 BTED 的**协作与可复现性主仓库**：入库标准、来源登记模板、协作流程、站点演示与逐来源处理记录都通过本仓库评审和合并。原始测序数据与出版商补充工作簿不进入本仓库，仅以登录号 / DOI 链接到 GEO、SRA、ENA、ArrayExpress、Figshare、Zenodo 等公共仓库。

## 当前正式入口

- 协作流程与分支/PR 规范：[`CONTRIBUTING.md`](CONTRIBUTING.md)；
- 新增文献收集与入库教程：[`docs/standards/协作者_新增文献收集与入库指南.md`](docs/standards/协作者_新增文献收集与入库指南.md)；
- 入库标准与证据分层：[`docs/standards/BTED_数据入库标准流程_v0.1.md`](docs/standards/BTED_数据入库标准流程_v0.1.md)、[`docs/standards/证据分层与发布边界.md`](docs/standards/证据分层与发布边界.md)；
- 数据字段字典：[`docs/standards/数据字段字典_v0.1.md`](docs/standards/数据字段字典_v0.1.md)；
- 13 篇论文总索引：[`docs/literature/README.md`](docs/literature/README.md)；
- 22 个来源注册表：[`data/registry/batter_s1_source_registry.tsv`](data/registry/batter_s1_source_registry.tsv) 及其数据字典 [`data/registry/batter_s1_source_registry_dictionary.md`](data/registry/batter_s1_source_registry_dictionary.md)；
- 来源级处理记录目录：[`docs/sources/README.md`](docs/sources/README.md)。

## 收什么、不收什么

| 收录 | 不收录 |
|------|--------|
| 公开文献中实验支持的细菌转录 3′ end / TTS 坐标与元数据 | 纯计算预测位点（BATTER、RhoTermPredict、TransTermHP、ARNold 等） |
| 作者补充表中可追溯的实验端点（`author_called_endpoint`） | 无法核实参考版本、坐标体系或链方向的记录 |
| 按公开规则从实验信号调用的候选端点（`called_endpoint`，标注为候选） | 原始测序文件（FASTQ/BAM/BigWig）与出版商 xlsx/PDF —— 只链接 |
| 经审计的实验信号派生展示轨道（`observed_signal`） | 作者整合实验与预测的混合结果（`author_integrated_mixed_evidence`，仅内部审计） |

用词边界：“实验支持的 3′ end”不等于每个位点都独立完成了终止功能验证；候选端点不是终止子结论。详见 [证据分层与发布边界](docs/standards/证据分层与发布边界.md)。

## 统计口径（统一表述）

- **“13 篇原始研究文献”是论文数**（BATTER Table S1 来源文献，PMID 清单见 `report_BATTER_supplementary.md`）；
- **“22 个来源记录”是来源/物种数据记录数**（Table S1 中这些论文下的记录）；
- 两者单位不同，**不能混写为同一个“数据集数量”**；
- 在完成逐来源重新审计之前，任何公开页面不得声称“所有 22 个来源均已公开发布”，也不得声称“所有端点均为功能验证终止子”。

## 协作者入口

第一次参与请按顺序阅读：

1. [`CONTRIBUTING.md`](CONTRIBUTING.md) —— 分支命名、PR 流程、来源接入流程与验证要求；
2. [协作者：新增文献收集与入库指南](docs/standards/协作者_新增文献收集与入库指南.md) —— 照着做即可的教程，含一页式检查清单；
3. [数据入库标准流程（SOP v0.1）](docs/standards/BTED_数据入库标准流程_v0.1.md) —— 证据分层、坐标规则、状态定义；
4. [数据字段字典 v0.1](docs/standards/数据字段字典_v0.1.md) —— 两个模板全部 50 列的含义与合法值；
5. [项目目录与协作规范](docs/standards/项目目录与协作规范.md) —— 目录用途、命名、统计口径、PR 流程；
6. 登记模板：[`data/registry/templates/`](data/registry/templates/)（来源登记表 26 列、端点表 24 列）。

提交前校验：

```bash
python3 scripts/validate_bted_templates.py   # 模板结构（无第三方依赖）
python3 scripts/validate-site.py             # 站点产物
git diff --check
```

## 网站 demo

`site/` 是一个纯静态演示骨架（面向 GitHub Pages），用于演示目录与页面结构；**它不是完整的生产数据库**：不含坐标数据、不含 JBrowse、不含记录级条目。部署与边界见 [docs/github-pages-demo-plan.md](docs/github-pages-demo-plan.md)。

## 目录结构

```
README.md                  本文件
docs/
  standards/               入库标准与协作规范（v0.1）
  literature/              13 篇论文正式调研 README 与总索引
  sources/                 来源级处理记录（按 source_id 组织）
  legacy/                  历史探索性笔记（只读，不作为标准结论）
  tasks/                   分支任务计划
  HANDOFF.md               协作交接记录
  WORKLOG.md               工作日志
  current-bted-status.md   已核实现状 vs 待核实事项、迁移验收门槛
  cleanup-proposal.md      仓库卫生清理方案
data/
  registry/                来源级注册表与模板
  public/                  可公开标准化数据（预留，当前为空）
  audit/                   证据审计与排除记录（公开审计摘要）
scripts/                   校验脚本
site/                      GitHub Pages 静态演示骨架
CONTRIBUTING.md            贡献指南与 PR 流程
.github/                   PR 模板
文献N-PMIDxxxxxxxx/        13 篇来源文献的逐篇核查记录（保持现状）
```

## 来源注册表与数据字典

- 来源级注册表：`data/registry/batter_s1_source_registry.tsv`（22 行，一行一个来源记录）。
- 注册表数据字典：`data/registry/batter_s1_source_registry_dictionary.md`，解释 16 个历史字段含义、已知 `published_year` 冲突与 schema 改进方案。
- 新外部来源请使用 `data/registry/templates/external_literature_source_intake.tsv`（26 列）与 `external_literature_endpoint_schema.tsv`（24 列）。

## 历史资料

- `accession_list_verified.csv` —— 13 篇文献经核实的公开数据登录号；
- `data_verification_report.md` —— 逐篇补充材料核查报告（结论以其中校准表述为准）；
- `report_BATTER_supplementary.md` / `report_zenodo_and_documents.md` —— BATTER 补充材料与 Zenodo 仓库审查；
- `PROGRESS.md` —— 早期工作日志。

## 许可与反馈

项目自产内容（文档、站点代码、派生元数据）的许可证将在正式发布前评审确定；原始数据遵循各公共仓库与出版方条款，本项目只链接、不复制。问题与建议请通过 GitHub Issues 提交。
