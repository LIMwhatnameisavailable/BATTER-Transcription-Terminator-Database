#!/usr/bin/env python3
"""Generate the English-first, assembly-centred BTED v0.2.0 website."""

from __future__ import annotations

import csv
import html
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote


REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_ROOT = REPO_ROOT / "site"
RELEASE_PATH = REPO_ROOT / "data/public/v0.2.0/release_manifest.json"
REGISTRY_PATH = REPO_ROOT / "data/registry/batter_s1_source_registry.tsv"
RECORD_ROOT = REPO_ROOT / "data/public/v0.2.0/records"
REPOSITORY_URL = "https://github.com/seu-yolo/BATTER-Transcription-Terminator-Database"
JBROWSE_CONFIG_VERSION = "20260814-strand-ui-v4"

EVIDENCE_LABELS = {
    "author_called_endpoint": "Author-called experimental endpoint",
    "curated_record": "Literature-curated record",
    "audit_only": "Source metadata audit only",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def bi(en: str, _future_translation: str = "") -> str:
    """Emit English only while retaining a stable hook for future translations."""
    return f'<span class="i18n" data-i18n-key="{esc(en)}">{esc(en)}</span>'


def assembly_accession_url(assembly: str) -> str:
    return f"https://www.ncbi.nlm.nih.gov/datasets/genome/{quote(assembly)}/"


def split_accessions(value: object) -> list[str]:
    return [item for item in re.split(r"[;,\s]+", str(value).strip()) if item and item != "NA"]


def accession_destination(accession: str, fallback_url: str = "") -> tuple[str, str]:
    """Return a stable public landing page and repository label for an accession."""
    if re.fullmatch(r"GSE\d+", accession):
        return f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={quote(accession)}", "NCBI GEO"
    if re.fullmatch(r"SR[APRX]\d+", accession):
        return f"https://www.ncbi.nlm.nih.gov/sra/?term={quote(accession)}", "NCBI SRA"
    if re.fullmatch(r"PRJNA\d+", accession):
        return f"https://www.ncbi.nlm.nih.gov/bioproject/{quote(accession)}", "NCBI BioProject"
    if re.fullmatch(r"PRJEB\d+", accession):
        return f"https://www.ebi.ac.uk/ena/browser/view/{quote(accession)}", "ENA"
    if re.fullmatch(r"E-MTAB-\d+", accession):
        return f"https://www.ebi.ac.uk/biostudies/arrayexpress/studies/{quote(accession)}", "BioStudies"
    return fallback_url, "Source repository"


def accession_links(accessions: object, fallback_url: str = "", compact: bool = False) -> str:
    items = []
    for accession in split_accessions(accessions):
        url, repository = accession_destination(accession, fallback_url)
        label = f'<code>{esc(accession)}</code><span>{esc(repository)}</span>'
        if url:
            label = f'<a href="{esc(url)}" target="_blank" rel="noopener" data-accession="{esc(accession)}">{label}</a>'
        items.append(f"<li>{label}</li>")
    class_name = "accession-list compact" if compact else "accession-list"
    return f'<ul class="{class_name}">{"".join(items)}</ul>' if items else "—"


def nav(current: str, depth: int = 0) -> str:
    prefix = "../" * depth
    items = [
        ("index", "index.html", "Home", "首页"),
        ("sources", "sources.html", "Genomes", "基因组"),
        ("catalog", "catalog.html", "Download", "下载"),
        ("methodology", "methodology.html", "Data notes", "数据说明"),
        ("about", "about.html", "About", "关于"),
    ]
    links = "".join(
        f'<a href="{prefix}{path}"' + (' aria-current="page"' if key == current else "") + f'>{bi(en, zh)}</a>'
        for key, path, en, zh in items
    )
    return f"""
<header class="site-header"><div class="header-inner">
  <a class="brand" href="{prefix}index.html"><span class="brand-mark">BTED</span><span class="brand-name">Bacterial Transcript 3′ End Database</span></a>
  <nav class="site-nav" aria-label="Primary navigation">{links}</nav>
</div></header>"""


def page(title: str, current: str, content: str, depth: int = 0, description: str = "BTED v0.2.0") -> str:
    prefix = "../" * depth
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description)}"><title>{esc(title)} · BTED</title>
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}css/style.css"></head>
<body>{nav(current, depth)}{content}
<footer class="site-footer"><div class="footer-inner"><span>BTED v0.2.0</span><span>{bi('20 assemblies · 22 source tracks · 28,399 records', '20 个参考组装 · 22 个来源 track · 28,399 条记录')}</span><a href="{REPOSITORY_URL}">GitHub</a></div></footer>
<script src="{prefix}assets/site.js"></script></body></html>"""


def external_link(url: str, label: str) -> str:
    if not url or url == "NA":
        return "—"
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>'


def status_badge(status: str) -> str:
    if status == "audit_only":
        return f'<span class="badge badge-audit">{bi("Metadata only", "仅元数据")}</span>'
    return f'<span class="badge badge-published">{bi("Data available", "数据可用")}</span>'


def assembly_browser_config(assembly: str, records: list[dict[str, object]]) -> str | None:
    published = [record for record in records if record["has_jbrowse"]]
    if not published:
        return None
    if len(published) > 1:
        return f"assemblies/{assembly}.config.json"
    return f"{published[0]['source_id']}.config.json"


def assembly_download_url(assembly: str, filename: str, prefix: str = "") -> str:
    return f"{prefix}downloads/assemblies/{quote(assembly)}/{filename}"


def record_download_url(source_id: str, filename: str, prefix: str = "") -> str:
    return f"{prefix}downloads/records/{source_id}/{filename}"


def jbrowse_href(config: str, prefix: str = "") -> str:
    versioned_config = f"{config}?v={JBROWSE_CONFIG_VERSION}"
    return f"{prefix}jbrowse/index.html?config={quote(versioned_config, safe='')}"


def browser_reading_guide(assays: list[str]) -> str:
    """Explain the strand-aware Rend-seq view only where that view exists."""

    if not any("rend-seq" in assay.lower() for assay in assays):
        return ""
    return """
    <section class="panel browser-guide"><div class="panel-header"><div><p class="eyebrow">Genome browser guide</p><h2>Read both strands in one compact view</h2></div><span class="browser-guide-hint">Click a candidate for details</span></div>
      <div class="strand-legend" aria-label="Strand colour legend"><div><span class="strand-swatch plus"></span><strong>+ strand</strong><span>blue signal above zero · arrows point right</span></div><div><span class="strand-swatch minus"></span><strong>− strand</strong><span>orange signal below zero · arrows point left</span></div></div>
      <p class="section-note"><strong>Important:</strong> values below zero are a display convention for the − strand, not negative abundance. Candidate marks are local signal peaks, not automatically proven terminators. Click a mark to inspect its stable ID, 1-based coordinate, strand, raw support and evidence warning.</p>
    </section>"""


def record_page(record: dict[str, object], assembly_track_count: int) -> str:
    source_id = str(record["source_id"])
    source = record["source"]
    manifest = record["manifest"]
    status = str(record["release_status"])
    browser = (
        f'<a class="button primary" href="{jbrowse_href(f"{source_id}.config.json", "../")}">{bi("Open source track", "打开来源 track")}</a>'
        if record["has_jbrowse"] else f'<span class="button disabled">{bi("No endpoint track", "无端点 track")}</span>'
    )
    bed = (
        f'<a class="download-card featured" href="{record_download_url(source_id, "endpoints.bed", "../")}"><strong>{bi("BED coordinates", "BED 坐标")}</strong><code>endpoints.bed</code></a>'
        if status != "audit_only" else ""
    )
    metadata = f'<a class="download-card" href="{assembly_download_url(str(record["assembly"]), "metadata.json", "../")}"><strong>{bi("Assembly metadata", "组装元数据")}</strong><code>metadata.json</code></a>'
    evidence = str(record["evidence_class"])
    assembly = str(record["assembly"])
    raw_accessions = accession_links(source["raw_data_accessions"], str(manifest.get("raw_data_url", "")))
    browser_guide = browser_reading_guide([str(source["assay_family"])]) if record["has_jbrowse"] else ""
    content = f"""
