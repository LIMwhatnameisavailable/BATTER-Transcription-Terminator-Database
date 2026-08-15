# BTED accession + Range delivery prototype

This directory is a deployment prototype, not a new biological dataset. It uses the already curated `GCF_000739105.1` records from `BATTER_S1_007` and `BATTER_S1_013` to test a scalable delivery contract:

```text
assembly accession
  -> D1 metadata lookup
  -> same-origin /api/remote-data/{asset_key}
  -> byte-Range request to an allowlisted object store
```

The endpoint coordinates, evidence classes and public BED files are unchanged.

## Why this assembly

Both sources use the exact assembly `GCF_000739105.1` and contig `CP009124.1`, but they remain independent experimental tracks:

| Source | Year | Records | Public evidence |
|---|---:|---:|---|
| `BATTER_S1_007` | 2019 | 1,640 | `author_called_endpoint` |
| `BATTER_S1_013` | 2020 | 1,208 | `author_called_endpoint` |

The two existing release copies of FASTA, FAI, gene GFF3 and TBI are byte-identical. The prototype resolves one shared reference object and avoids one duplicated 8,628,614-byte reference/annotation set.

## Files

- `registry.json`: checksum-frozen local object map used by the demo server;
- `schema.sql`: proposed Cloudflare D1 schema;
- `seed.sql`: one-assembly pilot rows;
- `src/worker.js`: production-shaped Worker routes;
- `wrangler.jsonc`: deployment skeleton; real D1 and Hugging Face identifiers are intentionally unset.

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

Open `http://127.0.0.1:8016/accession-range-demo.html`. The bilingual user page searches the local registry by assembly accession, lists the available independent studies, and links to downloads and a dynamically constructed JBrowse view. D1, API routes, object paths, and Range diagnostics are intentionally kept out of the public-facing interface; the tests below verify those implementation details directly.

The local object backend is intentional. It demonstrates and tests the browser/API contract without publishing data to an external service or requiring Cloudflare credentials.

## API contract

### `GET /api/assemblies/{accession}`

Returns exact assembly identity, reference assets, independent source tracks, evidence labels, checksums, byte sizes and a dynamic JBrowse config URL.

### `GET /api/assemblies/{accession}/jbrowse-config`

Builds one reference assembly plus independent experiment tracks. All data locations point to same-origin asset keys rather than exposing storage URLs.

### `GET|HEAD /api/remote-data/{asset_key}`

Only registered asset keys are accepted. The route forwards `Range` and conditional headers to the allowlisted origin and preserves `206`, `Content-Range`, `Accept-Ranges`, `ETag`, `Content-Length` and content type. It does not accept an arbitrary `?url=` parameter and therefore is not an open proxy.

## Production steps not performed in this branch

1. Create the Cloudflare D1 database and apply `schema.sql` / reviewed seed rows.
2. Upload checksum-verified objects to an approved Hugging Face dataset repository or another object store.
3. Replace the placeholder D1 ID and `HF_RESOLVE_BASE` in deployment configuration.
4. Verify `HEAD`, `206 Partial Content`, content range, caching and failure behavior against the real origin.
5. Route both the frontend and `/api` through the same Cloudflare site or custom domain.
6. Keep versioned BED, metadata, manifest and checksum release snapshots for reproducibility.

Do not migrate the remaining assemblies until the pilot reproduces the existing JBrowse coordinates and track counts without evidence reinterpretation.
