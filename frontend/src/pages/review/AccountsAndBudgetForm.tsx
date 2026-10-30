import { useState, type FormEvent } from "react";
import toast from "react-hot-toast";
import { LuPlus } from "react-icons/lu";

import Input from "../../components/ui/Input";
import { firstError } from "../../lib/api";
import { digitsOnly } from "../../lib/format";
import { useAccounts, useCreateAccount } from "../../lib/queries";
import type { Bank } from "../../lib/types";

export interface SetupValues {
  month: string;
  budget: string;
  accounts: string[];
}

interface Props {
  initial: SetupValues;
  submitLabel: string;
  busy: boolean;
  onSubmit: (values: SetupValues, e?: FormEvent) => void;
}

const BANKS: { value: Bank; label: string }[] = [
  { value: "kaspi", label: "Kaspi Gold" },
  { value: "halyk", label: "Halyk card" },
];

export default function AccountsAndBudgetForm({ initial, submitLabel, busy, onSubmit }: Props) {
  const accounts = useAccounts();
  const createAccount = useCreateAccount();
  const [values, setValues] = useState(initial);
  const [newBank, setNewBank] = useState<Bank>("kaspi");
  const [newLabel, setNewLabel] = useState("");

  const toggle = (id: string) =>
    setValues((v) => ({
      ...v,
      accounts: v.accounts.includes(id) ? v.accounts.filter((a) => a !== id) : [...v.accounts, id],
    }));

  const addAccount = () => {
    const label = newLabel.trim() || BANKS.find((b) => b.value === newBank)!.label;
    createAccount.mutate(
      { bank: newBank, label },
      {
        onSuccess: (account) => {
          setValues((v) => ({ ...v, accounts: [...v.accounts, account.id] }));
          setNewLabel("");
        },
        onError: (err) => toast.error(firstError(err)),
      },
    );
  };

  const budgetError = values.budget === "" ? null : Number(values.budget) < 0 ? "Budget can't be negative." : null;
  const canSubmit = values.accounts.length > 0 && values.budget !== "" && !budgetError;

  return (
    <form
      className="card space-y-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (canSubmit) onSubmit(values, e);
      }}
    >
      <fieldset>
        <legend className="text-[13px] font-medium text-slate-800">Accounts in this review</legend>
        <p className="mt-0.5 text-xs text-slate-500">
          Select the accounts you have a statement for. One account is enough.
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          {accounts.data?.map((a) => {
            const on = values.accounts.includes(a.id);
            return (
              <button
                type="button"
                key={a.id}
                aria-pressed={on}
                onClick={() => toggle(a.id)}
                className={`cursor-pointer rounded-full border px-4 py-2 text-sm ${
                  on ? "border-primary bg-mint font-medium text-primary" : "border-slate-200 bg-white"
                }`}
              >
                {a.label}
                {a.last4 ? ` ••${a.last4}` : ""}
              </button>
            );
          })}
          {!accounts.data?.length && <p className="text-sm text-slate-500">Add the accounts you used this month.</p>}
        </div>

        <div className="mt-4 flex flex-wrap items-end gap-2 rounded-xl bg-slate-50 p-3">
          <label className="text-xs text-slate-600">
            Bank
            <select
              className="mt-1 block rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              value={newBank}
              onChange={(e) => setNewBank(e.target.value as Bank)}
            >
              {BANKS.map((b) => (
                <option key={b.value} value={b.value}>
                  {b.label}
                </option>
              ))}
            </select>
          </label>
          <label className="min-w-40 grow text-xs text-slate-600">
            Name (optional)
            <input
              className="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              value={newLabel}
              maxLength={60}
              placeholder="e.g. Halyk stipend card"
              onChange={(e) => setNewLabel(e.target.value)}
            />
          </label>
          <button type="button" className="add-btn" onClick={addAccount} disabled={createAccount.isPending}>
            <LuPlus /> Add account
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">Other banks are not supported yet. We save only a name and the card's last four digits.</p>
      </fieldset>

      <div className="grid gap-x-4 pt-4 sm:grid-cols-2">
        <Input
          label="Budget month"
          type="month"
          value={values.month.slice(0, 7)}
          onChange={(m) => setValues((v) => ({ ...v, month: m ? `${m}-01` : v.month }))}
        />
        <Input
          label="Monthly spending budget"
          inputMode="numeric"
          value={values.budget}
          suffix="₸"
          placeholder="100000"
          error={budgetError}
          hint="What you plan to spend this month. Not your bank balance."
          onChange={(b) => setValues((v) => ({ ...v, budget: digitsOnly(b) }))}
        />
      </div>

      <button type="submit" className="btn-primary" disabled={!canSubmit || busy}>
        {busy ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}