<main class="page-shell record-shell">
  <nav class="breadcrumbs"><a href="../sources.html">{bi('Genomes', '基因组')}</a><span>/</span><a href="../assemblies/{esc(assembly)}.html">{esc(assembly)}</a><span>/</span><span>{source_id}</span></nav>
  <div class="record-heading"><div><p class="eyebrow">{source_id}</p><h1><em>{esc(source['species'])}</em></h1><p class="record-title">{esc(source['paper_title'])}</p></div>{status_badge(status)}</div>
  <section class="metric-grid"><div class="metric"><span>{bi('Records', '记录数')}</span><strong>{int(record['record_count']):,}</strong></div><div class="metric"><span>{bi('Evidence', '证据')}</span><strong>{esc(evidence)}</strong></div><div class="metric"><span>{bi('Assembly accession', '参考组装')}</span><strong><a href="{assembly_accession_url(assembly)}" target="_blank" rel="noopener">{esc(assembly)}</a></strong></div><div class="metric"><span>{bi('Assay', '实验方法')}</span><strong>{esc(source['assay_family'])}</strong></div></section>
  <div class="record-layout"><div class="record-main">
    <section class="panel"><div class="panel-header"><h2>{bi('Source overview', '来源概况')}</h2>{browser}</div><dl class="data-list">
      <dt>{bi('Dataset', '数据集')}</dt><dd>{esc(manifest.get('dataset_id', 'NA'))}</dd><dt>{bi('Publication year', '发表年份')}</dt><dd>{esc(source['published_year'])}</dd>
      <dt>{bi('Evidence', '证据说明')}</dt><dd><code>{esc(evidence)}</code> · {esc(EVIDENCE_LABELS.get(evidence, evidence))}</dd><dt>{bi('Tracks on this assembly', '该组装上的 track')}</dt><dd>{assembly_track_count}</dd>
    </dl></section>{browser_guide}
    <section class="panel"><h2>{bi('Raw data accessions', '原始数据')}</h2><p class="section-note">Open the public repository record for each accession number.</p>{raw_accessions}</section>
    <section class="panel"><h2>{bi('Download', '下载')}</h2><p class="section-note">{bi('The page exposes the analysis-ready BED and one metadata document. Detailed provenance remains in the repository.', '页面只突出分析所需的 BED 和一份元数据；完整追溯信息仍保留在仓库中。')}</p><div class="download-grid compact-downloads">{bed}{metadata}</div></section>
    <section class="panel"><h2>{bi('Data note', '数据说明')}</h2><p>{esc(manifest.get('known_limitations', source['blocker_or_note']))}</p><div class="evidence-note">{bi('A 3′ end record is not automatically a functionally proven terminator. Tracks from the same assembly remain separate evidence sources.', '3′ end 记录不自动等同于功能性终止子；同一组装上的不同 track 仍是独立证据来源。')}</div></section>
  </div><aside class="record-side">
    <section class="panel compact"><h2>{bi('Publication', '依据文献')}</h2><ul class="link-list"><li>{external_link(str(manifest.get('pubmed_url', '')), f"PubMed {source['pmid']}")}</li><li>{external_link(str(manifest.get('doi_url', '')), f"DOI {source['doi']}")}</li><li>{external_link(str(manifest.get('pmc_url', '')), str(source.get('pmc', 'PMC')))}</li></ul></section>
    <section class="panel compact"><h2>{bi('Identity', '标识')}</h2><dl class="mini-list"><dt>Source ID</dt><dd>{source_id}</dd><dt>Assembly</dt><dd><a href="{assembly_accession_url(assembly)}" target="_blank" rel="noopener">{esc(assembly)}</a></dd><dt>Version</dt><dd>v0.2.0</dd></dl></section>
  </aside></div>
