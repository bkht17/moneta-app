import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { api, tokens } from "../lib/api";
import type { User } from "../lib/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(tokens.access));

  const logout = useCallback(() => {
    tokens.clear();
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  useEffect(() => {
    if (!tokens.access) return;
    api
      .get<User>("/auth/me/")
      .then(({ data }) => setUser(data))
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, [logout]);

  useEffect(() => {
    window.addEventListener("moneta:logout", logout);
    return () => window.removeEventListener("moneta:logout", logout);
  }, [logout]);

  const login = async (email: string, password: string) => {
    const { data } = await api.post("/auth/login/", { email, password });
    tokens.set(data.access, data.refresh);
    const me = await api.get<User>("/auth/me/");
    setUser(me.data);
  };

  const register = async (fullName: string, email: string, password: string) => {
    const { data } = await api.post("/auth/register/", {
      full_name: fullName,
      email,
      password,
    });
    tokens.set(data.access, data.refresh);
    setUser(data.user);
  };

  const deleteAccount = async () => {
    await api.delete("/auth/me/");
    logout();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, deleteAccount }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
