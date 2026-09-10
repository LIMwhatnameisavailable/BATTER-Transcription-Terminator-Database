import Link from "next/link";
import { notFound } from "next/navigation";
import { getSource, ApiClientError, Source } from "@/lib/api";
import { ExternalLink, ErrorState, PageIntro, ReleaseNote, StatusBadge } from "@/components/PageFrame";

function SourceLinks({ source }: { source: Source }) {
  const publication = source.publication ?? {};
  return <ul className="link-list">
    <li><ExternalLink href={publication.links?.pubmed}>PubMed</ExternalLink></li>
    <li><ExternalLink href={publication.links?.doi}>{publication.doi ?? "DOI"}</ExternalLink></li>
    <li><ExternalLink href={publication.links?.pmc}>{publication.pmc ?? "PMC"}</ExternalLink></li>
    {source.accessions.map((item) => <li key={`${item.namespace}-${item.accession}`}><ExternalLink href={item.url}>{item.namespace ?? "Repository"}: {item.accession}</ExternalLink></li>)}
  </ul>;
}

export default async function SourceDetailPage({ params }: { params: { sourceId: string } }) {
  let source;
  try { source = await getSource(decodeURIComponent(params.sourceId)); }
  catch (reason) { if (reason instanceof ApiClientError && reason.status === 404) notFound(); return <ErrorState message="The source record could not be loaded." />; }
  const audit = source.release_status === "audit_only";
  return <>
    <PageIntro eyebrow={`Source / ${source.source_id}`} title={source.species}><span>{source.assay_family} · {source.evidence_class.replaceAll("_", " ")}</span></PageIntro>
    <ReleaseNote release={source.release} />
    <div className="detail-grid">
      <div>
        {audit && <div className="notice"><strong>Metadata audit only</strong>This source is retained for provenance, but it has no publishable endpoint table or JBrowse entry.</div>}
        <section className="panel"><div className="source-card-top"><h2>Dataset summary</h2><StatusBadge value={source.release_status} /></div><dl className="facts">
          <div><dt>Species</dt><dd>{source.species}</dd></div><div><dt>Strain</dt><dd>{source.assembly?.strain ?? "Not recorded"}</dd></div>
          <div><dt>Assembly</dt><dd>{source.assembly?.accession ?? "Not recorded"}</dd></div><div><dt>Experiment</dt><dd>{source.assay_family}</dd></div>
          <div><dt>Evidence</dt><dd>{source.evidence_class.replaceAll("_", " ")}</dd></div><div><dt>Records</dt><dd>{source.record_count.toLocaleString()}</dd></div>
          <div><dt>Redistribution</dt><dd>{source.redistribution_status ?? "Not recorded"}</dd></div><div><dt>Augmentation</dt><dd>{source.augmentation_eligible ? "Eligible source" : "Not eligible"}</dd></div>
        </dl></section>
        <section className="panel"><h2>Publication</h2><p><strong>{source.publication.title ?? "Title not recorded"}</strong></p><p className="muted">{source.publication.journal ?? "Journal not recorded"} · {source.publication.year ?? "Year not recorded"}</p><SourceLinks source={source} /></section>
        {(source.known_limitations || source.decision_note || source.source_note) && <section className="panel"><h2>Curatorial notes</h2>{source.decision_note && <p>{source.decision_note}</p>}{source.known_limitations && <p className="muted">{source.known_limitations}</p>}{source.source_note && <p className="muted">{source.source_note}</p>}</section>}
      </div>
      <aside>
        <section className="panel"><h2>Use this source</h2><ul className="link-list">
          {!audit && source.links.endpoints_download && <li><a href={source.links.endpoints_download}>Download endpoint table</a></li>}
          {!audit && source.links.jbrowse && <li><a href={source.links.jbrowse}>Open JBrowse context</a></li>}
          {audit && <li className="muted">Endpoint download unavailable</li>}
          {audit && <li className="muted">JBrowse unavailable</li>}
          {source.links.manifest && <li><a href={source.links.manifest}>View source manifest</a></li>}
        </ul></section>
        <section className="panel"><h2>Record identity</h2><dl className="facts"><div><dt>Source ID</dt><dd>{source.source_id}</dd></div><div><dt>Release</dt><dd>{source.release?.release_version}</dd></div></dl><p className="muted">The source ID is stable within this release and keeps this study separate from other tracks on the same assembly.</p></section>
      </aside>
    </div>
    <p className="back-link"><Link href="/sources">← Back to sources</Link></p>
  </>;
}