</main>"""
    return page(f"{source_id} · {source['species']}", "sources", content, depth=1)


def assembly_page(assembly: str, records: list[dict[str, object]]) -> str:
    total = sum(int(record["record_count"]) for record in records)
    published = [record for record in records if record["release_status"] != "audit_only"]
    browser_config = assembly_browser_config(assembly, records)
    browser = (
        f'<a class="button primary" href="{jbrowse_href(browser_config, "../")}">{bi("Open genome browser", "打开基因组浏览器")}</a>'
        if browser_config else f'<span class="button disabled">{bi("Browser unavailable", "浏览器不可用")}</span>'
    )
    track_rows = []
    for record in records:
        source = record["source"]
        manifest = record["manifest"]
        track_rows.append(f"""<tr><td><a class="source-id" href="../records/{record['source_id']}.html">{record['source_id']}</a></td><td>{esc(source['published_year'])}<small>{external_link(str(manifest.get('pubmed_url', '')), f"PMID {source['pmid']}")}</small></td><td>{accession_links(source['raw_data_accessions'], str(manifest.get('raw_data_url', '')), compact=True)}</td><td>{esc(source['assay_family'])}</td><td><code>{esc(record['evidence_class'])}</code></td><td class="number">{int(record['record_count']):,}</td></tr>""")
    bed = (
        f'<a class="download-card featured" href="{assembly_download_url(assembly, "endpoints.bed", "../")}"><strong>{bi("BED coordinates", "BED 坐标")}</strong><code>endpoints.bed · {total:,} records</code></a>'
        if published else ""
    )
    organisms = sorted({str(record["source"]["species"]) for record in records})
    years = sorted(int(record["source"]["published_year"]) for record in records)
    browser_guide = browser_reading_guide(
        [str(record["source"]["assay_family"]) for record in records if record["has_jbrowse"]]
    )
    content = f"""
