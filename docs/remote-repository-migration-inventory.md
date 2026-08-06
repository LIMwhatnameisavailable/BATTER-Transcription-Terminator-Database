# Remote Repository Migration Inventory

**Task:** 01 — Reconcile the remote repository with the current BTED state
**Branch:** `agent/reconcile-current-bted-state`
**Date:** 2026-08-07
**Scope:** inventory and gap mapping only. No data was migrated, deleted, renamed, or reformatted in this task.

---

## 1. Current remote inventory (verified in this repository)

Verified by `git ls-files` on branch `agent/reconcile-current-bted-state` (commit `6d596a1`).

### 1.1 Project-level documentation (Chinese)

| File | Content | Source of truth for |
|------|---------|---------------------|
| `README.md` | Project background, Phase 1 completion summary, 13-source core-data table, next-step plan | Project stage statement |
| `PROGRESS.md` | Work log 2026-07-28/29: MOESM1–3 review, Zenodo investigation, A/B/C classification (13/13 class A), batch download, cross-check | Process history |
| `data_verification_report.md` | Per-source cross-check of README claims vs downloaded files; coordinate fields and row counts verified 13/13 | Coordinate-data verification claims |
| `report_BATTER_supplementary.md` | BATTER paper MOESM1–3 review; Table S1 (20 species/strains, 22 records, 13 PMIDs) is the source list | BATTER supplementary content |
| `report_zenodo_and_documents.md` | Zenodo repo (DOI: 10.5281/zenodo.16761763) contents; conclusion: Zenodo holds model code/training data/predictions, not the 13 papers' experimental coordinates | External raw-data links |
| `accession_list_verified.csv` | Verified GEO/SRA/ENA/ArrayExpress/Figshare/PRIDE/GenBank accessions for the 13 PMIDs | Accession metadata |

### 1.2 Per-source directories (`文献N-PMIDxxxxxxxx/`, N = 1–13)

- Each contains a `README.md` with the source verification report: citation, A/B/C classification (all A), confirmed accessions, coordinate-data pointers, third-party platform judgment, open confirmation items.
- `文献13-PMID38030608/` additionally contains:
  - `supplementary_data_1to5_findings.md` (MOESM4–8 structure review);
  - 6 `*_read_starts.txt` files, **~168 MB total, ~6.31 M lines, tracked in git** (raw read-start counts from MOESM10 source data);
  - `__MACOSX/` AppleDouble files (`._*`), **tracked in git** — macOS archive junk that should not be in the repository (flagged for a future cleanup decision; not removed in this task).

### 1.3 Task plans

- `docs/tasks/README.md`, `docs/tasks/01-reconcile-current-bted-state.md`, `docs/tasks/02-github-pages-demo.md`.

### 1.4 What is intentionally NOT in the repository

- `.gitignore` excludes `*.xlsx`, `*.pdf`, `*.zip`. The core coordinate workbooks described in `data_verification_report.md` (e.g. `mmc3.xlsx`, `ppat.1007461.s006.xlsx`, MOESM5/6) exist only in the local working copy, not in git.
- `README.md` references an `archive/` directory (historical reports); it is **not present** in the repository. Its only mentioned content (`supplementary_data1_raw_findings.md`) is superseded per `PROGRESS.md`.
- `.git` is ~31 MB, dominated by the tracked `文献13` read-starts text files.

---

## 2. Candidate materials to add

The current BTED working state exists **outside** this repository and was **not accessible** during this task. All statements about its contents are reported from the task description and are marked `to verify`. Nothing below is migrated by this task.

### 2.1 Documentation

| Candidate | Source of truth | Expected size | Publication suitability | Migration risk |
|-----------|----------------|---------------|------------------------|----------------|
| Evidence-layer SOP | External BTED working tree (`to verify`) | KB–MB | Suitable after review | Low technical risk; **high wording risk**: must not re-label prediction-only or mixed-evidence records as experimentally validated |
| Per-source processing records | External BTED working tree (`to verify`) | KB–MB | Suitable after review | May contain local absolute paths, machine-specific environment notes, or private comments — needs scrubbing |

### 2.2 Source metadata

