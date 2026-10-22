import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";

import AuthLayout from "../../components/layouts/AuthLayout";
import Input from "../../components/ui/Input";
import { useAuth } from "../../context/AuthContext";
import { firstError } from "../../lib/api";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Enter your email and password.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await login(email.trim(), password);
      navigate("/");
    } catch (err) {
      setError(firstError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout>
      <div className="w-full lg:w-[70%]">
        <h3 className="text-xl font-semibold">Welcome back</h3>
        <p className="mt-1 mb-6 text-xs text-slate-700">Log in to see your combined spending review.</p>
        <form onSubmit={submit} noValidate>
          <Input label="Email" type="email" autoComplete="email" value={email} onChange={setEmail} placeholder="you@example.com" />
          <Input label="Password" type="password" autoComplete="current-password" value={password} onChange={setPassword} />
          {error && <p className="pb-2.5 text-xs text-red-600">{error}</p>}
          <button type="submit" className="btn-primary" disabled={busy}>
            {busy ? "Logging in…" : "Log in"}
          </button>
          <p className="mt-3 text-[13px] text-slate-800">
            New to MONETA?{" "}
            <Link className="font-medium text-primary underline" to="/signup">
              Create an account
            </Link>
          </p>
        </form>
      </div>
    </AuthLayout>
  );
}