<main class="page-shell record-shell">
  <nav class="breadcrumbs"><a href="../sources.html">{bi('Genomes', '基因组')}</a><span>/</span><span>{esc(assembly)}</span></nav>
  <div class="record-heading"><div><p class="eyebrow">{bi('Reference assembly', '参考组装')}</p><h1>{esc(assembly)}</h1><p class="record-title"><em>{esc(' / '.join(organisms))}</em></p><p><a href="{assembly_accession_url(assembly)}" target="_blank" rel="noopener">View assembly in NCBI Datasets</a></p></div>{status_badge('published' if published else 'audit_only')}</div>
  <section class="metric-grid"><div class="metric"><span>{bi('Source tracks', '来源 track')}</span><strong>{len(records)}</strong></div><div class="metric"><span>{bi('Endpoint records', '端点记录')}</span><strong>{total:,}</strong></div><div class="metric"><span>{bi('Years', '年份')}</span><strong>{years[0] if len(years) == 1 else f'{years[0]}–{years[-1]}'}</strong></div><div class="metric"><span>{bi('Browser view', '浏览器视图')}</span><strong>{bi('Combined tracks' if len(records) > 1 else 'Single track', '多 track' if len(records) > 1 else '单 track')}</strong></div></section>
  <section class="panel assembly-summary"><div><h2>{bi('Datasets on this genome', '该基因组上的数据集')}</h2><p>{bi('Sources with the exact same assembly accession are shown together. They remain independent tracks and are not collapsed into a consensus.', '参考组装 accession 完全相同的来源在此集中展示；各来源仍保留为独立 track，不合并成共识结果。')}</p></div>{browser}</section>{browser_guide}
  <section class="panel"><div class="table-wrap"><table class="source-table"><thead><tr><th>Track / Source</th><th>{bi('Year / paper', '年份 / 文献')}</th><th>Raw data accessions</th><th>{bi('Assay', '方法')}</th><th>{bi('Evidence', '证据')}</th><th>{bi('Records', '记录数')}</th></tr></thead><tbody>{''.join(track_rows)}</tbody></table></div></section>
  <section class="panel"><h2>{bi('Download this genome', '下载该基因组数据')}</h2><div class="download-grid compact-downloads">{bed}<a class="download-card" href="{assembly_download_url(assembly, 'metadata.json', '../')}"><strong>{bi('Metadata', '元数据')}</strong><code>metadata.json</code></a></div></section>
