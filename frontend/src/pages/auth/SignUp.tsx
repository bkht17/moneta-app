import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";

import AuthLayout from "../../components/layouts/AuthLayout";
import Input from "../../components/ui/Input";
import { useAuth } from "../../context/AuthContext";
import { apiErrors } from "../../lib/api";

export default function SignUp() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || password.length < 8) {
      setErrors(["Enter an email and a password of at least 8 characters."]);
      return;
    }
    setBusy(true);
    setErrors([]);
    try {
      await register(fullName.trim(), email.trim(), password);
      navigate("/reviews/new");
    } catch (err) {
      setErrors(apiErrors(err).map((e) => e.message));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout>
      <div className="w-full lg:w-[70%]">
        <h3 className="text-xl font-semibold">Create your account</h3>
        <p className="mt-1 mb-6 text-xs text-slate-700">Free. No bank login needed.</p>
        <form onSubmit={submit} noValidate>
          <Input label="Name" autoComplete="name" value={fullName} onChange={setFullName} placeholder="Aruzhan K." />
          <Input label="Email" type="email" autoComplete="email" value={email} onChange={setEmail} placeholder="you@example.com" />
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={setPassword}
            hint="At least 8 characters."
          />
          {errors.map((m) => (
            <p key={m} className="pb-2.5 text-xs text-red-600">
              {m}
            </p>
          ))}
          <button type="submit" className="btn-primary" disabled={busy}>
            {busy ? "Creating…" : "Create account"}
          </button>
          <p className="mt-3 text-[13px] text-slate-800">
            Already have an account?{" "}
            <Link className="font-medium text-primary underline" to="/login">
              Log in
            </Link>
          </p>
        </form>
      </div>
    </AuthLayout>
  );
}
