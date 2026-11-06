"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
export function DistributionChart({ data }: { data: { name: string; count: number }[] }) {
  return (
    <div
      style={{ height: 220, width: "100%" }}
      role="img"
      aria-label={`Analysis score distribution: ${data.map((d) => `${d.name}: ${d.count}`).join(", ")}`}
    >
      <ResponsiveContainer>
        <BarChart data={data} margin={{ left: -25, right: 5 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eeedf5" />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#939bae" }} axisLine={false} tickLine={false} />
          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 10, fill: "#939bae" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip cursor={{ fill: "#f5f3fc" }} />
          <Bar dataKey="count" fill="#a795dc" radius={[5, 5, 0, 0]} maxBarSize={45} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
