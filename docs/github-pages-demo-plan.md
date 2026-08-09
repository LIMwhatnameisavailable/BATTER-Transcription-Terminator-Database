# GitHub Pages 发布索引方案

**更新：** 2026-08-10
**对应数据版本：** v0.2.0

## 定位

GitHub Pages 用于展示 BTED 的项目说明、来源目录、逐来源记录页、标准化下载和 JBrowse。它是静态公开演示，不提供服务端数据库查询。

站点位于 `site/`，由 `scripts/build_v0_2_site.py` 从来源注册表和 v0.2 release manifest 自动生成。

## 当前展示范围

- 22 个来源的物种、方法、参考组装、PMID、原始数据登录号与发布状态；
- 22 个详情页；21 个公开来源提供标准下载和 JBrowse，S1_002 只展示审计原因；
- 英文默认、中文切换；按物种、方法、年份、证据和状态筛选；
- 证据边界：预测和不可拆分的混合证据不进入公开端点数据；
- 方法、局限和 GitHub 文档入口。

小型 TSV/BED 保存在仓库的 `data/public/v0.2.0/`，部署时复制到 Pages artifact 的 `downloads/`，因此详情页不依赖默认分支的 raw URL。JBrowse 参考与轨道从 GitHub Release 固定版本资产解压到 `jbrowse/`；原始 FASTQ/BAM/WIG 和出版商工作簿不进入 Pages。

## 页面结构

| 页面 | 内容 | 数据来源 |
|---|---|---|
| `index.html` | 项目目的、v0.2 摘要和证据边界 | release manifest |
| `sources.html` | 22 来源筛选目录 | registry + release manifest |
| `catalog.html` | 逐来源标准下载和 Release 入口 | release manifest |
| `methodology.html` | 坐标、证据边界、局限 | 正式标准文档 |
| `about.html` | 项目与贡献入口 | 手工维护 |
| `records/*.html` | 来源、参考、数量、限制、下载和 JBrowse | 22 份来源 manifest |

## 部署建议

1. 从经过评审的分支构建 `site/`，不要直接部署个人本地工作目录。
2. 发布 `BTED-v0.2.0-jbrowse-assets.tar.gz` 及其 SHA-256 到同名 GitHub Release。
3. 在 GitHub Pages 设置中选择 GitHub Actions；工作流下载固定 Release 资产后组合 `_site/`。
4. 部署前运行：

   ```bash
   python3 scripts/validate_bted_v0_2.py
   python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
   python3 scripts/stage_pages.py --jbrowse-dir dist/BTED-v0.2.0-jbrowse --output-dir .pages-preview
   python3 scripts/validate-site.py .pages-preview
   ```

5. 部署后在 `/<repository-name>/` 子路径下抽查首页、筛选、S1_002、S1_005 双 contig 和至少一个作者端点来源。

## JBrowse 发布条件

每个公开浏览器配置必须有参考 assembly、FASTA/FAI、注释、轨道清单、SHA-256、版本号和来源级证据说明。v0.2.0 恰好 21 份配置；S1_002 无按钮。所有资产带 source 前缀，多 contig 保持在同一 assembly 中。

## 安全与范围边界

- 不上传原始数据、补充工作簿、私有资料、凭据、令牌或本机绝对路径；
- 不把预测/混合证据显示为实验端点；
- 不在页面中声称所有 22 个来源均已发布；当前是 21 个标准化来源和 1 个仅审计来源；
- 每次发布后更新 `docs/WORKLOG.md`、`docs/HANDOFF.md` 与 release manifest。
