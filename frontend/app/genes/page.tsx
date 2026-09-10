import Link from "next/link";
import { ApiClientError, getGenes } from "@/lib/api";
import { EmptyState, ErrorState, PageIntro, ReleaseNote } from "@/components/PageFrame";
import { Pagination } from "@/components/Pagination";

type GeneParams = {
  page?: string;
  assembly_accession?: string;
  contig_accession?: string;
  locus_tag?: string;
  gene_id?: string;
  feature_type?: string;
  start_min?: string;
  start_max?: string;
};

function integerParam(value?: string): number | undefined {
  if (!value || !/^\d+$/.test(value)) return undefined;
  return Number(value);
}

export default async function GenesPage({ searchParams }: { searchParams?: GeneParams }) {
  const page = Math.max(1, Number(searchParams?.page ?? "1") || 1);
  const startMin = integerParam(searchParams?.start_min);
  const startMax = integerParam(searchParams?.start_max);
  const params = {
    page,
    page_size: 25,
    assembly_accession: searchParams?.assembly_accession,
    contig_accession: searchParams?.contig_accession,
    locus_tag: searchParams?.locus_tag,
    gene_id: searchParams?.gene_id,
    feature_type: searchParams?.feature_type,
    start_min: startMin,
    start_max: startMax,
  };

  try {
    const result = await getGenes(params);
    const makeHref = (nextPage: number) => {
      const query = new URLSearchParams();
      Object.entries({ ...searchParams, page: String(nextPage) }).forEach(([key, value]) => {
        if (value) query.set(key, value);
      });
      return `/genes?${query.toString()}`;
    };
    return <>
      <PageIntro eyebrow="Catalogue / genes" title="Browse reference genes"><span>Search the GFF-derived gene query layer by assembly, contig, locus tag, stable gene ID, feature type, or 1-based start interval. Gene annotations do not add endpoint evidence or endpoint context.</span></PageIntro>
      <ReleaseNote release={result.release} />
      <form className="filter-bar" action="/genes" method="get">
        <div><label htmlFor="assembly_accession">Assembly</label><input id="assembly_accession" name="assembly_accession" defaultValue={searchParams?.assembly_accession} placeholder="GCF_..." /></div>
        <div><label htmlFor="contig_accession">Contig</label><input id="contig_accession" name="contig_accession" defaultValue={searchParams?.contig_accession} placeholder="CP... / NC_..." /></div>
        <div><label htmlFor="locus_tag">Locus tag</label><input id="locus_tag" name="locus_tag" defaultValue={searchParams?.locus_tag} placeholder="SLIV_00320" /></div>
        <div><label htmlFor="gene_id">Stable gene ID</label><input id="gene_id" name="gene_id" defaultValue={searchParams?.gene_id} placeholder="assembly:original-ID" /></div>
        <div><label htmlFor="feature_type">Feature type</label><input id="feature_type" name="feature_type" defaultValue={searchParams?.feature_type} placeholder="gene" /></div>
        <div><label htmlFor="start_min">Start ≥</label><input id="start_min" name="start_min" inputMode="numeric" defaultValue={searchParams?.start_min} placeholder="1" /></div>
        <div><label htmlFor="start_max">Start ≤</label><input id="start_max" name="start_max" inputMode="numeric" defaultValue={searchParams?.start_max} placeholder="100000" /></div>
        <div><label>&nbsp;</label><button className="button primary" type="submit">Filter genes</button></div>
      </form>
      {result.data.length === 0 ? <EmptyState>No genes match these filters.</EmptyState> : <>
        <div className="section-heading"><div><h2>{result.pagination.total.toLocaleString()} matching genes</h2><p>Coordinates are shown as 1-based inclusive intervals from the registered GFF-derived query layer.</p></div></div>
        <div className="table-wrap"><table><thead><tr><th>Gene / locus</th><th>Assembly / contig</th><th>Coordinates</th><th>Strand</th><th>Feature</th><th>Detail / context</th></tr></thead><tbody>{result.data.map((gene) => {
          const location = `${gene.contig_accession}:${gene.start_1based}-${gene.end_1based}`;
          const detailHref = `/genes/${encodeURIComponent(gene.gene_id)}`;
          const assemblyHref = `/assemblies/${encodeURIComponent(gene.assembly_accession)}#${encodeURIComponent(location)}`;
          return <tr key={gene.gene_id}><td><Link href={detailHref}><strong>{gene.locus_tag || gene.gene_name || gene.gene_id}</strong></Link><br /><span className="muted">{gene.gene_id}</span></td><td><Link href={`/assemblies/${encodeURIComponent(gene.assembly_accession)}`}>{gene.assembly_accession}</Link><br /><span className="muted">{gene.contig_accession}</span></td><td>{gene.start_1based.toLocaleString()}–{gene.end_1based.toLocaleString()}</td><td>{gene.strand}</td><td>{gene.feature_type ?? "—"}</td><td><Link href={detailHref}>Details / JBrowse context</Link><br /><Link href={assemblyHref}>Assembly context</Link></td></tr>;
        })}</tbody></table></div>
        <Pagination page={result.pagination.page} hasNext={result.pagination.has_next} makeHref={makeHref} />
      </>}
    </>;
  } catch (reason) {
    return <><PageIntro eyebrow="Catalogue / genes" title="Browse reference genes" /><ErrorState message={reason instanceof ApiClientError ? reason.message : "The gene list could not be loaded."} /></>;
  }
}
