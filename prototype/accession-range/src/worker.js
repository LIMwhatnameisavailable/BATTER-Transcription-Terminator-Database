const PUBLIC_EVIDENCE = new Set([
  "observed_signal",
  "called_endpoint",
  "author_called_endpoint",
  "curated_record",
]);

const RESPONSE_HEADERS = [
  "accept-ranges",
  "cache-control",
  "content-length",
  "content-range",
  "content-type",
  "last-modified",
];

function json(payload, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...extraHeaders },
  });
}

function bad(code, message, field) {
  return json({ error: { code, message, ...(field ? { field } : {}) } }, 422);
}

function decodePath(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return null;
  }
}

function isLoopbackHost(hostname) {
  return hostname === "localhost" || hostname === "127.0.0.1";
}

function pageParams(url) {
  const page = Number(url.searchParams.get("page") || "1");
  const pageSize = Number(url.searchParams.get("page_size") || "50");
  if (!Number.isInteger(page) || page < 1) return { error: bad("invalid_pagination", "page must be an integer >= 1", "page") };
  if (!Number.isInteger(pageSize) || pageSize < 1 || pageSize > 100) {
    return { error: bad("invalid_pagination", "page_size must be between 1 and 100", "page_size") };
  }
  return { page, pageSize, offset: (page - 1) * pageSize };
}

function pageResult(data, page, pageSize, total) {
  return {
    data,
    pagination: {
      page,
      page_size: pageSize,
      returned: data.length,
      total,
      has_next: page * pageSize < total,
    },
  };
}

async function currentRelease(env, requested) {
  const query = requested
    ? "SELECT * FROM release_versions WHERE release_version = ?"
    : "SELECT * FROM release_versions WHERE is_current = 1 LIMIT 1";
  return env.BTED_DB.prepare(query).bind(...(requested ? [requested] : [])).first();
}

function releasePayload(release) {
  return {
    release_version: release.release_version,
    status: release.status,
    canonical_manifest_path: release.canonical_manifest_path,
    canonical_manifest_sha256: release.canonical_manifest_sha256,
    asset_origin_status: release.asset_origin_status,
    materializer_version: release.materializer_version,
  };
}

async function withRelease(env, url) {
  const release = await currentRelease(env, url.searchParams.get("release_version"));
  return release ? { release, summary: releasePayload(release) } : null;
}

function assetUrl(request, assetKey, route = "/api/assets/") {
  return new URL(`${route}${encodeURIComponent(assetKey)}`, request.url).href;
}

async function publicAsset(env, releaseVersion, assetKey) {
  return env.BTED_DB.prepare(
    "SELECT asset_key, release_version, assembly_accession, source_id, asset_kind, logical_path, origin_host, content_type, byte_size, sha256, supports_range, redistribution_status, is_public FROM assets WHERE asset_key = ? AND release_version = ? AND active = 1 AND is_public = 1",
  ).bind(assetKey, releaseVersion).first();
}

async function allAssets(env, releaseVersion, accession, sourceId) {
  let sql = "SELECT asset_key, release_version, assembly_accession, source_id, asset_kind, logical_path, origin_host, content_type, byte_size, sha256, supports_range, redistribution_status, is_public FROM assets WHERE release_version = ? AND active = 1";
  const params = [releaseVersion];
  if (accession) {
    sql += " AND assembly_accession = ?";
    params.push(accession);
  }
  if (sourceId) {
    sql += " AND source_id = ?";
    params.push(sourceId);
  }
  sql += " ORDER BY asset_kind, logical_path";
  const result = await env.BTED_DB.prepare(sql).bind(...params).all();
  return result.results || [];
}

async function sourceAccessions(env, releaseVersion, sourceId) {
  const result = await env.BTED_DB.prepare(
    "SELECT accession_namespace, accession, raw_value, accession_type, ordinal, external_url FROM source_accessions WHERE release_version = ? AND source_id = ? ORDER BY ordinal, accession",
  ).bind(releaseVersion, sourceId).all();
  return result.results || [];
}

async function sourceRow(env, releaseVersion, sourceId) {
  return env.BTED_DB.prepare(
    "SELECT * FROM sources WHERE release_version = ? AND source_id = ?",
  ).bind(releaseVersion, sourceId).first();
}

async function publication(env, pmid) {
  return pmid ? env.BTED_DB.prepare("SELECT * FROM publications WHERE pmid = ?").bind(pmid).first() : null;
}