| Candidate | Source of truth | Expected size | Publication suitability | Migration risk |
|-----------|----------------|---------------|------------------------|----------------|
| 22-source registry | External BTED working tree (`to verify`) | KB | Suitable after review | **Count mismatch must be explained**: this repository verifies 13 sources; the external registry reportedly covers 22 records (consistent with BATTER Table S1's 22 records / 13 PMIDs, `to verify`). The 9 extra records' provenance and evidence class are unverified |
| Source manifests (per-source file lists, checksums, versions) | External BTED working tree (`to verify`) | KB–MB | Suitable after review | Checksums and reference-genome versions must match primary sources; risk of propagating unverified coordinate claims |

### 2.3 Code

| Candidate | Source of truth | Expected size | Publication suitability | Migration risk |
|-----------|----------------|---------------|------------------------|----------------|
| Standardization/conversion pipeline scripts | External BTED working tree (`to verify`) | KB–MB | Suitable after review | Must be checked for hard-coded credentials, API keys, local absolute paths |
| Regression tests | External BTED working tree (`to verify`) | KB–MB | Suitable after review | Test fixtures may embed raw data or unverified expected values; fixture provenance must be documented |

### 2.4 Processed / public assets

| Candidate | Source of truth | Expected size | Publication suitability | Migration risk |
|-----------|----------------|---------------|------------------------|----------------|
| Standardized coordinate outputs (BED/GFF or equivalent) | External BTED working tree (`to verify`) | MB–tens of MB | Potentially suitable | **Highest scientific risk**: coordinate convention (0/1-base), reference-genome version alignment, and evidence-class labels are all unverified. Must pass the acceptance gate in `docs/current-bted-status.md` before any import |
| JBrowse resources (configs, track files) | External BTED working tree (`to verify`) | MB–hundreds of MB | Partially suitable (GitHub Pages size limits) | Large track files may exceed practical Pages/git limits; may need external hosting or down-sampling |

### 2.5 Raw inputs

| Candidate | Source of truth | Expected size | Publication suitability | Migration risk |
|-----------|----------------|---------------|------------------------|----------------|
| Publisher supplementary workbooks (`*.xlsx`) for the 13 sources | Publishers / local working copy (this repo's `.gitignore` already excludes them) | KB–MB each | **Do not copy into git**; redistribute by citing the DOI/accession | Publisher redistribution terms; duplication of primary sources |
| Raw sequencing reads (FASTQ) | GEO/SRA/ENA/ArrayExpress (see `accession_list_verified.csv`) | GB–TB | **Never copy**; link only | Size; duplication; no added value |
| BATTER Zenodo artifacts (`TES.bed.gz` 1.19 GB, `terminators.flanked.fa.gz` 487 MB) | Zenodo DOI: 10.5281/zenodo.16761763 (see `report_zenodo_and_documents.md`) | GB | **Never copy**; link only | Prediction-only data — must never be presented as experimental evidence |

### 2.6 Temporary artifacts

| Candidate | Source of truth | Expected size | Publication suitability | Migration risk |
|-----------|----------------|---------------|------------------------|----------------|
| Caches, intermediate conversion outputs, logs | External BTED working tree / local (`to verify`) | varies | Not suitable | Regenerable; no archival value |
| `__MACOSX/` AppleDouble files | This repository (`文献13-PMID38030608/__MACOSX/`, tracked) | KB | Not suitable | Already committed; removal is a separate decision, out of scope for Task 01 |

---

## 3. Files that must not be copied to GitHub

- Credentials, API keys, tokens, `.env` files, SSH keys, or any config containing secrets.
- Private or unpublished data; personal data; local user paths embedded in documents or code.
- Raw sequencing files (FASTQ/FASTQ.gz) and any multi-GB raw archive.
- Duplicate raw data already hosted under a public DOI/accession (Zenodo, GEO, SRA, ENA, ArrayExpress, Figshare, PRIDE) — link, never copy.
- Caches, temporary outputs, editor/OS artifacts (`.DS_Store`, `__MACOSX/`, `._*`).
- The large `文献13` read-starts text files are **already tracked** (~168 MB); do not add further files of this class. Whether to prune them from history is an open decision recorded in `docs/current-bted-status.md`.

---

## 4. Not changed in this task

- No existing file was modified, deleted, renamed, or relocated.
- No external BTED material was imported.
- No scientific claim, coordinate, evidence class, or source count was altered.
