#!/usr/bin/env python3
"""Generate bted-augmentation.html — BATTER augmentation data page."""
import pathlib

SITE = pathlib.Path(r'D:\SEU\实习\BATTER数据整理\BTED\repo\site')

# Build HTML in parts to avoid encoding issues
parts = []

# Part 1: head + header + main start
parts.append(r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BATTER augmentation &middot; BTED</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="css/style.css">
<style>
.aug-header { background: var(--soft); border: 1px solid var(--line); border-radius: 8px; padding: 20px 24px; margin-bottom: 24px; }
.aug-header h1 { margin: 0 0 8px; font-size: 22px; }
.aug-header p { margin: 4px 0; font-size: 14px; color: var(--muted); }
.aug-header .badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
.badge-aug { background: #e8f5e9; color: #2e7d32; }
.badge-warn { background: #fff3e0; color: #e65100; }
.filters { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; align-items: center; }
.filters input, .filters select { padding: 6px 10px; border: 1px solid var(--line); border-radius: 4px; font-size: 14px; }
.filters label { font-size: 13px; color: var(--muted); }
table.data { width: 100%; border-collapse: collapse; font-size: 13px; }
table.data th { background: var(--navy); color: var(--white); padding: 8px 10px; text-align: left; font-weight: 600; white-space: nowrap; cursor: pointer; }
table.data td { padding: 6px 10px; border-bottom: 1px solid var(--line); white-space: nowrap; }
table.data tr:nth-child(even) td { background: var(--soft); }
table.data tr:hover td { background: #e3f2fd; }
.pagination { display: flex; gap: 8px; align-items: center; margin: 16px 0; flex-wrap: wrap; }
.pagination button { padding: 4px 12px; border: 1px solid var(--line); border-radius: 4px; background: var(--white); cursor: pointer; font-size: 13px; }
.pagination button:hover { background: var(--soft); }
.pagination .active { background: var(--navy); color: var(--white); border-color: var(--navy); }
.summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 24px; }
.card { background: var(--white); border: 1px solid var(--line); border-radius: 8px; padding: 16px; text-align: center; }
.card .num { font-size: 28px; font-weight: 700; color: var(--navy); }
.card .label { font-size: 12px; color: var(--muted); margin-top: 4px; }
.collapse { margin-bottom: 12px; }
.collapse summary { cursor: pointer; font-weight: 600; padding: 8px 12px; background: var(--soft); border-radius: 4px; }
.collapse[open] summary { border-radius: 4px 4px 0 0; border-bottom: 1px solid var(--line); }
.collapse table { margin-top: 0; }
.loading { text-align: center; padding: 40px; color: var(--muted); }
.error { text-align: center; padding: 40px; color: #c62828; }
table.data .num-col { text-align: right; font-variant-numeric: tabular-nums; }
</style>
</head>
<body data-lang="en">

<header class="site-header">
<div class="header-inner">
<a class="brand" href="index.html"><span class="brand-mark">BTED</span><span class="brand-name">Bacterial Transcript 3&prime; End Database</span></a>
<nav class="site-nav" aria-label="Primary navigation">
<a href="index.html">Home</a>
<a href="sources.html">Genomes</a>
<a href="catalog.html">Download</a>
<a href="bted-augmentation.html" class="active">Augmentation</a>
<a href="methodology.html">Data notes</a>
<a href="about.html">About</a>
</nav>
</div>
</header>

<main class="page-shell">

<div class="aug-header">
<h1>BATTER data augmentation</h1>
<p>This page presents the <strong>BATTER augmentation dataset</strong> (C-layer evidence) derived from the BATTER paper (Xu et al., 2026).</p>
<p>The augmentation pipeline starts with experimentally validated Term-seq 3&prime; ends, clusters them by sequence identity (cd-hit, 40%), searches 42,905 bacterial genomes (GEMs catalog) for homologs via hmmsearch(Pfam), and predicts stem-loop structures with CMfinder.</p>
<p><span class="badge badge-aug">~2.4M stem-loop instances</span> <span class="badge badge-warn">Prediction &mdash; not experimentally validated</span></p>
</div>

<div class="summary-cards" id="summary-cards">
<div class="card"><div class="num" id="stat-otu">&hellip;</div><div class="label">Bacterial OTUs</div></div>
<div class="card"><div class="num" id="stat-inst">&hellip;</div><div class="label">Augmented instances</div></div>
<div class="card"><div class="num" id="stat-phyla">&hellip;</div><div class="label">Phyla</div></div>
<div class="card"><div class="num" id="stat-genes">&hellip;</div><div class="label">Gene clusters</div></div>
<div class="card"><div class="num" id="stat-rfam">&hellip;</div><div class="label">Rfam families</div></div>
</div>

<div class="filters">
<label>Search:</label>
<input type="text" id="search-input" placeholder="OTU id, phylum, taxonomy&hellip;" style="flex:1;max-width:400px">
<label>Phylum:</label>
<select id="phylum-filter"></select>
<label>Min instances:</label>
<input type="number" id="min-inst" value="1" min="1" style="width:80px">
<span style="font-size:13px;color:var(--muted)">(<span id="filter-count">0</span> match)</span>
</div>

<div id="loading" class="loading">Loading augmentation data&hellip;</div>
<div id="error" class="error" style="display:none"></div>
<div id="table-container" style="display:none">
<div style="overflow-x:auto">
<table class="data" id="otu-table">
<thead><tr>
<th data-col="otu_id">OTU ID</th>
<th data-col="augmented_instances" class="num-col">Instances</th>
<th data-col="forward" class="num-col">+</th>
<th data-col="reverse" class="num-col">&minus;</th>
<th data-col="unique_genes" class="num-col">Genes</th>
<th data-col="phylum">Phylum</th>
<th data-col="taxonomy">Taxonomy (abbrev.)</th>
<th data-col="genome_id">Genome</th>
<th data-col="completeness" class="num-col">Comp. %</th>
</tr></thead>
<tbody id="otu-tbody"></tbody>
</table>
</div>
<div style="font-size:13px;color:var(--muted);margin-bottom:24px">Page <span id="cur-page">1</span> of <span id="tot-pages">1</span> (<span id="filter-count2">0</span> OTUs)</div>
<div class="pagination" id="pagination"></div>
</div>

<h2>Gene clusters (115)</h2>
<p>Seed gene families identified by clustering Term-seq 3&prime; ends (cd-hit 40% identity) and selecting clusters with representatives from &ge;3 phyla.</p>
<div id="gene-clusters-container" class="loading">Loading&hellip;</div>

<details class="collapse"><summary>Rfam families (928)</summary>
<p style="font-size:13px;color:var(--muted);margin:8px 0">Riboswitch and RNA family annotations associated with the augmentation dataset.</p>
<div id="rfam-container" class="loading">Loading&hellip;</div>
</details>

<details class="collapse"><summary>Stem-loop properties (2,048 OTU)</summary>
<p style="font-size:13px;color:var(--muted);margin:8px 0">Predicted stem-loop structural features per OTU.</p>
<div id="stemloop-container" class="loading">Loading&hellip;</div>
</details>

<details class="collapse"><summary>Rho dependency (15,748 OTU)</summary>
<p style="font-size:13px;color:var(--muted);margin:8px 0">Rho-dependent termination likelihood scores per OTU.</p>
<div id="rho-container" class="loading">Loading&hellip;</div>
</details>

<h2>Data downloads</h2>
<div class="summary-cards" style="grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));">
<div class="card">
<div class="label" style="font-weight:700;margin-bottom:8px">Full dataset (Zenodo)</div>
<p style="font-size:12px;color:var(--muted);margin:0"><strong>terminators.flanked.fa.gz</strong> (487 MB) &mdash; all augmented instances as FASTA<br>
<strong>TES.bed.gz</strong> (1.2 GB) &mdash; genome-wide BATTER predictions<br>
<strong>combined-statistics.txt</strong> (10 MB) &mdash; per-OTU statistics</p>
</div>
<div class="card">
<div class="label" style="font-weight:700;margin-bottom:8px">Local tables</div>
<p style="font-size:12px;color:var(--muted);margin:0">
<a href="data/augmentation/per_otu_index.json">per_otu_index.json</a> (42,637 OTUs)<br>
<a href="data/augmentation/gene_clusters.tsv">gene_clusters.tsv</a> (115)<br>
<a href="data/augmentation/rfam_families.tsv">rfam_families.tsv</a> (928)<br>
<a href="data/augmentation/stem_loop_properties.tsv">stem_loop_properties.tsv</a> (2,048)<br>
<a href="data/augmentation/rho_dependency.tsv">rho_dependency.tsv</a> (15,748)<br>
<a href="data/augmentation/combined-statistics.txt">combined-statistics.txt</a> (42,905 OTU)</p>
</div>
</div>

<p style="font-size:13px;color:#c62828;background:#ffebee;padding:12px;border-radius:4px;margin-top:24px">
<strong>Disclaimer:</strong> The BATTER augmentation dataset (C-layer) consists of <strong>bioinformatically predicted stem-loop structures</strong> that are homologous to experimentally observed 3&prime; ends. These <strong>have not been experimentally validated</strong>. See <a href="https://doi.org/10.1186/s40168-026-02454-5">Xu et al. 2026</a> for the full methodology and validation statistics.</p>

</main>

<footer class="site-footer">
<div class="footer-inner">
<span>BTED v0.2.0</span>
<span>22 source records &middot; 21 browser-ready datasets</span>
<a href="https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database">GitHub</a>
</div>
</footer>

<script>
""")

# Part 2: JavaScript (avoid any string that might confuse the heredoc)
js = r"""(function() {
"use strict";

var DATA_URL = 'data/augmentation/per_otu_index.json';
var GC_URL = 'data/augmentation/gene_clusters.tsv';
var RF_URL = 'data/augmentation/rfam_families.tsv';
var SL_URL = 'data/augmentation/stem_loop_properties.tsv';
var RD_URL = 'data/augmentation/rho_dependency.tsv';

var otuData = [];
var filtered = [];
var sortCol = 'augmented_instances';
var sortAsc = false;
var page = 1;
var ROWS_PER_PAGE = 50;

function qs(s) { return document.querySelector(s); }
function qsa(s) { return document.querySelectorAll(s); }

function loadData() {
  var loadEl = qs('#loading');
  var errEl = qs('#error');
  var tblEl = qs('#table-container');

  fetch(DATA_URL)
    .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function(d) {
      otuData = d.otus;
      qs('#stat-otu').textContent = d.metadata.total_otus.toLocaleString();
      qs('#stat-inst').textContent = d.metadata.total_instances.toLocaleString();
      // Count phyla
      var phyla = {};
      otuData.forEach(function(o) { if (o.phylum) phyla[o.phylum] = (phyla[o.phylum] || 0) + 1; });
      qs('#stat-phyla').textContent = Object.keys(phyla).length;
      // Populate phylum filter
      var sel = qs('#phylum-filter');
      var phyList = Object.keys(phyla).sort();
      sel.innerHTML = '<option value="">All phyla</option>' + phyList.map(function(p) { return '<option>' + p + '</option>'; }).join('');

      loadGeneClusters();
      loadRfam();
      loadStemloop();
      loadRho();

      loadEl.style.display = 'none';
      tblEl.style.display = 'block';
      onSearch();
    })
    .catch(function(e) {
      loadEl.style.display = 'none';
      errEl.style.display = 'block';
      errEl.textContent = 'Failed to load: ' + e.message;
    });
}

function loadGeneClusters() {
  fetch(GC_URL).then(function(r) { return r.text(); }).then(function(t) {
    var rows = t.trim().split('\n').slice(1);
    var html = '<table class="data"><thead><tr><th>Cluster</th><th>Gene</th><th>Pfam</th></tr></thead><tbody>';
    rows.forEach(function(r) { var c = r.split('\t'); html += '<tr><td>' + c[0] + '</td><td>' + c[1] + '</td><td>' + (c[2] || '') + '</td></tr>'; });
    html += '</tbody></table>';
    qs('#gene-clusters-container').innerHTML = html;
    qs('#stat-genes').textContent = rows.length;
  }).catch(function() { qs('#gene-clusters-container').innerHTML = '<span class="error">Load failed</span>'; });
}

function loadRfam() {
  fetch(RF_URL).then(function(r) { return r.text(); }).then(function(t) {
    var rows = t.trim().split('\n').slice(1);
    var cats = {};
    rows.forEach(function(r) {
      var c = r.split('\t');
      var cat = c[3] || 'Other';
      if (!cats[cat]) cats[cat] = [];
      cats[cat].push(c);
    });
    var html = '';
    Object.keys(cats).sort().forEach(function(c) {
      html += '<details class="collapse"><summary>' + c + ' (' + cats[c].length + ')</summary><table class="data"><thead><tr><th>Rfam</th><th>Name</th><th>Desc.</th></tr></thead><tbody>';
      cats[c].forEach(function(r) {
        html += '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td><td>' + (r[2] || '') + '</td></tr>';
      });
      html += '</tbody></table></details>';
    });
    qs('#rfam-container').innerHTML = html;
    qs('#stat-rfam').textContent = rows.length;
  }).catch(function() { qs('#rfam-container').innerHTML = '<span class="error">Load failed</span>'; });
}

function loadStemloop() {
  fetch(SL_URL).then(function(r) { return r.text(); }).then(function(t) {
    var rows = t.trim().split('\n');
    var html = '<div style="overflow-x:auto"><table class="data"><thead><tr>';
    rows[0].split('\t').forEach(function(h) { html += '<th>' + h + '</th>'; });
    html += '</tr></thead><tbody>';
    for (var i = 1; i < rows.length; i++) {
      html += '<tr>';
      rows[i].split('\t').forEach(function(c) { html += '<td>' + c + '</td>'; });
      html += '</tr>';
    }
    html += '</tbody></table></div>';
    qs('#stemloop-container').innerHTML = html;
  }).catch(function() { qs('#stemloop-container').innerHTML = '<span class="error">Load failed</span>'; });
}

function loadRho() {
  fetch(RD_URL).then(function(r) { return r.text(); }).then(function(t) {
    var rows = t.trim().split('\n');
    var html = '<div style="overflow-x:auto"><table class="data"><thead><tr>';
    rows[0].split('\t').forEach(function(h) { html += '<th>' + h + '</th>'; });
    html += '</tr></thead><tbody>';
    for (var i = 1; i < rows.length; i++) {
      html += '<tr>';
      rows[i].split('\t').forEach(function(c) { html += '<td>' + c + '</td>'; });
      html += '</tr>';
    }
    html += '</tbody></table></div>';
    qs('#rho-container').innerHTML = html;
  }).catch(function() { qs('#rho-container').innerHTML = '<span class="error">Load failed</span>'; });
}

function filterData() {
  var q = qs('#search-input').value.trim().toLowerCase();
  var phy = qs('#phylum-filter').value;
  var min = parseInt(qs('#min-inst').value) || 1;
  filtered = otuData.filter(function(o) {
    if (o.augmented_instances < min) return false;
    if (phy && o.phylum !== phy) return false;
    if (q) {
      if (o.otu_id.toLowerCase().indexOf(q) !== -1) return true;
      if (o.phylum && o.phylum.toLowerCase().indexOf(q) !== -1) return true;
      if (o.taxonomy && o.taxonomy.toLowerCase().indexOf(q) !== -1) return true;
      if (o.genome_id && o.genome_id.toLowerCase().indexOf(q) !== -1) return true;
      return false;
    }
    return true;
  });
  sortData();
}

function sortData() {
  filtered.sort(function(a, b) {
    var va = a[sortCol], vb = b[sortCol];
    if (typeof va === 'string') { va = va.toLowerCase(); vb = (vb || '').toLowerCase(); }
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  });
  page = 1;
  render();
}

function render() {
  var start = (page - 1) * ROWS_PER_PAGE;
  var end = Math.min(start + ROWS_PER_PAGE, filtered.length);
  var pageData = filtered.slice(start, end);
  var html = '';
  pageData.forEach(function(o) {
    var abrvTax = '';
    if (o.taxonomy) {
      var p = o.taxonomy.split(';');
      abrvTax = p.slice(0, 4).map(function(s) { return s.split('__')[1] || ''; }).filter(Boolean).join('; ');
    }
    html += '<tr>' +
      '<td>' + htmlEscape(o.otu_id) + '</td>' +
      '<td class="num-col">' + o.augmented_instances.toLocaleString() + '</td>' +
      '<td class="num-col">' + o.forward + '</td>' +
      '<td class="num-col">' + o.reverse + '</td>' +
      '<td class="num-col">' + o.unique_genes.toLocaleString() + '</td>' +
      '<td>' + htmlEscape(o.phylum || '') + '</td>' +
      '<td style="font-size:12px" title="' + htmlEscape(o.taxonomy) + '">' + htmlEscape(abrvTax) + '</td>' +
      '<td>' + htmlEscape(o.genome_id || '') + '</td>' +
      '<td class="num-col">' + (o.completeness || '') + '</td>' +
      '</tr>';
  });
  qs('#otu-tbody').innerHTML = html;
  qs('#filter-count').textContent = filtered.length.toLocaleString();
  qs('#filter-count2').textContent = filtered.length.toLocaleString();
  qs('#cur-page').textContent = page;
  var ttl = Math.ceil(filtered.length / ROWS_PER_PAGE) || 1;
  qs('#tot-pages').textContent = ttl;
  renderPagination(ttl);
}

function onSearch() { filterData(); }

function renderPagination(ttl) {
  var el = qs('#pagination');
  var html = '';
  html += '<button onclick="page=1;render()" ' + (page === 1 ? 'disabled' : '') + '>&laquo;</button>';
  html += '<button onclick="page=Math.max(1,page-1);render()" ' + (page === 1 ? 'disabled' : '') + '>&#8249;</button>';
  var start = Math.max(1, page - 2);
  var end = Math.min(ttl, page + 2);
  for (var p = start; p <= end; p++) {
    html += '<button onclick="page=' + p + ';render()" ' + (p === page ? 'class="active"' : '') + '>' + p + '</button>';
  }
  html += '<button onclick="page=Math.min(ttl,page+1);render()" ' + (page === ttl ? 'disabled' : '') + '>&#8250;</button>';
  html += '<button onclick="page=ttl;render()" ' + (page === ttl ? 'disabled' : '') + '>&raquo;</button>';
  el.innerHTML = html;
}

function htmlEscape(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Event listeners
qs('#search-input').addEventListener('input', onSearch);
qs('#phylum-filter').addEventListener('change', onSearch);
qs('#min-inst').addEventListener('input', onSearch);

// Sort clicks
qsa('#otu-table th[data-col]').forEach(function(th) {
  th.style.cursor = 'pointer';
  th.style.userSelect = 'none';
  th.addEventListener('click', function() {
    sortCol = th.dataset.col;
    sortAsc = !sortAsc;
    sortData();
  });
});

loadData();

})();
</script>
</body>
</html>
"""

parts.append(js)

# Write it all
out = SITE / 'bted-augmentation.html'
out.write_text(''.join(parts), encoding='utf-8')
print('Written', out, 'size:', out.stat().st_size, 'bytes')