function publicBrowserAvailable(source, assets, assemblyAssets) {
  const bed = source && source.release_status === "published_standardized" && Number(source.record_count) > 0
    ? assets.find((asset) => asset.asset_kind === "bed" && Number(asset.is_public) === 1)
    : null;
  const fasta = assemblyAssets.find((asset) => asset.asset_kind === "fasta" && Number(asset.is_public) === 1);
  const fai = assemblyAssets.find((asset) => asset.asset_kind === "fai" && Number(asset.is_public) === 1);
  return Boolean(bed && fasta && fai);
}

async function trackRows(env, releaseVersion, accession, sourceId) {
  let sql = "SELECT * FROM tracks WHERE release_version = ?";
  const params = [releaseVersion];
  if (accession) {
    sql += " AND assembly_accession = ?";
    params.push(accession);
  }
  if (sourceId) {
    sql += " AND source_id = ?";
    params.push(sourceId);
  }
  sql += " ORDER BY display_order";
  const result = await env.BTED_DB.prepare(sql).bind(...params).all();
  return result.results || [];
}

async function sourcePayload(request, env, release, sourceId) {
  const source = await sourceRow(env, release.release_version, sourceId);
  if (!source) return null;
  const [paper, accessions, assets, tracks, assemblyAssets] = await Promise.all([
    publication(env, source.publication_pmid),
    sourceAccessions(env, release.release_version, sourceId),
    allAssets(env, release.release_version, null, sourceId),
    trackRows(env, release.release_version, null, sourceId),
    allAssets(env, release.release_version, source.assembly_accession, null),
  ]);
  const browserAvailable = publicBrowserAvailable(source, assets, assemblyAssets);
  const links = {
    bted_record: `/records/${encodeURIComponent(sourceId)}.html`,
  };
  if (source.release_status === "published_standardized" && Number(source.record_count) > 0) {
    links.endpoints = `/api/endpoints?source_id=${encodeURIComponent(sourceId)}`;
    if (browserAvailable) {
      const config = new URL(`/api/assemblies/${encodeURIComponent(source.assembly_accession)}/jbrowse-config`, request.url);
      config.searchParams.set("source_id", sourceId);
      links.jbrowse_config = config.href;
    }
  }
  return {
    release: releasePayload(release),
    source: {
      ...source,
      augmentation_eligible: Boolean(source.used_for_batter_augmentation),
      publication: paper,
      accessions,
      tracks,
      assets,
      browser_available: browserAvailable,
      links,
      provenance: {
        release_version: release.release_version,
        source_manifest_sha256: source.manifest_sha256,
      },
    },
  };
}

async function sourcesList(request, env, release, url) {
  const paging = pageParams(url);
  if (paging.error) return paging.error;
  const { page, pageSize, offset } = paging;
  const filters = [];
  const params = [release.release_version];
  const exact = [["source_id", "source_id"], ["species", "species"], ["assay_family", "assay_family"], ["release_status", "release_status"], ["evidence_class", "evidence_class"], ["assembly_accession", "assembly_accession"]];
  for (const [queryName, column] of exact) {
    const value = url.searchParams.get(queryName);
    if (value) {
      filters.push(`s.${column} = ?`);
      params.push(value);
    }
  }
  const augmentation = url.searchParams.get("augmentation_eligible");
  if (augmentation !== null) {
    if (!["true", "false", "1", "0"].includes(augmentation)) return bad("invalid_filter", "augmentation_eligible must be true or false", "augmentation_eligible");
    filters.push("s.used_for_batter_augmentation = ?");
    params.push(["true", "1"].includes(augmentation) ? 1 : 0);
  }
  const q = url.searchParams.get("q");
  if (q) {
    filters.push("(s.source_id LIKE ? OR s.species LIKE ? OR s.manifest_path LIKE ? OR p.pmid LIKE ? OR p.paper_title LIKE ?)");
    const pattern = `%${q}%`;
    params.push(pattern, pattern, pattern, pattern, pattern);
  }
  const where = filters.length ? ` AND ${filters.join(" AND ")}` : "";
  const count = await env.BTED_DB.prepare(`SELECT COUNT(*) AS total FROM sources s LEFT JOIN publications p ON p.pmid = s.publication_pmid WHERE s.release_version = ?${where}`).bind(...params).first();
  const rows = await env.BTED_DB.prepare(`SELECT s.*, p.paper_title, p.published_year, p.doi FROM sources s LEFT JOIN publications p ON p.pmid = s.publication_pmid WHERE s.release_version = ?${where} ORDER BY s.source_id LIMIT ? OFFSET ?`).bind(...params, pageSize, offset).all();
  const data = (rows.results || []).map((row) => ({
    ...row,
    augmentation_eligible: Boolean(row.used_for_batter_augmentation),
    links: { detail: `/api/sources/${encodeURIComponent(row.source_id)}` },
    provenance: { release_version: release.release_version, source_manifest_sha256: row.manifest_sha256 },
  }));
  return json({ release: releasePayload(release), ...pageResult(data, page, pageSize, Number(count?.total || 0)) });
}

