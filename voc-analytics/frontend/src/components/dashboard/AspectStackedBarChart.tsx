'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { AspectSummary } from '@/lib/types';
import { getAspectLabel, getSentimentLabel } from '@/lib/utils';

interface AspectStackedBarChartProps {
  data: AspectSummary[];
}

const COLORS = {
  positive: '#10b981', // emerald-500
  neutral: '#f59e0b',  // amber-500
  negative: '#ef4444', // red-500
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    dataKey: string;
    value: number;
    fill: string;
  }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !label) return null;

  const total = payload.reduce((sum, item) => sum + item.value, 0);
  // label is the aspect key (e.g., 'equipment'), convert to Thai
  const aspectLabel = getAspectLabel(label);

  return (
    <div className="bg-white px-3 py-2 rounded-lg shadow-lg border border-slate-200">
      <p className="text-sm font-medium text-slate-900 mb-1">
        {aspectLabel}
      </p>
      <p className="text-xs text-slate-500 mb-2">Total: {total}</p>
      {payload.map((item, index) => (
        <div key={index} className="flex items-center gap-2 text-sm">
          <div
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: item.fill }}
          />
          <span className="text-slate-600">{getSentimentLabel(item.dataKey)}:</span>
          <span className="font-medium text-slate-900">{item.value}</span>
        </div>
      ))}
    </div>
  );
}

export function AspectStackedBarChart({ data }: AspectStackedBarChartProps) {
  // Sort by total mentions (most to least)
  const sortedData = [...data]
    .sort((a, b) => b.total_mentions - a.total_mentions)
    .map((item) => ({
      aspect: item.aspect,
      positive: item.positive,
      neutral: item.neutral,
      negative: item.negative,
      total: item.total_mentions,
    }));

  if (sortedData.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
        <h3 className="text-base font-semibold text-slate-900 mb-4">
          Aspect-Based Sentiment
        </h3>
        <div className="flex items-center justify-center h-[300px] text-slate-400">
          No data available
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
      <h3 className="text-base font-semibold text-slate-900 mb-4">
        Aspect-Based Sentiment
      </h3>

      <div className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={sortedData}
            layout="vertical"
            margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={true} vertical={false} />
            <XAxis
              type="number"
              tick={{ fontSize: 12, fill: '#64748b' }}
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
            />
            <YAxis
              type="category"
              dataKey="aspect"
              tickFormatter={(value) => getAspectLabel(value)}
              tick={{ fontSize: 12, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              width={100}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              iconSize={8}
              formatter={(value) => (
                <span className="text-sm text-slate-600">{getSentimentLabel(value)}</span>
              )}
            />
            <Bar
              dataKey="positive"
              stackId="a"
              fill={COLORS.positive}
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="neutral"
              stackId="a"
              fill={COLORS.neutral}
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="negative"
              stackId="a"
              fill={COLORS.negative}
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
