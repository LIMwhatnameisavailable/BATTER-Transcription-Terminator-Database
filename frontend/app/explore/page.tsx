"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { ApiClientError, Endpoint, Page, getEndpoints } from "@/lib/api";
import { EmptyState, ErrorState, PageIntro, ReleaseNote, StatusBadge } from "@/components/PageFrame";

type FilterState = {
  source_id: string;
  assembly_accession: string;
  contig_accession: string;
  gene_or_locus: string;
  strand: string;
  evidence_class: string;
  position_min: string;
  position_max: string;
};

const EMPTY_FILTERS: FilterState = {
  source_id: "",
  assembly_accession: "",
  contig_accession: "",
  gene_or_locus: "",
  strand: "",
  evidence_class: "",
  position_min: "",
  position_max: "",
};

function parseQuery(queryString: string): { filters: FilterState; page: number } {
  const query = new URLSearchParams(queryString);
  return {
    filters: {
      source_id: query.get("source_id") ?? "",
      assembly_accession: query.get("assembly_accession") ?? "",
      contig_accession: query.get("contig_accession") ?? "",
      gene_or_locus: query.get("gene_or_locus") ?? "",
      strand: query.get("strand") ?? "",
      evidence_class: query.get("evidence_class") ?? "",
      position_min: query.get("position_min") ?? "",
      position_max: query.get("position_max") ?? "",
    },
    page: Math.max(1, Number(query.get("page") ?? "1") || 1),
  };
}

