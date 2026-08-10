#!/usr/bin/env python3
"""从来源注册表生成 site/sources.html 展示页（仅依赖 Python 标准库）。

输入：data/registry/batter_s1_source_registry.tsv（22 条 BATTER Table S1 来源记录）
输出：site/sources.html —— 纯元数据展示页，不含坐标、端点数据或 JBrowse 轨道。

用法：
    python3 scripts/build_sources_page.py
"""

from __future__ import annotations

import csv
import html
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "data/registry/batter_s1_source_registry.tsv"
OUTPUT = REPO_ROOT / "site/sources.html"

COORDINATE_STATUS_LABELS = {
    "verified": "已核实",
    "verified_with_metadata_conflict": "已核实（有元数据冲突）",
}

PROCESSING_STATUS_LABELS = {
    "curated": "已整理",
    "standardized": "已标准化",
    "accessible": "已定位",
    "to_review": "待核查",
    "published": "已发布",
    "blocked": "已阻塞",
}

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>来源目录 —— BTED 演示站点</title>
  <meta name="description" content="BTED 来源目录：BATTER Table S1 的 22 条来源记录的元数据（物种、实验方法、参考组装、登录号、处理状态）。不含坐标或端点数据。">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <header class="site-header">
    <div class="wrap">
      <p class="site-title"><a href="index.html">BTED 演示站点</a> <span class="tag">骨架阶段 · 无科学结论</span></p>
      <nav class="site-nav" aria-label="主导航">
        <a href="index.html">首页</a>
        <a href="sources.html" aria-current="page">来源目录</a>
        <a href="catalog.html">数据目录</a>
        <a href="methodology.html">方法与局限</a>
        <a href="about.html">关于</a>
      </nav>
    </div>
  </header>

  <main class="wrap">
    <h1>来源目录（22 条来源记录）</h1>
    <p class="lede">本表展示 BTED 来源注册表的<strong>来源级元数据</strong>，数据文件为仓库中的 <code>data/registry/batter_s1_source_registry.tsv</code>（由 <code>scripts/build_sources_page.py</code> 生成，请勿直接编辑本页）。</p>

    <div class="notice" role="note">
      <p><strong>本表只含元数据。</strong>标准化坐标、端点数据与 JBrowse 轨道<strong>尚未迁移到本仓库</strong>，须按验收门槛逐来源审计后才公开；表中的处理状态描述的是本地工作树的整理进度，不代表相应数据已在本站发布。候选端点是信号峰，不是终止子结论；统计口径为 <strong>__N_PAPERS__ 篇原始研究文献 / __N_SOURCES__ 条来源记录</strong>，两者不混写。</p>
    </div>

    <div class="table-scroll">
      <table class="catalog">
        <caption>共 __N_SOURCES__ 条来源记录，对应 __N_PAPERS__ 篇论文。PMID 可跳转至 PubMed；原始数据登录号请复制后到对应公共仓库查询。</caption>
        <thead>
          <tr>
            <th>来源 ID</th>
            <th>年份</th>
            <th>物种 / 菌株</th>
            <th>实验方法</th>
            <th>参考组装</th>
            <th>PMID</th>
            <th>原始数据登录号</th>
            <th>坐标核查</th>
            <th>处理状态</th>
            <th>备注</th>
          </tr>
        </thead>
        <tbody>
__ROWS__
        </tbody>
      </table>
    </div>

    <p class="table-note">更新方式：修改注册表 TSV 后运行 <code>python3 scripts/build_sources_page.py</code> 重新生成，并运行 <code>python3 scripts/validate-site.py</code> 校验。</p>
  </main>

  <footer class="site-footer">
    <div class="wrap">
      <p>BTED 静态演示骨架 v0.1 · 2026-08-07 · 本站点不包含科学结论 · 仅链接公开数据仓库，不复制原始数据</p>
    </div>
  </footer>
</body>
</html>
"""


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def build_row(rec: dict[str, str]) -> str:
    pmid = rec["pmid"].strip()
    pmid_cell = (
        f'<a href="https://pubmed.ncbi.nlm.nih.gov/{esc(pmid)}/">{esc(pmid)}</a>'
        if pmid
        else "NA"
    )
    coordinate_status = COORDINATE_STATUS_LABELS.get(
        rec["coordinate_status"].strip(), esc(rec["coordinate_status"])
    )
    processing_status = PROCESSING_STATUS_LABELS.get(
        rec["processing_status"].strip(), esc(rec["processing_status"])
    )
    cells = [
        esc(rec["source_id"]),
        esc(rec["published_year"]),
        f"<em>{esc(rec['species'])}</em>",
        esc(rec["assay_family"]),
        f"<code>{esc(rec['reference_genome'])}</code>",
        pmid_cell,
        esc(rec["raw_data_accessions"]),
        coordinate_status,
        processing_status,
        esc(rec["blocker_or_note"]),
    ]
    tds = "\n".join(f"            <td>{c}</td>" for c in cells)
    return f"          <tr>\n{tds}\n          </tr>"


def main() -> int:
    if not REGISTRY.is_file():
        print(f"FAIL 注册表不存在: {REGISTRY}")
        return 1

    with REGISTRY.open(encoding="utf-8", newline="") as fh:
        records = list(csv.DictReader(fh, delimiter="\t"))

    if not records:
        print("FAIL 注册表为空")
        return 1

    n_sources = len(records)
    n_papers = len({r["pmid"].strip() for r in records if r["pmid"].strip()})

    rows = "\n".join(build_row(r) for r in records)
    page = (
        PAGE_TEMPLATE.replace("__ROWS__", rows)
        .replace("__N_SOURCES__", str(n_sources))
        .replace("__N_PAPERS__", str(n_papers))
    )
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"PASS 已生成 {OUTPUT.relative_to(REPO_ROOT)}（{n_sources} 条来源记录，{n_papers} 篇论文）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
