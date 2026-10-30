export type Bank = "kaspi" | "halyk";

export interface User {
  id: string;
  email: string;
  full_name: string;
  date_joined: string;
}

export interface BankAccount {
  id: string;
  bank: Bank;
  label: string;
  last4: string;
  created_at: string;
}

export type ReviewStatus = "draft" | "needs_confirmation" | "complete";

export interface Review {
  id: string;
  month: string;
  budget_kzt: number;
  accounts: string[];
  status: ReviewStatus;
  cutoff_date: string | null;
  cash_kzt: number | null;
  later_cash_kzt: number | null;
  later_cash_until: string | null;
  created_at: string;
  intake_completed_at: string | null;
  completed_at: string | null;
  open_flags: number;
  sources: ReviewSource[];
}

export interface ReviewSource {
  id: string;
  label: string;
  bank: Bank;
  last4: string;
  statements: { file_name: string; period_start: string; period_end: string }[];
}

export interface StatementImport {
  id: string;
  account: string;
  period_start: string;
  period_end: string;
  file_name: string;
  row_count: number;
  new_rows: number;
  layout: string;
  imported_at: string;
}

export interface ApiError {
  code: string;
  message: string;
  account?: string;
}

export interface AccountCoverage {
  id: string;
  label: string;
  bank: Bank;
  covered_until: string | null;
  starts_late_on: string | null;
  gap_after: string | null;
  statements: StatementImport[];
}

export interface Coverage {
  cutoff: string | null;
  errors: ApiError[];
  accounts: AccountCoverage[];
}

export interface FlagTransaction {
  id: string;
  booked_on: string;
  amount: number;
  description: string;
  operation: string;
  account_label: string;
}

export type FlagType = "possible_duplicate" | "possible_own_transfer";
export type Resolution = "keep_both" | "same_purchase" | "own_transfer" | "not_own_transfer";

export interface Flag {
  id: string;
  type: FlagType;
  first: FlagTransaction;
  second: FlagTransaction;
  resolution: Resolution | "";
  resolved_at: string | null;
}

export type TxKind =
  | "purchase"
  | "income"
  | "transfer_out"
  | "transfer_in"
  | "own_transfer"
  | "withdrawal"
  | "refund";

export interface OverviewTransaction {
  id: string;
  date: string;
  amount: number;
  description: string;
  operation: string;
  kind: TxKind;
  category: string;
  category_editable: boolean;
  excluded_reason: string;
  account: { id: string; label: string };
}

export interface Overview {
  review_id: string;
  month: string;
  period: { start: string; end: string };
  is_current: boolean;
  budget: number;
  spending: number;
  remaining: number;
  incoming: number;
  income: number;
  own_transfers: number;
  refunds: number;
  withdrawals: number;
  cash: { amount: number | null; until: string };
  categories: { name: string; amount: number }[];
  daily: { date: string; amount: number }[];
  accounts: {
    id: string;
    label: string;
    bank: Bank;
    last4: string;
    covered_until: string | null;
  }[];
  transactions: OverviewTransaction[];
  outside: {
    from: string;
    until: string | null;
    month_end: string;
    transactions: OverviewTransaction[];
    bank_spending: number;
    cash: number | null;
  };
}