function numberValue(value: string): number | undefined {
  if (!value) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function endpointParams(filters: FilterState, page: number) {
  return {
    page,
    page_size: 25,
    source_id: filters.source_id || undefined,
    assembly_accession: filters.assembly_accession || undefined,
    contig_accession: filters.contig_accession || undefined,
    gene_or_locus: filters.gene_or_locus || undefined,
    strand: filters.strand || undefined,
    evidence_class: filters.evidence_class || undefined,
    position_min: numberValue(filters.position_min),
    position_max: numberValue(filters.position_max),
  };
}

function downloadHref(filters: FilterState, format: "tsv" | "bed6"): string {
  const query = new URLSearchParams({ format });
  if (filters.source_id) query.set("source_id", filters.source_id);
  if (filters.assembly_accession) query.set("assembly_accession", filters.assembly_accession);
  if (filters.contig_accession) query.set("contig_accession", filters.contig_accession);
  if (filters.gene_or_locus) query.set("gene_or_locus", filters.gene_or_locus);
  if (filters.strand) query.set("strand", filters.strand);
  if (filters.evidence_class) query.set("evidence_class", filters.evidence_class);
  if (filters.position_min) query.set("position_min", filters.position_min);
  if (filters.position_max) query.set("position_max", filters.position_max);
  return `/api/v1/downloads/endpoints?${query.toString()}`;
}

export default function ExplorePage() {
  const [queryString, setQueryString] = useState<string | null>(null);
  const [draft, setDraft] = useState<FilterState>(EMPTY_FILTERS);
  const [result, setResult] = useState<Page<Endpoint> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const parsed = useMemo(() => parseQuery(queryString ?? ""), [queryString]);

  useEffect(() => {
    const sync = () => setQueryString(window.location.search);
    sync();
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  useEffect(() => {
    setDraft(parsed.filters);
  }, [parsed]);

  useEffect(() => {
    if (queryString === null) return;
    let active = true;
    setLoading(true);
    setError(null);
    setResult(null);
    getEndpoints(endpointParams(parsed.filters, parsed.page))
      .then((value) => {
        if (active) setResult(value);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof ApiClientError ? reason.message : "The endpoint table could not be loaded.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [parsed, queryString, retry]);

  const updateUrl = (filters: FilterState, page: number) => {
    const query = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });
    if (page > 1) query.set("page", String(page));
    const href = query.toString() ? `/explore?${query.toString()}` : "/explore";
    window.history.pushState({}, "", href);
    setQueryString(window.location.search);
  };

  const updateDraft = (key: keyof FilterState, value: string) => {
    setDraft((current) => ({ ...current, [key]: value }));
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateUrl(draft, 1);
  };

  return <>
    <PageIntro eyebrow="Catalogue / endpoints" title="Explore endpoint records"><span>Filter the public endpoint table without collapsing source, sample, contig, strand, or evidence identity. Results update in place; the URL remains shareable.</span></PageIntro>
    {result && <ReleaseNote release={result.release} />}
    <form className="filter-bar" onSubmit={submit}>
      <div><label htmlFor="source_id">Source</label><input id="source_id" name="source_id" value={draft.source_id} onChange={(event) => updateDraft("source_id", event.target.value)} placeholder="BATTER_S1_007" /></div>
      <div><label htmlFor="assembly_accession">Assembly</label><input id="assembly_accession" name="assembly_accession" value={draft.assembly_accession} onChange={(event) => updateDraft("assembly_accession", event.target.value)} placeholder="GCF_..." /></div>
      <div><label htmlFor="contig_accession">Contig</label><input id="contig_accession" name="contig_accession" value={draft.contig_accession} onChange={(event) => updateDraft("contig_accession", event.target.value)} placeholder="CP..." /></div>
      <div><label htmlFor="gene_or_locus">Gene / locus</label><input id="gene_or_locus" name="gene_or_locus" value={draft.gene_or_locus} onChange={(event) => updateDraft("gene_or_locus", event.target.value)} placeholder="locus tag" /></div>
      <div><label htmlFor="strand">Strand</label><select id="strand" name="strand" value={draft.strand} onChange={(event) => updateDraft("strand", event.target.value)}><option value="">Both strands</option><option value="+">+ plus</option><option value="-">− minus</option></select></div>
      <div><label htmlFor="evidence_class">Evidence</label><select id="evidence_class" name="evidence_class" value={draft.evidence_class} onChange={(event) => updateDraft("evidence_class", event.target.value)}><option value="">All public evidence</option><option value="author_called_endpoint">Author-called endpoint</option><option value="curated_record">Curated record</option><option value="observed_signal">Observed signal</option><option value="called_endpoint">Called endpoint</option></select></div>
      <div><label htmlFor="position_min">Position ≥</label><input id="position_min" name="position_min" inputMode="numeric" value={draft.position_min} onChange={(event) => updateDraft("position_min", event.target.value)} placeholder="1" /></div>
      <div><label htmlFor="position_max">Position ≤</label><input id="position_max" name="position_max" inputMode="numeric" value={draft.position_max} onChange={(event) => updateDraft("position_max", event.target.value)} placeholder="100000" /></div>
      <div><label>&nbsp;</label><button className="button primary" type="submit">Filter records</button></div>
    </form>
    {loading && <div className="empty-state"><strong>Loading endpoint records…</strong><p>Applying the current release and filter set.</p></div>}
    {!loading && error && <><ErrorState message={error} /><button className="button secondary" type="button" onClick={() => setRetry((value) => value + 1)}>Retry</button></>}
    {!loading && !error && result && <div className="section-heading"><div><h2>{result.pagination.total.toLocaleString()} matching records</h2><p>Showing page {result.pagination.page}; positions remain 1-based in the record view.</p></div><div className="card-actions"><a className="button secondary" href={downloadHref(parsed.filters, "tsv")} download>Download current results (TSV)</a><a className="button secondary" href={downloadHref(parsed.filters, "bed6")} download>Download current results (BED6)</a></div></div>}
    {!loading && !error && result && result.data.length === 0 && <EmptyState>No endpoint records match these filters.</EmptyState>}
    {!loading && !error && result && result.data.length > 0 && <>
      <div className="table-wrap"><table><thead><tr><th>Endpoint</th><th>Source</th><th>Assembly / contig</th><th>Position</th><th>Strand</th><th>Evidence</th><th>Associated locus</th><th>Context</th></tr></thead><tbody>{result.data.map((endpoint) => <tr key={endpoint.end_id}><td><Link href={`/endpoints/${encodeURIComponent(endpoint.end_id)}`}><strong>{endpoint.end_id}</strong></Link></td><td><Link href={`/sources/${encodeURIComponent(endpoint.source_id)}`}>{endpoint.source_id}</Link></td><td>{endpoint.reference_assembly}<br /><span className="muted">{endpoint.reference_name}</span></td><td>{endpoint.biological_coordinate_1based.toLocaleString()}</td><td>{endpoint.strand}</td><td><StatusBadge value={endpoint.evidence_class} /></td><td>{endpoint.associated_gene_or_locus ?? "—"}</td><td><Link href={`/endpoints/${encodeURIComponent(endpoint.end_id)}`}>View record</Link><br /><Link href={`/assemblies/${encodeURIComponent(endpoint.reference_assembly)}`}>Assembly details</Link></td></tr>)}</tbody></table></div>
      <div className="pagination"><button className="button secondary" type="button" disabled={parsed.page <= 1} onClick={() => updateUrl(parsed.filters, parsed.page - 1)}>Previous</button><span>Page {result.pagination.page}</span><button className="button secondary" type="button" disabled={!result.pagination.has_next} onClick={() => updateUrl(parsed.filters, parsed.page + 1)}>Next</button></div>
    </>}
  </>;
}