</main>"""
    return page(f"{assembly} · genome", "sources", content, depth=1)


def main() -> int:
    release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))
    with REGISTRY_PATH.open(encoding="utf-8", newline="") as handle:
        registry = {row["source_id"]: row for row in csv.DictReader(handle, delimiter="\t")}
    source_ids = list(release["sources"])
    expected = [f"BATTER_S1_{number:03d}" for number in range(1, 23)]
    if source_ids != expected:
        raise RuntimeError("Release manifest does not contain the expected 22 ordered sources")

    for directory in (SITE_ROOT / "records", SITE_ROOT / "assemblies", SITE_ROOT / "data", SITE_ROOT / "assets"):
        directory.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    for source_id in source_ids:
        source = registry[source_id]
        entry = release["sources"][source_id]
        manifest = json.loads((RECORD_ROOT / source_id / "manifest.json").read_text(encoding="utf-8"))
        records.append({
            "source_id": source_id,
            "source": source,
            "manifest": manifest,
            "assembly": source["reference_genome"],
            "year": int(source["published_year"]),
            "evidence_class": "audit_only" if entry["release_status"] == "audit_only" else entry["evidence_class"],
            "release_status": entry["release_status"],
            "record_count": int(entry["record_count"]),
            "has_jbrowse": bool(entry["has_jbrowse"]),
        })

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        grouped[str(record["assembly"])].append(record)

    for record in records:
        (SITE_ROOT / "records" / f"{record['source_id']}.html").write_text(
            record_page(record, len(grouped[str(record["assembly"])])), encoding="utf-8"
        )
    for assembly, group in grouped.items():
        (SITE_ROOT / "assemblies" / f"{assembly}.html").write_text(assembly_page(assembly, group), encoding="utf-8")

    catalog_sources = [{
        "source_id": record["source_id"], "species": record["source"]["species"],
        "year": record["year"], "assay": record["source"]["assay_family"], "assembly": record["assembly"],
        "pmid": record["source"]["pmid"], "evidence_class": record["evidence_class"],
        "release_status": record["release_status"], "record_count": record["record_count"],
        "raw_data_accessions": split_accessions(record["source"]["raw_data_accessions"]),
        "raw_data_url": record["manifest"].get("raw_data_url", ""),
        "has_jbrowse": record["has_jbrowse"], "record_url": f"records/{record['source_id']}.html",
    } for record in records]
    catalog_assemblies = []
    for assembly, group in grouped.items():
        source_ids_for_assembly = [str(record["source_id"]) for record in group]
        catalog_assemblies.append({
            "assembly": assembly,
            "assembly_url": assembly_accession_url(assembly),
            "species": sorted({str(record["source"]["species"]) for record in group}),
            "source_ids": source_ids_for_assembly,
            "track_count": len(group),
            "published_track_count": sum(record["release_status"] != "audit_only" for record in group),
            "record_count": sum(int(record["record_count"]) for record in group),
            "years": sorted({int(record["year"]) for record in group}),
            "assays": sorted({str(record["source"]["assay_family"]) for record in group}),
            "evidence_classes": sorted({str(record["evidence_class"]) for record in group}),
            "status": "published" if any(record["release_status"] != "audit_only" for record in group) else "audit_only",
            "browser_config": assembly_browser_config(assembly, group),
            "page_url": f"assemblies/{assembly}.html",
        })
    (SITE_ROOT / "data/catalog.json").write_text(json.dumps({
        "release_version": "v0.2.0", "language": "en", "sources": catalog_sources, "assemblies": catalog_assemblies,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index_content = f"""