async function assemblyPayload(request, env, release, accession) {
  const assembly = await env.BTED_DB.prepare(
    "SELECT * FROM assemblies WHERE release_version = ? AND accession = ?",
  ).bind(release.release_version, accession).first();
  if (!assembly) return null;
  const [contigs, tracks, assets, registeredAssets, endpointCount] = await Promise.all([
    env.BTED_DB.prepare("SELECT contig_accession, contig_name, length_bp, sequence_sha256, provenance_json FROM contigs WHERE release_version = ? AND assembly_accession = ? ORDER BY contig_accession").bind(release.release_version, accession).all(),
    trackRows(env, release.release_version, accession, null),
    allAssets(env, release.release_version, accession, null),
    allAssets(env, release.release_version, null, null),
    env.BTED_DB.prepare("SELECT COUNT(*) AS total FROM endpoints WHERE release_version = ? AND reference_assembly = ?").bind(release.release_version, accession).first(),
  ]);
  const trackData = [];
  for (const track of tracks) {
    const source = await sourceRow(env, release.release_version, track.source_id);
    const sourceAssets = registeredAssets.filter((asset) => asset.source_id === track.source_id);
    trackData.push({
      ...track,
      source_status: source?.release_status,
      browser_available: publicBrowserAvailable(source, sourceAssets, assets),
      links: { source: `/api/sources/${encodeURIComponent(track.source_id)}` },
    });
  }
  const browserAvailable = trackData.some((track) => track.browser_available);
  return {
    release: releasePayload(release),
    assembly: {
      ...assembly,
      contigs: contigs.results || [],
      tracks: trackData,
      assets,
      endpoint_count: Number(endpointCount?.total || 0),
      browser_available: browserAvailable,
      links: {
        catalogue: `/api/catalogue?assembly_accession=${encodeURIComponent(accession)}`,
        ...(browserAvailable ? { jbrowse_config: new URL(`/api/assemblies/${encodeURIComponent(accession)}/jbrowse-config`, request.url).href } : {}),
      },
      provenance: { release_version: release.release_version },
    },
  };
}

async function assembliesList(env, release, url) {
  const paging = pageParams(url);
  if (paging.error) return paging.error;
  const { page, pageSize, offset } = paging;
  const filters = [];
  const params = [release.release_version];
  const accession = url.searchParams.get("assembly_accession");
  const species = url.searchParams.get("species");
  const q = url.searchParams.get("q");
  if (accession) { filters.push("a.accession = ?"); params.push(accession); }
  if (species) { filters.push("a.organism_name = ?"); params.push(species); }
  if (q) { filters.push("(a.accession LIKE ? OR a.organism_name LIKE ? OR a.strain LIKE ?)"); const p = `%${q}%`; params.push(p, p, p); }
  const where = filters.length ? ` AND ${filters.join(" AND ")}` : "";
  const count = await env.BTED_DB.prepare(`SELECT COUNT(*) AS total FROM assemblies a WHERE a.release_version = ?${where}`).bind(...params).first();
  const rows = await env.BTED_DB.prepare(`SELECT a.*, (SELECT COUNT(*) FROM sources s WHERE s.release_version = a.release_version AND s.assembly_accession = a.accession) AS source_count, (SELECT COUNT(*) FROM endpoints e WHERE e.release_version = a.release_version AND e.reference_assembly = a.accession) AS endpoint_count, (SELECT COUNT(*) FROM assets x WHERE x.release_version = a.release_version AND x.assembly_accession = a.accession AND x.asset_kind = 'fasta' AND x.is_public = 1) AS public_fasta_count FROM assemblies a WHERE a.release_version = ?${where} ORDER BY a.accession LIMIT ? OFFSET ?`).bind(...params, pageSize, offset).all();
  const data = (rows.results || []).map((row) => ({ ...row, browser_candidate: Number(row.public_fasta_count) > 0, provenance: { release_version: release.release_version } }));
  return json({ release: releasePayload(release), ...pageResult(data, page, pageSize, Number(count?.total || 0)) });
}

