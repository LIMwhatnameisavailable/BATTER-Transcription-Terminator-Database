import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const requiredFiles = [
  "package.json",
  "next.config.mjs",
  ".env.example",
  "lib/api.ts",
  "app/page.tsx",
  "app/sources/page.tsx",
  "app/sources/[sourceId]/page.tsx",
  "app/assemblies/page.tsx",
  "app/assemblies/[assemblyId]/page.tsx",
  "app/genes/page.tsx",
  "app/endpoints/[endId]/page.tsx",
  "app/genes/[geneId]/page.tsx",
  "app/augmentation/page.tsx",
  "app/explore/page.tsx",
];

for (const relative of requiredFiles) {
  if (!existsSync(resolve(frontend, relative))) {
    throw new Error(`missing required frontend file: ${relative}`);
  }
}

const read = (relative) => readFileSync(resolve(frontend, relative), "utf8");
const home = read("app/page.tsx");
const api = read("lib/api.ts");
const config = read("next.config.mjs");
const source = read("app/sources/[sourceId]/page.tsx");
const explore = read("app/explore/page.tsx");
const endpoint = read("app/endpoints/[endId]/page.tsx");
const genes = read("app/genes/page.tsx");
const gene = read("app/genes/[geneId]/page.tsx");
const assertions = [
  [home, "getStats", "home loads dynamic release statistics"],
  [home, "Search by accession", "home has accession search entry"],
  [home, "Data augmentation", "home has augmentation entry"],
  [api, "/api/v1/stats", "API wrapper includes stats"],
  [api, "BTED_API_ORIGIN", "API origin is environment controlled"],
  [config, "BTED_API_ORIGIN", "rewrite uses API origin"],
  [config, "localhost", "rewrite must not hard-code localhost"],
  [source, "Metadata audit only", "audit-only source boundary is visible"],
  [source, "Download endpoint table", "source download entry exists"],
  [explore, "Filter records", "endpoint filters use the API"],
  [explore, "View record", "endpoint record context entry exists"],
  [explore, "Assembly details", "endpoint assembly details entry exists"],
  [explore, "useEffect", "explore updates client-side"],
  [explore, "pushState", "explore filters remain shareable in URL"],
  [explore, "Download current results", "explore exposes filtered downloads"],
  [explore, "position_min", "explore exposes position filters"],
  [explore, "Loading endpoint records", "explore exposes loading state"],
  [explore, "Retry", "explore exposes retry state"],
  [explore, "No endpoint records match", "explore exposes empty state"],
  [endpoint, "getAssembly", "endpoint detail loads assembly browser availability"],
  [endpoint, "Open JBrowse (±500 bp)", "endpoint detail exposes a located browser link"],
  [endpoint, "JBrowse unavailable", "endpoint detail explains missing browser availability"],
  [api, "getGenes", "API wrapper includes gene list"],
  [genes, "Filter genes", "gene list filters are server-side"],
  [genes, "Assembly context", "gene list provides assembly context"],
  [genes, "JBrowse context", "gene list provides browser context"],
  [api, "getGene", "API wrapper includes gene detail"],
  [gene, "getGene", "gene detail page loads gene"],
  [gene, "±500 bp", "gene page provides a flanked JBrowse window"],
  [gene, "/assemblies/", "gene page links to assembly context"],
];
for (const [content, needle, description] of assertions) {
  if (needle === "localhost" ? content.includes(needle) : !content.includes(needle)) {
    throw new Error(`contract assertion failed: ${description}`);
  }
}

console.log(`BTED frontend contract: PASS (${requiredFiles.length} route/config files checked)`);