<main><section class="hero"><div class="page-shell hero-inner"><p class="eyebrow">BTED v0.2.0</p><h1>{bi('Explore bacterial transcript 3′ ends by genome.', '按基因组浏览细菌转录 3′ 端数据。')}</h1><p>{bi('Public experimental datasets are organized by exact reference assembly, with each study retained as an independent track.', '公开实验数据按完全一致的参考组装整理，每项研究保留为独立 track。')}</p><div class="hero-actions"><a class="button primary" href="sources.html">{bi('Browse genomes', '浏览基因组')}</a><a class="button" href="catalog.html">{bi('Download data', '下载数据')}</a></div></div></section>
<section class="page-shell stat-strip"><div><strong>{len(grouped)}</strong><span>{bi('reference assemblies', '参考组装')}</span></div><div><strong>22</strong><span>{bi('source tracks', '来源 track')}</span></div><div><strong>28,399</strong><span>{bi('endpoint records', '端点记录')}</span></div><div><strong>21</strong><span>{bi('browser-ready tracks', '可浏览 track')}</span></div></section>
<section class="page-shell feature-grid"><article><h2>{bi('Genome-centred', '以基因组为入口')}</h2><p>{bi('Repeated studies on the same assembly are available in one view.', '相同组装上的不同研究可在同一视图中比较。')}</p></article><article><h2>{bi('Source-preserving', '保留来源')}</h2><p>{bi('Each study remains a named track with its paper and evidence class.', '每项研究均保留独立 track、文献与证据类别。')}</p></article><article><h2>{bi('Simple download', '简洁下载')}</h2><p>{bi('Choose genomes and download BED plus consolidated metadata.', '勾选基因组，一次下载 BED 与整合元数据。')}</p></article></section></main>"""
    (SITE_ROOT / "index.html").write_text(page("Home", "index", index_content), encoding="utf-8")

    species_values = sorted({species for item in catalog_assemblies for species in item["species"]})
    assay_values = sorted({assay for item in catalog_assemblies for assay in item["assays"]})
    evidence_values = sorted({evidence for item in catalog_assemblies for evidence in item["evidence_classes"]})
    species_options = "".join(f'<option value="{esc(value.lower())}">{esc(value)}</option>' for value in species_values)
    assay_options = "".join(f'<option value="{esc(value.lower())}">{esc(value)}</option>' for value in assay_values)
    evidence_options = "".join(
        f'<option value="{esc(value)}">{esc(EVIDENCE_LABELS.get(value, value))}</option>'
        for value in evidence_values
    )
    genome_rows = []
    for item in catalog_assemblies:
        species_text = " / ".join(item["species"])
        assay_text = " / ".join(item["assays"])
        years = item["years"]
        year_text = str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"
        study_label = "study" if item["track_count"] == 1 else "studies"
        evidence_text = " / ".join(
            EVIDENCE_LABELS.get(value, value) for value in item["evidence_classes"]
        )
        evidence_badge = status_badge(item["status"]) if item["status"] == "audit_only" else ""
        browser = (
            f'<a class="row-action secondary" href="{jbrowse_href(item["browser_config"])}">JBrowse</a>'
            if item["browser_config"] else ""
        )
        sources = " ".join(item["source_ids"])
        accession_search = " ".join(
            accession
            for source_id in item["source_ids"]
            for accession in split_accessions(registry[source_id]["raw_data_accessions"])
        )
        genome_rows.append(f"""<tr data-catalog-row data-species="{esc('|'.join(x.lower() for x in item['species']))}" data-assay="{esc('|'.join(x.lower() for x in item['assays']))}" data-evidence="{esc('|'.join(item['evidence_classes']))}" data-search="{esc((item['assembly']+' '+species_text+' '+assay_text+' '+sources+' '+accession_search).lower())}">
          <td class="select-cell"><input type="checkbox" data-download-choice value="{esc(item['assembly'])}" data-records="{item['record_count']}" aria-label="Select {esc(item['assembly'])}"></td>
          <td class="genome-identity"><a class="genome-name" href="{item['page_url']}"><em>{esc(species_text)}</em></a><small><code>{esc(item['assembly'])}</code> <a class="external-accession" href="{assembly_accession_url(item['assembly'])}" target="_blank" rel="noopener" aria-label="Open {esc(item['assembly'])} in NCBI Datasets">NCBI ↗</a></small></td>
          <td class="experiment-summary"><strong>{esc(assay_text)}</strong><small>{item['track_count']} {study_label} · {year_text}</small></td>
          <td class="evidence-summary">{esc(evidence_text)}{evidence_badge}</td>
          <td class="number endpoint-total"><strong>{int(item['record_count']):,}</strong></td>
          <td class="row-actions"><a class="row-action primary" href="{item['page_url']}">Details</a>{browser}</td>
        </tr>""")
    sources_content = f"""
