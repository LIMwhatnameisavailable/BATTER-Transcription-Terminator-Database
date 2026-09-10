"use client";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <div className="error-state"><strong>Unable to load this page</strong><p>The BTED API did not return a usable response.</p><button className="button primary" onClick={() => reset()}>Try again</button></div>;
}
