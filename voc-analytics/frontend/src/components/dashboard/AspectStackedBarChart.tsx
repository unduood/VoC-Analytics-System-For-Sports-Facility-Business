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

// All 8 aspects in display order
const ALL_ASPECTS = [
  'equipment',
  'staff',
  'cleanliness',
  'atmosphere',
  'price',
  'location',
  'programs',
  'amenities',
] as const;

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
  // Create chart data for all 8 aspects, filling missing ones with zeros
  // Aspects with data are sorted by total (descending), aspects without data come last
  const chartData = ALL_ASPECTS.map((aspect) => {
    const aspectData = data.find((d) => d.aspect === aspect);
    return {
      aspect,
      positive: aspectData?.positive ?? 0,
      neutral: aspectData?.neutral ?? 0,
      negative: aspectData?.negative ?? 0,
      total: aspectData?.total_mentions ?? 0,
      hasData: !!aspectData,
    };
  }).sort((a, b) => {
    // Sort: aspects with data first (by total descending), then aspects without data
    if (a.hasData && !b.hasData) return -1;
    if (!a.hasData && b.hasData) return 1;
    return b.total - a.total;
  });

  // Check if there's any data at all
  const hasAnyData = chartData.some((item) => item.hasData);

  // Find aspect with most negative feedback (only from aspects with actual data)
  const aspectsWithData = chartData.filter((item) => item.hasData);
  const mostNegativeAspect = aspectsWithData.length > 0
    ? aspectsWithData.reduce((prev, current) =>
        (current.negative > prev.negative) ? current : prev
      )
    : null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
      <div className="mb-3">
        <h3 className="text-base font-semibold text-slate-900">
          Aspect-Based Sentiment
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          What customers mention most, broken down by sentiment
        </p>
      </div>

      {/* Insight callout - only show if there's data and negative mentions */}
      {mostNegativeAspect && mostNegativeAspect.negative > 0 && (
        <div className="bg-red-50 border border-red-100 rounded-lg px-3 py-2 mb-3">
          <p className="text-xs text-red-700">
            <span className="font-medium">{getAspectLabel(mostNegativeAspect.aspect)}</span>
            {' '}has the most negative mentions ({mostNegativeAspect.negative})
          </p>
        </div>
      )}

      {/* No data message - shown when no aspects have data */}
      {!hasAnyData && (
        <div className="bg-slate-50 border border-slate-100 rounded-lg px-3 py-2 mb-3">
          <p className="text-xs text-slate-500">
            No aspect data available for the selected period
          </p>
        </div>
      )}

      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
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