<main class="page-shell genome-directory"><div class="page-heading directory-heading"><div><p class="eyebrow">BTED v0.2.0</p><h1>{bi('Genome assemblies', '基因组目录')}</h1><p>{bi('Find an exact reference genome, inspect its independent experimental studies, or open all available tracks in one coordinate view.', '查找精确参考基因组，查看独立实验研究，或在统一坐标下打开所有可用轨道。')}</p></div></div>
<section class="directory-stats" aria-label="Database coverage"><div><strong data-visible-count>{len(grouped)}</strong><span>reference assemblies shown</span></div><div><strong>22</strong><span>independent studies</span></div><div><strong>28,399</strong><span>transcript 3′-end records</span></div></section>
<section class="filters genome-filters" aria-label="Filter genome assemblies"><label><span>{bi('Search', '搜索')}</span><input type="search" data-filter-search placeholder="Organism, strain, assembly or data accession"></label><label><span>{bi('Organism', '物种')}</span><select data-filter="species"><option value="">All organisms</option>{species_options}</select></label><label><span>{bi('Assay', '方法')}</span><select data-filter="assay"><option value="">All assays</option>{assay_options}</select></label><label><span>{bi('Evidence', '证据')}</span><select data-filter="evidence"><option value="">All evidence types</option>{evidence_options}</select></label></section>
<section class="catalog-selection" aria-label="Selected genome downloads"><div><button type="button" class="text-button" data-select-visible>Select visible</button><button type="button" class="text-button" data-clear-all>Clear</button></div><p><strong data-selected-count>0</strong> genomes selected <span aria-hidden="true">·</span> <span data-selected-records>0</span> records</p><button type="button" class="button primary" data-download-selected disabled>Download BED + metadata</button></section><p class="download-status catalog-download-status" data-download-status aria-live="polite"></p>
<div class="table-wrap genome-table-wrap"><table class="source-table genome-table"><thead><tr><th class="select-cell"><span class="visually-hidden">Select</span></th><th>{bi('Genome', '基因组')}</th><th>{bi('Experimental data', '实验数据')}</th><th>{bi('Evidence', '证据')}</th><th>{bi('3′ ends', '3′ 端点')}</th><th>{bi('Access', '访问')}</th></tr></thead><tbody>{''.join(genome_rows)}</tbody></table></div><p class="empty-state" data-empty-state hidden>{bi('No genomes match the filters.', '没有符合筛选条件的基因组。')}</p>
<p class="directory-footnote">One row represents one exact reference assembly. Studies sharing that assembly remain separate tracks in the genome view.</p></main>"""
    (SITE_ROOT / "sources.html").write_text(page("Genomes", "sources", sources_content), encoding="utf-8")

    download_rows = []
    for item in catalog_assemblies:
        sources = ", ".join(item["source_ids"])
        files = "BED + metadata" if item["status"] == "published" else "metadata only"
        download_rows.append(f"""<tr><td class="select-cell"><input type="checkbox" data-download-choice value="{esc(item['assembly'])}" data-records="{item['record_count']}" checked aria-label="Select {esc(item['assembly'])}"></td><td><a class="source-id" href="{item['page_url']}">{esc(item['assembly'])}</a><small>{esc(sources)}</small></td><td><em>{esc(' / '.join(item['species']))}</em></td><td class="number">{item['track_count']}</td><td class="number">{int(item['record_count']):,}</td><td>{esc(files)}</td></tr>""")
    catalog_content = f"""
