import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import type { ApiError } from "./types";

const ACCESS = "moneta.access";
const REFRESH = "moneta.refresh";

export const tokens = {
  get access() {
    return localStorage.getItem(ACCESS);
  },
  get refresh() {
    return localStorage.getItem(REFRESH);
  },
  set(access: string, refresh?: string) {
    localStorage.setItem(ACCESS, access);
    if (refresh) localStorage.setItem(REFRESH, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
  },
};

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api",
  timeout: 70_000, // NFR2 allows 60 s for processing; leave room for the network.
});

api.interceptors.request.use((config) => {
  if (tokens.access) config.headers.Authorization = `Bearer ${tokens.access}`;
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccess(): Promise<string | null> {
  const refresh = tokens.refresh;
  if (!refresh) return null;
  try {
    const { data } = await axios.post(`${api.defaults.baseURL}/auth/refresh/`, { refresh });
    tokens.set(data.access, data.refresh);
    return data.access as string;
  } catch {
    tokens.clear();
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
    if (error.response?.status === 401 && original && !original._retried) {
      original._retried = true;
      refreshing ??= refreshAccess().finally(() => {
        refreshing = null;
      });
      const access = await refreshing;
      if (access) {
        original.headers.Authorization = `Bearer ${access}`;
        return api(original);
      }
      window.dispatchEvent(new Event("moneta:logout"));
    }
    return Promise.reject(error);
  },
);

/** Turn any API failure into a list of messages the UI can show. */
export function apiErrors(error: unknown): ApiError[] {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as Record<string, unknown> | undefined;
    if (data && Array.isArray(data.errors)) return data.errors as ApiError[];
    if (data && typeof data.detail === "string") return [{ code: "error", message: data.detail }];
    if (data && typeof data === "object") {
      return Object.entries(data).flatMap(([field, value]) =>
        (Array.isArray(value) ? value : [value]).map((message) => ({
          code: field,
          message: field === "non_field_errors" ? String(message) : `${field}: ${message}`,
        })),
      );
    }
    if (error.code === "ECONNABORTED") return [{ code: "timeout", message: "The server took too long. Try again." }];
    return [{ code: "network", message: "Can't reach MONETA. Check your connection and try again." }];
  }
  return [{ code: "error", message: "Something went wrong. Try again." }];
}

export function firstError(error: unknown) {
  return apiErrors(error)[0]?.message ?? "Something went wrong.";
}
