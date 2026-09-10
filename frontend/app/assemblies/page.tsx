import Link from "next/link";
import { getAssemblies, ApiClientError } from "@/lib/api";
import { EmptyState, ErrorState, PageIntro, ReleaseNote } from "@/components/PageFrame";
import { Pagination } from "@/components/Pagination";

export default async function AssembliesPage({ searchParams }: { searchParams?: { page?: string; q?: string; species?: string; assembly_accession?: string } }) {
  const page = Math.max(1, Number(searchParams?.page ?? "1") || 1);
  try {
    const result = await getAssemblies({ page, page_size: 20, q: searchParams?.q, species: searchParams?.species, assembly_accession: searchParams?.assembly_accession });
    const makeHref = (nextPage: number) => `/assemblies?${new URLSearchParams({ page: String(nextPage), ...(searchParams?.q ? { q: searchParams.q } : {}) }).toString()}`;
    return <>
      <PageIntro eyebrow="Catalogue / reference assemblies" title="Browse by assembly"><span>Start with a versioned reference sequence. One assembly can host multiple independently published source tracks; BTED keeps their endpoint records separate.</span></PageIntro>
      <ReleaseNote release={result.release} />
      <form className="filter-bar" action="/assemblies" method="get">
        <div><label htmlFor="q">Search</label><input id="q" name="q" defaultValue={searchParams?.q} placeholder="Accession, species, strain" /></div>
        <div><label htmlFor="assembly_accession">Assembly accession</label><input id="assembly_accession" name="assembly_accession" defaultValue={searchParams?.assembly_accession} placeholder="GCF_..." /></div>
        <div><label htmlFor="species">Species</label><input id="species" name="species" defaultValue={searchParams?.species} placeholder="Exact species" /></div>
        <div /><div /><div><label>&nbsp;</label><button className="button primary" type="submit">Search assemblies</button></div>
      </form>
      {result.data.length === 0 ? <EmptyState>Try a versioned assembly accession or species name.</EmptyState> : <>
        <div className="section-heading"><div><h2>{result.pagination.total.toLocaleString()} assemblies</h2><p>Reference context for published source tracks</p></div></div>
        <div className="table-wrap"><table><thead><tr><th>Assembly</th><th>Organism / strain</th><th>Contigs</th><th>Sources</th><th>Genes</th><th>Endpoint records</th><th /></tr></thead><tbody>{result.data.map((assembly) => <tr key={assembly.assembly_accession}><td><Link href={`/assemblies/${encodeURIComponent(assembly.assembly_accession)}`}><strong>{assembly.assembly_accession}</strong></Link></td><td>{assembly.organism_name ?? "—"}<br /><span className="muted">{assembly.strain ?? "Strain not recorded"}</span></td><td>{assembly.contigs?.length ?? 0}</td><td>{assembly.source_count}</td><td><Link href={`/genes?assembly_accession=${encodeURIComponent(assembly.assembly_accession)}`}>{assembly.gene_count.toLocaleString()}</Link></td><td>{assembly.endpoint_count.toLocaleString()}</td><td><Link href={`/assemblies/${encodeURIComponent(assembly.assembly_accession)}`}>View details</Link></td></tr>)}</tbody></table></div>
        <Pagination page={result.pagination.page} hasNext={result.pagination.has_next} makeHref={makeHref} />
      </>}
    </>;
  } catch (reason) { return <><PageIntro eyebrow="Catalogue / reference assemblies" title="Browse by assembly" /><ErrorState message={reason instanceof ApiClientError ? reason.message : "The assembly list could not be loaded."} /></>; }
}
