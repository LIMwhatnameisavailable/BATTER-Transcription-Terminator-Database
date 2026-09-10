# BTED frontend (v0.3)

**Deployment status:** this Next.js interface is retained as a future/alternative frontend
for the `/api/v1` FastAPI contract. The current preview deploys the existing `site/` static UX
with the Cloudflare Worker + D1 route described in [`docs/v0.3/deployment.md`](../docs/v0.3/deployment.md);
Next.js/Vercel is not a current deployment dependency.

This directory contains the English-only Next.js App Router interface for the
BTED v0.3 read API. It is aimed at researchers who need to find a species,
strain, versioned assembly, study, raw accession, evidence class, or endpoint
record. It is a thin catalogue UI: the canonical release and the PostgreSQL
read API remain the source of truth.

## Pages

- `/` — release statistics and the two main entry points: accession/assembly
  search and augmentation records.
- `/sources` and `/sources/[sourceId]` — study-level catalogue and details.
- `/assemblies` and `/assemblies/[assemblyId]` — shared reference context with
  independent source tracks kept separate.
- `/explore` — server-side endpoint filters and pagination.
- `/endpoints/[endId]` — the original 24-column endpoint record and context.
- `/genes/[geneId]` — gene identity, reference interval, related endpoint count,
  and assembly/JBrowse links around the gene.
- `/augmentation` — source-level BATTER augmentation metadata; this does not
  change the experimental evidence class.

An `audit_only` source is displayed for provenance, but the UI deliberately
does not show endpoint downloads or JBrowse links for it.

## Run locally

No dependencies are installed by this repository change. In a local checkout,
install the pinned ranges from `package.json`, then set the API origin for
server-side rendering:

```bash
cd frontend
cp .env.example .env.local
# Set BTED_API_ORIGIN to the API origin, for example http://127.0.0.1:8017
npm install
npm run dev
```

The browser uses same-origin `/api/v1/*` requests. `next.config.mjs` rewrites
those requests to `BTED_API_ORIGIN`; it does not hard-code localhost, so the
same build can be deployed behind a production API origin. Server-rendered
pages also require `BTED_API_ORIGIN` because a Node server cannot fetch a
relative URL.

## Contract check

The dependency-free check only verifies that the expected routes, API wrapper,
rewrite configuration, and user-facing labels are present:

```bash
node frontend/scripts/check-contract.mjs
```

It is not a substitute for `next build`, a browser smoke test, or a real API/
PostgreSQL deployment check. Do not put API credentials in the repository.
