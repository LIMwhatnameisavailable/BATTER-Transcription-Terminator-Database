# BTED 当前交接

**更新：** 2026-08-16

**当前分支：** `feature/accession-range-prototype-v0.1`

**当前里程碑：** `GCF_000739105.1` accession/Range 架构试点已具备面向用户的双语检索页；页面、API、HTTP 206 和动态 JBrowse 均在本地跑通，真实 Cloudflare D1 与 Hugging Face 对象上传尚未授权或执行。

## 2026-08-16 用户化双语检索页

- 页面入口仍为 `http://127.0.0.1:8016/accession-range-demo.html`，但可见内容已从开发架构说明改为“检索—研究概览—浏览/下载”的科研用户流程。
- 顶部 EN/中文按钮即时切换导航、表单、动态状态、统计、研究表、证据标签、下载区与页脚；选择写入 URL 和 localStorage。
- 用户页不显示 D1、API route、对象存储路径或 Range 检查。技术实现仍保留在 `prototype/accession-range/`，自动测试仍直接验证 API 和 Range。
- 页面解释收录范围、单条记录含义和证据边界，并列出适合用途与不可直接推断的结论。
- S1_007/013 分别展示论文标题、2019/2020、实验方法、证据类别、记录数、PubMed、PRJEB31507、来源详情和来源特异解读，继续保持独立 track。

## 2026-08-15 accession/Range 架构试点

- 入口：`http://127.0.0.1:8016/accession-range-demo.html`；必须用 `scripts/run_accession_range_demo.py`，普通静态服务器不提供 `/api`。
- 试点 assembly：`GCF_000739105.1 / CP009124.1`；S1_007（1,640）和 S1_013（1,208）仍是两条独立 `author_called_endpoint` track。
- 参考 FASTA/FAI/GFF3/TBI 在两个旧来源资产中 SHA-256 完全一致；原型只解析一组共享对象，避免重复 8,628,614 bytes。
- D1 schema、seed、Worker 和说明位于 `prototype/accession-range/`；本地等价API位于 `scripts/run_accession_range_demo.py`。
- 生产 Worker 不接受任意远程 URL，只允许 D1 中登记的 asset key，并校验 origin host。
- 本分支只验证部署架构，没有上传外部服务、创建Cloudflare资源或改变公开科学数据。

## 2026-08-14 Genomes 科研目录改版

- 主表只保留 `Genome / Experimental data / Evidence / 3′ ends / Access`，不再让内部 Source ID、track 数和重复状态占据主视图。
- 物种/菌株是第一视觉层级；assembly accession 位于其下并链接 NCBI Datasets。
- 可按物种、实验方法和证据类别筛选，搜索仍覆盖 assembly、source ID 与原始数据 accession。
- `Select visible` 按当前筛选结果选择 assembly；批量 ZIP 为每个 assembly 保留独立目录，并包含 BED 与合并 metadata。
- 多篇研究使用同一精确 assembly 时，在同一个 genome 详情/JBrowse 中保留独立来源轨道，不把研究结果静默合并。
- 完整本地演示地址：`http://127.0.0.1:8015/sources.html`（需在仓库根目录运行 `.pages-preview` 的本地服务器）。

## 2026-08-14 JBrowse 可读性补强

- 四个 Rend-seq 默认窗口均自动选择同时含 `+`/`-` 候选的约 3 kb 区域，打开即可验证箭头方向。
- 轨道标题直接写明蓝色/正链/向右与橙色/负链/向左；来源页和 assembly 页另有一张英文读图卡。
- 合并候选轨道使用浏览器专用富属性 GFF3；点击端点可查看稳定 ID、1-based 坐标、strand、raw support、上下文和证据警告。公开标准 BED 不变。
- signed-log BigWig 使用 `bedGraphToBigWig -unc`，规避 JBrowse 2.17 对本机生成的压缩 BigWig 的 range 索引错误；这是 display-only 资产，原始 BigWig 未变。
- S1_003 实际浏览器检查 0 alert；完整校验与 15 项回归通过。

## 2026-08-13 JBrowse 正负链紧凑视图

- S1_001/003/004/005 默认仅打开基因、正负链配对信号、正负链合并候选端点三条轨道。
- 默认配对信号使用 display-only `sign(strand) × log10(1 + raw signal)`：正链在零线上方，负链在零线下方；原始 BigWig 不变，并保留在 `Full evidence view`。
- 合并端点 BED 保留原 BED6 坐标和 strand；候选仍是 `called_endpoint`，不改述为终止子。
- 构建时发现旧 E. coli viewer BED 被 B. subtilis 同名文件覆盖；现改从各来源 canonical `processed/` 目录复制，并增加 contig/strand 硬检查。核心公开表未受影响。
- JBrowse、Pages、15 项回归和实际浏览器检查全部通过；控制台无 warning/error。

## 2026-08-13 英文与 accession 更新

- 全站当前只输出英文，不显示尚未审校的中文副本或语言按钮；生成标签保留 `data-i18n-key` 供后续语言切换。
- 22 个来源详情页均有 **Raw data accessions** 区域；多个 accession 分别链接到 GEO、SRA、BioProject、ENA 或 BioStudies。
- 参考 assembly accession 可点击跳转 NCBI Datasets；assembly 页面也展示各来源的原始数据入口。
- genome 搜索支持 accession number。
- 完整 Pages 预览、站点校验、14 项回归测试和浏览器检查均通过。

