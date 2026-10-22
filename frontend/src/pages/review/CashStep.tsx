import { useState, type FormEvent } from "react";

import Input from "../../components/ui/Input";
import { ErrorList } from "../../components/ui/Notice";
import Spinner from "../../components/ui/Spinner";
import { apiErrors } from "../../lib/api";
import { digitsOnly, formatDay, formatKzt } from "../../lib/format";
import { useCoverage, useSubmitReview } from "../../lib/queries";
import type { ApiError, Review } from "../../lib/types";

export default function CashStep({ review, onBack }: { review: Review; onBack: () => void }) {
  const coverage = useCoverage(review.id);
  const submit = useSubmitReview(review.id);
  // No default: an empty field means "not declared yet", never 0 (F1).
  const [cash, setCash] = useState(review.cash_kzt != null ? String(Math.round(review.cash_kzt)) : "");
  const [touched, setTouched] = useState(false);
  const [showLater, setShowLater] = useState(false);
  const [laterCash, setLaterCash] = useState("");
  const [laterUntil, setLaterUntil] = useState("");
  const [errors, setErrors] = useState<ApiError[]>([]);

  if (coverage.isPending) return <Spinner />;
  const cutoff = coverage.data?.cutoff;
  const blank = cash === "";

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setTouched(true);
    setErrors([]);
    submit.mutate(
      {
        cash_kzt: cash,
        later_cash_kzt: showLater && laterCash ? laterCash : undefined,
        later_cash_until: showLater && laterCash ? laterUntil || null : undefined,
      },
      { onError: (err) => setErrors(apiErrors(err)) },
    );
  };

  return (
    <form className="space-y-4" onSubmit={onSubmit} noValidate>
      <h1 className="text-2xl font-semibold">
        How much cash did you spend from {formatDay(review.month)} to {formatDay(cutoff)}?
      </h1>

      <div className="card">
        <Input
          label={`Cash spent, ${formatDay(review.month)} – ${formatDay(cutoff)}`}
          inputMode="numeric"
          placeholder="Amount"
          value={cash}
          suffix="₸"
          onChange={(v) => {
            setCash(digitsOnly(v));
            setTouched(true);
          }}
          error={touched && blank ? "Enter an amount, or 0 if you spent no cash. A blank field can't be counted." : null}
          hint="Your best total for this period. Cash withdrawals from the bank are not counted twice."
        />
        <div className="flex flex-wrap gap-2">
          <button type="button" className="card-btn" onClick={() => setCash("0")}>
            I spent no cash (0)
          </button>
        </div>

        <button type="button" className="mt-4 cursor-pointer text-sm text-primary underline" onClick={() => setShowLater((v) => !v)}>
          {showLater ? "Remove" : "Add"} cash spent after {formatDay(cutoff)} (optional)
        </button>
        {showLater && (
          <div className="mt-3 grid gap-x-4 sm:grid-cols-2">
            <Input label="Cash spent after the common date" inputMode="numeric" value={laterCash} suffix="₸" onChange={(v) => setLaterCash(digitsOnly(v))} />
            <Input
              label="Up to which date?"
              type="date"
              value={laterUntil}
              min={cutoff ?? undefined}
              onChange={setLaterUntil}
              hint="Kept outside the main total until every account covers these dates."
            />
          </div>
        )}
      </div>

      <div className="card text-sm">
        <p className="font-medium">Before we calculate</p>
        <ul className="mt-2 space-y-1 text-slate-600">
          {coverage.data?.accounts.map((a) => (
            <li key={a.id}>✓ {a.label} covered to {formatDay(a.covered_until)}</li>
          ))}
          <li>✓ Budget {formatKzt(review.budget_kzt)}</li>
          <li className={blank ? "text-red-600" : ""}>{blank ? "✗ Cash amount missing" : `✓ Cash ${formatKzt(Number(cash))}`}</li>
        </ul>
      </div>

      <ErrorList errors={errors} />

      <div className="flex gap-3">
        <button type="button" className="btn-secondary" onClick={onBack}>
          Back
        </button>
        <button type="submit" className="btn-primary" disabled={submit.isPending}>
          {submit.isPending ? "Calculating…" : "Calculate my overview"}
        </button>
      </div>
    </form>
  );
}
