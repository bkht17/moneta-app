import { useId, useState, type InputHTMLAttributes, type ReactNode } from "react";
import { FaRegEye, FaRegEyeSlash } from "react-icons/fa6";

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  label: string;
  value: string;
  onChange: (value: string) => void;
  hint?: ReactNode;
  error?: string | null;
  suffix?: ReactNode;
}

export default function Input({ label, value, onChange, hint, error, suffix, type, id, ...rest }: Props) {
  const [showPassword, setShowPassword] = useState(false);
  const autoId = useId();
  const inputId = id ?? autoId;
  const isPassword = type === "password";

  return (
    <div>
      <label htmlFor={inputId} className="text-[13px] font-medium text-slate-800">
        {label}
      </label>
      <div className={`input-box ${error ? "border-red-400" : ""}`}>
        <input
          id={inputId}
          type={isPassword && showPassword ? "text" : type}
          className="w-full bg-transparent outline-none"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-invalid={Boolean(error)}
          {...rest}
        />
        {suffix && <span className="font-medium text-slate-400">{suffix}</span>}
        {isPassword && (
          <button
            type="button"
            className="cursor-pointer text-slate-400"
            onClick={() => setShowPassword((v) => !v)}
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <FaRegEye size={20} className="text-primary" /> : <FaRegEyeSlash size={20} />}
          </button>
        )}
      </div>
      {(error || hint) && (
        <p className={`-mt-2 mb-4 text-xs ${error ? "text-red-600" : "text-slate-500"}`}>{error ?? hint}</p>
      )}
    </div>
  );
}
