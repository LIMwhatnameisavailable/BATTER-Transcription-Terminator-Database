import Link from "next/link";
import { getStats, ApiClientError } from "@/lib/api";
import { ErrorState, PageIntro, StatCard } from "@/components/PageFrame";

export default async function HomePage() {
  let stats;
  let error = false;
  try { stats = await getStats(); } catch (reason) { error = reason instanceof ApiClientError || reason instanceof Error; }

  return <>
    <section className="hero">
      <div>
        <p className="eyebrow">BTED · Release v0.3.0</p>
        <h1>Find experimental bacterial transcript 3′ ends.</h1>
        <p className="hero-copy">Browse public records by reference assembly, source study, or endpoint. Each record stays linked to its paper, raw-data accession, evidence class, and reference sequence.</p>
        <div className="hero-actions"><Link className="button primary" href="/sources">Browse all sources</Link><Link className="button secondary" href="/explore">Explore endpoints</Link></div>
      </div>
      <form className="search-box" action="/assemblies" method="get">
        <label htmlFor="assembly-search">Search by accession</label>
        <div className="search-row"><input id="assembly-search" name="q" placeholder="e.g. GCF_000739105.1" /><button className="button primary" type="submit">Search</button></div>
        <p className="muted">Use a versioned assembly accession to see its organisms, contigs, and independent source tracks.</p>
      </form>
    </section>
    {error || !stats ? <ErrorState message="The catalogue is available when the BTED API is configured. Set BTED_API_ORIGIN for server-side requests." /> : <div className="stat-grid">
      <StatCard label="Sources" value={stats.sources.total} note={`${stats.sources.published_standardized} published · ${stats.sources.audit_only} audit only`} />
      <StatCard label="Public endpoint records" value={stats.endpoints.total.toLocaleString()} note="Four public evidence layers" />
      <StatCard label="Reference assemblies" value={stats.assemblies.total} note="Versioned assemblies" />
      <StatCard label="Augmentation sources" value={stats.augmentation.eligible_sources} note="Source-level eligibility" />
    </div>}
    <section className="section-heading"><div><p className="eyebrow">Start with a question</p><h2>Two ways into the catalogue</h2></div></section>
    <section className="entry-grid">
      <article className="entry-card"><p className="entry-label">Reference context</p><h2><Link href="/assemblies">Search by accession</Link></h2><p>See the organism, strain, versioned assembly, contigs, and separate experimental source tracks mapped to that assembly.</p><Link className="text-action" href="/assemblies">Open assemblies →</Link></article>
      <article className="entry-card"><p className="entry-label">Dataset eligibility</p><h2><Link href="/augmentation">Data augmentation</Link></h2><p>Review the source-level Table S1 eligibility record. This view does not claim that every endpoint entered model training.</p><Link className="text-action" href="/augmentation">Open augmentation sources →</Link></article>
    </section>
  </>;
}
