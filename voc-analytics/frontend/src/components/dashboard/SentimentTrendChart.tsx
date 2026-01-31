'use client';

import { useMemo } from 'react';
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { th } from 'date-fns/locale';
import { useDashboardTrends } from '@/hooks/useDashboard';
import { useDashboardDate } from '@/context/DashboardDateContext';

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    dataKey: string;
    value: number;
    color: string;
  }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !label) return null;

  const formattedDate = format(parseISO(label), 'd MMM yyyy', { locale: th });

  const labelMap: Record<string, string> = {
    positive: 'Positive',
    neutral: 'Neutral',
    negative: 'Negative',
  };

  return (
    <div className="bg-white px-3 py-2 rounded-lg shadow-lg border border-slate-200">
      <p className="text-sm font-medium text-slate-900 mb-1">{formattedDate}</p>
      {payload.map((item, index) => (
        <div key={index} className="flex items-center gap-2 text-sm">
          <div
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-slate-600">{labelMap[item.dataKey]}:</span>
          <span className="font-medium text-slate-900">{item.value}</span>
        </div>
      ))}
    </div>
  );
}

// Granularity display labels
const GRANULARITY_LABELS = {
  daily: 'Daily',
  weekly: 'Weekly',
  monthly: 'Monthly',
  quarterly: 'Quarterly',
} as const;

export function SentimentTrendChart() {
  // Get dashboard date context
  const { effectiveDates } = useDashboardDate();

  // Fetch trend data using dashboard's date range
  const { data: trendResponse, isLoading } = useDashboardTrends(
    effectiveDates ? { start_date: effectiveDates.start_date, end_date: effectiveDates.end_date } : undefined
  );

  // Extract granularity and data from response
  const granularity = trendResponse?.granularity ?? 'daily';
  const trendData = trendResponse?.data ?? [];

  // Determine X-axis format based on granularity
  const formatXAxis = useMemo(() => {
    return (dateStr: string) => {
      try {
        const date = parseISO(dateStr);
        switch (granularity) {
          case 'daily':
            return format(date, 'd MMM', { locale: th });
          case 'weekly':
            return format(date, 'd MMM', { locale: th });
          case 'monthly':
            return format(date, 'MMM yy', { locale: th });
          case 'quarterly':
            // Show Q1, Q2, Q3, Q4 with year
            const quarter = Math.ceil((date.getMonth() + 1) / 3);
            return `Q${quarter} ${format(date, 'yy', { locale: th })}`;
          default:
            return format(date, 'd MMM', { locale: th });
        }
      } catch {
        return dateStr;
      }
    };
  }, [granularity]);

  // Reading guide text based on granularity
  const readingGuide = useMemo(() => {
    switch (granularity) {
      case 'daily':
        return 'Shaded areas = volume | Each point = daily count';
      case 'weekly':
        return 'Shaded areas = volume | Each point = weekly total';
      case 'monthly':
        return 'Shaded areas = volume | Each point = monthly total';
      case 'quarterly':
        return 'Shaded areas = volume | Each point = quarterly total';
      default:
        return 'Shaded areas = volume | Lines = count';
    }
  }, [granularity]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            Sentiment Trend
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Track sentiment changes over time to spot patterns
          </p>
        </div>
        <div className="px-3 py-1 text-sm font-medium text-slate-600 bg-slate-100 rounded-lg">
          {GRANULARITY_LABELS[granularity]}
        </div>
      </div>

      {/* Reading guide */}
      <div className="flex items-center gap-4 text-xs text-slate-400 mb-2">
        <span>{readingGuide}</span>
      </div>

      <div className="h-[280px]">
        {isLoading || trendData.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-pulse text-slate-400">Loading...</div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={trendData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="gradientPositive" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0.05} />
                </linearGradient>
                <linearGradient id="gradientNegative" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ef4444" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#ef4444" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={formatXAxis}
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
                width={40}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="bottom"
                height={36}
                iconType="circle"
                iconSize={8}
                formatter={(value) => {
                  const labelMap: Record<string, string> = {
                    positive: 'Positive',
                    neutral: 'Neutral',
                    negative: 'Negative',
                  };
                  return <span className="text-sm text-slate-600">{labelMap[value]}</span>;
                }}
              />
              {/* Positive Area */}
              <Area
                type="monotone"
                dataKey="positive"
                stroke="#10b981"
                strokeWidth={2}
                fill="url(#gradientPositive)"
              />
              {/* Negative Area */}
              <Area
                type="monotone"
                dataKey="negative"
                stroke="#ef4444"
                strokeWidth={2}
                fill="url(#gradientNegative)"
              />
              {/* Neutral Line with dots */}
              <Line
                type="monotone"
                dataKey="neutral"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ fill: '#f59e0b', r: 3 }}
                activeDot={{ r: 5 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
