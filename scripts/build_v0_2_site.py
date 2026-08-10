#!/usr/bin/env python3
"""Generate the bilingual BTED v0.2.0 static portal and 22 record pages."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from urllib.parse import quote


REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_ROOT = REPO_ROOT / "site"
RELEASE_PATH = REPO_ROOT / "data/public/v0.2.0/release_manifest.json"
REGISTRY_PATH = REPO_ROOT / "data/registry/batter_s1_source_registry.tsv"
RECORD_ROOT = REPO_ROOT / "data/public/v0.2.0/records"
REPOSITORY_URL = "https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database"

NOTES_ZH = {
    "BATTER_S1_001": "Rend-seq 文献整理记录；公开浏览器只显示 GEO 派生信号和候选端点，候选峰不等于终止子结论。",
    "BATTER_S1_002": "作者汇总表混合多个实验体系，逐条实验来源尚不能可靠拆分，因此仅保留来源审计。",
    "BATTER_S1_003": "Rend-seq 候选端点已从原始 WIG 重算并核对；候选峰不等于终止子结论。",
    "BATTER_S1_004": "实验坐标以 CP001340.1 为准；GEO 中误写的 E. coli 参考版本作为元数据冲突保留。",
    "BATTER_S1_005": "双染色体数据保留 CP009977.1 与 CP009978.1；坐标和匹配严格限制在同一 contig。",
    "BATTER_S1_006": "作者按覆盖度和富集阈值调用端点；同一物理位点可关联多个 locus。",
    "BATTER_S1_007": "作者发表的是 Term-seq 3′ end position，不能据此区分转录终止与 RNA 加工。",
    "BATTER_S1_008": "可重复 3′ 位点和基因关联解释分表保存；正文与补充表的 804/805 数量差异未被静默修正。",
    "BATTER_S1_009": "公开层只包含作者过滤后的 Term-seq TTS；纯 TransTermHP 预测不进入数据库。",
    "BATTER_S1_010": "作者发表的 Streptomyces Term-seq 端点；BA000030.4 与对应 RefSeq 序列一致。",
    "BATTER_S1_011": "作者发表的 Streptomyces Term-seq 端点，参考序列为 NC_010572.1。",
    "BATTER_S1_012": "作者发表的 Streptomyces Term-seq 端点，参考序列为 NC_003888.3。",
    "BATTER_S1_013": "与 S1_007 使用相同物种和参考，但来自不同论文和作者表，保持独立来源。",
    "BATTER_S1_014": "作者发表的 Streptomyces Term-seq 端点，参考序列为 CP020700.1。",
    "BATTER_S1_015": "染色体与质粒两个 replicon 均保留在同一数据集和浏览器组装中。",
    "BATTER_S1_016": "坐标固定在 CP059991.1；论文与 NCBI 的物种命名差异作为分类学冲突保留。",
    "BATTER_S1_017": "与 S1_015 使用相同菌株和参考，但来自不同论文；作者特异测量值独立保留。",
    "BATTER_S1_018": "染色体和三个质粒的端点均按作者 replicon 标签映射，不合并坐标。",
    "BATTER_S1_019": "作者人工整理的 Term-seq 3′ end position，不表述为逐位点功能验证。",
    "BATTER_S1_020": "公开层只包含 Nanopore native RNA 3′ ends；实验与预测混合的 S1C 表仅留审计指纹。",
    "BATTER_S1_021": "唯一端点表与条件级观察表分层保存；结构和终止分数只作为作者附属注释。",
    "BATTER_S1_022": "公开层只包含作者 Term-seq TTS；预测支持作为注释，纯 RhoTermPredict 位点不发布。",
}

EVIDENCE_ZH = {
    "author_called_endpoint": "作者调用的实验端点",
    "curated_record": "文献整理记录",
    "audit_only": "仅来源审计；未发布端点集合",
}

EVIDENCE_EN = {
    "author_called_endpoint": "author-called experimental endpoint",
    "curated_record": "literature-curated record",
    "audit_only": "source metadata only; no endpoint set published",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def bi(en: str, zh: str) -> str:
    return f'<span class="i18n i18n-en">{en}</span><span class="i18n i18n-zh">{zh}</span>'


def nav(current: str, depth: int = 0) -> str:
    prefix = "../" * depth
    items = [
        ("index", "index.html", "Home", "首页"),
        ("sources", "sources.html", "Sources", "来源"),
        ("catalog", "catalog.html", "Downloads", "下载"),
        ("methodology", "methodology.html", "Methods", "方法"),
        ("about", "about.html", "About", "关于"),
    ]
    links = "".join(
        f'<a href="{prefix}{path}"' + (' aria-current="page"' if key == current else "") + f'>{bi(en, zh)}</a>'
        for key, path, en, zh in items
    )
    return f"""
    <header class="site-header">
      <div class="header-inner">
        <a class="brand" href="{prefix}index.html"><span class="brand-mark">BTED</span><span class="brand-name">Bacterial Transcript 3′ End Database</span></a>
        <nav class="site-nav" aria-label="Primary navigation">{links}</nav>
        <div class="language-switch" aria-label="Language">
          <button type="button" data-lang-choice="en" aria-pressed="true">EN</button>
          <button type="button" data-lang-choice="zh" aria-pressed="false">中文</button>
        </div>
      </div>
    </header>"""


def page(title: str, current: str, content: str, depth: int = 0, description: str = "BTED v0.2.0") -> str:
    prefix = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(description)}">
  <title>{esc(title)} · BTED</title>
  <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{prefix}css/style.css">
</head>
<body data-lang="en">
{nav(current, depth)}
{content}
<footer class="site-footer"><div class="footer-inner"><span>BTED v0.2.0</span><span>{bi('22 source records · 21 browser-ready datasets', '22 条来源记录 · 21 个可浏览数据集')}</span><a href="{REPOSITORY_URL}">GitHub</a></div></footer>
<script src="{prefix}assets/site.js"></script>
</body>
</html>
"""


