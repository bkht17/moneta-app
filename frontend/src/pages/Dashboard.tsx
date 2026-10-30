import { LuFileText, LuLayers, LuWallet } from "react-icons/lu";
import { Link } from "react-router";

import OverviewView from "../components/OverviewView";
import { ErrorList } from "../components/ui/Notice";
import Spinner from "../components/ui/Spinner";
import { apiErrors } from "../lib/api";
import { formatMonth } from "../lib/format";
import { useOverview, useReviews } from "../lib/queries";

export default function Dashboard() {
  const reviews = useReviews();
  const latestComplete = reviews.data?.find((r) => r.status === "complete");
  const unfinished = reviews.data?.find((r) => r.status !== "complete");
  const overview = useOverview(latestComplete?.id);

  if (reviews.isPending) return <Spinner />;
  if (reviews.isError) return <ErrorList errors={apiErrors(reviews.error)} />;

  return (
    <div className="space-y-6">
      {unfinished && (!latestComplete || unfinished.created_at > latestComplete.created_at) && (
        <div className="card flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-medium">Unfinished draft for {formatMonth(unfinished.month)}</p>
            <p className="text-sm text-slate-500">
              {unfinished.status === "needs_confirmation"
                ? `${unfinished.open_flags} item(s) need your answer before the total is shown.`
                : "Add the remaining statements and your cash amount."}
            </p>
          </div>
          <Link to={`/reviews/${unfinished.id}`} className="add-btn">
            Continue draft
          </Link>
        </div>
      )}

      {latestComplete ? (
        overview.isPending ? (
          <Spinner label="Calculating your overview" />
        ) : overview.isError ? (
          <ErrorList errors={apiErrors(overview.error)} />
        ) : (
          <OverviewView overview={overview.data} />
        )
      ) : (
        !unfinished && <EmptyState />
      )}
    </div>
  );
}

function EmptyState() {
  const steps = [
    { icon: LuLayers, title: "Declare your accounts and budget", text: "Kaspi Gold, Halyk card and how much you plan to spend this month." },
    { icon: LuFileText, title: "Upload this month's PDF statements", text: "From the 1st of the month. We read them once and don't keep the files." },
    { icon: LuWallet, title: "Add cash and see what is left", text: "One total across banks and cash, with the dates it covers." },
  ];
  return (
    <div className="card mx-auto max-w-3xl">
      <h1 className="text-2xl font-semibold">Your first combined review</h1>
      <p className="mt-1 text-sm text-slate-500">It takes a few minutes and is free.</p>
      <ol className="mt-6 space-y-4">
        {steps.map((s, i) => (
          <li key={s.title} className="flex gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-mint text-xl text-primary">
              <s.icon />
            </span>
            <span>
              <span className="block font-medium">
                {i + 1}. {s.title}
              </span>
              <span className="text-sm text-slate-500">{s.text}</span>
            </span>
          </li>
        ))}
      </ol>
      <Link to="/reviews/new" className="btn-primary mt-6 block text-center">
        Start my review
      </Link>
    </div>
  );
}