## 2026-08-12 网站改版

- 20 个精确 assembly 作为主目录，22 个来源作为独立 track 和追溯记录；
- `GCF_000739105.1` 与 `GCF_005519465.1` 各有一套自动打开的双来源 JBrowse 视图；
- 下载页可全选/多选，输出按 assembly 分目录的 ZIP；
- 主要公开文件收敛为 BED + metadata，后台 24 列表、字段字典、manifest 与 checksum 不删除；
- 组会教程：[`demo/BTED_组会展示教程_2026-08-12.md`](demo/BTED_组会展示教程_2026-08-12.md)。
- feature 分支 Pages build 已成功，部署环境按策略拒绝非 `main` 分支；合并后 `push: main` 会触发正式部署。

## 已交付

- 22 个来源均有 manifest 和详情页；21 个来源公开标准数据，S1_002 为 `audit_only`。
- 21 个来源共 28,399 条 24 列核心记录；17 个许可允许的来源另有来源特异表。
- 每个公开来源有 BED6、字段清单、manifest 和 checksum。
- 21 套独立 JBrowse 配置；S1_005 的 CP009977.1/CP009978.1 位于同一 assembly。
- 双语静态网站包含首页、筛选目录、下载页、方法页、关于页和 22 个来源页。
- 数据/JBrowse Release 资产、CI、Pages workflow 和本地 Pages staging 已具备。
- S1_005、S1_020、S1_022 的工程审计和处理记录已补齐。
- 外部链接审计已保存为 `data/audit/v0.2.0/external_link_audit.tsv`，无失败或缺失必填入口。
- PR #3 的根目录清理已同步：旧报告和登录号快照归档，重复的 `docs/legacy/original-directories/`、read-starts 与 `__MACOSX` 已退出当前 Git 树；历史未改写。

## 接手前阅读

1. [`docs/releases/v0.2.0.md`](releases/v0.2.0.md)
2. [`docs/standards/BTED_数据入库标准流程_v0.2.md`](standards/BTED_数据入库标准流程_v0.2.md)
3. [`docs/standards/BTED_数据发布接口_v0.2.md`](standards/BTED_数据发布接口_v0.2.md)
4. [`data/public/v0.2.0/release_manifest.json`](../data/public/v0.2.0/release_manifest.json)
5. [`data/registry/batter_s1_publication_status.v0.2.0.tsv`](../data/registry/batter_s1_publication_status.v0.2.0.tsv)

## 重新构建

```bash
python3 scripts/build_v0_2_release.py --input-root /path/to/BGIRNA
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/build_release_archives.py
python3 scripts/build_jbrowse_release.py --input-root /path/to/BGIRNA
python3 scripts/build_v0_2_site.py
python3 scripts/stage_pages.py --jbrowse-dir dist/BTED-v0.2.0-jbrowse --output-dir .pages-preview
```

## 完整验证

```bash
python3 scripts/validate_bted_templates.py
python3 scripts/validate_bted_release.py
python3 scripts/validate_repo_layout.py
python3 scripts/validate_bted_v0_2.py
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
python3 scripts/validate-site.py site
python3 scripts/validate-site.py .pages-preview
python3 -m unittest -v tests/test_bted_ingestion.py tests/test_bted_v0_2.py
git diff --check
```

## 待完成

1. 审阅已同步 PR #3 结构清理的 Draft PR #4，保持串联 PR 的改动范围清晰。
2. 按 #1 → #2 → #3 → #4 顺序处理 PR 基线，避免直接把全部历史一次展开到 `main`。
3. 评审通过后发布 `v0.2.0` Release，再合并包含 Pages workflow 的分支。
4. 在 Settings → Pages 选择 GitHub Actions，运行部署并检查稳定链接。
5. S1_002 只有在未来能可靠拆出纯实验端点时才改变 `audit_only`。

## 远端发布状态

- 实现提交：`142e371 feat: build BTED v0.2 public demo`。
- 分支：`agent/bted-v0.2-public-demo`，已通过 SSH 推送。
- Draft PR：`https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database/pull/4`，CI 已通过。
- PR #3 结构清理提交：`61318db refactor: clean repository root and legacy assets`。
- `v0.2.0` Release 草稿包含四个发布资产；保持草稿，直至评审和 Pages 发布顺序确认。
- Pages workflow 仅允许手动触发；正式发布 Release 且管理员启用 Pages 后再运行，避免合并时产生预期失败。
- HTTPS OAuth 令牌仍缺少 `workflow` scope；继续推送本分支可使用已验证的 SSH 地址，无需重新构建数据。

## 不要做

- 不把协作者外部文献合入本分支；
- 不把混合证据或纯预测放进公开端点表/JBrowse；
- 不把作者预测注释解释为新的实验结果；
- 不把原始测序、出版商工作簿、大型 JBrowse 文件或凭据提交到 Git；
- 不在未确认参考、坐标、contig、strand 或许可时猜测补齐。