def external_link(url: str, label: str) -> str:
    if not url or url == "NA":
        return "—"
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>'


def download_url(source_id: str, filename: str, prefix: str = "") -> str:
    return f"{prefix}downloads/records/{source_id}/{quote(filename)}"


def status_badge(status: str) -> str:
    if status == "audit_only":
        return f'<span class="badge badge-audit">{bi("Audit only", "仅审计")}</span>'
    return f'<span class="badge badge-published">{bi("Published", "已发布")}</span>'


def record_page(source_id: str, source: dict[str, str], release_entry: dict[str, object], manifest: dict[str, object]) -> str:
    status = str(release_entry["release_status"])
    record_count = int(release_entry["record_count"])
    evidence = str(release_entry["evidence_class"])
    display_evidence = "audit_only" if status == "audit_only" else evidence
    files = {item["path"] for item in release_entry.get("files", [])}
    downloadable = [
        ("endpoints.tsv", "Core endpoint table", "核心端点表"),
        ("source_annotations.tsv", "Source-specific annotations", "来源特异注释"),
        ("endpoints.bed", "BED6 coordinates", "BED6 坐标"),
        ("gene_associations.tsv", "Gene associations", "基因关联表"),
        ("condition_observations.tsv", "Condition observations", "条件级观察表"),
        ("fields.json", "Field dictionary", "字段字典"),
        ("manifest.json", "Source manifest", "来源清单"),
        ("SHA256SUMS.txt", "Checksums", "校验值"),
    ]
    cards = []
    for filename, en, zh in downloadable:
        if filename not in files and filename not in {"fields.json", "manifest.json", "SHA256SUMS.txt"}:
            continue
        cards.append(
            f'<a class="download-card" href="{download_url(source_id, filename, "../")}"><strong>{bi(en, zh)}</strong><code>{esc(filename)}</code></a>'
        )
    if source_id in {"BATTER_S1_001", "BATTER_S1_003", "BATTER_S1_004", "BATTER_S1_005"}:
        cards.append(
            f'<div class="download-card download-disabled"><strong>{bi("Source-specific annotations", "来源特异注释")}</strong><span>{bi("External link only; see original supplement", "仅提供原始补充材料入口")}</span></div>'
        )

    browser = ""
    if release_entry.get("has_jbrowse"):
        browser = f'<a class="button primary" href="../jbrowse/index.html?config={source_id}.config.json">{bi("Open JBrowse", "打开 JBrowse")}</a>'
    else:
        browser = f'<span class="button disabled" aria-disabled="true">{bi("JBrowse unavailable", "JBrowse 不可用")}</span>'

    evidence_label = EVIDENCE_ZH.get(display_evidence, display_evidence)
    evidence_label_en = EVIDENCE_EN.get(display_evidence, display_evidence.replace("_", " "))
    content = f"""
<main class="page-shell record-shell">
  <nav class="breadcrumbs"><a href="../sources.html">{bi('Sources', '来源')}</a><span>/</span><span>{source_id}</span></nav>
  <div class="record-heading">
    <div><p class="eyebrow">{source_id}</p><h1><em>{esc(source['species'])}</em></h1><p class="record-title">{esc(source['paper_title'])}</p></div>
    <div>{status_badge(status)}</div>
  </div>
  <section class="metric-grid">
    <div class="metric"><span>{bi('Records', '记录数')}</span><strong>{record_count:,}</strong></div>
    <div class="metric"><span>{bi('Evidence', '证据层')}</span><strong>{esc(display_evidence)}</strong></div>
    <div class="metric"><span>{bi('Assembly', '参考组装')}</span><strong>{esc(source['reference_genome'])}</strong></div>
    <div class="metric"><span>{bi('Assay', '实验方法')}</span><strong>{esc(source['assay_family'])}</strong></div>
  </section>

  <div class="record-layout">
    <div class="record-main">
      <section class="panel">
        <div class="panel-header"><h2>{bi('Dataset summary', '数据概况')}</h2>{browser}</div>
        <dl class="data-list">
          <dt>{bi('Organism / strain', '物种 / 菌株')}</dt><dd><em>{esc(source['species'])}</em></dd>
          <dt>{bi('Publication year', '发表年份')}</dt><dd>{esc(source['published_year'])}</dd>
          <dt>{bi('Evidence interpretation', '证据解释')}</dt><dd>{esc(display_evidence)} · {bi(esc(evidence_label_en), esc(evidence_label))}</dd>
          <dt>{bi('Coordinate convention', '坐标规则')}</dt><dd>1-based biological coordinate; BED [position − 1, position)</dd>
          <dt>{bi('Redistribution', '再分发状态')}</dt><dd><code>{esc(release_entry['redistribution_status'])}</code></dd>
        </dl>
      </section>

      <section class="panel">
        <h2>{bi('Downloads', '数据下载')}</h2>
        <p class="section-note">{bi('Checksums and field definitions are supplied with every release record.', '每个发布条目均提供字段定义和校验值。')}</p>
        <div class="download-grid">{''.join(cards)}</div>
      </section>

      <section class="panel">
        <h2>{bi('Known limitations', '已知限制')}</h2>
        <p class="i18n i18n-en">{esc(manifest.get('known_limitations', source.get('blocker_or_note', 'NA')))}</p>
        <p class="i18n i18n-zh">{esc(NOTES_ZH[source_id])}</p>
        <div class="evidence-note">{bi('A measured 3′ end does not by itself establish transcription-termination function. Prediction annotations do not change the endpoint evidence class.', '测得的 3′ end 本身不能证明转录终止功能；预测注释不改变端点证据等级。')}</div>
      </section>
    </div>

    <aside class="record-side">
      <section class="panel compact">
        <h2>{bi('Publication', '依据文献')}</h2>
        <ul class="link-list">
          <li>{external_link(str(manifest.get('pubmed_url', '')), f"PubMed {manifest.get('pmid', source['pmid'])}")}</li>
          <li>{external_link(str(manifest.get('doi_url', '')), f"DOI {manifest.get('doi', source['doi'])}")}</li>
          <li>{external_link(str(manifest.get('pmc_url', '')), str(manifest.get('pmc', source.get('pmc', 'PMC'))))}</li>
        </ul>
      </section>
      <section class="panel compact">
        <h2>{bi('Data source', '原始数据')}</h2>
        <p><code>{esc(str(manifest.get('raw_data_accessions', source['raw_data_accessions'])))}</code></p>
        <p>{external_link(str(manifest.get('raw_data_url', '')), 'Open repository record')}</p>
      </section>
      <section class="panel compact">
        <h2>{bi('Record identity', '条目标识')}</h2>
        <dl class="mini-list"><dt>Source ID</dt><dd>{source_id}</dd><dt>Dataset ID</dt><dd>{esc(str(manifest.get('dataset_id', 'NA')))}</dd><dt>Version</dt><dd>v0.2.0</dd></dl>
      </section>
    </aside>
  </div>
</main>"""
    return page(f"{source_id} · {source['species']}", "sources", content, depth=1, description=f"BTED record for {source['species']}")


