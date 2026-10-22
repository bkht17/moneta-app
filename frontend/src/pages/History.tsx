import { Link } from "react-router";

import { ErrorList } from "../components/ui/Notice";
import Spinner from "../components/ui/Spinner";
import { apiErrors } from "../lib/api";
import { formatDay, formatKzt, formatMonth } from "../lib/format";
import { useReviews } from "../lib/queries";
import type { ReviewStatus } from "../lib/types";

const STATUS: Record<ReviewStatus, { label: string; style: string }> = {
  draft: { label: "Adding inputs", style: "bg-amber-50 text-amber-700" },
  needs_confirmation: { label: "Needs your answers", style: "bg-amber-50 text-amber-700" },
  complete: { label: "Complete", style: "bg-emerald-50 text-emerald-700" },
};

export default function History() {
  const reviews = useReviews();

  if (reviews.isPending) return <Spinner />;
  if (reviews.isError) return <ErrorList errors={apiErrors(reviews.error)} />;

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-semibold">Your reviews</h1>
      {!reviews.data.length && (
        <p className="text-sm text-slate-500">
          No reviews yet. <Link to="/reviews/new" className="text-primary underline">Start your first one.</Link>
        </p>
      )}
      <div className="card divide-y divide-gray-100 p-0">
        {reviews.data.map((r) => (
          <Link
            key={r.id}
            to={r.status === "complete" ? `/reviews/${r.id}/overview` : `/reviews/${r.id}`}
            className="flex flex-wrap items-center justify-between gap-3 p-5 hover:bg-mint/50"
          >
            <div>
              <p className="font-medium">{formatMonth(r.month)}</p>
              <p className="text-xs text-slate-500">
                Started {new Date(r.created_at).toLocaleDateString("en-GB")}
                {r.cutoff_date && ` · covers to ${formatDay(r.cutoff_date)}`} · budget {formatKzt(r.budget_kzt)}
              </p>
            </div>
            <span className={`chip ${STATUS[r.status].style}`}>{STATUS[r.status].label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
