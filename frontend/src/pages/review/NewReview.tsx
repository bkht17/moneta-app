import { useState, type FormEvent } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router";

import Notice, { ErrorList } from "../../components/ui/Notice";
import Spinner from "../../components/ui/Spinner";
import { apiErrors } from "../../lib/api";
import { firstOfMonth, formatMonth } from "../../lib/format";
import { useAccounts, useCreateReview, useDeleteReview, useReviews } from "../../lib/queries";
import AccountsAndBudgetForm, { type SetupValues } from "./AccountsAndBudgetForm";

export default function NewReview() {
  const navigate = useNavigate();
  const accounts = useAccounts();
  const reviews = useReviews();
  const createReview = useCreateReview();
  const deleteReview = useDeleteReview();
  const [errors, setErrors] = useState<{ message: string }[]>([]);

  if (accounts.isPending || reviews.isPending) return <Spinner />;

  const last = reviews.data?.[0];
  const draft = reviews.data?.find((r) => r.status !== "complete");
  const initial: SetupValues = {
    month: firstOfMonth(),
    budget: last ? String(Math.round(last.budget_kzt)) : "",
    accounts: last?.accounts ?? accounts.data?.map((a) => a.id) ?? [],
  };

  const submit = (values: SetupValues, e?: FormEvent) => {
    e?.preventDefault();
    setErrors([]);
    createReview.mutate(
      { month: values.month, budget_kzt: Number(values.budget), accounts: values.accounts },
      {
        onSuccess: (review) => navigate(`/reviews/${review.id}`),
        onError: (err) => setErrors(apiErrors(err)),
      },
    );
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <p className="text-sm text-slate-500">Step 1 of 4</p>
        <h1 className="text-2xl font-semibold">Which accounts do you want to review?</h1>
        <p className="text-sm text-slate-500">One account is enough. Add more if you spent from several.</p>
      </div>
      {draft && (
        <Notice tone="warn">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span>
              You have an unfinished draft for {formatMonth(draft.month)}. It is not saved as a result until you
              finish it.
            </span>
            <span className="flex gap-2">
              <Link to={`/reviews/${draft.id}`} className="add-btn">
                Continue draft
              </Link>
              <button
                type="button"
                className="btn-secondary"
                disabled={deleteReview.isPending}
                onClick={() => deleteReview.mutate(draft.id, { onSuccess: () => toast.success("Draft discarded.") })}
              >
                Discard draft
              </button>
            </span>
          </div>
        </Notice>
      )}
      <ErrorList errors={errors} />
      <AccountsAndBudgetForm
        initial={initial}
        submitLabel="Continue to statements"
        busy={createReview.isPending}
        onSubmit={submit}
      />
    </div>
  );
}
