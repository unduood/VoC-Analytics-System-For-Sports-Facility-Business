'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { getSourceLabel } from '@/lib/utils';
import type { SourceDistribution } from '@/lib/types';

interface SourceBarChartProps {
  data: SourceDistribution;
}

// Distinct colors for each source
const SOURCE_COLORS: Record<string, string> = {
  google_maps: '#4285f4',   // Google Blue
  facebook: '#1877f2',      // Facebook Blue
  google_form: '#34a853',   // Google Green
  instagram: '#e4405f',     // Instagram Pink
  email: '#6366f1',         // Indigo
  manual: '#8b5cf6',        // Purple
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      source: string;
      name: string;
      count: number;
    };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const { name, count, source } = payload[0].payload;

  return (
    <div className="bg-white px-3 py-2 rounded-lg shadow-lg border border-slate-200">
      <div className="flex items-center gap-2">
        <div
          className="w-3 h-3 rounded"
          style={{ backgroundColor: SOURCE_COLORS[source] }}
        />
        <span className="text-sm font-medium text-slate-900">{name}</span>
      </div>
      <p className="text-sm text-slate-600 mt-1">
        Count: <span className="font-medium">{count}</span>
      </p>
    </div>
  );
}

export function SourceBarChart({ data }: SourceBarChartProps) {
  const chartData = [
    { source: 'google_maps', name: getSourceLabel('google_maps'), count: data.google_maps },
    { source: 'facebook', name: getSourceLabel('facebook'), count: data.facebook },
    { source: 'google_form', name: getSourceLabel('google_form'), count: data.google_form },
    { source: 'instagram', name: getSourceLabel('instagram'), count: data.instagram },
    { source: 'email', name: getSourceLabel('email'), count: data.email },
    { source: 'manual', name: getSourceLabel('manual'), count: data.manual },
  ];

  const hasData = chartData.some((item) => item.count > 0);

  // Find top source
  const topSource = chartData.reduce((prev, current) =>
    (current.count > prev.count) ? current : prev
  );
  const totalFeedback = chartData.reduce((sum, item) => sum + item.count, 0);
  const activeChannels = chartData.filter(item => item.count > 0).length;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
      <div className="mb-3">
        <h3 className="text-base font-semibold text-slate-900">
          Feedback by Source
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          {activeChannels} of 6 channels active
        </p>
      </div>

      {hasData ? (
        <>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                  angle={-35}
                  textAnchor="end"
                  height={60}
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  width={35}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={SOURCE_COLORS[entry.source]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Top source insight */}
          <p className="text-xs text-slate-500 mt-2 pt-2 border-t border-slate-100">
            Top source: <span className="font-medium text-slate-700">{topSource.name}</span>
            {' '}({Math.round((topSource.count / totalFeedback) * 100)}%)
          </p>
        </>
      ) : (
        <div className="flex items-center justify-center h-[280px] text-slate-400">
          No data available
        </div>
      )}
    </div>
  );
}
