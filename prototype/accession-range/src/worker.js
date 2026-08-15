const RESPONSE_HEADERS = [
  "accept-ranges",
  "cache-control",
  "content-length",
  "content-range",
  "content-type",
  "etag",
  "last-modified",
];

function json(payload, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...extraHeaders },
  });
}

function objectUrl(request, assetKey) {
  return new URL(`/api/remote-data/${encodeURIComponent(assetKey)}`, request.url).href;
}

async function findAssembly(env, accession) {
  return env.BTED_DB.prepare(
    "SELECT accession, display_name, reference_name, reference_length, release_version, status FROM assemblies WHERE accession = ?",
  ).bind(accession).first();
}

async function findAssets(env, accession) {
  const result = await env.BTED_DB.prepare(
    "SELECT asset_key, role, format, object_path, content_type, byte_size, sha256 FROM assets WHERE assembly_accession = ? AND active = 1 ORDER BY role, asset_key",
  ).bind(accession).all();
  return result.results || [];
}

async function findTracks(env, accession) {
  const result = await env.BTED_DB.prepare(
    "SELECT track_id, source_id, publication_year, pmid, record_url, name, assay, evidence_class, record_count, asset_key, display_order FROM tracks WHERE assembly_accession = ? ORDER BY display_order",
  ).bind(accession).all();
  return result.results || [];
}

async function assemblyPayload(request, env, accession) {
  const assembly = await findAssembly(env, accession);
  if (!assembly) return null;
  const [assets, tracks] = await Promise.all([
    findAssets(env, accession),
    findTracks(env, accession),
  ]);
  return {
    schema_version: "0.1",
    delivery_mode: "d1_lookup_same_origin_range_proxy",
    assembly,
    record_count: tracks.reduce((sum, track) => sum + Number(track.record_count), 0),
    source_ids: [...new Set(tracks.map((track) => track.source_id))],
    assets: assets.map((asset) => ({
      ...asset,
      range_url: objectUrl(request, asset.asset_key),
    })),
    tracks: tracks.map((track) => ({
      ...track,
      range_url: objectUrl(request, track.asset_key),
    })),
    jbrowse_config_url: new URL(
      `/api/assemblies/${encodeURIComponent(accession)}/jbrowse-config`,
      request.url,
    ).href,
  };
}

function jbrowseConfig(request, payload) {
  const byRole = Object.fromEntries(payload.assets.map((asset) => [asset.role, asset]));
  const assemblyName = `BTED_EDGE_${payload.assembly.accession.replaceAll(".", "_")}`;
  const geneTrackId = `${assemblyName}_genes`;
  const trackConfigs = payload.tracks.map((track) => ({
    type: "FeatureTrack",
    trackId: track.track_id,
    name: `${track.source_id} · ${track.name}`,
    adapter: {
      type: "BedAdapter",
      bedLocation: { uri: objectUrl(request, track.asset_key), locationType: "UriLocation" },
    },
    category: ["BTED source tracks", track.source_id],
    assemblyNames: [assemblyName],
    metadata: {
      source_id: track.source_id,
      assay: track.assay,
      evidence_class: track.evidence_class,
      record_count: track.record_count,
      delivery: "same-origin Range proxy",
    },
    displays: [{
      type: "LinearBasicDisplay",
      displayId: `${track.track_id}_display`,
      showLabels: false,
      height: 38,
    }],
  }));
  return {
    assemblies: [{
      name: assemblyName,
      displayName: `${payload.assembly.display_name} (${payload.assembly.accession}) · edge prototype`,
      sequence: {
        type: "ReferenceSequenceTrack",
        trackId: `${assemblyName}_refseq`,
        adapter: {
          type: "IndexedFastaAdapter",
          fastaLocation: {
            uri: objectUrl(request, byRole.reference_sequence.asset_key),
            locationType: "UriLocation",
          },
          faiLocation: {
            uri: objectUrl(request, byRole.reference_index.asset_key),
            locationType: "UriLocation",
          },
        },
      },
    }],
    configuration: {},
    connections: [],
    tracks: [{
      type: "FeatureTrack",
      trackId: geneTrackId,
      name: "NCBI gene annotation · one shared assembly object",
      adapter: {
        type: "Gff3TabixAdapter",
        gffGzLocation: {
          uri: objectUrl(request, byRole.gene_annotation.asset_key),
          locationType: "UriLocation",
        },
        index: {
          location: {
            uri: objectUrl(request, byRole.gene_annotation_index.asset_key),
            locationType: "UriLocation",
          },
          indexType: "TBI",
        },
      },
      category: ["Reference annotation"],
      assemblyNames: [assemblyName],
      metadata: { delivery: "same-origin Range proxy" },
    }, ...trackConfigs],
    defaultSession: {
      name: `${payload.assembly.accession} · accession-driven remote tracks`,
      views: [{
        id: "bted_edge_linear_genome_view",
        type: "LinearGenomeView",
        offsetPx: 0,
        bpPerPx: 10.001,
        displayedRegions: [{
          refName: payload.assembly.reference_name,
          start: 62367,
          end: 72368,
          reversed: false,
          assemblyName,
        }],
        tracks: [geneTrackId, ...payload.tracks.map((track) => track.track_id)].map((trackId, index) => ({
          id: `bted_edge_track_${index + 1}`,
          type: "FeatureTrack",
          configuration: trackId,
          minimized: false,
          displays: [{
            id: `bted_edge_display_${index + 1}`,
            type: "LinearBasicDisplay",
            configuration: index === 0 ? `${trackId}-LinearBasicDisplay` : `${trackId}_display`,
          }],
        })),
      }],
    },
  };
}

