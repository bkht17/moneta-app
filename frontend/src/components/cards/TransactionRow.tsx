import type { IconType } from "react-icons";
import {
  LuArrowLeftRight,
  LuBanknote,
  LuBookOpen,
  LuBus,
  LuCoffee,
  LuHeartPulse,
  LuReceipt,
  LuShirt,
  LuShoppingCart,
  LuSmartphone,
  LuTicket,
  LuTrendingDown,
  LuTrendingUp,
  LuTruck,
  LuUndo2,
  LuUser,
} from "react-icons/lu";

import { formatDay, formatKzt } from "../../lib/format";
import type { OverviewTransaction } from "../../lib/types";

const CATEGORY_ICONS: Record<string, IconType> = {
  Groceries: LuShoppingCart,
  "Cafés": LuCoffee,
  "Food delivery": LuTruck,
  Transport: LuBus,
  Study: LuBookOpen,
  Subscriptions: LuReceipt,
  Clothing: LuShirt,
  Health: LuHeartPulse,
  "Mobile and internet": LuSmartphone,
  Entertainment: LuTicket,
  "Transfers to people": LuUser,
  "Cash, unspecified": LuBanknote,
};

const NOTES: Partial<Record<OverviewTransaction["kind"], string>> = {
  own_transfer: "Own-account transfer, not counted",
  withdrawal: "Cash withdrawal, not a purchase",
  refund: "Refund, reduces spending",
  income: "Income",
  transfer_in: "Income",
};

interface Props {
  tx: OverviewTransaction;
  categories?: string[];
  onCategoryChange?: (category: string) => void;
  saving?: boolean;
}

export default function TransactionRow({ tx, categories, onCategoryChange, saving }: Props) {
  const incoming = tx.amount > 0;
  const Icon =
    tx.kind === "own_transfer"
      ? LuArrowLeftRight
      : tx.kind === "withdrawal"
        ? LuBanknote
        : tx.kind === "refund"
          ? LuUndo2
          : CATEGORY_ICONS[tx.category] ?? LuReceipt;
  const note = tx.excluded_reason === "duplicate" ? "Removed: same purchase twice" : NOTES[tx.kind];
  const muted = Boolean(tx.excluded_reason) || tx.kind === "own_transfer" || tx.kind === "withdrawal";

  return (
    <div className={`flex items-center gap-4 rounded-lg p-3 hover:bg-gray-100/60 ${muted ? "opacity-70" : ""}`}>
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-mint text-xl text-primary">
        <Icon />
      </div>
      <div className="flex min-w-0 flex-1 flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <p className={`truncate text-sm font-medium text-gray-700 ${tx.excluded_reason ? "line-through" : ""}`}>
            {tx.description || tx.operation}
          </p>
          <p className="mt-1 flex flex-wrap items-center gap-x-2 text-xs text-gray-400">
            <span>{formatDay(tx.date)}</span>
            <span>· {tx.account.label}</span>
            {note && <span>· {note}</span>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {tx.category_editable && categories && onCategoryChange ? (
            <select
              aria-label={`Category for ${tx.description}`}
              className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs"
              value={tx.category}
              disabled={saving}
              onChange={(e) => onCategoryChange(e.target.value)}
            >
              {categories.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          ) : null}
          <div
            className={`flex items-center gap-2 rounded-md px-3 py-1.5 ${
              incoming ? "bg-green-50 text-green-600" : "bg-red-50 text-red-500"
            }`}
          >
            <h6 className="text-xs font-medium tabular-nums">
              {incoming ? "+" : "−"} {formatKzt(Math.abs(tx.amount))}
            </h6>
            {incoming ? <LuTrendingUp /> : <LuTrendingDown />}
          </div>
        </div>
      </div>
    </div>
  );
}
