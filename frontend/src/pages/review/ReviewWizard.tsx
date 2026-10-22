import { Navigate, useParams, useSearchParams } from "react-router";

import { ErrorList } from "../../components/ui/Notice";
import Spinner from "../../components/ui/Spinner";
import { apiErrors } from "../../lib/api";
import { formatMonth } from "../../lib/format";
import { useReview } from "../../lib/queries";
import CashStep from "./CashStep";
import CheckStep from "./CheckStep";
import StatementsStep from "./StatementsStep";

const STEPS = ["Accounts and budget", "Statements", "Cash", "Check"];

export default function ReviewWizard() {
  const { id = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const review = useReview(id);

  if (review.isPending) return <Spinner />;
  if (review.isError) return <ErrorList errors={apiErrors(review.error)} />;

  const r = review.data;
  if (r.status === "complete") return <Navigate to={`/reviews/${r.id}/overview`} replace />;

  const step = r.status === "needs_confirmation" ? 3 : params.get("step") === "cash" ? 2 : 1;
  const goTo = (next: "statements" | "cash") => setParams(next === "cash" ? { step: "cash" } : {});

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div>
        <p className="text-sm text-slate-500">Review for {formatMonth(r.month)}</p>
        <ol className="mt-3 grid grid-cols-4 gap-2" aria-label="Progress">
          {STEPS.map((label, i) => (
            <li key={label} aria-current={i === step ? "step" : undefined}>
              <span className={`block h-1.5 rounded-full ${i <= step ? "bg-primary" : "bg-slate-200"}`} />
              <span className={`mt-1.5 block text-xs ${i === step ? "font-medium text-primary" : "text-slate-500"}`}>
                {i + 1}. {label}
              </span>
            </li>
          ))}
        </ol>
      </div>

      {step === 1 && <StatementsStep review={r} onNext={() => goTo("cash")} />}
      {step === 2 && <CashStep review={r} onBack={() => goTo("statements")} />}
      {step === 3 && <CheckStep review={r} />}
    </div>
  );
}