async function proxyAsset(request, env, assetKey) {
  const asset = await env.BTED_DB.prepare(
    "SELECT asset_key, object_path, origin_url, content_type, sha256 FROM assets WHERE asset_key = ? AND active = 1",
  ).bind(assetKey).first();
  if (!asset) return json({ error: "unknown_asset", asset_key: assetKey }, 404);

  const base = String(env.HF_RESOLVE_BASE || "").replace(/\/$/, "");
  const origin = asset.origin_url || `${base}/${asset.object_path.split("/").map(encodeURIComponent).join("/")}`;
  let originUrl;
  try {
    originUrl = new URL(origin);
  } catch {
    return json({ error: "invalid_origin_configuration" }, 500);
  }
  if (originUrl.hostname !== env.ALLOWED_ORIGIN_HOST) {
    return json({ error: "origin_not_allowed" }, 403);
  }

  const upstreamHeaders = new Headers();
  for (const header of ["range", "if-range", "if-none-match", "if-modified-since"]) {
    const value = request.headers.get(header);
    if (value) upstreamHeaders.set(header, value);
  }
  const upstream = await fetch(originUrl, {
    method: request.method,
    headers: upstreamHeaders,
    redirect: "follow",
  });
  const headers = new Headers();
  for (const header of RESPONSE_HEADERS) {
    const value = upstream.headers.get(header);
    if (value) headers.set(header, value);
  }
  if (!headers.has("content-type")) headers.set("content-type", asset.content_type);
  headers.set("x-bted-asset-key", asset.asset_key);
  headers.set("x-bted-sha256", asset.sha256);
  return new Response(request.method === "HEAD" ? null : upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers,
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!new Set(["GET", "HEAD"]).has(request.method)) {
      return json({ error: "method_not_allowed" }, 405, { allow: "GET, HEAD" });
    }
    if (url.pathname === "/api/health") {
      return json({ status: "ok", backend: "Cloudflare D1 + Hugging Face Range proxy" });
    }
    if (url.pathname.startsWith("/api/remote-data/")) {
      const assetKey = decodeURIComponent(url.pathname.slice("/api/remote-data/".length));
      return proxyAsset(request, env, assetKey);
    }
    const match = url.pathname.match(/^\/api\/assemblies\/([^/]+)(\/jbrowse-config)?$/);
    if (match) {
      const accession = decodeURIComponent(match[1]);
      const payload = await assemblyPayload(request, env, accession);
      if (!payload) return json({ error: "assembly_not_found", accession }, 404);
      return json(match[2] ? jbrowseConfig(request, payload) : payload, 200, {
        "cache-control": "public, max-age=300",
      });
    }
    return json({ error: "not_found" }, 404);
  },
};
