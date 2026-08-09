# GitHub Pages 发布索引方案

**更新：** 2026-08-10
**对应数据版本：** v0.1 local snapshot

## 定位

GitHub Pages 用于展示 BTED 的项目说明、来源目录、发布状态和原始数据入口。它不是生产数据库，也不承担 JBrowse、原始数据下载或服务端查询。

当前静态站点位于 `site/`，由 `scripts/build_sources_page.py` 从来源注册表和发布状态表生成 `site/sources.html`。

## 当前展示范围

- 22 个来源的物种、方法、参考组装、PMID、原始数据登录号与坐标核查状态；
- v0.1 的逐来源发布判定、标准化记录计数与仓库内数据资产路径；
- 证据边界：预测和不可拆分的混合证据不进入公开端点数据；
- 方法、局限和 GitHub 文档入口。

端点 TSV/BED 保存在仓库的 `data/public/`，不复制到 Pages 产物。原始 FASTQ/BAM、出版商工作簿、FASTA/GFF、BigWig 和 JBrowse 不进入 Pages。

## 页面结构

| 页面 | 内容 | 数据来源 |
|---|---|---|
| `index.html` | 项目目的、v0.1 摘要、边界和下一步 | 手工维护，链接发布说明 |
| `sources.html` | 22 来源与 release 状态表 | `data/registry/batter_s1_source_registry.tsv` + `batter_s1_publication_status.tsv` |
| `catalog.html` | 外部公开数据登录号索引 | `data/audit/legacy/accession_list_verified.csv` 的既有静态目录 |
| `methodology.html` | 坐标、证据边界、局限 | 正式标准文档 |
| `about.html` | 项目与贡献入口 | 手工维护 |

## 部署建议

1. 从经过评审的分支构建 `site/`，不要直接部署个人本地工作目录。
2. 在 GitHub Pages 设置中选择 GitHub Actions 或专用部署分支，以 `site/` 作为唯一发布目录。
3. 部署前运行：

   ```bash
   python3 scripts/build_sources_page.py
   python3 scripts/validate-site.py
   python3 scripts/validate_bted_release.py
   ```

4. 部署后在 `/<repository-name>/` 子路径下抽查全部内部链接与来源目录计数。

## JBrowse 的后续发布条件

只有每个浏览器包同时有参考 assembly、FASTA/FAI、注释、轨道清单、文件 SHA-256、版本号、外部托管位置和来源级证据说明时，才在来源页加入 “Open JBrowse”。未达成时宁可显示“浏览器包待发布”，不放空链接。

## 安全与范围边界

- 不上传原始数据、补充工作簿、私有资料、凭据、令牌或本机绝对路径；
- 不把预测/混合证据显示为实验端点；
- 不在页面中声称所有 22 个来源均已发布；当前是 21 个标准化来源和 1 个仅审计来源；
- 每次发布后更新 `docs/WORKLOG.md`、`docs/HANDOFF.md` 与 release manifest。