function endpointFilters(url) {
  const filters = [];
  const params = [];
  const sources = url.searchParams.getAll("source_id");
  if (sources.length) { filters.push(`e.source_id IN (${sources.map(() => "?").join(",")})`); params.push(...sources); }
  for (const [name, column] of [["assembly_accession", "reference_assembly"], ["contig_accession", "reference_name"], ["sample_id", "sample_id"], ["strand", "strand"], ["evidence_class", "evidence_class"]]) {
    const value = url.searchParams.get(name);
    if (value) { if (name === "evidence_class" && !PUBLIC_EVIDENCE.has(value)) return { error: bad("invalid_filter", `${value} is not a public endpoint evidence class`, name) }; if (name === "strand" && !["+", "-"].includes(value)) return { error: bad("invalid_filter", "strand must be + or -", name) }; filters.push(`e.${column} = ?`); params.push(value); }
  }
  for (const [name, operator] of [["position_min", ">="], ["position_max", "<="]]) {
    const value = url.searchParams.get(name);
    if (value !== null) { const n = Number(value); if (!Number.isInteger(n) || n < 1) return { error: bad("invalid_filter", `${name} must be a positive integer`, name) }; filters.push(`e.biological_coordinate_1based ${operator} ?`); params.push(n); }
  }
  const locus = url.searchParams.get("gene_or_locus");
  if (locus) { filters.push("e.associated_gene_or_locus = ?"); params.push(locus); }
  const q = url.searchParams.get("q");
  if (q) { filters.push("(e.end_id LIKE ? OR e.author_endpoint_id LIKE ? OR e.original_row_reference LIKE ?)"); const p = `%${q}%`; params.push(p, p, p); }
  return { sql: filters.length ? ` AND ${filters.join(" AND ")}` : "", params };
}

async function endpointsList(env, release, url) {
  const paging = pageParams(url);
  if (paging.error) return paging.error;
  const filter = endpointFilters(url);
  if (filter.error) return filter.error;
  const { page, pageSize, offset } = paging;
  const count = await env.BTED_DB.prepare(`SELECT COUNT(*) AS total FROM endpoints e WHERE e.release_version = ?${filter.sql}`).bind(release.release_version, ...filter.params).first();
  const order = url.searchParams.get("sort") || "end_id";
  const orderMap = { end_id: "e.end_id", position: "e.biological_coordinate_1based", source_id: "e.source_id", contig_accession: "e.reference_name" };
  if (!Object.prototype.hasOwnProperty.call(orderMap, order)) return bad("invalid_sort", `unsupported endpoint sort: ${order}`, "sort");
  const direction = url.searchParams.get("order") === "desc" ? "DESC" : "ASC";
  const rows = await env.BTED_DB.prepare(`SELECT e.* FROM endpoints e WHERE e.release_version = ?${filter.sql} ORDER BY ${orderMap[order]} ${direction}, e.end_id ASC LIMIT ? OFFSET ?`).bind(release.release_version, ...filter.params, pageSize, offset).all();
  const data = rows.results || [];
  return json({ release: releasePayload(release), ...pageResult(data, page, pageSize, Number(count?.total || 0)) });
}

async function augmentation(env, release, url) {
  const paging = pageParams(url);
  if (paging.error) return paging.error;
  const { page, pageSize, offset } = paging;
  const count = await env.BTED_DB.prepare("SELECT COUNT(*) AS total FROM sources WHERE release_version = ? AND used_for_batter_augmentation = 1").bind(release.release_version).first();
  const rows = await env.BTED_DB.prepare("SELECT source_id, assembly_accession, evidence_class, record_count, publication_pmid, manifest_sha256 FROM sources WHERE release_version = ? AND used_for_batter_augmentation = 1 ORDER BY source_id LIMIT ? OFFSET ?").bind(release.release_version, pageSize, offset).all();
  return json({ release: releasePayload(release), scope: "source", selection_rule: "BATTER Table S1 used_for_batter_augmentation = TRUE", eligible_source_count: Number(count?.total || 0), training_claim: "none; source-level eligibility only", ...pageResult(rows.results || [], page, pageSize, Number(count?.total || 0)) });
}

async function catalogue(env, release, url) {
  const [stats, assemblies] = await Promise.all([
    statsPayload(env, release),
    assembliesList(env, release, url),
  ]);
  const assemblyJson = await assemblies.json();
  return json({ release: releasePayload(release), stats, assemblies: assemblyJson });
}

