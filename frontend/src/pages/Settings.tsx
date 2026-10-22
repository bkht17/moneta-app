import { useState } from "react";
import toast from "react-hot-toast";
import { LuTrash2 } from "react-icons/lu";
import { useNavigate } from "react-router";

import Modal from "../components/ui/Modal";
import Notice from "../components/ui/Notice";
import { useAuth } from "../context/AuthContext";
import { firstError } from "../lib/api";
import { useAccounts, useDeleteAccount } from "../lib/queries";
import type { BankAccount } from "../lib/types";

export default function Settings() {
  const { user, deleteAccount } = useAuth();
  const navigate = useNavigate();
  const accounts = useAccounts();
  const removeAccount = useDeleteAccount();
  const [confirmAccount, setConfirmAccount] = useState<BankAccount | null>(null);
  const [confirmAll, setConfirmAll] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const deleteEverything = async () => {
    setDeleting(true);
    try {
      await deleteAccount();
      navigate("/login");
      toast.success("Your MONETA account and data are deleted.");
    } catch (err) {
      toast.error(firstError(err));
      setDeleting(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>

      <section className="card">
        <h5 className="text-lg">Profile</h5>
        <p className="mt-2 text-sm">{user?.full_name || "No name"}</p>
        <p className="text-sm text-slate-500">{user?.email}</p>
      </section>

      <section className="card">
        <h5 className="text-lg">Accounts</h5>
        <p className="text-xs text-slate-500">Only a name and the card's last four digits are stored.</p>
        <ul className="mt-3 divide-y divide-gray-100">
          {accounts.data?.map((a) => (
            <li key={a.id} className="flex items-center justify-between py-3 text-sm">
              <span>
                {a.label} {a.last4 && <span className="text-slate-500">••{a.last4}</span>}
                <span className="ml-2 text-xs text-slate-400">{a.bank === "kaspi" ? "Kaspi" : "Halyk"}</span>
              </span>
              <button
                type="button"
                className="cursor-pointer text-slate-400 hover:text-red-600"
                aria-label={`Delete ${a.label}`}
                onClick={() => setConfirmAccount(a)}
              >
                <LuTrash2 />
              </button>
            </li>
          ))}
          {!accounts.data?.length && <li className="py-3 text-sm text-slate-500">No accounts yet.</li>}
        </ul>
      </section>

      <section className="card space-y-3">
        <h5 className="text-lg">Your data</h5>
        <Notice>
          Statement PDFs are read once and never stored. MONETA keeps the transactions it read from them so you can
          compare months. Deleting your data removes your account, accounts, transactions and every review.
        </Notice>
        <button type="button" className="cursor-pointer rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700" onClick={() => setConfirmAll(true)}>
          Delete my data
        </button>
      </section>

      <Modal isOpen={Boolean(confirmAccount)} onClose={() => setConfirmAccount(null)} title="Delete this account?">
        <p className="text-sm">
          {confirmAccount?.label} and all transactions read from its statements will be removed. Past reviews that used
          it will change.
        </p>
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-secondary" onClick={() => setConfirmAccount(null)}>
            Cancel
          </button>
          <button
            type="button"
            className="cursor-pointer rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white"
            disabled={removeAccount.isPending}
            onClick={() =>
              confirmAccount &&
              removeAccount.mutate(confirmAccount.id, {
                onSuccess: () => {
                  toast.success("Account deleted.");
                  setConfirmAccount(null);
                },
                onError: (err) => toast.error(firstError(err)),
              })
            }
          >
            Delete account
          </button>
        </div>
      </Modal>

      <Modal isOpen={confirmAll} onClose={() => setConfirmAll(false)} title="Delete all your MONETA data?">
        <p className="text-sm">This removes your login, accounts, transactions and reviews. It can't be undone.</p>
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-secondary" onClick={() => setConfirmAll(false)}>
            Cancel
          </button>
          <button
            type="button"
            className="cursor-pointer rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white"
            disabled={deleting}
            onClick={deleteEverything}
          >
            {deleting ? "Deleting…" : "Delete everything"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
