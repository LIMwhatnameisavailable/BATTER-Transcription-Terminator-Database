# BTED 网页维护文档

## 1. 网页是什么

**BTED (Bacterial Transcript 3′ End Database)** — 细菌转录 3′ 端数据库。将已发表论文中的转录终止位点数据整理为标准格式，提供浏览、下载和 JBrowse 可视化。v0.2.0 demo 版: **22 来源 · 13 论文 · 28,399 条记录 · 20 基因组 · 21 套 JBrowse**。

## 2. 网站结构 (当前线上版)

```
site/                      ← 纯静态站点 (HTML/CSS/JS，无需数据库)
├── index.html             ← 首页
├── sources.html           ← 来源表格 (22 来源 × 20 基因组，可筛选)
├── catalog.html           ← 下载页面
├── methodology.html       ← 数据方法与标准
├── about.html             ← 关于
├── records/BATTER_S1_*.html ← 22 个来源详情页 (构建时生成)
├── css/style.css          ← 单文件 CSS
├── assets/site.js         ← 语言切换 + 表格过滤 (~57 行)
└── data/catalog.json      ← 来源目录数据 (构建时生成)
```
- **中英双语**：`data-lang` 属性 + `.i18n-en/.i18n-zh`，JS 切换记忆
- **数据来源**：`data/public/v0.2.0/` 下的 TSV/BED/JSON 文件

## 3. 部署方式

```
main 分支 → GitHub Actions (手动触发，传 release_tag)
         → 下载 JBrowse 大资产 (GitHub Release 中)
         → 验证数据 + 拼装 _site → GitHub Pages
```
部署入口：GitHub → Actions → "Deploy BTED Pages" → `workflow_dispatch`

## 4. v0.3 预开发版 (handoff 分支)

队友开发但**没上线**：`Cloudflare Worker + D1 (SQLite) + Hugging Face 固定版本资产`，复用 `site/` 目录。当前线上 v0.2.0 无需这些服务。**需你的 GitHub / Cloudflare / HF 账号**才能接入。

## 5. 怎么修改

**改数据**：改 `data/registry/` 登记表 → 更新 `data/public/v0.2.0/records/` 数据 → 运行 `build_v0_2_site.py` 重新生成页面 → 运行 `validate_bted_v0_2.py` 验证 → 提交 PR → main → 触发部署。

**改样式/交互**：直接修改 `site/css/style.css` (单文件) 或 `site/assets/site.js`。

**加新页面**：在 `site/` 下新建 `.html` 复用 `<header>/<footer>` 模板 → 更新 `catalog.json` 和导航栏。

## 6. 常见问题

| 症状 | 原因 | 解决 |
|---|---|---|
| Sources 页空白 | `catalog.json` 损坏 | 重新运行 `build_v0_2_site.py` |
| JBrowse 打不开 | Release 资产路径不对 | 检查 Release 的 tar.gz 结构 |
| 下载 404 | 数据文件缺失 | 检查 `data/public/v0.2.0/` |
| 语言切换不生效 | site.js 或 localStorage 异常 | 检查浏览器控制台 |
| 新来源不显示 | `catalog.json` 未更新 | 运行构建脚本 |

## 7. 你需要向队友要什么

1. **GitHub** → `seu-yolo/BATTER-…` 仓库 Write 权限
2. **Cloudflare** → 加入团队，能 `wrangler whoami` + 只读 D1 (v0.3 用)
3. **Hugging Face** → 加入 `seu-yolo/BTED-v0.3-assets` 读取权限 (v0.3 用)
4. **JBrowse 大资产** → 确认你能下载 `BTED-v0.2.0-jbrowse-assets.tar.gz`
5. **验收** → 让队友带你过 `DEMO_AND_ACCEPTANCE.md` 的 20 分钟讲解

## 8. 你能独立修改吗？

- ✅ **改文字/样式/布局** — 直接改 HTML/CSS，本地预览
- ✅ **加已有格式的新来源** — 填 registry 模板，运行构建脚本
- ✅ **重新部署** — GitHub → Actions → 手动触发
- �? **v0.3 上线** — 需队友协助首次配置 Cloudflare/HF
- ❌ **加新数据格式/证据层** — 需理解数据标准 SOP 和构建脚本
- ❌ **JBrowse 大资产** — 生成来自队友持有的原始数据 (BigWig/GFF)