async function statsPayload(env, release) {
  const [sources, endpoints, assemblies, augmentation, evidence] = await Promise.all([
    env.BTED_DB.prepare("SELECT release_status, COUNT(*) AS total FROM sources WHERE release_version = ? GROUP BY release_status").bind(release.release_version).all(),
    env.BTED_DB.prepare("SELECT COUNT(*) AS total FROM endpoints WHERE release_version = ?").bind(release.release_version).first(),
    env.BTED_DB.prepare("SELECT COUNT(*) AS total FROM assemblies WHERE release_version = ?").bind(release.release_version).first(),
    env.BTED_DB.prepare("SELECT COUNT(*) AS total FROM sources WHERE release_version = ? AND used_for_batter_augmentation = 1").bind(release.release_version).first(),
    env.BTED_DB.prepare("SELECT evidence_class, COUNT(*) AS total FROM endpoints WHERE release_version = ? GROUP BY evidence_class ORDER BY evidence_class").bind(release.release_version).all(),
  ]);
  const sourceCounts = Object.fromEntries((sources.results || []).map((row) => [row.release_status, Number(row.total)]));
  return {
    sources: { total: Object.values(sourceCounts).reduce((sum, value) => sum + value, 0), published_standardized: sourceCounts.published_standardized || 0, audit_only: sourceCounts.audit_only || 0 },
    endpoints: { total: Number(endpoints?.total || 0), by_evidence_class: Object.fromEntries((evidence.results || []).map((row) => [row.evidence_class, Number(row.total)])) },
    assemblies: { total: Number(assemblies?.total || 0) },
    augmentation: { eligible_sources: Number(augmentation?.total || 0), scope: "source" },
  };
}

async function stats(env, release) {
  return json({ release: releasePayload(release), ...(await statsPayload(env, release)) });
}

async function endpointDetail(env, release, endId) {
  const row = await env.BTED_DB.prepare("SELECT * FROM endpoints WHERE release_version = ? AND end_id = ?").bind(release.release_version, endId).first();
  return row ? json({ release: releasePayload(release), endpoint: { ...row, provenance: { release_version: release.release_version, source_id: row.source_id, contig_accession: row.reference_name } } }) : json({ error: "endpoint_not_found", end_id: endId }, 404);
}

