import { ReactNode } from "react";
import { SiteHeader } from "./SiteHeader";

export function PageFrame({ children }: { children: ReactNode }) {
  return (
    <>
      <SiteHeader />
      <main className="page-shell">{children}</main>
      <footer className="site-footer">
        <div className="content-width">
          BTED v0.3 · Public experimental bacterial transcript 3′-end records · Release-aware and provenance-first
        </div>
      </footer>
    </>
  );
}

export function PageIntro({ eyebrow, title, children }: { eyebrow?: string; title: string; children?: ReactNode }) {
  return (
    <div className="page-intro">
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h1>{title}</h1>
      {children && <p className="intro-copy">{children}</p>}
    </div>
  );
}

export function EmptyState({ title = "No records found", children }: { title?: string; children?: ReactNode }) {
  return <div className="empty-state"><strong>{title}</strong>{children && <p>{children}</p>}</div>;
}

export function ErrorState({ message = "The data service is temporarily unavailable." }: { message?: string }) {
  return <div className="error-state"><strong>Unable to load this view</strong><p>{message}</p><p className="muted">Please check the API connection and try again.</p></div>;
}

export function StatusBadge({ value }: { value: string }) {
  const tone = value.includes("published") || value === "author_called_endpoint" || value === "curated_record" ? "good" : value === "audit_only" ? "audit" : "neutral";
  return <span className={`status-badge ${tone}`}>{value.replaceAll("_", " ")}</span>;
}

export function StatCard({ label, value, note }: { label: string; value: string | number; note?: string }) {
  return <div className="stat-card"><span>{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</div>;
}

export function ExternalLink({ href, children }: { href?: string | null; children: ReactNode }) {
  if (!href) return <span className="muted">Not available</span>;
  return <a href={href} target="_blank" rel="noreferrer">{children}</a>;
}

export function ReleaseNote({ release }: { release?: { release_version?: string; status?: string } }) {
  return <p className="release-note">Release <strong>{release?.release_version ?? "v0.3.0"}</strong> · {release?.status ?? "published"}</p>;
}
