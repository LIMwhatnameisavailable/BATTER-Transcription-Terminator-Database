(function () {
  "use strict";

  const body = document.body;
  const languageButtons = document.querySelectorAll("[data-lang-choice]");

  function setLanguage(language) {
    const selected = language === "zh" ? "zh" : "en";
    body.dataset.lang = selected;
    document.documentElement.lang = selected === "zh" ? "zh-CN" : "en";
    languageButtons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.langChoice === selected));
    });
    try { localStorage.setItem("bted-language", selected); } catch (_error) { /* optional */ }
  }

  let initialLanguage = "en";
  try { initialLanguage = localStorage.getItem("bted-language") || "en"; } catch (_error) { /* optional */ }
  setLanguage(initialLanguage);
  languageButtons.forEach((button) => button.addEventListener("click", () => setLanguage(button.dataset.langChoice)));

  const rows = Array.from(document.querySelectorAll("[data-catalog-row]"));
  if (rows.length) {
    const search = document.querySelector("[data-filter-search]");
    const selects = Array.from(document.querySelectorAll("[data-filter]"));
    const count = document.querySelector("[data-visible-count]");
    const empty = document.querySelector("[data-empty-state]");
    const applyFilters = function () {
      const query = (search && search.value ? search.value : "").trim().toLowerCase();
      const active = Object.fromEntries(selects.map((select) => [select.dataset.filter, select.value]));
      let visible = 0;
      rows.forEach((row) => {
        const matchesSearch = !query || row.dataset.search.includes(query);
        const matchesFilters = Object.entries(active).every(([key, value]) => {
          if (!value) return true;
          return (row.dataset[key] || "").split("|").includes(value);
        });
        const show = matchesSearch && matchesFilters;
        row.hidden = !show;
        if (show) visible += 1;
      });
      if (count) count.textContent = String(visible);
      if (empty) empty.hidden = visible !== 0;
    };
    if (search) search.addEventListener("input", applyFilters);
    selects.forEach((select) => select.addEventListener("change", applyFilters));
  }

  const choices = Array.from(document.querySelectorAll("[data-download-choice]"));
  if (!choices.length) return;

  const selectedCount = document.querySelector("[data-selected-count]");
  const selectedRecords = document.querySelector("[data-selected-records]");
  const status = document.querySelector("[data-download-status]");
  const downloadButton = document.querySelector("[data-download-selected]");

  function updateSelection() {
    const checked = choices.filter((choice) => choice.checked);
    selectedCount.textContent = String(checked.length);
    selectedRecords.textContent = checked.reduce((sum, choice) => sum + Number(choice.dataset.records || 0), 0).toLocaleString("en-US");
    downloadButton.disabled = checked.length === 0;
  }

  document.querySelector("[data-select-all]").addEventListener("click", () => {
    choices.forEach((choice) => { choice.checked = true; });
    updateSelection();
  });
  document.querySelector("[data-clear-all]").addEventListener("click", () => {
    choices.forEach((choice) => { choice.checked = false; });
    updateSelection();
  });
  choices.forEach((choice) => choice.addEventListener("change", updateSelection));

  const crcTable = Array.from({ length: 256 }, (_, index) => {
    let value = index;
    for (let bit = 0; bit < 8; bit += 1) value = (value & 1) ? (0xedb88320 ^ (value >>> 1)) : (value >>> 1);
    return value >>> 0;
  });

  function crc32(bytes) {
    let crc = 0xffffffff;
    bytes.forEach((byte) => { crc = crcTable[(crc ^ byte) & 0xff] ^ (crc >>> 8); });
    return (crc ^ 0xffffffff) >>> 0;
  }

  function put16(view, offset, value) { view.setUint16(offset, value, true); }
  function put32(view, offset, value) { view.setUint32(offset, value >>> 0, true); }

  function createZip(files) {
    const encoder = new TextEncoder();
    const localParts = [];
    const centralParts = [];
    let localOffset = 0;

    files.forEach((file) => {
      const name = encoder.encode(file.name);
      const data = file.data;
      const checksum = crc32(data);
      const local = new Uint8Array(30 + name.length);
      const localView = new DataView(local.buffer);
      put32(localView, 0, 0x04034b50); put16(localView, 4, 20); put16(localView, 6, 0x0800);
      put16(localView, 8, 0); put16(localView, 10, 0); put16(localView, 12, 0);
      put32(localView, 14, checksum); put32(localView, 18, data.length); put32(localView, 22, data.length);
      put16(localView, 26, name.length); put16(localView, 28, 0); local.set(name, 30);
      localParts.push(local, data);

      const central = new Uint8Array(46 + name.length);
      const centralView = new DataView(central.buffer);
      put32(centralView, 0, 0x02014b50); put16(centralView, 4, 20); put16(centralView, 6, 20);
      put16(centralView, 8, 0x0800); put16(centralView, 10, 0); put16(centralView, 12, 0); put16(centralView, 14, 0);
      put32(centralView, 16, checksum); put32(centralView, 20, data.length); put32(centralView, 24, data.length);
      put16(centralView, 28, name.length); put16(centralView, 30, 0); put16(centralView, 32, 0);
      put16(centralView, 34, 0); put16(centralView, 36, 0); put32(centralView, 38, 0); put32(centralView, 42, localOffset);
      central.set(name, 46); centralParts.push(central);
      localOffset += local.length + data.length;
    });

    const centralSize = centralParts.reduce((sum, part) => sum + part.length, 0);
    const end = new Uint8Array(22);
    const endView = new DataView(end.buffer);
    put32(endView, 0, 0x06054b50); put16(endView, 4, 0); put16(endView, 6, 0);
    put16(endView, 8, files.length); put16(endView, 10, files.length);
    put32(endView, 12, centralSize); put32(endView, 16, localOffset); put16(endView, 20, 0);
    return new Blob([...localParts, ...centralParts, end], { type: "application/zip" });
  }

  async function fetchFile(url, archiveName, required) {
    const response = await fetch(url);
    if (!response.ok) {
      if (required) throw new Error(`${response.status} ${url}`);
      return null;
    }
    return { name: archiveName, data: new Uint8Array(await response.arrayBuffer()) };
  }

  downloadButton.addEventListener("click", async () => {
    const selected = choices.filter((choice) => choice.checked).map((choice) => choice.value);
    if (!selected.length) return;
    downloadButton.disabled = true;
    status.textContent = body.dataset.lang === "zh" ? "正在准备下载…" : "Preparing download…";
    try {
      const files = [];
      for (const assembly of selected) {
        const base = `downloads/assemblies/${encodeURIComponent(assembly)}`;
        const metadata = await fetchFile(`${base}/metadata.json`, `${assembly}/metadata.json`, true);
        const bed = await fetchFile(`${base}/endpoints.bed`, `${assembly}/endpoints.bed`, false);
        files.push(metadata);
        if (bed) files.push(bed);
      }
      const blob = createZip(files);
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `BTED-v0.2.0-${selected.length}-assemblies.zip`;
      document.body.appendChild(link); link.click(); link.remove();
      URL.revokeObjectURL(link.href);
      status.textContent = body.dataset.lang === "zh" ? `已打包 ${selected.length} 个基因组。` : `Packaged ${selected.length} genome assemblies.`;
    } catch (error) {
      status.textContent = body.dataset.lang === "zh" ? "下载准备失败，请刷新页面后重试。" : "Download preparation failed. Refresh and try again.";
      console.error(error);
    } finally {
      downloadButton.disabled = false;
      updateSelection();
    }
  });

  updateSelection();
})();
