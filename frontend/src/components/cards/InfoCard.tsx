import type { ReactNode } from "react";

interface Props {
  icon: ReactNode;
  label: string;
  value: string;
  note?: string;
  color: string;
}

export default function InfoCard({ icon, label, value, note, color }: Props) {
  return (
    <div className="flex gap-6 rounded-2xl border border-gray-200/50 bg-white p-6 shadow-md shadow-gray-100">
      <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-full text-[26px] drop-shadow-xl ${color}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <h6 className="mb-1 text-sm text-gray-500">{label}</h6>
        <span className="text-[22px] font-medium tabular-nums">{value}</span>
        {note && <p className="mt-0.5 text-xs text-gray-500">{note}</p>}
      </div>
    </div>
  );
}
