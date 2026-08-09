# Task 01 — Reconcile the remote repository with the current BTED state

## Branch and outcome

- **Branch:** `agent/reconcile-current-bted-state`
- **Target:** a draft pull request to `main`
- **Outcome:** a reviewable migration inventory and an accurate project-status document. This task does **not** migrate or delete scientific data.

## Background

The repository README describes an early project stage: 13 papers have been checked and the project is entering standardization/database construction. A newer BTED working state exists outside this repository with a 22-source registry, source manifests, evidence-layer SOP, standardized outputs, JBrowse resources, per-source processing records, and regression tests.

The purpose of this task is to map the two states before any large-scale import or website deployment. Treat the external working state as a source of candidate material, not as something to copy blindly.

## Read first

1. `README.md`
2. `docs/legacy/project-reports/PROGRESS.md`
3. `docs/legacy/project-reports/data_verification_report.md`
4. `docs/legacy/project-reports/report_BATTER_supplementary.md`
5. Every source-directory README relevant to a proposed migration

If access to the current BTED working tree is available, also read its SOP, source registry, processing records, and test suite before making claims about its contents.

## Required deliverables

Create these Markdown files only:

1. `docs/remote-repository-migration-inventory.md`
   - current remote inventory;
   - candidate materials to add, grouped as documentation, source metadata, code, processed/public assets, raw inputs, and temporary artifacts;
   - for each group: source of truth, expected size, publication suitability, and migration risk;
   - files that must not be copied to GitHub (credentials, private data, caches, temporary outputs, duplicate raw data).
2. `docs/current-bted-status.md`
   - clearly distinguish the remote repository's verified current state from the proposed/externally reported current BTED state;
   - list open decisions rather than asserting unverified completion;
   - define the acceptance gate for a later data migration.
3. `docs/github-pages-demo-plan.md`
   - static-site scope, page map, expected public assets, external raw-data links, GitHub Pages deployment approach, and validation plan;
   - state that GitHub Pages has no server-side database or private-data access.

## Non-negotiable rules

- Do not delete, rename, reformat, or relocate existing repository data in this task.
- Do not import raw sequencing files, private data, credentials, API keys, caches, or generated temporary files.
- Do not change genomic coordinates, evidence classes, source counts, or claims of scientific validation.
- Do not describe prediction-only or mixed-evidence records as experimentally validated endpoints.
- Link every scientific statement to an existing repository document or a primary source; mark unverified external claims as `to verify`.

## Validation and handoff

Run:

```bash
git diff --check
git status --short
```

The draft PR must include:

- changed-file list;
- explicit statement that only task documents were added;
- items intentionally excluded from migration;
- a proposed, bounded Task 02 scope.

## Done when

Reviewers can decide exactly what to migrate next, what not to migrate, and how a public static demo will avoid misrepresenting scientific evidence.