<main class="page-shell"><div class="page-heading"><div><p class="eyebrow">v0.2.0</p><h1>{bi('Download by genome', '按基因组下载')}</h1><p>{bi('Select one or more assemblies. The ZIP keeps each genome in a separate directory with BED and metadata.', '勾选一个或多个组装；ZIP 会为每个基因组保留独立目录，其中包含 BED 和元数据。')}</p></div></div>
<section class="download-toolbar"><div><button type="button" class="button" data-select-all>{bi('Select all', '全选')}</button><button type="button" class="button" data-clear-all>{bi('Clear', '清空')}</button></div><div class="selection-summary"><strong data-selected-count>{len(grouped)}</strong> {bi('genomes selected', '个基因组已选择')} · <span data-selected-records>28,399</span> {bi('records', '条记录')}</div><button type="button" class="button primary" data-download-selected>{bi('Download selected (.zip)', '下载所选数据（.zip）')}</button></section><p class="download-status" data-download-status aria-live="polite"></p>
<div class="table-wrap"><table class="source-table download-table"><thead><tr><th class="select-cell"></th><th>{bi('Assembly / sources', '组装 / 来源')}</th><th>{bi('Organism', '物种')}</th><th>Tracks</th><th>{bi('Records', '记录数')}</th><th>{bi('Files', '文件')}</th></tr></thead><tbody>{''.join(download_rows)}</tbody></table></div>
<section class="panel download-help"><h2>{bi('What is included?', '下载内容')}</h2><div class="file-pair"><div><code>endpoints.bed</code><span>{bi('Genome coordinates for analysis and browser import', '用于分析和浏览器导入的基因组坐标')}</span></div><div><code>metadata.json</code><span>{bi('Sources, papers, accessions, evidence, limits, and checksum', '来源、文献、登录号、证据、限制和校验值')}</span></div></div></section></main>"""
    (SITE_ROOT / "catalog.html").write_text(page("Download", "catalog", catalog_content), encoding="utf-8")

    methodology_content = f"""<main class="page-shell prose"><div class="page-heading"><div><p class="eyebrow">Data notes</p><h1>{bi('How to interpret BTED', '如何理解 BTED 数据')}</h1></div></div><section><h2>{bi('Assembly grouping', '按组装聚合')}</h2><p>{bi('Datasets are grouped only when the complete reference assembly accession is identical. Grouping changes the presentation, not source identity.', '只有完整参考组装 accession 一致时才聚合；聚合只改变展示方式，不改变来源身份。')}</p></section><section><h2>{bi('Independent tracks', '独立 track')}</h2><p>{bi('A track represents one processed source. Agreement between tracks is useful for comparison but is not automatically a consensus or functional proof.', '一个 track 对应一个处理来源。不同 track 的一致性可用于比较，但不自动构成共识或功能证明。')}</p></section><section><h2>{bi('Evidence boundary', '证据边界')}</h2><p>{bi('Observed signals, locally called candidates, author-called endpoints, curated records, and predictions remain distinct. Prediction-only records are not published as endpoint data.', '实验信号、本站候选、作者端点、整理记录和预测保持分层；纯预测记录不作为端点数据发布。')}</p></section><section><h2>{bi('Files', '文件')}</h2><p>{bi('BED is the main interoperable coordinate file. One metadata JSON consolidates provenance, evidence, publications, accessions, limitations, and checksums.', 'BED 是主要的通用坐标文件；一份 metadata JSON 汇总来源、证据、文献、登录号、限制与校验值。')}</p></section></main>"""
    (SITE_ROOT / "methodology.html").write_text(page("Data notes", "methodology", methodology_content), encoding="utf-8")

    about_content = f"""<main class="page-shell prose"><div class="page-heading"><div><p class="eyebrow">BTED</p><h1>{bi('About the database', '关于数据库')}</h1></div></div><section><h2>{bi('Purpose', '目的')}</h2><p>{bi('BTED makes public bacterial transcript 3′-end datasets easier to find, compare, download, and inspect in a genome browser.', 'BTED 让公开的细菌转录 3′ 端数据更容易检索、比较、下载和在基因组浏览器中查看。')}</p></section><section><h2>{bi('Current scope', '当前范围')}</h2><p>{bi('The v0.2.0 demonstration covers 22 sources listed in BATTER Table S1: 21 endpoint datasets and one metadata-only audit record.', 'v0.2.0 演示版覆盖 BATTER Table S1 的 22 个来源：21 个端点数据集和 1 个仅元数据审计条目。')}</p></section><section><h2>{bi('Repository', '项目仓库')}</h2><p><a href="{REPOSITORY_URL}">{REPOSITORY_URL}</a></p></section></main>"""
    (SITE_ROOT / "about.html").write_text(page("About", "about", about_content), encoding="utf-8")

    print(f"PASS  Generated assembly-centred site: {len(grouped)} genome pages, 22 source records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
