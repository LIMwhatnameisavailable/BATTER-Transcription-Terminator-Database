import json
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKER = REPO_ROOT / "prototype/accession-range/src/worker.js"


class WorkerAssetProxyTests(unittest.TestCase):
    def run_worker(
        self,
        *,
        request_url: str = "http://localhost:8787",
        local_asset_base: str | None = None,
        fetch_mode: str = "success",
    ) -> dict[str, object]:
        worker_path = json.dumps(str(WORKER))
        request_url_js = json.dumps(request_url)
        local_asset_base_js = json.dumps(local_asset_base)
        fetch_mode_js = json.dumps(fetch_mode)
        script = f"""
import {{ readFileSync }} from "node:fs";

const source = readFileSync({worker_path}, "utf8")
  .replace("export default {{", "const worker = {{") + "\\nexport {{ worker }};";
const moduleUrl = "data:text/javascript;base64," + Buffer.from(source).toString("base64");
const {{ worker }} = await import(moduleUrl);

const release = {{
  release_version: "v0.2.0",
  status: "preview",
  canonical_manifest_path: "release_manifest.json",
  canonical_manifest_sha256: "a".repeat(64),
  asset_origin_status: "verified",
  materializer_version: "test",
  is_current: 1,
}};
const asset = {{
  asset_key: "v0.2.0--assembly-GCF_000009045.1--fai",
  release_version: "v0.2.0",
  assembly_accession: "GCF_000009045.1",
  source_id: null,
  asset_kind: "fai",
  logical_path: "assemblies/GCF_000009045.1/reference/reference.fna.fai",
  origin_host: "huggingface.co",
  content_type: "text/plain",
  byte_size: 29,
  sha256: "b".repeat(64),
  supports_range: 1,
  redistribution_status: "verified_redistributable",
  is_public: 1,
}};
const db = {{
  prepare(sql) {{
    if (sql.includes("FROM release_versions")) return {{ bind() {{ return {{ first: async () => release }}; }} }};
    if (sql.includes("FROM assets")) return {{ bind() {{ return {{ first: async () => asset }}; }} }};
    throw new Error(`Unexpected query: ${{sql}}`);
  }},
}};

let fetchedUrl = null;
const fetchMode = {fetch_mode_js};
globalThis.fetch = async (url) => {{
  fetchedUrl = String(url);
  if (fetchMode === "throw") throw new Error("Network connection lost");
  const body = "NC_000964.3\\t4215606\\t72\\t70\\t71\\n";
  return new Response(body, {{ status: 200, headers: {{ "content-type": "text/plain", "content-length": "29" }} }});
}};
const env = {{
  BTED_DB: db,
  HF_RESOLVE_BASE: "https://huggingface.co/datasets/x/resolve/y",
  ALLOWED_ORIGIN_HOST: "huggingface.co",
}};
if ({local_asset_base_js} !== null) env.LOCAL_ASSET_BASE = {local_asset_base_js};
const response = await worker.fetch(
  new Request({request_url_js} + "/api/assets/" + asset.asset_key),
  env,
);
let body;
try {{ body = await response.clone().json(); }} catch {{ body = await response.text(); }}
process.stdout.write(JSON.stringify({{
  status: response.status,
  body,
  cacheControl: response.headers.get("cache-control"),
  fetchedUrl,
}}));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_loopback_request_can_use_explicit_loopback_asset_base(self):
        payload = self.run_worker(local_asset_base="http://127.0.0.1:8790")
        self.assertEqual(payload["status"], 200)
        self.assertEqual(payload["body"], "NC_000964.3\t4215606\t72\t70\t71\n")
        self.assertEqual(
            payload["fetchedUrl"],
            "http://127.0.0.1:8790/assemblies/GCF_000009045.1/reference/reference.fna.fai",
        )

    def test_non_loopback_request_ignores_local_asset_base(self):
        payload = self.run_worker(
            request_url="https://preview.example.test",
            local_asset_base="http://127.0.0.1:8790",
        )
        self.assertEqual(payload["status"], 200)
        self.assertEqual(
            payload["fetchedUrl"],
            "https://huggingface.co/datasets/x/resolve/y/assemblies/GCF_000009045.1/reference/reference.fna.fai",
        )

    def test_loopback_request_rejects_non_loopback_local_asset_base(self):
        payload = self.run_worker(local_asset_base="http://assets.example.test")
        self.assertEqual(payload["status"], 403)
        self.assertEqual(payload["body"], {"error": "local_origin_not_allowed"})
        self.assertIsNone(payload["fetchedUrl"])

    def test_network_error_becomes_structured_502_without_leaking_opaque_500(self):
        payload = self.run_worker(fetch_mode="throw")
        self.assertEqual(payload["status"], 502)
        self.assertEqual(
            payload["body"],
            {
                "error": "asset_origin_unavailable",
                "asset_key": "v0.2.0--assembly-GCF_000009045.1--fai",
            },
        )
        self.assertEqual(payload["cacheControl"], "no-store")


if __name__ == "__main__":
    unittest.main()
