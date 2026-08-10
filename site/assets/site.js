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
    try {
      localStorage.setItem("bted-language", selected);
    } catch (_error) {
      // Language selection still works when storage is unavailable.
    }
  }

  let initialLanguage = "en";
  try {
    initialLanguage = localStorage.getItem("bted-language") || "en";
  } catch (_error) {
    initialLanguage = "en";
  }
  setLanguage(initialLanguage);
  languageButtons.forEach((button) => {
    button.addEventListener("click", () => setLanguage(button.dataset.langChoice));
  });

  const rows = Array.from(document.querySelectorAll("[data-source-row]"));
  if (!rows.length) return;

  const search = document.querySelector("[data-filter-search]");
  const selects = Array.from(document.querySelectorAll("[data-filter]"));
  const count = document.querySelector("[data-visible-count]");
  const empty = document.querySelector("[data-empty-state]");

  function applyFilters() {
    const query = (search && search.value ? search.value : "").trim().toLowerCase();
    const active = Object.fromEntries(selects.map((select) => [select.dataset.filter, select.value]));
    let visible = 0;
    rows.forEach((row) => {
      const matchesSearch = !query || row.dataset.search.includes(query);
      const matchesFilters = Object.entries(active).every(([key, value]) => !value || row.dataset[key] === value);
      const show = matchesSearch && matchesFilters;
      row.hidden = !show;
      if (show) visible += 1;
    });
    if (count) count.textContent = String(visible);
    if (empty) empty.hidden = visible !== 0;
  }

  if (search) search.addEventListener("input", applyFilters);
  selects.forEach((select) => select.addEventListener("change", applyFilters));
})();
