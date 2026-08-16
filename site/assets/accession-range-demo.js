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

  const messages = {
    en: {
      pageTitle: "Search genome data · BTED",
      ready: "Enter an accession to begin.",
      loading: "Searching for {accession}…",
      found: "Found {studies} studies and {records} transcript 3′-end records.",
      error: "No data were found for this accession. Check the accession and try again.",
      sourceNote: "{sources} are shown as independent experimental tracks on this exact reference assembly.",
      details: "View source",
      publication: "Publication",
      rawData: "Raw data",
      authorEndpoint: "Author-called endpoint",
      curatedRecord: "Literature-curated record",
      auditOnly: "Metadata only",
      unknownYear: "—",
    },
    zh: {
      pageTitle: "检索基因组数据 · BTED",
      ready: "输入登录号开始检索。",
      loading: "正在检索 {accession}…",
      found: "已找到 {studies} 项研究和 {records} 条转录本 3′ 端记录。",
      error: "未找到该登录号对应的数据，请检查后重试。",
      sourceNote: "{sources} 在这一精确参考组装上作为相互独立的实验轨道展示。",
      details: "查看来源",
      publication: "文献",
      rawData: "原始数据",
      authorEndpoint: "作者定义的实验端点",
      curatedRecord: "文献整理记录",
      auditOnly: "仅元数据",
      unknownYear: "—",
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

  function renderStudies(tracks) {
    const body = root.querySelector("[data-edge-studies]");
    body.replaceChildren();
    tracks.forEach((track) => {
      const row = document.createElement("tr");

      const study = document.createElement("td");
      const title = document.createElement("strong");
      title.textContent = track.paper_title || track.name;
      const source = document.createElement("small");
      source.textContent = `${track.source_id} · ${track.publication_year || message("unknownYear")}`;
      study.append(title, source);

      const assay = document.createElement("td");
      assay.textContent = track.assay;

      const evidence = document.createElement("td");
      evidence.textContent = evidenceLabel(track.evidence_class);

      const count = document.createElement("td");
      count.className = "number";
      count.textContent = formatNumber(track.record_count);

      const links = document.createElement("td");
      links.className = "source-link-stack";
      if (track.publication_url) {
        const publication = document.createElement("a");
        publication.href = track.publication_url;
        publication.target = "_blank";
        publication.rel = "noopener";
        publication.textContent = `${message("publication")} · PMID ${track.pmid}`;
        links.appendChild(publication);
      }
      if (track.raw_data_url) {
        const rawData = document.createElement("a");
        rawData.href = track.raw_data_url;
        rawData.target = "_blank";
        rawData.rel = "noopener";
        rawData.textContent = `${message("rawData")} · ${track.raw_data_accession}`;
        links.appendChild(rawData);
      }
      const details = document.createElement("a");
      details.href = track.record_url || `records/${encodeURIComponent(track.source_id)}.html`;
      details.textContent = message("details");
      links.appendChild(details);

      row.append(study, assay, evidence, count, links);
      body.appendChild(row);
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
    setText("[data-edge-assembly]", payload.assembly.accession);
    setText("[data-edge-reference]", payload.assembly.reference_name);
    setText("[data-edge-tracks]", formatNumber(payload.tracks.length));
    setText("[data-edge-records]", formatNumber(payload.record_count));
    setText("[data-edge-organism]", payload.assembly.display_name);
    setText("[data-edge-summary-note]", message("sourceNote", {
      sources: payload.source_ids.join(currentLanguage === "zh" ? "、" : " and "),
    }));
    renderStudies(payload.tracks);
    renderInterpretations(payload.tracks);

    root.querySelector("[data-edge-jbrowse]").href =
      `jbrowse/index.html?config=${encodeURIComponent(payload.jbrowse_config_url)}`;
    root.querySelector("[data-edge-assembly-page]").href =
      `assemblies/${encodeURIComponent(payload.assembly.accession)}.html`;
    root.querySelector("[data-edge-bed]").href =
      `downloads/assemblies/${encodeURIComponent(payload.assembly.accession)}/endpoints.bed`;
    root.querySelector("[data-edge-metadata]").href =
      `downloads/assemblies/${encodeURIComponent(payload.assembly.accession)}/metadata.json`;
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
        studies: formatNumber(currentPayload.tracks.length),
        records: formatNumber(currentPayload.record_count),
      });
    } else {
      status.textContent = message("ready");
    }
  }

  async function resolveAccession(accession) {
    status.className = "edge-query-status loading";
    status.textContent = message("loading", { accession });
    results.hidden = true;
    try {
      const response = await fetch(`api/assemblies/${encodeURIComponent(accession)}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      const payload = await response.json();
      render(payload);
      status.className = "edge-query-status success";
      status.textContent = message("found", {
        studies: formatNumber(payload.tracks.length),
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
