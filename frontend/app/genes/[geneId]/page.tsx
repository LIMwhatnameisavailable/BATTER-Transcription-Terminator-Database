import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiClientError, Gene, getAssembly, getEndpoints, getGene, Release } from "@/lib/api";
import { ErrorState, PageIntro, ReleaseNote } from "@/components/PageFrame";

function valueText(value: unknown): string {
  return value === null || value === undefined || value === "" ? "—" : typeof value === "object" ? JSON.stringify(value) : String(value);
}

function productText(attributes: Gene["attributes"]): string {
  const product = attributes?.product;
  return typeof product === "string" && product ? product : "Not recorded";
}

function jbrowseHref(href: string | null | undefined, location: string): string | null {
  if (!href) return null;
  const [path, query = ""] = href.split("?", 2);
  const params = new URLSearchParams(query);
  params.set("loc", location);
  return `${path}?${params.toString()}`;
}

export default async function GeneDetailPage({ params }: { params: { geneId: string } }) {
  let gene: { release: Release } & Gene;
  try {
    gene = await getGene(decodeURIComponent(params.geneId));
  } catch (reason) {
    if (reason instanceof ApiClientError && reason.status === 404) notFound();
    return <ErrorState message="The gene record could not be loaded." />;
  }

  const windowStart = Math.max(1, gene.start_1based - 500);
  const windowEnd = gene.end_1based + 500;
  const location = `${gene.contig_accession}:${windowStart}-${windowEnd}`;
  const relatedLabel = gene.locus_tag || gene.gene_id;

  const [assemblyResult, endpointResult] = await Promise.all([
    getAssembly(gene.assembly_accession).catch(() => null),
    getEndpoints({
      assembly_accession: gene.assembly_accession,
      contig_accession: gene.contig_accession,
      gene_or_locus: relatedLabel,
      page: 1,
      page_size: 1,
    }).catch(() => null),
  ]);
  const assemblyHref = `/assemblies/${encodeURIComponent(gene.assembly_accession)}#${encodeURIComponent(location)}`;
  const browserHref = jbrowseHref(assemblyResult?.links?.jbrowse, location);

  return <>
    <PageIntro eyebrow="Gene record" title={gene.locus_tag || gene.gene_id}>
      <span>{gene.gene_name || "Name not recorded"} · {gene.feature_type || "Feature type not recorded"}</span>
    </PageIntro>
    <ReleaseNote release={gene.release} />
    <div className="detail-grid"><div>
      <section className="panel"><h2>Gene identity</h2><dl className="facts">
        <dt>Gene ID</dt><dd>{gene.gene_id}</dd>
        <dt>Locus tag</dt><dd>{valueText(gene.locus_tag)}</dd>
        <dt>Name</dt><dd>{valueText(gene.gene_name)}</dd>
        <dt>Product</dt><dd>{productText(gene.attributes)}</dd>
        <dt>Feature type</dt><dd>{valueText(gene.feature_type)}</dd>
      </dl></section>
      <section className="panel"><h2>Reference interval</h2><dl className="facts">
        <dt>Assembly</dt><dd><Link href={assemblyHref}>{gene.assembly_accession}</Link></dd>
        <dt>Contig</dt><dd>{gene.contig_accession}{gene.contig_name ? ` · ${gene.contig_name}` : ""}</dd>
        <dt>Coordinates</dt><dd>{gene.start_1based.toLocaleString()}–{gene.end_1based.toLocaleString()} (1-based)</dd>
        <dt>Strand</dt><dd>{gene.strand}</dd>
        <dt>Browser window</dt><dd>{location}</dd>
      </dl></section>
      <section className="panel"><h2>Related endpoints</h2>
        {endpointResult ? <><p>{endpointResult.pagination.total.toLocaleString()} endpoint{endpointResult.pagination.total === 1 ? "" : "s"} are associated with <strong>{relatedLabel}</strong> on this assembly and contig.</p><Link href={`/explore?assembly_accession=${encodeURIComponent(gene.assembly_accession)}&contig_accession=${encodeURIComponent(gene.contig_accession)}&gene_or_locus=${encodeURIComponent(relatedLabel)}`}>Explore related endpoints</Link></> : <p className="muted">Endpoint associations are not available from the current API query.</p>}
      </section>
      <section className="panel"><h2>Annotation provenance</h2><dl className="facts">
        <dt>Annotation asset</dt><dd>{valueText(gene.annotation_asset_id)}</dd>
        <dt>Annotation SHA-256</dt><dd>{valueText(gene.annotation_sha256)}</dd>
      </dl></section>
    </div><aside>
      <section className="panel"><h2>Browse this region</h2><p className="muted">Open the shared assembly context or JBrowse around this gene with a 500 bp flank on each side.</p><ul className="link-list"><li><Link href={assemblyHref}>View assembly context</Link></li>{browserHref ? <li><a href={browserHref}>Open JBrowse (±500 bp)</a></li> : <li className="muted">JBrowse unavailable</li>}</ul></section>
    </aside></div>
  </>;
}
