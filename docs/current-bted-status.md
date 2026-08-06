# Current BTED Status — Verified vs Reported

**Task:** 01 — Reconcile the remote repository with the current BTED state
**Branch:** `agent/reconcile-current-bted-state`
**Date:** 2026-08-07

This document separates two things that are easy to conflate: what this repository can prove today, and what has been reported about a newer BTED working state that lives outside this repository.

---

## 1. Verified current state of this repository

Every claim below is backed by a tracked repository document or by direct inspection of the git tree.

1. **Source corpus:** 13 original papers (BATTER Table S1, PMIDs 29606352, 30517198, 31555254, 31594819, 32694125, 33319794, 33947798, 34054774, 34874777, 35491820, 37402717, 37096044, 38030608) covering 20 species/strains and 22 data records per BATTER Table S1 (`report_BATTER_supplementary.md`).
2. **Classification:** all 13 papers were manually classified as class A — publisher supplementary files contain ready-to-use terminator/TTS/TEP coordinate tables (`PROGRESS.md`).
3. **Verification:** coordinate fields (Position/Strand/Start-End) and row counts were cross-checked against paper claims for all 13 sources; 13/13 passed (`data_verification_report.md`). The verified workbooks themselves are local-only (`.gitignore` excludes `*.xlsx`).
4. **Accessions:** verified GEO/SRA/ENA/ArrayExpress/Figshare/PRIDE/GenBank accessions are consolidated in `accession_list_verified.csv` and `report_zenodo_and_documents.md`.
5. **External model data:** the BATTER Zenodo repository (DOI: 10.5281/zenodo.16761763) contains model code, augmented training FASTA, and genome-wide **predictions** for 42,905 GEMs genomes — **not** the experimental coordinates of the 13 papers (`report_zenodo_and_documents.md`).
6. **Project stage:** per `README.md` and `PROGRESS.md`, the project has finished information checking and is **entering** standardization/database construction. No standardized coordinate dataset, database schema, or website exists in this repository.
7. **Repository hygiene issues (verified):** ~168 MB of read-starts text files and `__MACOSX/` junk are tracked under `文献13-PMID38030608/`; `README.md` references an `archive/` directory that does not exist in the repository; `文献13-PMID38030608/README.md` contains a typo "PMID: 38030638" (correct: 38030608).

---

## 2. Reported external BTED state — all `to verify`

The task description reports a newer BTED working state outside this repository. It was **not accessible** during this task, so none of the following has been confirmed against primary sources:

- a 22-source registry (`to verify`);
- per-source manifests (`to verify`);
- an evidence-layer SOP (`to verify`);
- standardized coordinate outputs (`to verify`);
- JBrowse resources (`to verify`);
- per-source processing records (`to verify`);
- a regression test suite (`to verify`).

Nothing in this section should be quoted as established fact. Until the working tree (or an export of it) is available for inspection, these items are candidate materials only — see `docs/remote-repository-migration-inventory.md`.

---

## 3. Open decisions

1. **Source count semantics.** This repository verifies 13 papers; BATTER Table S1 lists 22 records across 13 PMIDs; the external registry reportedly has 22 sources. Decide whether the registry unit is "paper", "record", or "species × condition dataset", and reconcile before any migration.
2. **Coordinate conventions.** 0-base vs 1-base, single-point vs interval, and reference-genome version alignment per source are unresolved (`README.md` lists these as next steps; the per-source READMEs flag them as "待人工确认事项").
3. **Evidence-layer definitions.** The external SOP's evidence classes are unknown. The mapping from Term-seq/Rend-seq/dRNA-seq-derived tables, computational predictions inside otherwise experimental papers (e.g. TransTermHP/ARNold/RhoTermPredict sheets noted in `data_verification_report.md`), and BATTER genome-wide predictions to evidence labels must be defined and reviewed before publication.
4. **Hosting of large processed assets.** Whether standardized outputs and JBrowse tracks fit GitHub/Pages limits or need external hosting (Zenodo or similar).
5. **Repository cleanup.** Whether to prune the tracked ~168 MB read-starts files and `__MACOSX/` from git history, and whether to restore or remove the `archive/` reference in `README.md`. Out of scope for Task 01.
6. **Language of public documentation.** Existing documents are Chinese; public-facing Pages content likely needs an English version or bilingual plan.
7. **Access to the external BTED working tree.** Required before any claim in Section 2 can be verified or migrated.

---

## 4. Acceptance gate for a later data migration

A data migration task may start only when **all** of the following hold:

1. **Source of truth identified:** every file to migrate has a named origin (external working tree path or public accession) and a named reviewer who has inspected it.
2. **Evidence labels reviewed:** every migrated record carries an evidence class from a written, reviewed SOP; prediction-only or mixed-evidence records are never labeled as experimentally validated endpoints.
3. **Coordinates pinned:** coordinate convention, reference-genome version, and strand encoding are documented per source, with the per-source "待人工确认事项" resolved.
4. **Publication eligibility confirmed:** licenses/redistribution terms checked; raw sequencing data and publisher workbooks are linked, not copied.
5. **No secrets or private data:** automated scan plus manual review for credentials, API keys, local absolute paths, and private comments.
6. **Size and format fit:** git/GitHub Pages limits respected; large assets have an external hosting decision (Decision 4).
7. **Regression checks pass:** any migrated test suite runs green, and `git diff --check` is clean.
8. **Reviewable scope:** the migration is split into small PRs (documentation, metadata, code, assets — separately), each stating what was intentionally excluded.

---

## 5. Not changed in this task

No data, coordinate, evidence class, source count, or validation claim was modified. This document records status and open decisions only.
