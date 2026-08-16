"use client";

import { formatKRW } from "@/lib/format";
import type { AllocationItem, HistoryPoint, InvestmentPosition } from "@/lib/types";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const palette = ["#19725d", "#55a98c", "#a6d5bd", "#d7ad5b", "#c97b63", "#7f8da2", "#bdc4cc"];

function MoneyTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value?: number; name?: string; color?: string }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      {label && <span>{label}</span>}
      {payload.map((item) => <strong key={item.name} style={{ color: item.color }}>{item.name}: {formatKRW(Number(item.value))}</strong>)}
    </div>
  );
}

export function AllocationDonut({ data, compact = false }: { data: AllocationItem[]; compact?: boolean }) {
  return (
    <div className={compact ? "donut-wrap compact" : "donut-wrap"}>
      <div className="donut-chart">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="current_value" nameKey="asset_class" innerRadius="68%" outerRadius="94%" paddingAngle={2} stroke="none">
              {data.map((entry, index) => <Cell key={entry.asset_class} fill={palette[index % palette.length]} />)}
            </Pie>
            <Tooltip content={<MoneyTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-center"><span>총자산</span><strong>{formatKRW(data.reduce((sum, item) => sum + item.current_value, 0), true)}</strong></div>
      </div>
      <div className="chart-legend">
        {data.map((item, index) => (
          <div className="legend-row" key={item.asset_class}>
            <span className="legend-label"><i style={{ background: palette[index % palette.length] }} />{item.asset_class}</span>
            <strong>{item.current_weight.toFixed(1)}%</strong>
            {!compact && <small>{formatKRW(item.current_value, true)}</small>}
          </div>
        ))}
      </div>
    </div>
  );
}

export function NetWorthChart({ data }: { data: HistoryPoint[] }) {
  const chartData = data.map((item) => ({ ...item, label: item.date.slice(2, 7).replace("-", ".") }));
  return (
    <div className="history-chart">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 12, right: 6, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="netWorthFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#27896f" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#27896f" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#e9ebe7" strokeDasharray="3 5" vertical={false} />
          <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: "#8b918b", fontSize: 11 }} dy={10} />
          <YAxis hide domain={["dataMin - 5000000", "dataMax + 3000000"]} />
          <Tooltip content={<MoneyTooltip />} />
          <Area type="monotone" dataKey="net_worth" name="순자산" stroke="#19725d" strokeWidth={2.5} fill="url(#netWorthFill)" activeDot={{ r: 5, fill: "#19725d", stroke: "#fff", strokeWidth: 3 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function InvestmentComposition({ positions }: { positions: InvestmentPosition[] }) {
  const groups = positions.reduce<Record<string, number>>((acc, item) => {
    acc[item.security_type] = (acc[item.security_type] ?? 0) + item.market_value_krw;
    return acc;
  }, {});
  const data = Object.entries(groups).map(([name, value]) => ({ name, value }));
  return (
    <div className="bar-chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 4, right: 18, top: 8, bottom: 4 }}>
          <CartesianGrid stroke="#e9ebe7" strokeDasharray="3 5" horizontal={false} />
          <XAxis type="number" hide />
          <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: "#5f675f", fontSize: 12 }} width={64} />
          <Tooltip content={<MoneyTooltip />} />
          <Bar dataKey="value" name="평가금액" radius={[0, 6, 6, 0]} barSize={22}>
            {data.map((entry, index) => <Cell key={entry.name} fill={palette[index]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
