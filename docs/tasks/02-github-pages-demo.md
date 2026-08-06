# Task 02 — Build a GitHub Pages static demonstration site

## Dependency and branch

- Start only after Task 01 is reviewed and its migration inventory is accepted.
- **Suggested branch:** `agent/github-pages-demo`
- **Target:** draft pull request to `main`

## Goal

Create a small, static, reviewable demonstration of the BTED database. It must explain the project, expose only approved public metadata/derived assets, and link to external public raw-data repositories rather than copying large raw data into the Pages deployment.

## First decide, then build

Before writing site code, record the approved source of truth for:

- source metadata and processing status;
- evidence-layer labels;
- download links and their publication eligibility;
- any JBrowse assets;
- version/date shown on the site.

If these are not yet approved, stop and return to Task 01; do not create placeholder scientific claims.

## Minimum static-site scope

1. Home page: project purpose, evidence boundary, scope, source count/version, and limitations.
2. Data catalog: static, searchable/filterable source table from an approved generated metadata file.
3. Record page or record template: organism, assay, reference, evidence class, status, public downloads, citations, and external source links.
4. Methods/limitations page: coordinate convention, evidence-layer definitions, exclusions, and reproducibility links.
5. Optional JBrowse link only when the corresponding public configuration and assets are verified.

## GitHub Pages requirements

- Use relative paths compatible with project Pages (`/<repository-name>/`), never assume a site served from `/`.
- Include `.nojekyll` if static assets or directory names need Jekyll bypass.
- Keep raw large inputs outside the Pages artifact; link to GEO/SRA/ENA/DOI or other approved public repositories.
- Do not include credentials, tokens, unpublished data, local absolute paths, caches, or API calls requiring a secret.
- Prefer a deployment workflow that builds into a dedicated static artifact; do not deploy directly from an experimental development directory.

## Validation

1. Run any project regression tests supplied by the accepted migration.
2. Run `git diff --check`.
3. Serve the static site locally and test:
   - home page loads under the repository subpath;
   - catalog search/filter works;
   - links and downloads are relative/valid;
   - at least one record page and any JBrowse link load;
   - site never labels predictions or mixed evidence as experimental endpoints.
4. Include screenshots and the local validation command in the draft PR.

## Done when

The draft PR contains a static demo only, documents its data provenance and limits, passes validation, and gives reviewers a safe path to enable GitHub Pages after merge.
