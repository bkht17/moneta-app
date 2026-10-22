import { useEffect } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router";

import Notice, { ErrorList } from "../../components/ui/Notice";
import Spinner from "../../components/ui/Spinner";
import { apiErrors, firstError } from "../../lib/api";
import { formatDay, formatKzt } from "../../lib/format";
import { useFlags, useReopenReview, useResolveFlag } from "../../lib/queries";
import type { Flag, Resolution, Review } from "../../lib/types";

const QUESTIONS = {
  possible_duplicate: {
    tag: "Possible duplicate",
    question: "Were these two separate purchases?",
    yes: { label: "Yes, two purchases", value: "keep_both" },
    no: { label: "No, the same one twice", value: "same_purchase" },
  },
  possible_own_transfer: {
    tag: "Possible own transfer",
    question: "Is this money moved between your own accounts?",
    yes: { label: "Yes, my own transfer", value: "own_transfer" },
    no: { label: "No, a real payment", value: "not_own_transfer" },
  },
} as const;

export default function CheckStep({ review }: { review: Review }) {
  const navigate = useNavigate();
  const flags = useFlags(review.id, review.status === "needs_confirmation");
  const resolve = useResolveFlag(review.id);
  const reopen = useReopenReview(review.id);

  useEffect(() => {
    if (flags.data && flags.data.length === 0) navigate(`/reviews/${review.id}/overview`, { replace: true });
  }, [flags.data, navigate, review.id]);

  if (flags.isPending) return <Spinner />;
  if (flags.isError) return <ErrorList errors={apiErrors(flags.error)} />;

  const answer = (flag: Flag, resolution: Resolution) =>
    resolve.mutate(
      { flag: flag.id, resolution },
      {
        onSuccess: (data: { review_status: string }) => {
          if (data.review_status === "complete") navigate(`/reviews/${review.id}/overview`);
        },
        onError: (err) => toast.error(firstError(err)),
      },
    );

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">
          {flags.data.length} item{flags.data.length === 1 ? " needs" : "s need"} your answer
        </h1>
        <p className="text-sm text-slate-500">
          We never delete a row only because the date and amount match. Each answer changes your remaining budget, so
          the total stays hidden until they are all in.
        </p>
      </div>

      {flags.data.map((flag) => {
        const q = QUESTIONS[flag.type];
        return (
          <section key={flag.id} className="card space-y-3">
            <span className="chip bg-amber-50 text-amber-700">{q.tag}</span>
            <div className="grid gap-2 sm:grid-cols-2">
              {[flag.first, flag.second].map((tx) => (
                <div key={tx.id} className="rounded-xl bg-slate-50 p-3 text-sm">
                  <p className="font-medium">{tx.description || tx.operation}</p>
                  <p className="text-xs text-slate-500">
                    {formatDay(tx.booked_on)} · {tx.account_label}
                  </p>
                  <p className={`mt-1 font-medium tabular-nums ${tx.amount > 0 ? "text-green-600" : "text-red-500"}`}>
                    {tx.amount > 0 ? "+" : "−"} {formatKzt(Math.abs(tx.amount))}
                  </p>
                </div>
              ))}
            </div>
            <p className="text-sm">{q.question}</p>
            <div className="flex flex-wrap gap-2">
              {[q.yes, q.no].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  className="btn-secondary grow"
                  disabled={resolve.isPending}
                  onClick={() => answer(flag, opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </section>
        );
      })}

      <Notice>Cash withdrawals are never counted as purchases: your cash spending comes from the amount you declared.</Notice>

      <button
        type="button"
        className="cursor-pointer text-sm text-primary underline"
        onClick={() => reopen.mutate()}
        disabled={reopen.isPending}
      >
        Go back to add a statement or change cash
      </button>
    </div>
  );
}
