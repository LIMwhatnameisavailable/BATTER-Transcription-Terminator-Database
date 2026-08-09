#!/usr/bin/env python3
"""从来源注册表和发布状态表生成 site/sources.html（仅依赖标准库）。

输入：22 条 BATTER Table S1 来源记录，以及 v0.1 发布状态表。
输出：site/sources.html —— 静态发布索引，不直接承载坐标数据或 JBrowse 轨道。

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
PUBLICATION_STATUS = REPO_ROOT / "data/registry/batter_s1_publication_status.tsv"
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

RELEASE_STATUS_LABELS = {
    "published_standardized": "已发布（标准化）",
    "audit_only": "仅审计",
}

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>来源目录 —— BTED</title>
  <meta name="description" content="BTED v0.1 local snapshot 来源目录：22 条 BATTER Table S1 来源的元数据、发布状态和标准化记录计数。">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <header class="site-header">
    <div class="wrap">
      <p class="site-title"><a href="index.html">BTED</a> <span class="tag">v0.1 local snapshot</span></p>
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
    <p class="lede">本表展示来源级元数据与本版 Git 发布判定。数据来自仓库的 <code>data/registry/batter_s1_source_registry.tsv</code> 与 <code>batter_s1_publication_status.tsv</code>（由 <code>scripts/build_sources_page.py</code> 生成，请勿直接编辑本页）。</p>

    <div class="notice" role="note">
      <p><strong>本版已发布 __N_PUBLIC__ 个标准化来源、__N_RECORDS__ 条记录。</strong>端点 TSV/BED 位于仓库 <code>data/public/</code>，不直接嵌入静态页面；JBrowse、BigWig 与原始测序尚未随本版发布。候选端点不等于终止子结论；统计口径为 <strong>__N_PAPERS__ 篇原始研究文献 / __N_SOURCES__ 条来源记录</strong>，两者不混写。</p>
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
            <th>仓库发布</th>
            <th>标准化记录数</th>
            <th>公开资产</th>
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
      <p>BTED v0.1 local snapshot · 2026-08-10 · 静态发布索引 · 原始数据通过公共数据库获取</p>
    </div>
  </footer>
</body>
</html>
"""


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def build_row(rec: dict[str, str], release: dict[str, str]) -> str:
    pmid = rec["pmid"].strip()
    pmid_cell = (
        f'<a href="https://pubmed.ncbi.nlm.nih.gov/{esc(pmid)}/">{esc(pmid)}</a>'
        if pmid
        else "NA"
    )
    coordinate_status = COORDINATE_STATUS_LABELS.get(
        rec["coordinate_status"].strip(), esc(rec["coordinate_status"])
    )
    release_status = RELEASE_STATUS_LABELS.get(
        release["release_status"].strip(), esc(release["release_status"])
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
        release_status,
        esc(release["record_count"]),
        f"<code>{esc(release['public_asset'])}</code>" if release["public_asset"] != "NA" else "—",
        esc(rec["blocker_or_note"]),
    ]
    tds = "\n".join(f"            <td>{c}</td>" for c in cells)
    return f"          <tr>\n{tds}\n          </tr>"


def main() -> int:
    if not REGISTRY.is_file() or not PUBLICATION_STATUS.is_file():
        print(f"FAIL 注册表或发布状态表不存在: {REGISTRY} / {PUBLICATION_STATUS}")
        return 1

    with REGISTRY.open(encoding="utf-8", newline="") as fh:
        records = list(csv.DictReader(fh, delimiter="\t"))
    with PUBLICATION_STATUS.open(encoding="utf-8", newline="") as fh:
        releases = {row["source_id"]: row for row in csv.DictReader(fh, delimiter="\t")}

    if not records:
        print("FAIL 注册表为空")
        return 1
    if {row["source_id"] for row in records} != set(releases):
        print("FAIL 来源注册表与发布状态表的 source_id 集合不一致")
        return 1

    n_sources = len(records)
    n_papers = len({r["pmid"].strip() for r in records if r["pmid"].strip()})

    rows = "\n".join(build_row(r, releases[r["source_id"]]) for r in records)
    n_public = sum(r["release_status"] == "published_standardized" for r in releases.values())
    n_records = sum(int(r["record_count"]) for r in releases.values())
    page = (
        PAGE_TEMPLATE.replace("__ROWS__", rows)
        .replace("__N_SOURCES__", str(n_sources))
        .replace("__N_PAPERS__", str(n_papers))
        .replace("__N_PUBLIC__", str(n_public))
        .replace("__N_RECORDS__", f"{n_records:,}")
    )
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"PASS 已生成 {OUTPUT.relative_to(REPO_ROOT)}（{n_sources} 条来源记录，{n_public} 个已发布来源，{n_records} 条记录）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
