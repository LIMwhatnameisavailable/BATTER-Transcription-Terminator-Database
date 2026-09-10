export type Release = {
  release_version: string;
  status: string;
  canonical_manifest_sha256?: string;
  import_run_id?: number | null;
};

export type Publication = {
  pmid?: string | null;
  doi?: string | null;
  pmc?: string | null;
  year?: number | null;
  journal?: string | null;
  title?: string | null;
  links?: Record<string, string>;
};

export type Accession = {
  namespace?: string;
  accession?: string;
  raw_value?: string | null;
  type?: string | null;
  url?: string | null;
};

export type Asset = {
  asset_id: string;
  asset_kind: string;
  logical_path: string;
  sha256?: string;
};

export type Source = {
  source_id: string;
  release_status: string;
  species: string;
  phylum?: string | null;
  strain?: string | null;
  assay_family: string;
  evidence_class: string;
  record_count: number;
  used_for_batter_augmentation?: boolean;
  augmentation_eligible?: boolean;
  redistribution_status?: string;
  publication: Publication;
  assembly: {
    accession?: string | null;
    name?: string | null;
    organism_name?: string | null;
    strain?: string | null;
  };
  accessions: Accession[];
  assets?: Asset[];
  links: {
    bted_record?: string;
    manifest?: string;
    endpoints_download?: string;
    jbrowse?: string | null;
    jbrowse_config?: string | null;
    jbrowse_note?: string;
  };
  provenance: Record<string, unknown>;
  known_limitations?: string | null;
  decision_note?: string | null;
  source_note?: string | null;
};

export type Contig = { accession: string; name?: string; length_bp?: number };

export type Assembly = {
  assembly_accession: string;
  assembly_name?: string | null;
  organism_name?: string | null;
  strain?: string | null;
  contigs: Contig[];
  source_count: number;
  endpoint_count: number;
  gene_count: number;
  source_tracks: Array<{ source_id: string; record_count?: number }>;
  links?: { jbrowse?: string | null; jbrowse_config?: string | null };
  provenance: Record<string, unknown>;
};

export type Endpoint = Record<string, unknown> & {
  end_id: string;
  source_id: string;
  reference_assembly: string;
  reference_name: string;
  biological_coordinate_1based: number;
  strand: "+" | "-";
  evidence_class: string;
  associated_gene_or_locus?: string;
  pmid?: string | null;
  doi?: string | null;
  source_annotations_summary?: unknown;
  provenance?: Record<string, unknown>;
};

export type Gene = {
  gene_id: string;
  locus_tag?: string | null;
  gene_name?: string | null;
  feature_type?: string | null;
  start_1based: number;
  end_1based: number;
  strand: "+" | "-";
  assembly_accession: string;
  contig_accession: string;
  contig_name?: string | null;
  annotation_asset_id?: string | null;
  annotation_sha256?: string | null;
  attributes: Record<string, unknown>;
  provenance: Record<string, unknown>;
};

export type Page<T> = {
  release: Release;
  data: T[];
  pagination: { page: number; page_size: number; returned: number; total: number; has_next: boolean };
};

export type Stats = {
  release: Release;
  sources: { total: number; published_standardized: number; audit_only: number };
  endpoints: { total: number; by_evidence_class: Record<string, number> };
  assemblies: { total: number };
  augmentation: { eligible_sources: number; scope: string };
};

export class ApiClientError extends Error {
  status: number;
  code: string;

  constructor(message: string, status: number, code = "api_error") {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
  }
}

function apiOrigin(): string {
  if (typeof window === "undefined") return process.env.BTED_API_ORIGIN?.replace(/\/$/, "") ?? "";
  return "";
}

function apiUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const url = `${apiOrigin()}${path}`;
  return query.toString() ? `${url}?${query.toString()}` : url;
}

async function request<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const response = await fetch(apiUrl(path, params), { next: { revalidate: 30 } });
  if (!response.ok) {
    let message = `API request failed (${response.status})`;
    let code = "api_error";
    try {
      const payload = await response.json();
      message = payload?.error?.message ?? message;
      code = payload?.error?.code ?? code;
    } catch {
      // Keep the HTTP status message when the API did not return JSON.
    }
    throw new ApiClientError(message, response.status, code);
  }
  return response.json() as Promise<T>;
}

export const getStats = () => request<Stats>("/api/v1/stats");
export const getSources = (params: Record<string, string | number | boolean | undefined> = {}) => request<Page<Source>>("/api/v1/sources", params);
export const getSource = (sourceId: string) => request<{ release: Release } & Source>(`/api/v1/sources/${encodeURIComponent(sourceId)}`);
export const getAssemblies = (params: Record<string, string | number | boolean | undefined> = {}) => request<Page<Assembly>>("/api/v1/assemblies", params);
export const getAssembly = (assemblyId: string) => request<{ release: Release } & Assembly>(`/api/v1/assemblies/${encodeURIComponent(assemblyId)}`);
export const getEndpoint = (endId: string) => request<{ release: Release } & Endpoint>(`/api/v1/endpoints/${encodeURIComponent(endId)}`);
export const getEndpoints = (params: Record<string, string | number | boolean | undefined> = {}) => request<Page<Endpoint>>("/api/v1/endpoints", params);
export const getGenes = (params: Record<string, string | number | boolean | undefined> = {}) => request<Page<Gene>>("/api/v1/genes", params);
export const getGene = (geneId: string) => request<{ release: Release } & Gene>(`/api/v1/genes/${encodeURIComponent(geneId)}`);
export const getAugmentation = (params: Record<string, string | number | boolean | undefined> = {}) => request<Page<Source> & { scope: string; training_claim: string; eligible_source_count: number }>("/api/v1/augmentation", params);
