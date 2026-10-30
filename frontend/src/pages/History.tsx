import { useState } from "react";
import toast from "react-hot-toast";
import { LuFileText } from "react-icons/lu";
import { Link } from "react-router";

import Modal from "../components/ui/Modal";
import { ErrorList } from "../components/ui/Notice";
import Spinner from "../components/ui/Spinner";
import { apiErrors, firstError } from "../lib/api";
import { formatDay, formatKzt, formatMonth } from "../lib/format";
import { useDeleteReview, useReviews } from "../lib/queries";
import type { Review } from "../lib/types";

/** "October 2026 · Kaspi Gold + Halyk card" */
function reviewName(r: Review) {
  const accounts = r.sources.map((s) => s.label).join(" + ");
  return accounts ? `${formatMonth(r.month)} · ${accounts}` : formatMonth(r.month);
}

export default function History() {
  const reviews = useReviews();
  const deleteReview = useDeleteReview();
  const [discarding, setDiscarding] = useState<Review | null>(null);

  if (reviews.isPending) return <Spinner />;
  if (reviews.isError) return <ErrorList errors={apiErrors(reviews.error)} />;

  const completed = reviews.data.filter((r) => r.status === "complete");
  const drafts = reviews.data.filter((r) => r.status !== "complete");

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <section className="space-y-3">
        <div>
          <h1 className="text-2xl font-semibold">Completed reviews</h1>
          <p className="text-sm text-slate-500">Finished reviews with a calculated total. Open one to see its overview.</p>
        </div>
        {!completed.length && (
          <p className="card text-sm text-slate-500">
            No completed reviews yet.{" "}
            <Link to="/reviews/new" className="text-primary underline">
              Start a review
            </Link>{" "}
            and finish all four steps to see it here.
          </p>
        )}
        {completed.map((r) => (
          <Link key={r.id} to={`/reviews/${r.id}/overview`} className="card block space-y-3 hover:border-primary/40">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-medium">{reviewName(r)}</p>
                <p className="text-xs text-slate-500">
                  Covers {formatDay(r.month)} – {formatDay(r.cutoff_date)} · budget {formatKzt(r.budget_kzt)} · finished{" "}
                  {r.completed_at ? new Date(r.completed_at).toLocaleDateString("en-GB") : "—"}
                </p>
              </div>
              <span className="chip bg-emerald-50 text-emerald-700">Complete</span>
            </div>
            <Sources review={r} />
          </Link>
        ))}
      </section>

      {drafts.length > 0 && (
        <section className="space-y-3">
          <div>
            <h2 className="text-lg font-semibold">Unfinished drafts</h2>
            <p className="text-sm text-slate-500">
              Not results yet. Continue a draft to finish it, or discard it.
            </p>
          </div>
          {drafts.map((r) => (
            <div key={r.id} className="space-y-3 rounded-2xl border border-dashed border-amber-300 bg-amber-50/40 p-5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-medium">{reviewName(r)}</p>
                  <p className="text-xs text-slate-500">
                    Started {new Date(r.created_at).toLocaleDateString("en-GB")} ·{" "}
                    {r.status === "needs_confirmation"
                      ? `${r.open_flags} item(s) waiting for your answer`
                      : "statements or cash still missing"}
                  </p>
                </div>
                <span className="chip bg-amber-100 text-amber-800">Draft</span>
              </div>
              <Sources review={r} />
              <div className="flex gap-2">
                <Link to={`/reviews/${r.id}`} className="add-btn">
                  Continue draft
                </Link>
                <button type="button" className="btn-secondary" onClick={() => setDiscarding(r)}>
                  Discard
                </button>
              </div>
            </div>
          ))}
        </section>
      )}

      <Modal isOpen={Boolean(discarding)} onClose={() => setDiscarding(null)} title="Discard this draft?">
        <p className="text-sm">
          The draft for {discarding && reviewName(discarding)} will be removed. Statements you uploaded stay with your
          accounts and can be used in a new review.
        </p>
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-secondary" onClick={() => setDiscarding(null)}>
            Keep it
          </button>
          <button
            type="button"
            className="cursor-pointer rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white"
            disabled={deleteReview.isPending}
            onClick={() =>
              discarding &&
              deleteReview.mutate(discarding.id, {
                onSuccess: () => {
                  toast.success("Draft discarded.");
                  setDiscarding(null);
                },
                onError: (err) => toast.error(firstError(err)),
              })
            }
          >
            Discard draft
          </button>
        </div>
      </Modal>
    </div>
  );
}

function Sources({ review }: { review: Review }) {
  return (
    <ul className="flex flex-wrap gap-2">
      {review.sources.map((s) => (
        <li key={s.id} className="flex items-center gap-2 rounded-lg bg-mint px-3 py-1.5 text-xs text-ink">
          <LuFileText className="shrink-0 text-primary" />
          <span className="font-medium">
            {s.label}
            {s.last4 ? ` ••${s.last4}` : ""}
          </span>
          <span className="text-slate-500">
            {s.statements.length
              ? s.statements
                  .map((st) => `${st.file_name} (${formatDay(st.period_start)}–${formatDay(st.period_end)})`)
                  .join(", ")
              : "no statement yet"}
          </span>
        </li>
      ))}
    </ul>
  );
}
