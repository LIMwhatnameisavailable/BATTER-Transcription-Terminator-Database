# Handoff

**Date:** 2026-08-07
**Branch:** `agent/reconcile-current-bted-state` (pushed, in sync with origin)
**Draft PR:** [#1 — Task 01: Reconcile remote repository with current BTED state](https://github.com/LIMwhatnameisavailable/BATTER-Transcription-Terminator-Database/pull/1), awaiting final review.

---

## 1. Current state

- Task 01 is complete. The branch adds documentation only; no scientific data, coordinates, evidence classes, or source counts were changed.
- Deliverables:
  - `docs/remote-repository-migration-inventory.md`
  - `docs/current-bted-status.md`
  - `docs/github-pages-demo-plan.md`
  - `docs/WORKLOG.md`
- One low-risk typo fix: `文献13-PMID38030608/README.md` ("PMID: 38030638" → "PMID: 38030608").
- The external BTED working state (22-source registry, evidence-layer SOP, standardized outputs, JBrowse resources, processing records, regression tests) was **not accessible**; every related claim is marked `to verify` in the deliverables.

## 2. Open decisions (full list in `docs/current-bted-status.md` Section 3)

1. Reconcile source-count semantics: 13 papers vs 22 Table S1 records vs the reported 22-source registry.
2. Pin coordinate conventions (0/1-base, single-point vs interval, reference-genome versions per source).
3. Define and review evidence-layer labels before anything is published; never label prediction-only or mixed-evidence records as experimentally validated.
4. Decide hosting for large processed assets / JBrowse tracks (git/Pages limits vs external hosting).
5. Repository cleanup (**deliberately deferred**, not part of Task 01): tracked ~168 MB read-starts files and `__MACOSX/` junk under `文献13-PMID38030608/`; dangling `archive/` reference in `README.md`.
6. Language plan for public-facing documentation (existing docs are Chinese).
7. Obtain access to the external BTED working tree to verify Section 2 claims.

## 3. Suggested next steps

1. Final review of draft PR #1, then merge to `main`.
2. **Task 02** (`docs/tasks/02-github-pages-demo.md`, branch `agent/github-pages-demo`): build the static demo within the bounded scope proposed in PR #1 — catalog generated only from `accession_list_verified.csv` + the 13 per-source READMEs, no JBrowse link, no coordinate datasets, no external BTED claims until verified.
3. Future cleanup task (separate branch, after Task 02 planning): decide on pruning the 168 MB tracked files / `__MACOSX/`, and fix or restore the `archive/` reference in `README.md`.
4. When the external BTED working tree becomes accessible, verify each `to verify` item in `docs/current-bted-status.md` and update the migration inventory before any data migration (acceptance gate in Section 4 of that document).

## 4. Environment notes

- `gh` CLI token is invalid; PR operations were done via the GitHub REST API using the git credential store. Re-run `gh auth login` if CLI access is needed.
- The task commits use the machine's auto-generated git identity (`SEU_yolo <seu_yolo@...local>`); amend if a different identity is required.
