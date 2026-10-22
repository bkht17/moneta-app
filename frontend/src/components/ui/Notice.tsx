import type { ReactNode } from "react";
import { LuCircleAlert, LuCircleCheck, LuInfo, LuTriangleAlert } from "react-icons/lu";

const STYLES = {
  info: { box: "bg-mint text-ink", icon: <LuInfo className="text-primary" /> },
  ok: { box: "bg-emerald-50 text-ink", icon: <LuCircleCheck className="text-emerald-600" /> },
  warn: { box: "bg-amber-50 text-ink", icon: <LuTriangleAlert className="text-amber-600" /> },
  error: { box: "bg-red-50 text-ink", icon: <LuCircleAlert className="text-red-600" /> },
};

export default function Notice({
  tone = "info",
  children,
}: {
  tone?: keyof typeof STYLES;
  children: ReactNode;
}) {
  const style = STYLES[tone];
  return (
    <div className={`flex gap-3 rounded-xl px-4 py-3 text-sm ${style.box}`} role={tone === "error" ? "alert" : "status"}>
      <span className="mt-0.5 shrink-0 text-lg">{style.icon}</span>
      <div className="min-w-0">{children}</div>
    </div>
  );
}

export function ErrorList({ errors }: { errors: { message: string }[] }) {
  if (!errors.length) return null;
  return (
    <Notice tone="error">
      {errors.length === 1 ? (
        errors[0].message
      ) : (
        <ul className="list-disc space-y-1 pl-4">
          {errors.map((e, i) => (
            <li key={i}>{e.message}</li>
          ))}
        </ul>
      )}
    </Notice>
  );
}
