import { useState } from "react";
import toast from "react-hot-toast";
import { LuCalendarRange, LuHandCoins, LuWallet, LuWalletMinimal } from "react-icons/lu";
import { Link } from "react-router";

import { firstError } from "../lib/api";
import { formatDay, formatKzt, formatMonth } from "../lib/format";
import { useCategories, useSetCategory } from "../lib/queries";
import type { Overview } from "../lib/types";
import InfoCard from "./cards/InfoCard";
import TransactionRow from "./cards/TransactionRow";
import CategoryPieChart from "./charts/CategoryPieChart";
import DailySpendingChart from "./charts/DailySpendingChart";
import Notice from "./ui/Notice";

export default function OverviewView({ overview }: { overview: Overview }) {
  const categories = useCategories();
  const setCategory = useSetCategory(overview.review_id);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const o = overview;
  const outside = o.outside;
  const hasOutside = outside.transactions.length > 0 || (outside.cash ?? 0) > 0;
  const transactions = [...o.transactions].reverse();
  const visible = showAll ? transactions : transactions.slice(0, 8);

  const changeCategory = (id: string, category: string) => {
    setSavingId(id);
    setCategory.mutate(
      { id, category },
      {
        onSuccess: () => toast.success("Category updated. Total spending is unchanged."),
        onError: (err) => toast.error(firstError(err)),
        onSettled: () => setSavingId(null),
      },
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-slate-500">{formatMonth(o.month)}</p>
          <h1 className="text-2xl font-semibold">
            Spending {formatDay(o.period.start)} – {formatDay(o.period.end)}
          </h1>
        </div>
        <Link to="/reviews/new" className="add-btn">
          Start a newer review
        </Link>
      </div>

      {!o.is_current && (
        <Notice tone="warn">
          This overview ends on {formatDay(o.period.end)}, more than a week ago. Upload newer statements to see where
          you are now.
        </Notice>
      )}

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <InfoCard
          icon={<LuWallet />}
          label="Remaining budget"
          value={formatKzt(o.remaining)}
          note={`of ${formatKzt(o.budget)} for ${formatMonth(o.month).split(" ")[0]}`}
          color={o.remaining < 0 ? "bg-red-500 text-white" : "bg-primary text-lime"}
        />
        <InfoCard
          icon={<LuHandCoins />}
          label="Spent"
          value={formatKzt(o.spending)}
          note={`incl. ${formatKzt(o.cash.amount ?? 0)} cash`}
          color="bg-lime text-ink"
        />
        <InfoCard
          icon={<LuWalletMinimal />}
          label="Income"
          value={formatKzt(o.income)}
          note={o.own_transfers ? `${formatKzt(o.own_transfers)} own transfers not counted` : undefined}
          color="bg-emerald-500 text-white"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs">
        <LuCalendarRange className="text-primary" />
        <span className="text-slate-500">Covered:</span>
        {o.accounts.map((a) => (
          <span key={a.id} className="chip bg-mint text-primary">
            {a.label}
            {a.last4 ? ` ••${a.last4}` : ""} · to {formatDay(a.covered_until)}
          </span>
        ))}
        <span className="chip bg-mint text-primary">Cash · declared to {formatDay(o.cash.until)}</span>
      </div>

      {hasOutside && (
        <Notice tone="warn">
          <b>Outside this total: from {formatDay(outside.from)}.</b>{" "}
          {outside.transactions.length > 0 &&
            `${outside.transactions.length} bank rows (${formatKzt(outside.bank_spending)} spent)`}
          {outside.transactions.length > 0 && (outside.cash ?? 0) > 0 && " and "}
          {(outside.cash ?? 0) > 0 && `${formatKzt(outside.cash)} cash`} are not in the remaining budget because not
          every account covers those dates yet. Add newer statements in a new review to include them.
        </Notice>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="card">
          <h5 className="text-lg">Spending by category</h5>
          {o.categories.length ? (
            <CategoryPieChart data={o.categories} label="Total spent" total={formatKzt(o.spending)} />
          ) : (
            <p className="py-10 text-center text-sm text-slate-500">No spending in this period.</p>
          )}
        </section>
        <section className="card">
          <h5 className="text-lg">Spending by day</h5>
          <p className="text-xs text-slate-500">Bank purchases only; cash has no dates.</p>
          <DailySpendingChart data={o.daily} />
        </section>
      </div>

      <section className="card">
        <div className="flex items-center justify-between">
          <h5 className="text-lg">Transactions</h5>
          {transactions.length > 8 && (
            <button type="button" className="card-btn" onClick={() => setShowAll((v) => !v)}>
              {showAll ? "Show fewer" : `Show all ${transactions.length}`}
            </button>
          )}
        </div>
        <p className="mt-1 text-xs text-slate-500">Change a category to fix it. Your total stays the same.</p>
        <div className="mt-3 divide-y divide-gray-100">
          {visible.map((tx) => (
            <TransactionRow
              key={tx.id}
              tx={tx}
              categories={categories.data}
              saving={savingId === tx.id}
              onCategoryChange={(c) => changeCategory(tx.id, c)}
            />
          ))}
        </div>
        {outside.transactions.length > 0 && (
          <div className="mt-5 rounded-xl bg-amber-50/60 p-3">
            <p className="px-3 text-xs font-medium text-amber-700">Not counted yet: after {formatDay(o.period.end)}</p>
            {outside.transactions.map((tx) => (
              <TransactionRow key={tx.id} tx={tx} />
            ))}
          </div>
        )}
      </section>

      <p className="text-xs text-slate-500">
        Remaining budget is your monthly budget minus spending through {formatDay(o.period.end)}. It is not your bank
        balance.
      </p>
    </div>
  );
}
