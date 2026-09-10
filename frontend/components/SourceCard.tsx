import Link from "next/link";
import { Source } from "@/lib/api";
import { ExternalLink, StatusBadge } from "./PageFrame";

export function SourceCard({ source }: { source: Source }) {
  const audit = source.release_status === "audit_only";
  return (
    <article className="source-card">
      <div className="source-card-top">
        <div>
          <p className="record-id">{source.source_id}</p>
          <h2><Link href={`/sources/${encodeURIComponent(source.source_id)}`}>{source.species}</Link></h2>
          <p className="muted">{source.assembly?.accession ?? "Assembly not recorded"}{source.assembly?.strain ? ` · ${source.assembly.strain}` : ""}</p>
        </div>
        <StatusBadge value={source.release_status} />
      </div>
      <dl className="compact-facts">
        <div><dt>Experiment</dt><dd>{source.assay_family}</dd></div>
        <div><dt>Evidence</dt><dd>{source.evidence_class.replaceAll("_", " ")}</dd></div>
        <div><dt>Records</dt><dd>{source.record_count.toLocaleString()}</dd></div>
        <div><dt>Publication</dt><dd>{source.publication?.year ?? "—"} · {source.publication?.journal ?? "—"}</dd></div>
      </dl>
      <div className="card-actions">
        <Link className="button secondary" href={`/sources/${encodeURIComponent(source.source_id)}`}>View source</Link>
        {!audit && source.links?.endpoints_download && <a className="text-action" href={source.links.endpoints_download}>Download endpoints</a>}
        {!audit && source.links?.jbrowse && <a className="text-action" href={source.links.jbrowse}>Open browser</a>}
        {audit && <span className="muted">Metadata audit only</span>}
      </div>
      {source.accessions?.length > 0 && <p className="accession-line">Raw data: {source.accessions.map((item) => <ExternalLink key={`${item.namespace}-${item.accession}`} href={item.url}>{item.accession ?? "accession"}</ExternalLink>)}</p>}
    </article>
  );
}
