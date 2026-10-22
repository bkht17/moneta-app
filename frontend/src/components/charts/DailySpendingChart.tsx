import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatDay } from "../../lib/format";
import ChartTooltip from "./ChartTooltip";

export default function DailySpendingChart({ data }: { data: { date: string; amount: number }[] }) {
  const rows = data.map((d) => ({ ...d, label: formatDay(d.date) }));
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={rows}>
        <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#5A6E64" }} stroke="none" interval="preserveStartEnd" />
        <YAxis
          tick={{ fontSize: 11, fill: "#5A6E64" }}
          stroke="none"
          tickFormatter={(v: number) => (v >= 1000 ? `${Math.round(v / 1000)}k` : String(v))}
        />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "#EAF2ED" }} />
        <Bar dataKey="amount" fill="#006D4B" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