def main() -> int:
    release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))
    with REGISTRY_PATH.open(encoding="utf-8", newline="") as handle:
        registry = {row["source_id"]: row for row in csv.DictReader(handle, delimiter="\t")}
    source_ids = list(release["sources"])
    if source_ids != [f"BATTER_S1_{number:03d}" for number in range(1, 23)]:
        raise RuntimeError("Release manifest does not contain the expected 22 ordered sources")

    (SITE_ROOT / "records").mkdir(parents=True, exist_ok=True)
    (SITE_ROOT / "data").mkdir(parents=True, exist_ok=True)
    (SITE_ROOT / "assets").mkdir(parents=True, exist_ok=True)

    catalog_records = []
    for source_id in source_ids:
        source = registry[source_id]
        entry = release["sources"][source_id]
        manifest = json.loads((RECORD_ROOT / source_id / "manifest.json").read_text(encoding="utf-8"))
        (SITE_ROOT / "records" / f"{source_id}.html").write_text(
            record_page(source_id, source, entry, manifest), encoding="utf-8"
        )
        catalog_records.append({
            "source_id": source_id,
            "species": source["species"],
            "year": int(source["published_year"]),
            "assay": source["assay_family"],
            "assembly": source["reference_genome"],
            "pmid": source["pmid"],
            "evidence_class": "audit_only" if entry["release_status"] == "audit_only" else entry["evidence_class"],
            "release_status": entry["release_status"],
            "record_count": entry["record_count"],
            "has_jbrowse": entry["has_jbrowse"],
            "note_en": manifest.get("known_limitations", source["blocker_or_note"]),
            "note_zh": NOTES_ZH[source_id],
            "record_url": f"records/{source_id}.html",
        })
    (SITE_ROOT / "data/catalog.json").write_text(
        json.dumps({"release_version": "v0.2.0", "sources": catalog_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    index_content = f"""
<main>
  <section class="hero"><div class="page-shell hero-inner"><p class="eyebrow">BTED v0.2.0</p><h1>{bi('Bacterial transcript 3′ ends, organized for reuse.', '可追溯、可下载的细菌转录 3′ 端数据。')}</h1><p>{bi('A curated catalog of public bacterial transcript-end experiments with stable coordinates, source-level fields, and genome-browser views.', '将公开的细菌转录端点实验整理为稳定坐标、来源字段和基因组浏览器视图。')}</p><div class="hero-actions"><a class="button primary" href="sources.html">{bi('Browse sources', '浏览来源')}</a><a class="button" href="methodology.html">{bi('Read data standard', '查看数据标准')}</a></div></div></section>
  <section class="page-shell stat-strip"><div><strong>22</strong><span>{bi('source records', '来源记录')}</span></div><div><strong>13</strong><span>{bi('research papers', '研究论文')}</span></div><div><strong>28,399</strong><span>{bi('standardized records', '标准化记录')}</span></div><div><strong>21</strong><span>{bi('JBrowse datasets', 'JBrowse 数据集')}</span></div></section>
  <section class="page-shell feature-grid"><article><h2>{bi('Traceable', '可追溯')}</h2><p>{bi('Every record links to its paper, public accession, reference assembly, source row, and checksums.', '每条记录均关联论文、公共登录号、参考组装、原始行和校验值。')}</p></article><article><h2>{bi('Evidence-aware', '证据分层')}</h2><p>{bi('Observed signals, called endpoints, author endpoints, annotations, and predictions remain separate.', '实验信号、候选端点、作者端点、注释和预测保持分层。')}</p></article><article><h2>{bi('Browser-ready', '可浏览')}</h2><p>{bi('Twenty-one source-specific JBrowse configurations retain contig and strand identity.', '21 套独立 JBrowse 配置保留 contig 与链方向。')}</p></article></section>
</main>"""
    (SITE_ROOT / "index.html").write_text(page("Home", "index", index_content), encoding="utf-8")

    species_options = "".join(f'<option value="{esc(value.lower())}">{esc(value)}</option>' for value in sorted({r["species"] for r in catalog_records}))
    assay_options = "".join(f'<option value="{esc(value.lower())}">{esc(value)}</option>' for value in sorted({r["assay"] for r in catalog_records}))
    year_options = "".join(f'<option value="{value}">{value}</option>' for value in sorted({r["year"] for r in catalog_records}))
    rows = []
    for record in catalog_records:
        entry = release["sources"][record["source_id"]]
        action = f'<a href="{record["record_url"]}">{bi("View record", "查看条目")}</a>'
        browser = f'<a href="jbrowse/index.html?config={record["source_id"]}.config.json">JBrowse</a>' if record["has_jbrowse"] else "—"
        rows.append(f"""<tr data-source-row data-species="{esc(record['species'].lower())}" data-assay="{esc(record['assay'].lower())}" data-year="{record['year']}" data-evidence="{esc(record['evidence_class'])}" data-status="{esc(record['release_status'])}" data-search="{esc((record['source_id']+' '+record['species']+' '+record['assay']+' '+record['pmid']).lower())}"><td><a class="source-id" href="{record['record_url']}">{record['source_id']}</a></td><td><em>{esc(record['species'])}</em><small>{esc(record['assembly'])}</small></td><td>{esc(record['assay'])}<small>{record['year']}</small></td><td><code>{esc(record['evidence_class'])}</code></td><td>{status_badge(record['release_status'])}</td><td class="number">{int(record['record_count']):,}</td><td class="actions">{action}{browser}</td></tr>""")
    sources_content = f"""
<main class="page-shell">
  <div class="page-heading"><div><p class="eyebrow">BTED v0.2.0</p><h1>{bi('Source catalog', '来源目录')}</h1><p>{bi('One row represents one independently processed source, not one paper.', '一行代表一个独立处理的来源，不等同于一篇论文。')}</p></div><div class="count-box"><strong data-visible-count>22</strong><span>{bi('visible sources', '当前来源')}</span></div></div>
  <section class="filters" aria-label="Catalog filters">
    <label><span>{bi('Search', '搜索')}</span><input type="search" data-filter-search placeholder="Source, organism, PMID"></label>
    <label><span>{bi('Organism', '物种')}</span><select data-filter="species"><option value="">All organisms / 全部物种</option>{species_options}</select></label>
    <label><span>{bi('Assay', '方法')}</span><select data-filter="assay"><option value="">All assays / 全部方法</option>{assay_options}</select></label>
    <label><span>{bi('Year', '年份')}</span><select data-filter="year"><option value="">All years / 全部年份</option>{year_options}</select></label>
    <label><span>{bi('Evidence', '证据')}</span><select data-filter="evidence"><option value="">All evidence / 全部证据</option><option value="author_called_endpoint">author_called_endpoint</option><option value="curated_record">curated_record</option><option value="audit_only">audit_only</option></select></label>
    <label><span>{bi('Status', '状态')}</span><select data-filter="status"><option value="">All statuses / 全部状态</option><option value="published_standardized">published</option><option value="audit_only">audit_only</option></select></label>
  </section>
  <div class="table-wrap"><table class="source-table"><thead><tr><th>Source</th><th>{bi('Organism / assembly', '物种 / 组装')}</th><th>{bi('Assay / year', '方法 / 年份')}</th><th>{bi('Evidence', '证据')}</th><th>{bi('Status', '状态')}</th><th>{bi('Records', '记录数')}</th><th>{bi('Access', '访问')}</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
  <p class="empty-state" data-empty-state hidden>{bi('No sources match the current filters.', '没有符合当前筛选条件的来源。')}</p>
</main>"""
    (SITE_ROOT / "sources.html").write_text(page("Sources", "sources", sources_content), encoding="utf-8")

    catalog_rows = []
    for record in catalog_records:
        sid = record["source_id"]
        entry = release["sources"][sid]
        record_files = [item["path"] for item in entry.get("files", [])]
        main_file = "endpoints.tsv" if "endpoints.tsv" in record_files else "manifest.json"
        catalog_rows.append(f'<tr><td><a href="records/{sid}.html">{sid}</a></td><td><em>{esc(record["species"])}</em></td><td class="number">{int(record["record_count"]):,}</td><td><code>{esc(record["evidence_class"])}</code></td><td><a href="{download_url(sid, main_file)}">{esc(main_file)}</a></td><td><a href="{download_url(sid, "SHA256SUMS.txt")}">SHA-256</a></td></tr>')
    catalog_content = f"""<main class="page-shell"><div class="page-heading"><div><p class="eyebrow">v0.2.0</p><h1>{bi('Data downloads', '数据下载')}</h1><p>{bi('Core tables use the shared 24-column schema. Source-specific fields are provided separately when redistribution is permitted.', '核心表统一为 24 列；许可允许时，作者特异字段通过独立附表提供。')}</p></div><a class="button" href="{REPOSITORY_URL}/releases/tag/v0.2.0">{bi('Release assets', 'Release 文件')}</a></div><div class="table-wrap"><table class="source-table"><thead><tr><th>Source</th><th>{bi('Organism', '物种')}</th><th>{bi('Records', '记录数')}</th><th>{bi('Evidence', '证据')}</th><th>{bi('Primary file', '主文件')}</th><th>{bi('Checksum', '校验')}</th></tr></thead><tbody>{''.join(catalog_rows)}</tbody></table></div></main>"""
    (SITE_ROOT / "catalog.html").write_text(page("Downloads", "catalog", catalog_content), encoding="utf-8")

    methodology_content = f"""<main class="page-shell prose"><div class="page-heading"><div><p class="eyebrow">Data standard</p><h1>{bi('Methods and evidence boundaries', '方法与证据边界')}</h1></div></div><section><h2>{bi('Two-layer data model', '双层数据模型')}</h2><p>{bi('The core endpoint table provides 24 stable columns for cross-source queries. A source-annotation table retains author-specific measurements and labels, linked by end_id.', '核心端点表以 24 个稳定字段支持跨来源查询；来源注释表通过 end_id 保留作者特异测量值和标签。')}</p></section><section><h2>{bi('Coordinates', '坐标')}</h2><p>{bi('BTED stores 1-based biological positions. Single-base BED uses start = position − 1 and end = position. Matching never crosses contigs.', 'BTED 保存 1-based 生物学坐标；单碱基 BED 使用 start = position − 1、end = position，匹配不得跨 contig。')}</p></section><section><h2>{bi('Evidence', '证据')}</h2><p>{bi('Observed signal, locally called candidates, author-called endpoints, curated records, mixed evidence, and predictions are stored as distinct classes. Mixed or prediction-only records are not published as endpoints.', '实验信号、本站候选、作者端点、整理记录、混合证据和预测分别保存；混合证据与纯预测不得作为端点发布。')}</p></section><section><h2>{bi('Licensing', '许可')}</h2><p>{bi('Author-specific supplementary fields are redistributed only when reuse terms are verified. Otherwise the database supplies factual core records and links to the original source.', '只有核实再利用条款后才复制作者特异补充字段；否则仅提供事实型核心记录和原始入口。')}</p></section></main>"""
    (SITE_ROOT / "methodology.html").write_text(page("Methods", "methodology", methodology_content), encoding="utf-8")

    about_content = f"""<main class="page-shell prose"><div class="page-heading"><div><p class="eyebrow">BTED</p><h1>{bi('About the project', '关于项目')}</h1></div></div><section><h2>{bi('Purpose', '项目目的')}</h2><p>{bi('BTED turns public bacterial transcript-end experiments into traceable records, downloadable tables, and genome-browser views.', 'BTED 将公开细菌转录端点实验整理为可追溯记录、标准下载表和基因组浏览器视图。')}</p></section><section><h2>{bi('Current release', '当前版本')}</h2><p>{bi('v0.2.0 is a public demonstration release covering the 22 BATTER Table S1 source records. It is not a manuscript submission or long-term DOI archive.', 'v0.2.0 是覆盖 BATTER Table S1 22 条来源的公开演示版本，不等同于论文投稿或 DOI 长期归档。')}</p></section><section><h2>{bi('Repository', '代码仓库')}</h2><p><a href="{REPOSITORY_URL}">{REPOSITORY_URL}</a></p></section></main>"""
    (SITE_ROOT / "about.html").write_text(page("About", "about", about_content), encoding="utf-8")

    print("PASS  Generated bilingual BTED v0.2.0 site: 5 top-level pages, 22 record pages, catalog.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
