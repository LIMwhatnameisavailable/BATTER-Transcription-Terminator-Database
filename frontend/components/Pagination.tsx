import Link from "next/link";

export function Pagination({ page, hasNext, makeHref }: { page: number; hasNext: boolean; makeHref: (page: number) => string }) {
  if (page <= 1 && !hasNext) return null;
  return <div className="pagination">
    {page > 1 ? <Link className="button secondary" href={makeHref(page - 1)}>Previous</Link> : <span />}
    <span>Page {page}</span>
    {hasNext ? <Link className="button secondary" href={makeHref(page + 1)}>Next</Link> : <span />}
  </div>;
}
