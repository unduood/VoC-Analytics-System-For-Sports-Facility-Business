'use client';

import { useState } from 'react';
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
import { cn } from '@/lib/utils';

type Period = '7d' | '30d' | '90d';

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

export function SentimentTrendChart() {
  const [period, setPeriod] = useState<Period>('7d');
  const { data: trendData, isLoading } = useDashboardTrends(period);

  const periodOptions: { value: Period; label: string }[] = [
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
    { value: '90d', label: '90 Days' },
  ];

  const formatXAxis = (dateStr: string) => {
    try {
      const date = parseISO(dateStr);
      if (period === '7d') {
        return format(date, 'd MMM', { locale: th });
      } else if (period === '30d') {
        return format(date, 'd MMM', { locale: th });
      } else {
        return format(date, 'MMM', { locale: th });
      }
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-slate-900">
          Sentiment Trend
        </h3>
        <div className="flex gap-1 bg-slate-100 p-1 rounded-lg">
          {periodOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setPeriod(option.value)}
              className={cn(
                'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                period === option.value
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-[280px]">
        {isLoading || !trendData ? (
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
