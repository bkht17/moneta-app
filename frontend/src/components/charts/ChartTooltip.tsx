import { formatKzt } from "../../lib/format";

interface Props {
  active?: boolean;
  payload?: { name?: string; value?: number; payload?: { label?: string } }[];
}

export default function ChartTooltip({ active, payload }: Props) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-2 shadow-md">
      <p className="mb-1 text-xs font-semibold text-primary">{item.payload?.label ?? item.name}</p>
      <p className="text-sm text-gray-600">
        Amount: <span className="font-medium text-gray-900">{formatKzt(item.value ?? 0)}</span>
      </p>
    </div>
  );
}
