import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./api";
import type {
  Bank,
  BankAccount,
  Coverage,
  Flag,
  Overview,
  Resolution,
  Review,
  StatementImport,
} from "./types";

export const keys = {
  accounts: ["accounts"] as const,
  reviews: ["reviews"] as const,
  review: (id: string) => ["reviews", id] as const,
  coverage: (id: string) => ["reviews", id, "coverage"] as const,
  flags: (id: string) => ["reviews", id, "flags"] as const,
  overview: (id: string) => ["reviews", id, "overview"] as const,
  categories: ["categories"] as const,
};

export function useAccounts() {
  return useQuery({
    queryKey: keys.accounts,
    queryFn: async () => (await api.get<BankAccount[]>("/accounts/")).data,
  });
}

export function useCreateAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { bank: Bank; label: string }) =>
      (await api.post<BankAccount>("/accounts/", body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.accounts }),
  });
}

export function useDeleteAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => api.delete(`/accounts/${id}/`),
    onSuccess: () => qc.invalidateQueries(),
  });
}

export function useReviews() {
  return useQuery({
    queryKey: keys.reviews,
    queryFn: async () => (await api.get<Review[]>("/reviews/")).data,
  });
}

export function useReview(id: string) {
  return useQuery({
    queryKey: keys.review(id),
    queryFn: async () => (await api.get<Review>(`/reviews/${id}/`)).data,
  });
}

export function useCreateReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { month: string; budget_kzt: number; accounts: string[] }) =>
      (await api.post<Review>("/reviews/", body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.reviews }),
  });
}

export function useUpdateReview(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: Partial<Pick<Review, "budget_kzt" | "accounts" | "month">>) =>
      (await api.patch<Review>(`/reviews/${id}/`, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.review(id) }),
  });
}

export function useCoverage(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.coverage(id),
    queryFn: async () => (await api.get<Coverage>(`/reviews/${id}/coverage/`)).data,
    enabled,
  });
}

export function useUploadStatement(reviewId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ account, file }: { account: string; file: File }) => {
      const form = new FormData();
      form.append("account", account);
      form.append("file", file);
      return (await api.post<StatementImport>(`/reviews/${reviewId}/statements/`, form)).data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.coverage(reviewId) }),
  });
}

export function useSubmitReview(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      cash_kzt: string;
      later_cash_kzt?: string;
      later_cash_until?: string | null;
    }) => (await api.post<Review>(`/reviews/${id}/submit/`, body)).data,
    onSuccess: (review) => {
      qc.setQueryData(keys.review(id), review);
      qc.invalidateQueries({ queryKey: keys.flags(id) });
      qc.invalidateQueries({ queryKey: keys.reviews });
    },
  });
}

export function useReopenReview(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post<Review>(`/reviews/${id}/reopen/`)).data,
    onSuccess: (review) => qc.setQueryData(keys.review(id), review),
  });
}

export function useFlags(id: string, enabled: boolean) {
  return useQuery({
    queryKey: keys.flags(id),
    queryFn: async () => (await api.get<Flag[]>(`/reviews/${id}/flags/`)).data,
    enabled,
  });
}

export function useResolveFlag(reviewId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ flag, resolution }: { flag: string; resolution: Resolution }) =>
      (await api.post(`/flags/${flag}/resolve/`, { resolution })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.review(reviewId) });
      qc.invalidateQueries({ queryKey: keys.flags(reviewId) });
      qc.invalidateQueries({ queryKey: keys.reviews });
    },
  });
}

export function useOverview(id: string | undefined) {
  return useQuery({
    queryKey: keys.overview(id ?? "none"),
    queryFn: async () => (await api.get<Overview>(`/reviews/${id}/overview/`)).data,
    enabled: Boolean(id),
  });
}

export function useCategories() {
  return useQuery({
    queryKey: keys.categories,
    queryFn: async () => (await api.get<string[]>("/categories/")).data,
    staleTime: Infinity,
  });
}

export function useSetCategory(reviewId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, category }: { id: string; category: string }) =>
      (await api.patch(`/transactions/${id}/`, { category })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.overview(reviewId) }),
  });
}
