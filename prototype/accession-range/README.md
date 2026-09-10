# BTED Cloudflare catalogue prototype

This directory is the current Cloudflare Worker + D1 + Worker Static Assets preview, not
a new biological dataset. It extends the earlier one-assembly accession/Range experiment
to the complete BTED catalogue without changing the canonical v0.2 release or endpoint
interpretation. The request path is:

```text
verified materialized bundle
  -> scripts/generate_bted_d1.py
  -> D1 preview projection
  -> Cloudflare Worker /api/*
  -> registered HF object key + same-origin GET/HEAD/Range
  -> existing site/ static UX
```

The preview covers 22 sources (21 `published_standardized` + 1 `audit_only`), 20 release
assembly records, 49 contigs, 32 source accessions, 22 tracks, 28,399 endpoints and 211
registered assets (208 public). Source annotations remain HF/metadata assets; genes are
omitted from D1 because the current catalogue UI/API does not query them. The D1 row is
`release_version=v0.2.0, status=preview`: a rebuildable query projection, not promotion or
a new `v0.3.0` dataset.

## Why this assembly

Both sources use the exact assembly `GCF_000739105.1` and contig `CP009124.1`, but they remain independent experimental tracks:

| Source | Year | Records | Public evidence |
|---|---:|---:|---|
| `BATTER_S1_007` | 2019 | 1,640 | `author_called_endpoint` |
| `BATTER_S1_013` | 2020 | 1,208 | `author_called_endpoint` |

The two existing release copies of FASTA, FAI, gene GFF3 and TBI are byte-identical. The prototype resolves one shared reference object and avoids one duplicated 8,628,614-byte reference/annotation set.

## Files

- `registry.json`: checksum-frozen local object map from the historical one-assembly pilot;
- `schema.sql`: complete Cloudflare D1 preview schema;
- `seed.sql`: historical pilot rows, not the catalogue import source;
- `src/worker.js`: catalogue API, static fallback and allowlisted HF proxy;
- `wrangler.jsonc`: current Worker, D1 binding, static `site/` directory and pinned HF origin;
- `../../scripts/generate_bted_d1.py`: deterministic batch generator from the verified bundle.
  Generated SQL belongs in `/private/tmp` or another external staging directory, not Git.

## Local demonstration

Build the existing release and staged website first, then start the API-aware server:

```bash
python3 scripts/build_jbrowse_release.py --input-root /Users/seu_yolo/Desktop/BGIRNA
python3 scripts/build_v0_2_site.py
python3 scripts/stage_pages.py \
  --jbrowse-dir dist/BTED-v0.2.0-jbrowse \
  --output-dir .pages-preview
python3 scripts/run_accession_range_demo.py --port 8016
```

Open `http://127.0.0.1:8016/accession-range-demo.html`. The bilingual user page searches by assembly accession and shows the already curated core fields: organism, strain, assembly, publication, assay, raw-data accession and evidence class. Endpoint definitions and limitations remain available in a secondary disclosure. D1, API routes, object paths, and Range diagnostics are intentionally kept out of the public-facing interface; the tests below verify those implementation details directly.

The local object backend is intentional. It demonstrates and tests the browser/API contract without publishing data to an external service or requiring Cloudflare credentials.

## API contract

### `GET /api/assemblies/{accession}`

Returns exact assembly identity, reference assets, independent source tracks, evidence labels, checksums, byte sizes and a dynamic JBrowse config URL.

### `GET /api/assemblies/{accession}/jbrowse-config`

Builds one reference assembly plus independent experiment tracks. All data locations point to same-origin asset keys rather than exposing storage URLs.

### `GET|HEAD /api/remote-data/{asset_key}`

Only registered asset keys are accepted. The route forwards `Range` and conditional headers to the allowlisted origin and preserves `206`, `Content-Range`, `Accept-Ranges`, `ETag`, `Content-Length` and content type. It does not accept an arbitrary `?url=` parameter and therefore is not an open proxy.

## Complete catalogue local import

```bash
python3 scripts/generate_bted_d1.py \
  --bundle-dir /path/to/verified-bundle \
  --output-dir /private/tmp/bted-v03-d1-import

npx wrangler d1 execute bted-catalogue-v03-preview --local \
  --file /private/tmp/bted-v03-d1-import/schema.sql \
  --config prototype/accession-range/wrangler.jsonc
for f in /private/tmp/bted-v03-d1-import/[0-8][0-9]*.sql; do
  npx wrangler d1 execute bted-catalogue-v03-preview --local \
    --file "$f" --config prototype/accession-range/wrangler.jsonc || exit 1
done
```

Wrangler 4.125 local D1 rejects explicit SQL `BEGIN/COMMIT`; the generator emits plain
INSERT batches and lets D1 handle statement execution. The final local smoke count is
28,399 endpoints, 211 assets, 208 public assets, 22 sources and 20 assemblies.

## Remote deployment boundary

The fixed HF revision
`463cfc8bd582a5ed9d2c426822148c3f1e56c4d0` has passed 208/208 HEAD +
single-byte Range audit (196,667,360 bytes). The remote preview was last fully verified on
2026-08-23 at
`https://bted-catalogue-v03-preview.bted-v0-3-dynamic-service.workers.dev`, backed by the
`bted-catalogue-v03-preview` D1 database. Do not put tokens/passwords in Git or logs. See
[`docs/v0.3/deployment.md`](../../docs/v0.3/deployment.md) for the measured counts and smoke
results. A 2026-09-06 check from the maintainer environment timed out while connecting to
both Cloudflare and Hugging Face; treat current availability as not reverified, not as a
confirmed outage.

FastAPI/PostgreSQL/Next.js code remains a future/alternative path; Render/Neon/Vercel are not
current deployment dependencies.