async function jbrowseConfig(request, env, release, accession, sourceId) {
  const assembly = await env.BTED_DB.prepare("SELECT * FROM assemblies WHERE release_version = ? AND accession = ?").bind(release.release_version, accession).first();
  if (!assembly) return json({ error: "assembly_not_found", accession }, 404);
  const threeLayerPilot = new URL(request.url).searchParams.get("pilot") === "three-layer"
    && accession === "GCF_000009045.1"
    && (!sourceId || sourceId === "BATTER_S1_003");
  const [assemblyAssets, tracks] = await Promise.all([
    allAssets(env, release.release_version, accession, null),
    trackRows(env, release.release_version, accession, sourceId),
  ]);
  const fasta = assemblyAssets.find((asset) => asset.asset_kind === "fasta" && Number(asset.is_public) === 1);
  const fai = assemblyAssets.find((asset) => asset.asset_kind === "fai" && Number(asset.is_public) === 1);
  if (!fasta || !fai) return json({ error: "jbrowse_unavailable", reason: "public FASTA+FAI are not registered for this assembly" }, 404);
  const publicTracks = [];
  for (const track of tracks) {
    const source = await sourceRow(env, release.release_version, track.source_id);
    if (!source || source.release_status !== "published_standardized" || Number(track.is_public) !== 1 || !track.asset_key) continue;
    const bed = await publicAsset(env, release.release_version, track.asset_key);
    if (!bed) continue;
    const sourceAssets = await allAssets(env, release.release_version, null, source.source_id);
    publicTracks.push({ track, source, bed, sourceAssets });
  }
  if (!publicTracks.length) return json({ error: "jbrowse_unavailable", reason: "no public published endpoint track" }, 404);
  const assemblyName = `BTED_${accession.replaceAll(".", "_")}`;
  const gff = assemblyAssets.find((asset) => asset.asset_kind === "gff3" && Number(asset.is_public) === 1);
  const tbi = assemblyAssets.find((asset) => asset.asset_kind === "tbi" && Number(asset.is_public) === 1);
  const contig = await env.BTED_DB.prepare("SELECT contig_accession, length_bp FROM contigs WHERE release_version = ? AND assembly_accession = ? ORDER BY contig_accession LIMIT 1").bind(release.release_version, accession).first();
  const firstEndpoint = await env.BTED_DB.prepare("SELECT reference_name, biological_coordinate_1based FROM endpoints WHERE release_version = ? AND reference_assembly = ? AND source_id = ? ORDER BY biological_coordinate_1based, end_id LIMIT 1").bind(release.release_version, accession, publicTracks[0].source.source_id).first();
  const contigName = threeLayerPilot ? "NC_000964.3" : (firstEndpoint?.reference_name || contig?.contig_accession);
  const center = Number(firstEndpoint?.biological_coordinate_1based || 1);
  const length = Number(contig?.length_bp || center + 1000);
  const regionStart = threeLayerPilot ? 17999 : Math.max(0, center - 501);
  const regionEnd = threeLayerPilot ? 28000 : Math.min(length, center + 500);
  const tracksConfig = [];
  for (const { track, source, bed, sourceAssets } of publicTracks) {
    const rawAccessions = JSON.parse(track.raw_accessions_json || "[]");
    const metadata = {
      source_id: source.source_id,
      evidence_class: source.evidence_class,
      record_count: source.record_count,
      publication_title: track.paper_title,
      PubMed: track.pmid ? `https://pubmed.ncbi.nlm.nih.gov/${track.pmid}/` : null,
      DOI: track.doi ? `https://doi.org/${track.doi}` : null,
      raw_data_accessions: rawAccessions.map((item) => item.accession).join(", "),
      raw_data_links: rawAccessions.map((item) => item.external_url).filter(Boolean).join(" ; "),
      BTED_record: new URL(`/records/${encodeURIComponent(source.source_id)}.html`, request.url).href,
      BED_download: assetUrl(request, bed.asset_key),
      BED_asset_key: bed.asset_key,
      release_version: release.release_version,
    };
    for (const [strand, label] of [["forward", "+"], ["reverse", "-"]]) {
      const signal = sourceAssets.find((asset) => asset.asset_kind === "bigwig" && asset.logical_path.endsWith(`signal.${strand}.bw`) && Number(asset.is_public) === 1);
      if (!signal) continue;
      const signalId = `${track.track_id}_${strand}_signal`;
      tracksConfig.push({
        type: "QuantitativeTrack",
        trackId: signalId,
        name: `${source.source_id} · raw 3′-end signal (${label} strand)`,
        adapter: { type: "BigWigAdapter", bigWigLocation: { uri: assetUrl(request, signal.asset_key), locationType: "UriLocation" } },
        category: ["BTED experimental signal", source.source_id],
        assemblyNames: [assemblyName],
        metadata: { ...metadata, signal_values: "Raw repository values; not normalized by BTED", strand: label },
        displays: [{ type: "LinearWiggleDisplay", displayId: `${signalId}_display` }],
      });
    }
    tracksConfig.push({
      type: "FeatureTrack",
      trackId: track.track_id,
      name: `${source.source_id} · ${track.assay} endpoints`,
      adapter: { type: "BedAdapter", bedLocation: { uri: assetUrl(request, bed.asset_key), locationType: "UriLocation" } },
      category: ["BTED endpoint tracks", source.source_id],
      assemblyNames: [assemblyName],
      metadata,
      displays: [{ type: "LinearBasicDisplay", displayId: `${track.track_id}_display`, showLabels: false, height: 38 }],
    });
  }
  const configTracks = [];
  if (gff && tbi) {
    configTracks.push({
      type: "FeatureTrack",
      trackId: `${assemblyName}_genes`,
      name: "Reference gene annotation",
      adapter: { type: "Gff3TabixAdapter", gffGzLocation: { uri: assetUrl(request, gff.asset_key), locationType: "UriLocation" }, index: { location: { uri: assetUrl(request, tbi.asset_key), locationType: "UriLocation" }, indexType: "TBI" } },
      category: ["Reference annotation"],
      assemblyNames: [assemblyName],
      metadata: { release_version: release.release_version, gff3_sha256: gff.sha256, tbi_sha256: tbi.sha256 },
    });
  }
  configTracks.push(...tracksConfig);
  // The BATTER-TPE pilot is a static, source-scoped model track. It is kept
  // outside the endpoint catalogue so a prediction can never be mistaken for
  // an experimental endpoint. The BED and provenance JSON are shipped with
  // the site and are served from this same Worker origin.
  if (threeLayerPilot) {
    const pilotPath = "/data/pilots/BATTER_S1_003_batter_tpe_regional_pilot.bed";
    const provenancePath = "/data/pilots/BATTER_S1_003_batter_tpe_regional_pilot.provenance.json";
    const pilotTrackId = "bsub_batter_tpe_regional_pilot";
    configTracks.push({
      type: "FeatureTrack",
      trackId: pilotTrackId,
      name: "BATTER_S1_003 · BATTER-TPE prediction (compatibility pilot)",
      adapter: { type: "BedAdapter", bedLocation: { uri: new URL(pilotPath, request.url).href, locationType: "UriLocation" } },
      category: ["BTED model predictions", "BATTER_S1_003"],
      assemblyNames: [assemblyName],
      metadata: {
        source_id: "BATTER_S1_003",
        evidence_class: "model_prediction",
        experimental: false,
        prediction_scope: "regional pilot; NC_000964.3:18000-28000",
        model: "BATTER-TPE pretrained model · compatibility pilot",
        repository: "https://github.com/xu-research-lab/BATTER",
        commit: "9133d2d36b60c238a1e36760a296eff9f001fb72",
        provenance: new URL(provenancePath, request.url).href,
        warning: "Computational prediction; not an experimental endpoint and not an exact single-base call.",
      },
      displays: [{ type: "LinearBasicDisplay", displayId: `${pilotTrackId}_display`, showLabels: false, height: 42 }],
    });
  }
  const sessionTracks = configTracks.map((track, index) => ({
    id: `bted_track_${index + 1}`,
    type: track.type,
    configuration: track.trackId,
    minimized: false,
    displays: [{
      id: `bted_display_${index + 1}`,
      type: track.type === "QuantitativeTrack" ? "LinearWiggleDisplay" : "LinearBasicDisplay",
      configuration: track.displays?.[0]?.displayId || `${track.trackId}-LinearBasicDisplay`,
    }],
  }));
  return json({
    assemblies: [{ name: assemblyName, displayName: `${assembly.display_name || assembly.organism_name} (${accession})`, sequence: { type: "ReferenceSequenceTrack", trackId: `${assemblyName}_refseq`, adapter: { type: "IndexedFastaAdapter", fastaLocation: { uri: assetUrl(request, fasta.asset_key), locationType: "UriLocation" }, faiLocation: { uri: assetUrl(request, fai.asset_key), locationType: "UriLocation" } } } }],
    tracks: configTracks,
    defaultSession: { name: `${accession} BTED catalogue`, views: [{ id: "bted_linear_genome_view", type: "LinearGenomeView", offsetPx: 0, bpPerPx: 10.001, displayedRegions: [{ refName: contigName, start: regionStart, end: regionEnd, reversed: false, assemblyName }], tracks: sessionTracks }] },
    metadata: { release_version: release.release_version, assembly_accession: accession, source_ids: publicTracks.map(({ source }) => source.source_id), browser_asset_origin: release.asset_origin_status, three_layer_pilot: threeLayerPilot },
  });
}

