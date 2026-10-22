import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import ChartTooltip from "./ChartTooltip";

const CATEGORY_COLORS = [
  "#006D4B",
  "#2FB27C",
  "#9BD6B8",
  "#C7E86A",
  "#E1FA6E",
  "#0B8F4D",
  "#5A6E64",
  "#7FC8A9",
  "#B4C9BD",
  "#3E5A4D",
];

interface Props {
  data: { name: string; amount: number }[];
  label: string;
  total: string;
}

export default function CategoryPieChart({ data, label, total }: Props) {
  return (
    <ResponsiveContainer width="100%" height={380}>
      <PieChart>
        <Pie data={data} dataKey="amount" nameKey="name" cx="50%" cy="45%" outerRadius={130} innerRadius={100} labelLine={false}>
          {data.map((entry, index) => (
            <Cell key={entry.name} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<ChartTooltip />} />
        <Legend
          iconType="circle"
          wrapperStyle={{ fontSize: 12 }}
          formatter={(value: string) => <span className="text-ink">{value}</span>}
        />
        <text x="50%" y="45%" dy={-20} textAnchor="middle" fill="#5A6E64" fontSize="14px">
          {label}
        </text>
        <text x="50%" y="45%" dy={12} textAnchor="middle" fill="#10261C" fontSize="22px" fontWeight={600}>
          {total}
        </text>
      </PieChart>
    </ResponsiveContainer>
  );
}
