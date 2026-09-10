import Link from "next/link";
import { getAugmentation, ApiClientError } from "@/lib/api";
import { EmptyState, ErrorState, PageIntro, ReleaseNote, StatusBadge } from "@/components/PageFrame";
import { Pagination } from "@/components/Pagination";

export default async function AugmentationPage({ searchParams }: { searchParams?: { page?: string } }) {
  const page = Math.max(1, Number(searchParams?.page ?? "1") || 1);
  try {
    const result = await getAugmentation({ page, page_size: 50 });
    const makeHref = (nextPage: number) => `/augmentation?page=${nextPage}`;
    return <>
      <PageIntro eyebrow="Catalogue / data augmentation" title="Augmentation sources"><span>This is a source-level view of the Table S1 eligibility flag. It records which sources were marked for augmentation; it does not claim that every endpoint entered model training.</span></PageIntro>
      <ReleaseNote release={result.release} />
      <div className="notice"><strong>Interpretation boundary</strong>Eligibility is attached to a source, not to individual endpoint records. Prediction-only or mixed-evidence records are not silently added to the public endpoint catalogue.</div>
      {result.data.length === 0 ? <EmptyState>No augmentation-eligible sources are listed in this release.</EmptyState> : <>
        <div className="section-heading"><div><h2>{result.eligible_source_count} eligible sources</h2><p>{result.training_claim}</p></div></div>
        <div className="table-wrap"><table><thead><tr><th>Source</th><th>Organism / strain</th><th>Assembly</th><th>Publication</th><th>Evidence</th><th>Records</th><th /></tr></thead><tbody>{result.data.map((source) => <tr key={source.source_id}><td><Link href={`/sources/${encodeURIComponent(source.source_id)}`}><strong>{source.source_id}</strong></Link></td><td>{source.species}<br /><span className="muted">{source.assembly?.strain ?? "Strain not recorded"}</span></td><td>{source.assembly?.accession ?? "—"}</td><td>{source.publication?.year ?? "—"}<br /><span className="muted">{source.publication?.journal ?? "—"}</span></td><td><StatusBadge value={source.evidence_class} /></td><td>{source.record_count.toLocaleString()}</td><td><Link href={`/sources/${encodeURIComponent(source.source_id)}`}>View source</Link></td></tr>)}</tbody></table></div>
        <Pagination page={result.pagination.page} hasNext={result.pagination.has_next} makeHref={makeHref} />
      </>}
    </>;
  } catch (reason) { return <><PageIntro eyebrow="Catalogue / data augmentation" title="Augmentation sources" /><ErrorState message={reason instanceof ApiClientError ? reason.message : "The augmentation list could not be loaded."} /></>; }
}
