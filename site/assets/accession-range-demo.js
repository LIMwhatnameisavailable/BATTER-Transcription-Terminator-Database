(function () {
  "use strict";

  const root = document.querySelector("[data-accession-demo]");
  if (!root) return;

  const form = root.querySelector("[data-accession-form]");
  const input = form.elements.accession;
  const status = root.querySelector("[data-edge-status]");
  const results = root.querySelector("[data-edge-results]");
  const languageButtons = Array.from(document.querySelectorAll("[data-language-choice]"));
  let currentPayload = null;
  let currentLanguage = "en";
  let assemblyCatalog = null;
  let assemblyCatalogPromise = null;

  const messages = {
    en: {
      pageTitle: "Search genome datasets · BTED",
      ready: "Enter an accession to begin.",
      loading: "Searching for {accession}…",
      found: "Found {sources} source datasets and {records} transcript 3′-end records.",
      error: "No data were found for this accession. Check the accession and try again.",
      assay: "Assay",
      evidence: "Evidence",
      accession: "Raw-data accession",
      records: "Records",
      publication: "Publication",
      rawData: "Raw sequencing",
      details: "Dataset record",
      authorEndpoint: "author-called endpoints",
      curatedRecord: "literature-curated records",
      auditOnly: "metadata records",
    },
    zh: {
      pageTitle: "检索基因组数据集 · BTED",
      ready: "输入登录号开始检索。",
      loading: "正在检索 {accession}…",
      found: "已找到 {sources} 个来源数据集和 {records} 条转录本 3′ 端记录。",
      error: "未找到该登录号对应的数据，请检查后重试。",
      assay: "实验方法",
      evidence: "证据类型",
      accession: "原始数据登录号",
      records: "记录数",
      publication: "论文",
      rawData: "原始测序",
      details: "数据集详情",
      authorEndpoint: "作者定义端点",
      curatedRecord: "文献整理记录",
      auditOnly: "仅元数据",
    },
  };

  function message(key, values = {}) {
    let output = messages[currentLanguage][key];
    Object.entries(values).forEach(([name, value]) => {
      output = output.replace(`{${name}}`, String(value));
    });
    return output;
  }

  function locale() {
    return currentLanguage === "zh" ? "zh-CN" : "en-US";
  }

  function formatNumber(value) {
    return Number(value).toLocaleString(locale());
  }

  function setText(selector, value) {
    root.querySelector(selector).textContent = value;
  }

  function evidenceLabel(value) {
    const labels = {
      author_called_endpoint: "authorEndpoint",
      curated_record: "curatedRecord",
      audit_only: "auditOnly",
    };
    return labels[value] ? message(labels[value]) : value.replaceAll("_", " ");
  }

  function trackStatusLabel(status) {
    const labels = {
      signal_endpoints: { en: "Signal + endpoints", zh: "信号 + 端点" },
      endpoints_only: { en: "Endpoints only", zh: "仅端点" },
      metadata_only: { en: "Metadata only", zh: "仅元数据" },
    };
    const label = labels[status] || { en: status, zh: status };
    return label[currentLanguage];
  }

  function addFact(list, label, value) {
    const item = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value || "—";
    item.append(term, description);
    list.appendChild(item);
  }

  function actionLink(label, href, external = false) {
    const link = document.createElement("a");
    link.className = "study-link";
    link.href = href;
    link.textContent = label;
    if (external) {
      link.target = "_blank";
      link.rel = "noopener";
    }
    return link;
  }

  function renderSourceCards(tracks) {
    const list = root.querySelector("[data-edge-study-cards]");
    list.replaceChildren();
    tracks.forEach((track) => {
      const card = document.createElement("article");
      card.className = "source-dataset-card";

      const header = document.createElement("header");
      const meta = document.createElement("div");
      meta.className = "source-card-meta";
      const identity = document.createElement("span");
      identity.textContent = `${track.source_id} · ${track.publication_year}`;
      meta.append(identity);
      const title = document.createElement("h3");
      title.textContent = track.paper_title || track.name;
      header.append(meta, title);

      if (track.track_status) {
        const badge = document.createElement("span");
        badge.className = `source-status-badge status-${track.track_status}`;
        badge.textContent = trackStatusLabel(track.track_status);
        header.append(badge);
      }

      const facts = document.createElement("dl");
      facts.className = "source-card-facts";
      addFact(facts, message("assay"), track.assay);
      addFact(facts, message("accession"), track.raw_data_accession);
      addFact(facts, message("evidence"), evidenceLabel(track.evidence_class));
      addFact(facts, message("records"), formatNumber(track.record_count));

      const footer = document.createElement("footer");
      footer.append(
        actionLink(`${message("publication")} · PMID ${track.pmid}`, track.publication_url, true),
        actionLink(`${message("rawData")} · ${track.raw_data_accession}`, track.raw_data_url, true),
        actionLink(message("details"), track.record_url || `records/${encodeURIComponent(track.source_id)}.html`),
      );

      card.append(header, facts, footer);
      list.appendChild(card);
    });
  }

  function renderInterpretations(tracks) {
    const list = root.querySelector("[data-edge-interpretations]");
    list.replaceChildren();
    tracks.forEach((track) => {
      const item = document.createElement("li");
      const source = document.createElement("strong");
      source.textContent = `${track.source_id}: `;
      const note = document.createElement("span");
      note.textContent = currentLanguage === "zh"
        ? (track.interpretation_note_zh || track.interpretation_note)
        : track.interpretation_note;
      item.append(source, note);
      list.appendChild(item);
    });
  }

  function render(payload) {
    currentPayload = payload;
    setText("[data-edge-scientific-name]", payload.assembly.scientific_name || payload.assembly.display_name);
    setText("[data-edge-strain]", payload.assembly.strain || "");
    setText("[data-edge-assembly]", payload.assembly.accession);
    setText("[data-edge-reference]", payload.assembly.reference_name);
    setText("[data-edge-tracks]", formatNumber(payload.tracks.length));
    setText("[data-edge-records]", formatNumber(payload.record_count));
    renderSourceCards(payload.tracks);
    renderInterpretations(payload.tracks);

    const jbrowseButton = root.querySelector("[data-edge-jbrowse]");
    if (payload.jbrowse_config_url) {
      jbrowseButton.href = `browser.html?config=${encodeURIComponent(payload.jbrowse_config_url)}`;
      jbrowseButton.classList.remove("disabled");
      jbrowseButton.removeAttribute("aria-disabled");
    } else {
      jbrowseButton.href = "#";
      jbrowseButton.classList.add("disabled");
      jbrowseButton.setAttribute("aria-disabled", "true");
    }
    root.querySelector("[data-edge-assembly-page]").href =
      `assemblies/${encodeURIComponent(payload.assembly.accession)}.html`;

    const bedButton = root.querySelector("[data-edge-bed]");
    if (payload.bed_url) {
      bedButton.href = payload.bed_url;
      bedButton.classList.remove("disabled");
      bedButton.removeAttribute("aria-disabled");
    } else {
      bedButton.href = "#";
      bedButton.classList.add("disabled");
      bedButton.setAttribute("aria-disabled", "true");
    }
    root.querySelector("[data-edge-metadata]").href = payload.metadata_url;
    results.hidden = false;
  }

  function applyLanguage(language, persist = true) {
    currentLanguage = language === "zh" ? "zh" : "en";
    document.documentElement.lang = currentLanguage === "zh" ? "zh-CN" : "en";
    document.title = message("pageTitle");
    document.querySelectorAll("[data-lang-en][data-lang-zh]").forEach((element) => {
      element.textContent = currentLanguage === "zh" ? element.dataset.langZh : element.dataset.langEn;
    });
    document.querySelectorAll("[data-placeholder-en][data-placeholder-zh]").forEach((element) => {
      element.placeholder = currentLanguage === "zh" ? element.dataset.placeholderZh : element.dataset.placeholderEn;
    });
    languageButtons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.languageChoice === currentLanguage));
    });
    if (persist) window.localStorage.setItem("bted-language", currentLanguage);
    if (currentPayload) {
      render(currentPayload);
      status.textContent = message("found", {
        sources: formatNumber(currentPayload.tracks.length),
        records: formatNumber(currentPayload.record_count),
      });
    } else {
      status.textContent = message("ready");
    }
  }

  async function loadAssemblyCatalog() {
    if (assemblyCatalog) return assemblyCatalog;
    if (assemblyCatalogPromise) return assemblyCatalogPromise;
    assemblyCatalogPromise = fetch("data/assemblies.json", { headers: { Accept: "application/json" } })
      .then((response) => {
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.json();
      })
      .then((catalog) => {
        assemblyCatalog = catalog.assemblies || {};
        return assemblyCatalog;
      });
    return assemblyCatalogPromise;
  }

  async function resolveAccession(accession) {
    status.className = "edge-query-status loading";
    status.textContent = message("loading", { accession });
    results.hidden = true;
    try {
      const catalog = await loadAssemblyCatalog();
      const payload = catalog[accession];
      if (!payload) throw new Error("Assembly not found in static catalog");
      render(payload);
      status.className = "edge-query-status success";
      status.textContent = message("found", {
        sources: formatNumber(payload.tracks.length),
        records: formatNumber(payload.record_count),
      });
      const url = new URL(window.location.href);
      url.searchParams.set("accession", accession);
      url.searchParams.set("lang", currentLanguage);
      window.history.replaceState({}, "", url);
    } catch (error) {
      currentPayload = null;
      status.className = "edge-query-status error";
      status.textContent = message("error");
      console.error(error);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const accession = input.value.trim();
    if (accession) resolveAccession(accession);
  });

  languageButtons.forEach((button) => {
    button.addEventListener("click", () => {
      applyLanguage(button.dataset.languageChoice);
      const url = new URL(window.location.href);
      url.searchParams.set("lang", currentLanguage);
      window.history.replaceState({}, "", url);
    });
  });

  const parameters = new URLSearchParams(window.location.search);
  const requestedLanguage = parameters.get("lang") || window.localStorage.getItem("bted-language") || "en";
  applyLanguage(requestedLanguage, false);
  input.value = parameters.get("accession") || root.dataset.defaultAccession;
  resolveAccession(input.value);
})();
