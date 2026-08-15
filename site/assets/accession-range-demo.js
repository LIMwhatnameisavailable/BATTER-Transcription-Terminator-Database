(function () {
  "use strict";

  const root = document.querySelector("[data-accession-demo]");
  if (!root) return;
  const form = root.querySelector("[data-accession-form]");
  const input = form.elements.accession;
  const status = root.querySelector("[data-edge-status]");
  const results = root.querySelector("[data-edge-results]");
  const rangeButton = root.querySelector("[data-edge-range-test]");
  const rangeResult = root.querySelector("[data-edge-range-result]");
  let currentPayload = null;

  function formatBytes(value) {
    const bytes = Number(value);
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MiB`;
  }

  function setText(selector, value) {
    root.querySelector(selector).textContent = value;
  }

  function renderAssets(assets) {
    const body = root.querySelector("[data-edge-assets]");
    body.replaceChildren();
    assets.forEach((asset) => {
      const row = document.createElement("tr");
      [
        asset.role.replaceAll("_", " "),
        asset.format,
        formatBytes(asset.byte_size),
        asset.object_path,
        "Range API",
      ].forEach((value, index) => {
        const cell = document.createElement("td");
        if (index === 3) {
          const code = document.createElement("code");
          code.textContent = value;
          cell.appendChild(code);
        } else {
          cell.textContent = value;
        }
        row.appendChild(cell);
      });
      body.appendChild(row);
    });
  }

  function render(payload) {
    currentPayload = payload;
    setText("[data-edge-assembly]", payload.assembly.accession);
    setText("[data-edge-reference]", payload.assembly.reference_name);
    setText("[data-edge-tracks]", String(payload.tracks.length));
    setText("[data-edge-records]", Number(payload.record_count).toLocaleString("en-US"));
    setText("[data-edge-organism]", payload.assembly.display_name);
    setText("[data-edge-sources]", payload.source_ids.join(" and "));
    setText("[data-edge-delivery]", payload.origin_backend.replaceAll("_", " "));
    renderAssets(payload.assets);
    const browser = root.querySelector("[data-edge-jbrowse]");
    browser.href = `jbrowse/index.html?config=${encodeURIComponent(payload.jbrowse_config_url)}`;
    results.hidden = false;
    rangeResult.textContent = `Deduplicated reference and annotation: ${formatBytes(payload.duplicate_reference_bytes_avoided)} avoided for this shared assembly.`;
  }

  async function resolveAccession(accession) {
    status.className = "edge-query-status loading";
    status.textContent = `Resolving ${accession}…`;
    results.hidden = true;
    try {
      const response = await fetch(`api/assemblies/${encodeURIComponent(accession)}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      const payload = await response.json();
      render(payload);
      status.className = "edge-query-status success";
      status.textContent = `${accession} resolved: ${payload.assets.length} objects and ${payload.tracks.length} independent experiment tracks.`;
      const url = new URL(window.location.href);
      url.searchParams.set("accession", accession);
      window.history.replaceState({}, "", url);
    } catch (error) {
      currentPayload = null;
      status.className = "edge-query-status error";
      status.textContent = "The accession API is not available on this server. Start the API-aware prototype on port 8016.";
      console.error(error);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const accession = input.value.trim();
    if (accession) resolveAccession(accession);
  });

  rangeButton.addEventListener("click", async () => {
    if (!currentPayload) return;
    const reference = currentPayload.assets.find((asset) => asset.role === "reference_sequence");
    rangeButton.disabled = true;
    rangeResult.className = "range-result loading";
    rangeResult.textContent = "Requesting bytes 0–127 from the reference object…";
    try {
      const response = await fetch(reference.range_url, { headers: { Range: "bytes=0-127" } });
      const bytes = await response.arrayBuffer();
      const contentRange = response.headers.get("Content-Range") || "missing Content-Range";
      if (response.status !== 206 || bytes.byteLength !== 128) {
        throw new Error(`expected 206/128 bytes; received ${response.status}/${bytes.byteLength}`);
      }
      rangeResult.className = "range-result success";
      rangeResult.textContent = `PASS · HTTP 206 · ${contentRange} · received ${bytes.byteLength.toLocaleString("en-US")} bytes instead of the full ${formatBytes(reference.byte_size)} FASTA.`;
    } catch (error) {
      rangeResult.className = "range-result error";
      rangeResult.textContent = `Range test failed: ${error.message}`;
    } finally {
      rangeButton.disabled = false;
    }
  });

  const requested = new URLSearchParams(window.location.search).get("accession");
  input.value = requested || root.dataset.defaultAccession;
  resolveAccession(input.value);
})();