async function proxyAsset(request, env, release, assetKey) {
  if (new URL(request.url).searchParams.has("url")) return json({ error: "arbitrary_origin_not_supported" }, 400);
  const asset = await publicAsset(env, release.release_version, assetKey);
  if (!asset) return json({ error: "unknown_or_private_asset", asset_key: assetKey }, 404);
  const range = request.headers.get("range");
  if (range && Number(asset.supports_range) !== 1) return json({ error: "range_not_supported" }, 416, { "content-range": `bytes */${asset.byte_size}` });
  const requestUrl = new URL(request.url);
  const logicalPath = asset.logical_path.split("/").map(encodeURIComponent).join("/");
  const localBase = String(env.LOCAL_ASSET_BASE || "").trim();
  let origin;
  if (isLoopbackHost(requestUrl.hostname) && localBase) {
    let localUrl;
    try {
      localUrl = new URL(localBase);
    } catch {
      return json({ error: "local_origin_not_allowed" }, 403);
    }
    if (
      localUrl.protocol !== "http:"
      || !isLoopbackHost(localUrl.hostname)
      || localUrl.username
      || localUrl.password
      || localUrl.search
      || localUrl.hash
    ) {
      return json({ error: "local_origin_not_allowed" }, 403);
    }
    const prefix = localUrl.pathname.replace(/\/$/, "");
    origin = new URL(`${localUrl.origin}${prefix}/${logicalPath}`);
  } else {
    const base = String(env.HF_RESOLVE_BASE || "").replace(/\/$/, "");
    if (!base) return json({ error: "origin_not_configured" }, 500);
    origin = new URL(`${base}/${logicalPath}`);
    if (origin.protocol !== "https:" || origin.hostname !== String(env.ALLOWED_ORIGIN_HOST || "")) {
      return json({ error: "origin_not_allowed" }, 403);
    }
  }
  const headersIn = new Headers();
  for (const header of ["range", "if-range", "if-none-match", "if-modified-since"]) {
    const value = request.headers.get(header);
    if (value) headersIn.set(header, value);
  }
  let upstream;
  try {
    upstream = await fetch(origin, { method: request.method, headers: headersIn, redirect: "follow" });
  } catch {
    // Keep an unavailable upstream from surfacing as an opaque Worker 500. In
    // local Wrangler this commonly means the sandbox cannot reach HF; the
    // registered asset and its provenance remain valid, but the proxy cannot
    // deliver bytes until the origin is reachable again.
    return json(
      { error: "asset_origin_unavailable", asset_key: asset.asset_key },
      502,
      { "cache-control": "no-store" },
    );
  }
  const headers = new Headers();
  for (const header of RESPONSE_HEADERS) {
    const value = upstream.headers.get(header);
    if (value) headers.set(header, value);
  }
  if (!headers.has("content-type")) headers.set("content-type", asset.content_type);
  if (!headers.has("content-length") && upstream.status === 200) headers.set("content-length", String(asset.byte_size));
  if (range && upstream.status === 206) {
    const contentRange = headers.get("content-range") || "";
    const match = contentRange.match(/^bytes (\d+)-(\d+)\/(\d+)$/);
    const length = Number(headers.get("content-length"));
    if (!match || Number(match[3]) !== Number(asset.byte_size) || !Number.isInteger(length) || length !== Number(match[2]) - Number(match[1]) + 1) {
      return json({ error: "upstream_range_mismatch" }, 502);
    }
  } else if (upstream.status === 200 && headers.has("content-length") && Number(headers.get("content-length")) !== Number(asset.byte_size)) {
    return json({ error: "upstream_length_mismatch" }, 502);
  }
  headers.set("accept-ranges", "bytes");
  headers.set("cache-control", "public, max-age=31536000, immutable");
  headers.set("etag", `"sha256:${asset.sha256}"`);
  headers.set("x-bted-asset-key", asset.asset_key);
  headers.set("x-bted-release-version", release.release_version);
  headers.set("x-bted-sha256", asset.sha256);
  return new Response(request.method === "HEAD" ? null : upstream.body, { status: upstream.status, headers });
}

