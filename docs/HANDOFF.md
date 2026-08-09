# BTED 当前交接

**更新：** 2026-08-10

**当前分支：** `agent/bted-v0.2-public-demo`

**当前里程碑：** v0.2.0 数据、网站、JBrowse 和完整本地验收已完成并提交；仅远端上传与 GitHub 发布因网络阻塞未完成。

## 已交付

- 22 个来源均有 manifest 和详情页；21 个来源公开标准数据，S1_002 为 `audit_only`。
- 21 个来源共 28,399 条 24 列核心记录；17 个许可允许的来源另有来源特异表。
- 每个公开来源有 BED6、字段清单、manifest 和 checksum。
- 21 套独立 JBrowse 配置；S1_005 的 CP009977.1/CP009978.1 位于同一 assembly。
- 双语静态网站包含首页、筛选目录、下载页、方法页、关于页和 22 个来源页。
- 数据/JBrowse Release 资产、CI、Pages workflow 和本地 Pages staging 已具备。
- S1_005、S1_020、S1_022 的工程审计和处理记录已补齐。
- 外部链接审计已保存为 `data/audit/v0.2.0/external_link_audit.tsv`，无失败或缺失必填入口。

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
python3 scripts/validate_bted_v0_2.py
python3 scripts/audit_v0_2_priority_sources.py
python3 scripts/validate_jbrowse_release.py dist/BTED-v0.2.0-jbrowse
python3 scripts/validate-site.py site
python3 scripts/validate-site.py .pages-preview
python3 -m unittest -v tests/test_bted_ingestion.py tests/test_bted_v0_2.py
git diff --check
```

## 待完成

1. 终端网络恢复后推送当前分支（含实现提交 `142e371` 和本状态记录）：`git push -u origin agent/bted-v0.2-public-demo`。
2. 建立 Draft PR，目标分支由维护者确认；不要直接合并 `main`。
3. 以 `v0.2.0` 创建 GitHub Release 并上传 `dist/` 中四个资产/校验文件。
4. 评审通过后合并到 `main`，启用 GitHub Pages；部署后检查稳定链接。
5. S1_002 只有在未来能可靠拆出纯实验端点时才改变 `audit_only`。

## 远端发布阻塞

- 本地提交：`142e371 feat: build BTED v0.2 public demo`。
- 2026-08-10 多次推送均因无法稳定连接 `github.com:443` 失败；只读 `curl` 检查也超时。
- GitHub 应用确认远端尚无 `agent/bted-v0.2-public-demo` 分支。
- 该阻塞不影响本地数据包、网站、JBrowse、checksum 或测试结果；不要为解决网络问题重建或重新解释数据。

## 不要做

- 不把协作者外部文献合入本分支；
- 不把混合证据或纯预测放进公开端点表/JBrowse；
- 不把作者预测注释解释为新的实验结果；
- 不把原始测序、出版商工作簿、大型 JBrowse 文件或凭据提交到 Git；
- 不在未确认参考、坐标、contig、strand 或许可时猜测补齐。
