'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { SentimentDistribution } from '@/lib/types';
import { getSentimentLabel } from '@/lib/utils';

interface SentimentDonutChartProps {
  data: SentimentDistribution;
}

const COLORS = {
  positive: '#10b981', // emerald-500
  neutral: '#f59e0b',  // amber-500
  negative: '#ef4444', // red-500
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      name: string;
      value: number;
      percentage: number;
    };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const { name, value, percentage } = payload[0].payload;

  return (
    <div className="bg-white px-3 py-2 rounded-lg shadow-lg border border-slate-200">
      <p className="text-sm font-medium text-slate-900">
        {getSentimentLabel(name)}
      </p>
      <p className="text-sm text-slate-600">
        {value.toLocaleString()} ({percentage}%)
      </p>
    </div>
  );
}

export function SentimentDonutChart({ data }: SentimentDonutChartProps) {
  const total = data.positive + data.neutral + data.negative;

  const chartData = [
    {
      name: 'positive',
      value: data.positive,
      percentage: total > 0 ? Math.round((data.positive / total) * 100) : 0,
    },
    {
      name: 'neutral',
      value: data.neutral,
      percentage: total > 0 ? Math.round((data.neutral / total) * 100) : 0,
    },
    {
      name: 'negative',
      value: data.negative,
      percentage: total > 0 ? Math.round((data.negative / total) * 100) : 0,
    },
  ].filter((item) => item.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
        <h3 className="text-base font-semibold text-slate-900 mb-4">
          Sentiment Distribution
        </h3>
        <div className="flex items-center justify-center h-[250px] text-slate-400">
          No data available
        </div>
      </div>
    );
  }

  // Calculate dominant sentiment for insight
  const dominantSentiment = chartData.reduce((prev, current) =>
    (prev.value > current.value) ? prev : current
  );

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
      <div className="mb-3">
        <h3 className="text-base font-semibold text-slate-900">
          Sentiment Distribution
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          AI-analyzed emotional tone of all feedback
        </p>
      </div>

      <div className="h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={2}
              dataKey="value"
              strokeWidth={0}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[entry.name as keyof typeof COLORS]}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Legend at bottom */}
      <div className="flex justify-center gap-6 mt-2">
        {chartData.map((item) => (
          <div key={item.name} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: COLORS[item.name as keyof typeof COLORS] }}
            />
            <span className="text-sm text-slate-600">
              {getSentimentLabel(item.name)}{' '}
              <span className="font-medium text-slate-900">
                {item.value.toLocaleString()}
              </span>
            </span>
          </div>
        ))}
      </div>

      {/* Insight text */}
      <p className="text-xs text-slate-500 mt-3 pt-3 border-t border-slate-100 text-center">
        <span className="font-medium" style={{ color: COLORS[dominantSentiment.name as keyof typeof COLORS] }}>
          {dominantSentiment.percentage}% {getSentimentLabel(dominantSentiment.name)}
        </span>
        {' '}is the dominant sentiment
      </p>
    </div>
  );
}
