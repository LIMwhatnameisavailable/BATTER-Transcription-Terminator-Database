import { getSources, ApiClientError } from "@/lib/api";
import { EmptyState, ErrorState, PageIntro, ReleaseNote } from "@/components/PageFrame";
import { Pagination } from "@/components/Pagination";
import { SourceCard } from "@/components/SourceCard";

export default async function SourcesPage({ searchParams }: { searchParams?: { page?: string; q?: string; species?: string; evidence_class?: string; release_status?: string } }) {
  const page = Math.max(1, Number(searchParams?.page ?? "1") || 1);
  const filters = { page, page_size: 20, q: searchParams?.q, species: searchParams?.species, evidence_class: searchParams?.evidence_class, release_status: searchParams?.release_status };
  try {
    const result = await getSources(filters);
    const makeHref = (nextPage: number) => `/sources?${new URLSearchParams({ page: String(nextPage), ...(searchParams?.q ? { q: searchParams.q } : {}) }).toString()}`;
    return <>
      <PageIntro eyebrow="Catalogue / sources" title="Experimental data sources"><span>Each source keeps its own paper, assay, accession, reference assembly, and evidence boundary. Multiple sources on one assembly remain separate tracks.</span></PageIntro>
      <ReleaseNote release={result.release} />
      <form className="filter-bar" action="/sources" method="get">
        <div><label htmlFor="q">Search</label><input id="q" name="q" defaultValue={searchParams?.q} placeholder="Species, source ID, PMID, accession" /></div>
        <div><label htmlFor="species">Species</label><input id="species" name="species" defaultValue={searchParams?.species} placeholder="Exact species" /></div>
        <div><label htmlFor="evidence_class">Evidence</label><select id="evidence_class" name="evidence_class" defaultValue={searchParams?.evidence_class ?? ""}><option value="">All evidence</option><option value="author_called_endpoint">Author-called endpoint</option><option value="curated_record">Curated record</option><option value="observed_signal">Observed signal</option><option value="called_endpoint">Called endpoint</option></select></div>
        <div><label htmlFor="release_status">Status</label><select id="release_status" name="release_status" defaultValue={searchParams?.release_status ?? ""}><option value="">All statuses</option><option value="published_standardized">Published</option><option value="audit_only">Audit only</option></select></div>
        <div><label>&nbsp;</label><button className="button primary" type="submit">Apply filters</button></div>
      </form>
      {result.data.length === 0 ? <EmptyState>Try a broader species, accession, or evidence filter.</EmptyState> : <>
        <div className="section-heading"><div><h2>{result.pagination.total.toLocaleString()} sources</h2><p>Published records and source-level audit entries</p></div></div>
        <div className="source-list">{result.data.map((source) => <SourceCard key={source.source_id} source={source} />)}</div>
        <Pagination page={result.pagination.page} hasNext={result.pagination.has_next} makeHref={makeHref} />
      </>}
    </>;
  } catch (reason) {
    return <><PageIntro eyebrow="Catalogue / sources" title="Experimental data sources" /><ErrorState message={reason instanceof ApiClientError ? reason.message : "The source list could not be loaded."} /></>;
  }
}
