'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { IntentDistribution } from '@/lib/types';
import { getIntentLabel } from '@/lib/utils';

interface IntentPieChartProps {
  data: IntentDistribution;
}

const COLORS = {
  feedback: '#3b82f6',   // blue-500
  complaint: '#ef4444',  // red-500
  question: '#8b5cf6',   // purple-500
  off_topic: '#94a3b8',  // slate-400
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
        {getIntentLabel(name)}
      </p>
      <p className="text-sm text-slate-600">
        {value.toLocaleString()} ({percentage}%)
      </p>
    </div>
  );
}

export function IntentPieChart({ data }: IntentPieChartProps) {
  const total = data.feedback + data.complaint + data.question + data.off_topic;

  const chartData = [
    {
      name: 'feedback',
      value: data.feedback,
      percentage: total > 0 ? Math.round((data.feedback / total) * 100) : 0,
    },
    {
      name: 'complaint',
      value: data.complaint,
      percentage: total > 0 ? Math.round((data.complaint / total) * 100) : 0,
    },
    {
      name: 'question',
      value: data.question,
      percentage: total > 0 ? Math.round((data.question / total) * 100) : 0,
    },
    {
      name: 'off_topic',
      value: data.off_topic,
      percentage: total > 0 ? Math.round((data.off_topic / total) * 100) : 0,
    },
  ].filter((item) => item.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
        <h3 className="text-base font-semibold text-slate-900 mb-4">
          Intent Classification
        </h3>
        <div className="flex items-center justify-center h-[250px] text-slate-400">
          No data available
        </div>
      </div>
    );
  }

  // Find complaint data for insight display
  const complaintData = chartData.find(item => item.name === 'complaint');

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
      <div className="mb-3">
        <h3 className="text-base font-semibold text-slate-900">
          Intent Classification
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Why customers are reaching out
        </p>
      </div>

      <div className="h-[180px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={75}
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
      <div className="grid grid-cols-2 gap-2 mt-2">
        {chartData.map((item) => (
          <div key={item.name} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full flex-shrink-0"
              style={{ backgroundColor: COLORS[item.name as keyof typeof COLORS] }}
            />
            <div className="flex-1 min-w-0">
              <span className="text-xs text-slate-600 truncate block">
                {getIntentLabel(item.name)}
              </span>
              <span className="text-xs font-medium text-slate-900">
                {item.value} <span className="text-slate-400">({item.percentage}%)</span>
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Intent explanation */}
      {complaintData && complaintData.value > 0 && (
        <p className="text-xs text-red-600 mt-3 pt-2 border-t border-slate-100">
          {complaintData.percentage}% are complaints requiring action
        </p>
      )}
    </div>
  );
}
