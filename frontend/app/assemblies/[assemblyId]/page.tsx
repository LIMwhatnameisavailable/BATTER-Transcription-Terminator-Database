import Link from "next/link";
import { notFound } from "next/navigation";
import { getAssembly, ApiClientError } from "@/lib/api";
import { ErrorState, PageIntro, ReleaseNote } from "@/components/PageFrame";

export default async function AssemblyDetailPage({ params }: { params: { assemblyId: string } }) {
  let assembly;
  try { assembly = await getAssembly(decodeURIComponent(params.assemblyId)); }
  catch (reason) { if (reason instanceof ApiClientError && reason.status === 404) notFound(); return <ErrorState message="The assembly record could not be loaded." />; }
  return <>
    <PageIntro eyebrow="Assembly / reference context" title={assembly.assembly_accession}><span>{assembly.organism_name ?? "Organism not recorded"}{assembly.strain ? ` · ${assembly.strain}` : ""}</span></PageIntro>
    <ReleaseNote release={assembly.release} />
    <div className="detail-grid"><div>
      <section className="panel"><h2>Assembly summary</h2><dl className="facts"><div><dt>Assembly</dt><dd>{assembly.assembly_accession}</dd></div><div><dt>Organism</dt><dd>{assembly.organism_name ?? "Not recorded"}</dd></div><div><dt>Strain</dt><dd>{assembly.strain ?? "Not recorded"}</dd></div><div><dt>Contigs</dt><dd>{assembly.contigs.length}</dd></div><div><dt>Source tracks</dt><dd>{assembly.source_count}</dd></div><div><dt>Genes</dt><dd><Link href={`/genes?assembly_accession=${encodeURIComponent(assembly.assembly_accession)}`}>{assembly.gene_count.toLocaleString()}</Link></dd></div><div><dt>Endpoint records</dt><dd>{assembly.endpoint_count.toLocaleString()}</dd></div></dl></section>
      <section className="panel"><h2>Contigs</h2><div className="table-wrap"><table><thead><tr><th>Contig</th><th>Name</th><th>Length (bp)</th><th>Explore</th></tr></thead><tbody>{assembly.contigs.map((contig) => <tr key={contig.accession}><td><strong>{contig.accession}</strong></td><td>{contig.name ?? "—"}</td><td>{contig.length_bp?.toLocaleString() ?? "Not recorded"}</td><td><Link href={`/explore?assembly_accession=${encodeURIComponent(assembly.assembly_accession)}&contig_accession=${encodeURIComponent(contig.accession)}`}>Explore endpoints</Link></td></tr>)}</tbody></table></div></section>
      <section className="panel"><h2>Independent source tracks</h2><div className="track-list">{assembly.source_tracks.map((track) => <div className="track" key={track.source_id}><div><Link href={`/sources/${encodeURIComponent(track.source_id)}`}><strong>{track.source_id}</strong></Link><small>{track.record_count?.toLocaleString() ?? "—"} endpoint records</small></div><Link href={`/explore?assembly_accession=${encodeURIComponent(assembly.assembly_accession)}&source_id=${encodeURIComponent(track.source_id)}`}>Explore track</Link></div>)}</div></section>
    </div><aside><section className="panel"><h2>How to use this page</h2><p className="muted">The assembly is the shared coordinate context. Source tracks remain independent because they come from different studies, samples, or evidence definitions.</p>{assembly.links?.jbrowse && <a className="button primary" href={assembly.links.jbrowse}>Open JBrowse</a>}<Link className="button secondary" href={`/explore?assembly_accession=${encodeURIComponent(assembly.assembly_accession)}`}>Explore this assembly</Link></section></aside></div>
    <p className="back-link"><Link href="/assemblies">← Back to assemblies</Link></p>
  </>;
}
