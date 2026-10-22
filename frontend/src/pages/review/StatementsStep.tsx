import { useRef, useState } from "react";
import toast from "react-hot-toast";
import { LuFileUp } from "react-icons/lu";

import Notice, { ErrorList } from "../../components/ui/Notice";
import Spinner from "../../components/ui/Spinner";
import { apiErrors } from "../../lib/api";
import { formatDay, formatKzt } from "../../lib/format";
import { useAccounts, useCoverage, useUpdateReview, useUploadStatement } from "../../lib/queries";
import type { AccountCoverage, ApiError, Review } from "../../lib/types";
import AccountsAndBudgetForm from "./AccountsAndBudgetForm";

const BANK_STYLE = { kaspi: "bg-[#E3262B]", halyk: "bg-[#0B8F4D]" } as const;

export default function StatementsStep({ review, onNext }: { review: Review; onNext: () => void }) {
  const coverage = useCoverage(review.id);
  const accounts = useAccounts();
  const updateReview = useUpdateReview(review.id);
  const [editing, setEditing] = useState(false);
  const [uploadErrors, setUploadErrors] = useState<Record<string, ApiError[]>>({});

  if (coverage.isPending) return <Spinner />;
  if (coverage.isError) return <ErrorList errors={apiErrors(coverage.error)} />;

  const c = coverage.data;
  const missing = c.accounts.filter((a) => !a.covered_until || a.starts_late_on).length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Add a statement for each account</h1>
          <p className="text-sm text-slate-500">
            PDF from the 1st of the month to the latest date your bank shows. Budget {formatKzt(review.budget_kzt)}.
          </p>
        </div>
        <button type="button" className="card-btn" onClick={() => setEditing((v) => !v)}>
          {editing ? "Close" : "Change accounts or budget"}
        </button>
      </div>

      {editing && accounts.data && (
        <AccountsAndBudgetForm
          initial={{ month: review.month, budget: String(Math.round(review.budget_kzt)), accounts: review.accounts }}
          submitLabel="Save changes"
          busy={updateReview.isPending}
          onSubmit={(v) =>
            updateReview.mutate(
              { month: v.month, budget_kzt: Number(v.budget), accounts: v.accounts },
              {
                onSuccess: () => {
                  setEditing(false);
                  coverage.refetch();
                },
                onError: (err) => toast.error(apiErrors(err)[0]?.message ?? "Couldn't save."),
              },
            )
          }
        />
      )}

      {c.accounts.map((account) => (
        <AccountCard
          key={account.id}
          reviewId={review.id}
          account={account}
          errors={uploadErrors[account.id] ?? []}
          setErrors={(errs) => setUploadErrors((e) => ({ ...e, [account.id]: errs }))}
        />
      ))}

      {c.cutoff ? (
        <Notice tone="ok">
          <b>Common date: {formatDay(c.cutoff)}.</b> Your overview will run from {formatDay(review.month)} to{" "}
          {formatDay(c.cutoff)}, the last day every account covers. Later rows are shown separately.
        </Notice>
      ) : (
        <Notice tone="warn">
          {missing === 1 ? "1 account still needs" : `${missing} accounts still need`} a statement starting on{" "}
          {formatDay(review.month)}. The review can't start until every account is covered.
        </Notice>
      )}

      <button type="button" className="btn-primary" disabled={!c.cutoff} onClick={onNext}>
        Continue to cash
      </button>
    </div>
  );
}

function AccountCard({
  reviewId,
  account,
  errors,
  setErrors,
}: {
  reviewId: string;
  account: AccountCoverage;
  errors: ApiError[];
  setErrors: (errors: ApiError[]) => void;
}) {
  const upload = useUploadStatement(reviewId);
  const input = useRef<HTMLInputElement>(null);
  const ok = account.covered_until && !account.starts_late_on;

  const onFile = (file: File | undefined) => {
    if (!file) return;
    setErrors([]);
    upload.mutate(
      { account: account.id, file },
      {
        onSuccess: (s) =>
          toast.success(
            s.new_rows ? `${s.row_count} rows read, ${s.new_rows} new.` : `${s.row_count} rows read, all already imported.`,
          ),
        onError: (err) => setErrors(apiErrors(err)),
        onSettled: () => {
          if (input.current) input.current.value = "";
        },
      },
    );
  };

  return (
    <section className="card space-y-3">
      <div className="flex items-start gap-4">
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl font-semibold text-white ${BANK_STYLE[account.bank]}`}>
          {account.bank === "kaspi" ? "K" : "H"}
        </span>
        <div className="min-w-0 grow">
          <p className="font-medium">{account.label}</p>
          {ok ? (
            <span className="chip mt-1 bg-emerald-50 text-emerald-700">
              Covers {formatDay(account.statements[0]?.period_start)} – {formatDay(account.covered_until)}
            </span>
          ) : account.starts_late_on ? (
            <span className="chip mt-1 bg-red-50 text-red-700">Starts {formatDay(account.starts_late_on)}, needs the 1st</span>
          ) : (
            <span className="chip mt-1 bg-amber-50 text-amber-700">Statement needed</span>
          )}
          {account.gap_after && (
            <p className="mt-1 text-xs text-amber-700">
              Gap after {formatDay(account.gap_after)}: add the missing dates to extend the overview.
            </p>
          )}
          <ul className="mt-2 space-y-0.5 text-xs text-slate-500">
            {account.statements.map((s) => (
              <li key={s.id}>
                {s.file_name} · {formatDay(s.period_start)}–{formatDay(s.period_end)} · {s.row_count} rows
              </li>
            ))}
          </ul>
        </div>
        <input
          ref={input}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          aria-label={`PDF statement for ${account.label}`}
          onChange={(e) => onFile(e.target.files?.[0])}
        />
        <button
          type="button"
          className="add-btn"
          disabled={upload.isPending}
          onClick={() => input.current?.click()}
        >
          <LuFileUp /> {upload.isPending ? "Reading…" : ok ? "Add newer PDF" : "Choose PDF"}
        </button>
      </div>
      <ErrorList errors={errors} />
    </section>
  );
}
