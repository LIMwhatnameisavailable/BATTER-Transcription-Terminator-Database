(function () {
  "use strict";

  const root = document.querySelector("[data-browser-wrapper]");
  if (!root) return;

  const query = new URLSearchParams(window.location.search);
  const configValue = query.get("config");
  const sourceValue = query.get("source_id");
  const frame = root.querySelector("[data-browser-frame]");
  const select = root.querySelector("[data-browser-source]");
  const status = root.querySelector("[data-browser-status]");
  const sourceNote = root.querySelector("[data-browser-source-note]");
  let catalogue = null;
  let assembly = null;
  let baseConfig = null;
  let selectedSource = sourceValue || "";

  function text(selector, value) {
    const element = root.querySelector(selector);
    if (element) element.textContent = value || "—";
  }

  function showLink(selector, label, href) {
    const element = root.querySelector(selector);
    if (!element) return;
    element.hidden = !href;
    if (href) {
      element.href = href;
      element.textContent = label;
    }
  }

  function accessionParts(value) {
    return String(value || "").split(/[;,\s]+/).map((item) => item.trim()).filter(Boolean);
  }

  function accessionLink(accession, fallback) {
    if (/^GSE\d+$/.test(accession)) return `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=${encodeURIComponent(accession)}`;
    if (/^SR[APRX]\d+$/.test(accession)) return `https://www.ncbi.nlm.nih.gov/sra/?term=${encodeURIComponent(accession)}`;
    if (/^PRJNA\d+$/.test(accession)) return `https://www.ncbi.nlm.nih.gov/bioproject/${encodeURIComponent(accession)}`;
    if (/^PRJEB\d+$/.test(accession)) return `https://www.ebi.ac.uk/ena/browser/view/${encodeURIComponent(accession)}`;
    if (/^E-MTAB-\d+$/.test(accession)) return `https://www.ebi.ac.uk/biostudies/arrayexpress/studies/${encodeURIComponent(accession)}`;
    return fallback || "";
  }

  function resolveConfigUrl(value) {
    const config = new URL(value, window.location.href);
    // Worker Static Assets and the API share an origin in the deployed site. The
    // generated catalogue may still contain the preview hostname, so resolve only
    // BTED's known dynamic-config route against the page origin. External configs
    // remain untouched.
    if (/^\/api\/assemblies\/[^/]+\/jbrowse-config$/.test(config.pathname)) {
      return new URL(`${config.pathname}${config.search}`, window.location.origin);
    }
    return config;
  }

  function renderRawLinks(track) {
    const container = root.querySelector("[data-browser-raw]");
    container.replaceChildren();
    const tracks = Array.isArray(track) ? track : [track];
    const seen = new Set();
    tracks.flatMap((item) => accessionParts(item.raw_data_accession).map((accession) => ({
      accession,
      fallback: item.raw_data_url,
    }))).filter(({ accession }) => {
      if (seen.has(accession)) return false;
      seen.add(accession);
      return true;
    }).forEach(({ accession, fallback }, index) => {
      const link = document.createElement("a");
      link.target = "_blank";
      link.rel = "noopener";
      link.href = accessionLink(accession, index === 0 ? fallback : "");
      link.textContent = `Raw data · ${accession}`;
      if (link.href && link.href !== window.location.href) container.append(link);
    });
  }

  function renderStudyLinks(tracks) {
    const container = root.querySelector("[data-browser-studies]");
    container.replaceChildren();
    container.hidden = tracks.length < 2;
    if (container.hidden) return;
    tracks.forEach((track) => {
      const item = document.createElement("span");
      item.className = "browser-study-links-item";
      const label = document.createElement("strong");
      label.textContent = track.source_id;
      item.append(label);
      if (track.publication_url) {
        const pubmed = document.createElement("a");
        pubmed.href = track.publication_url;
        pubmed.target = "_blank";
        pubmed.rel = "noopener";
        pubmed.textContent = "PubMed";
        item.append(pubmed);
      }
      if (track.doi_url) {
        const doi = document.createElement("a");
        doi.href = track.doi_url;
        doi.target = "_blank";
        doi.rel = "noopener";
        doi.textContent = "DOI";
        item.append(doi);
      }
      if (track.record_url) {
        const record = document.createElement("a");
        record.href = track.record_url;
        record.textContent = "Dataset details";
        item.append(record);
      }
      container.append(item);
    });
  }

  function configFor(sourceId) {
    const config = new URL(baseConfig.href);
    if (sourceId) config.searchParams.set("source_id", sourceId);
    else config.searchParams.delete("source_id");
    return config;
  }

  function iframeUrl(config) {
    const params = new URLSearchParams();
    params.set("config", config.href);
    // Preserve JBrowse deep-link state while keeping wrapper-only parameters out.
    ["loc", "session", "tracks", "highlight", "assembly"].forEach((name) => {
      const value = query.get(name);
      if (value) params.set(name, value);
    });
    return `jbrowse/index.html?${params.toString()}`;
  }

  function updatePageUrl(sourceId) {
    const url = new URL(window.location.href);
    url.searchParams.set("config", configFor(sourceId).href);
    if (sourceId) url.searchParams.set("source_id", sourceId);
    else url.searchParams.delete("source_id");
    window.history.replaceState({}, "", url);
  }

  function renderTrack(track) {
    if (!track) return;
    selectedSource = track.source_id;
    select.value = selectedSource;
    text("[data-browser-study]", `${track.source_id} · ${track.publication_year} · ${track.assay}`);
    showLink("[data-browser-paper]", "Publication", track.publication_url);
    showLink("[data-browser-pubmed]", `PubMed ${track.pmid || ""}`.trim(), track.publication_url);
    showLink("[data-browser-doi]", track.doi ? `DOI ${track.doi}` : "DOI", track.doi_url);
    showLink("[data-browser-bed]", "Download BED", track.bed_url);
    showLink("[data-browser-record]", "Dataset details", track.record_url);
    renderStudyLinks([]);
    renderRawLinks(track);
    sourceNote.textContent = assembly.tracks.length > 1
      ? "Select a source to focus its track; sources sharing an assembly remain independent."
      : "This assembly has one published source track.";
  }

  function renderAllTracks() {
    selectedSource = "";
    select.value = "";
    text("[data-browser-study]", `${assembly.tracks.length} independent source tracks`);
    showLink("[data-browser-paper]", "Publication", "");
    showLink("[data-browser-pubmed]", "PubMed", "");
    showLink("[data-browser-doi]", "DOI", "");
    showLink("[data-browser-bed]", "Download BED", "");
    showLink("[data-browser-record]", "Dataset details", "");
    const tracks = assembly.tracks.filter((track) => track.track_status !== "metadata_only");
    renderStudyLinks(tracks);
    const raw = tracks.map((track) => ({
      raw_data_accession: track.raw_data_accession,
      raw_data_url: track.raw_data_url,
    }));
    const container = root.querySelector("[data-browser-raw]");
    container.replaceChildren();
    renderRawLinks(raw);
    sourceNote.textContent = "Sources sharing an assembly remain independent tracks and are not merged into a consensus.";
  }

  function loadFrame(sourceId) {
    const config = configFor(sourceId);
    frame.src = iframeUrl(config);
    updatePageUrl(sourceId);
    status.textContent = sourceId ? `Showing ${sourceId} in the browser.` : "Showing all independent source tracks.";
  }

  function renderAssembly() {
    const data = catalogue.assemblies[assembly.accession];
    if (!data) throw new Error(`Assembly ${assembly.accession} is not in the catalogue`);
    assembly = data;
    text("[data-browser-organism]", `${assembly.assembly.scientific_name}${assembly.assembly.strain ? ` · ${assembly.assembly.strain}` : ""}`);
    text("[data-browser-assembly]", assembly.assembly.accession);
    text("[data-browser-reference]", assembly.assembly.reference_name ? ` · ${assembly.assembly.reference_name}` : "");
    const ncbi = `https://www.ncbi.nlm.nih.gov/datasets/genome/${encodeURIComponent(assembly.assembly.accession)}/`;
    showLink("[data-browser-assembly-link]", assembly.assembly.accession, ncbi);
    showLink("[data-browser-genome]", "Genome details", assembly.assembly_page_url);
    select.replaceChildren();
    const all = document.createElement("option");
    all.value = "";
    all.textContent = "All source tracks";
    select.append(all);
    assembly.tracks.filter((track) => track.track_status !== "metadata_only").forEach((track) => {
      const option = document.createElement("option");
      option.value = track.source_id;
      option.textContent = `${track.source_id} · ${track.publication_year}`;
      select.append(option);
    });
    const available = assembly.tracks.filter((track) => track.track_status !== "metadata_only");
    const initial = available.find((track) => track.source_id === selectedSource);
    if (initial) renderTrack(initial);
    else if (available.length > 1) renderAllTracks();
    else if (available[0]) renderTrack(available[0]);
    loadFrame(selectedSource);
  }

  async function start() {
    if (!configValue) throw new Error("Missing config parameter");
    baseConfig = resolveConfigUrl(configValue);
    if (!selectedSource) selectedSource = baseConfig.searchParams.get("source_id") || "";
    const match = baseConfig.pathname.match(/\/assemblies\/([^/]+)\/jbrowse-config$/);
    const accession = match ? decodeURIComponent(match[1]) : null;
    if (!accession) throw new Error("Could not identify assembly from config");
    const response = await fetch("data/assemblies.json", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`Catalogue request failed: ${response.status}`);
    catalogue = await response.json();
    assembly = { accession };
    renderAssembly();
  }

  select.addEventListener("change", () => {
    const track = assembly.tracks.find((item) => item.source_id === select.value);
    if (track) renderTrack(track);
    else renderAllTracks();
    loadFrame(select.value);
  });

  start().catch((error) => {
    status.textContent = "The browser view could not be prepared. Open the genome details page to check the source.";
    console.error(error);
  });
})();