async function staticAsset(request, env) {
  if (env.ASSETS && typeof env.ASSETS.fetch === "function") return env.ASSETS.fetch(request);
  return json({ error: "static_assets_not_configured" }, 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!["GET", "HEAD"].includes(request.method)) return json({ error: "method_not_allowed" }, 405, { allow: "GET, HEAD" });
    if (!url.pathname.startsWith("/api/")) return staticAsset(request, env);
    const selected = await withRelease(env, url);
    if (url.pathname === "/api/health") return selected ? json({ status: "ok", deployment: "cloudflare-worker-d1-preview", release: releasePayload(selected.release) }) : json({ status: "error", error: "release_not_loaded" }, 503);
    if (!selected) return json({ error: "release_not_found" }, 404);
    if (url.pathname === "/api/stats") return stats(env, selected.release);
    if (url.pathname === "/api/catalogue") return catalogue(env, selected.release, url);
    if (url.pathname === "/api/sources") return sourcesList(request, env, selected.release, url);
    if (url.pathname === "/api/assemblies") return assembliesList(env, selected.release, url);
    if (url.pathname === "/api/endpoints") return endpointsList(env, selected.release, url);
    if (url.pathname === "/api/augmentation") return augmentation(env, selected.release, url);
    const assetPrefix = url.pathname.startsWith("/api/assets/") ? "/api/assets/" : url.pathname.startsWith("/api/remote-data/") ? "/api/remote-data/" : null;
    if (assetPrefix) {
      const assetKey = decodePath(url.pathname.slice(assetPrefix.length));
      return assetKey ? proxyAsset(request, env, selected.release, assetKey) : json({ error: "invalid_asset_key" }, 400);
    }
    const assemblyMatch = url.pathname.match(/^\/api\/assemblies\/([^/]+)(?:\/jbrowse-config)?$/);
    if (assemblyMatch) {
      const accession = decodePath(assemblyMatch[1]);
      if (!accession) return json({ error: "invalid_assembly_accession" }, 400);
      if (url.pathname.endsWith("/jbrowse-config")) return jbrowseConfig(request, env, selected.release, accession, url.searchParams.get("source_id"));
      const payload = await assemblyPayload(request, env, selected.release, accession);
      return payload ? json(payload) : json({ error: "assembly_not_found", accession }, 404);
    }
    const sourceMatch = url.pathname.match(/^\/api\/sources\/([^/]+)$/);
    if (sourceMatch) {
      const sourceId = decodePath(sourceMatch[1]);
      const payload = sourceId ? await sourcePayload(request, env, selected.release, sourceId) : null;
      return payload ? json(payload) : json({ error: "source_not_found", source_id: sourceId }, 404);
    }
    const endpointMatch = url.pathname.match(/^\/api\/endpoints\/([^/]+)$/);
    if (endpointMatch) {
      const endId = decodePath(endpointMatch[1]);
      return endId ? endpointDetail(env, selected.release, endId) : json({ error: "invalid_endpoint_id" }, 400);
    }
    return json({ error: "not_found" }, 404);
  },
};
