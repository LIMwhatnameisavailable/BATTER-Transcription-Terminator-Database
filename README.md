# BTED — Bacterial Transcript 3′ End Database

BTED 将公开的细菌转录 3′ end 实验整理为可追溯、可下载、可在 JBrowse 中核对的标准数据。

本仓库保存数据标准、来源注册表、小型发布表、处理记录、构建脚本和网站源文件。原始 FASTQ/BAM/WIG、出版商工作簿与大型浏览器资产不进入 Git；它们通过公共 accession 或版本化 GitHub Release 提供。

## BTED v0.2.0

| 指标 | 当前数量 |
|---|---:|
| BATTER Table S1 来源记录 | 22 |
| 精确参考组装 | 20 |
| 原始研究论文 | 13 |
| 公开标准化来源 | 21 |
| `audit_only` 来源 | 1（BATTER_S1_002） |
| 核心记录 | 28,399 |
| 来源特异表 | 17 |
| JBrowse 数据集 | 21 |

v0.2.0 保留固定的 24 列核心端点表，并增加通过 `end_id` 关联的来源特异表、逐字段说明、manifest 和 checksum。纯预测和不可拆分的混合证据不会作为公开端点发布。

- [v0.2.0 发布说明](docs/releases/v0.2.0.md)
- [来源目录](data/registry/batter_s1_publication_status.v0.2.0.tsv)
- [发布 manifest](data/public/v0.2.0/release_manifest.json)
- [数据发布接口 v0.2](docs/standards/BTED_数据发布接口_v0.2.md)
- [数据入库 SOP v0.2](docs/standards/BTED_数据入库标准流程_v0.2.md)
- [可编辑 draw.io 流程图](docs/diagrams/BTED_v0.2_数据入库与发布流程.drawio)

## 数据边界

| 公开层 | 说明 |
|---|---|
| `observed_signal` | 经审计的实验信号展示层 |
| `called_endpoint` | 按公开规则从信号得到的本站候选端点 |
| `author_called_endpoint` | 作者补充表中的端点调用 |
| `curated_record` | 文献整理记录，保持其原始语境 |

`author_integrated_mixed_evidence` 与 `prediction_only` 只进入审计/注释层，不进入公开核心端点表。作者表中的预测支持列可以作为 `prediction_annotation` 保留，但不会改变端点的主要证据类别。

数据库中的“实验支持 3′ end”不等于每个位点均完成独立终止功能试验。

这里的 13 是原始研究论文数，22 是论文下拆分出的来源记录数，两者不是同一统计单位。v0.2.0 公开 21 个来源，`BATTER_S1_002` 仅保留来源审计，不能表述为“22 个来源均已公开发布”。

## 发布目录

```text
data/public/v0.2.0/records/<source_id>/
├── endpoints.tsv                 24 列核心表
├── source_annotations.tsv        来源字段，许可允许时提供
├── endpoints.bed                 BED6
├── fields.json                   字段类型、单位、原列名和证据属性
├── manifest.json                 来源、参考、状态与限制
└── SHA256SUMS.txt                 文件完整性
```

少数一对多信息使用单独附表，例如 `gene_associations.tsv` 和 `condition_observations.tsv`。`audit_only` 来源不会生成空端点表或 JBrowse 按钮。

## 本地构建

构建标准数据需要本地 BGIRNA 来源快照：

```bash
python3 scripts/build_v0_2_release.py --input-root /path/to/BGIRNA
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_bted_v0_2.py
python3 scripts/build_release_archives.py
```

构建 JBrowse 与网站：

```bash
python3 scripts/build_jbrowse_release.py --input-root /path/to/BGIRNA
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
python3 scripts/build_v0_2_site.py
python3 scripts/stage_pages.py \
  --jbrowse-dir dist/BTED-v0.2.0-jbrowse \
  --output-dir .pages-preview
python3 scripts/validate-site.py .pages-preview
python3 -m http.server 8000 --directory .pages-preview
```

随后访问 `http://localhost:8000/`。

## 验证

```bash
python3 scripts/validate_bted_templates.py
python3 scripts/validate_bted_release.py
python3 scripts/validate_repo_layout.py
python3 scripts/validate_bted_v0_2.py
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
python3 scripts/validate-site.py site
python3 -m unittest -v tests/test_bted_ingestion.py tests/test_bted_v0_2.py
git diff --check
```

## 网站与大型资产

`site/` 是英文默认、可切换中文的静态目录。网站以 20 个精确参考组装为主入口，同时保留 22 个来源详情页。参考组装完全相同的来源在一个基因组页面和 JBrowse 视图中显示为独立 track，不做跨来源去重或共识推断。

下载页支持按组装全选、多选并生成 ZIP。每个组装目录只突出 `endpoints.bed` 与一份汇总来源、文献、登录号、证据、限制和校验值的 `metadata.json`。GitHub Pages 工作流会从固定的 `v0.2.0` GitHub Release 下载 JBrowse 资产，再生成组装级下载包并部署。

- [组会展示教程（2026-08-12）](docs/demo/BTED_组会展示教程_2026-08-12.md)

Release 资产：

- `BTED-v0.2.0-data.tar.gz`
- `BTED-v0.2.0-data.tar.gz.sha256`
- `BTED-v0.2.0-jbrowse-assets.tar.gz`
- `BTED-v0.2.0-jbrowse-assets.tar.gz.sha256`

## 项目结构

```text
.github/workflows/       CI 与 GitHub Pages 部署
data/registry/           22 来源注册表、manifest、许可与发布状态
data/public/v0.2.0/      可公开的小型标准数据
data/audit/v0.2.0/       工程审计结果
data/audit/legacy/       早期资料搜集阶段的小型元数据快照
docs/releases/           版本说明
docs/sources/            逐来源处理记录
docs/standards/          SOP、字段与发布接口
docs/diagrams/           可编辑流程图
docs/literature/         当前正式文献说明
docs/legacy/             早期探索笔记和项目报告（只读）
scripts/                 构建、校验和打包脚本
site/                    自动生成的静态网站
tests/                   v0.1/v0.2 回归测试
```

## 协作

新增来源或修改共享规则前，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)、[SOP v0.2](docs/standards/BTED_数据入库标准流程_v0.2.md) 和 [证据分层与发布边界](docs/standards/证据分层与发布边界.md)。一个来源的处理记录、manifest、输入指纹、输出和验证结果应在同一个 PR 中评审。

## 历史资料

- [`data/audit/legacy/accession_list_verified.csv`](data/audit/legacy/accession_list_verified.csv)：早期资料搜集阶段形成的公开登录号快照，不替代正式 registry/manifest；
- [`docs/legacy/project-reports/`](docs/legacy/project-reports/)：早期项目报告和补充材料核查记录；
- [`docs/legacy/literature-initial-review/`](docs/legacy/literature-initial-review/)：13 篇论文的早期探索笔记；
- [`docs/literature/`](docs/literature/)：当前正式文献说明。

重复的旧整目录副本和 read-starts 原始计数已从当前 Git 树移除，未改写历史。原始实验文件继续通过公共 accession 获取，不在仓库中重复保存。
