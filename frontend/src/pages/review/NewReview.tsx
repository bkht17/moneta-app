import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";

import { ErrorList } from "../../components/ui/Notice";
import Spinner from "../../components/ui/Spinner";
import { apiErrors } from "../../lib/api";
import { firstOfMonth } from "../../lib/format";
import { useAccounts, useCreateReview, useReviews } from "../../lib/queries";
import AccountsAndBudgetForm, { type SetupValues } from "./AccountsAndBudgetForm";

export default function NewReview() {
  const navigate = useNavigate();
  const accounts = useAccounts();
  const reviews = useReviews();
  const createReview = useCreateReview();
  const [errors, setErrors] = useState<{ message: string }[]>([]);

  if (accounts.isPending || reviews.isPending) return <Spinner />;

  const last = reviews.data?.[0];
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
        <h1 className="text-2xl font-semibold">Which accounts do you use this month?</h1>
      </div>
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
