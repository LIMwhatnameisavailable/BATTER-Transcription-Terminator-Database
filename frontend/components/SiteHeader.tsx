import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="header-inner">
        <Link className="brand" href="/" aria-label="BTED home">
          <span className="brand-mark">BTED</span>
          <span className="brand-name">Bacterial Transcript 3′ End Database</span>
        </Link>
        <nav className="main-nav" aria-label="Main navigation">
          <Link href="/sources">Sources</Link>
          <Link href="/assemblies">Assemblies</Link>
          <Link href="/genes">Genes</Link>
          <Link href="/explore">Explore endpoints</Link>
          <Link href="/augmentation">Augmentation</Link>
        </nav>
        <span className="release-pill">v0.3.0</span>
      </div>
    </header>
  );
}
