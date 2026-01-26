'use client';

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { AspectSummary } from '@/lib/types';
import { getAspectLabel } from '@/lib/utils';

interface SatisfactionRadarChartProps {
  data: AspectSummary[];
}

// All 8 aspects for the octagon shape
const ALL_ASPECTS = [
  'staff',
  'equipment',
  'price',
  'atmosphere',
  'cleanliness',
  'programs',
  'location',
  'amenities',
];

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      aspect: string;
      aspectLabel: string;
      score: number;
    };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const { aspectLabel, score } = payload[0].payload;

  return (
    <div className="bg-white px-3 py-2 rounded-lg shadow-lg border border-slate-200">
      <p className="text-sm font-medium text-slate-900">{aspectLabel}</p>
      <p className="text-sm text-slate-600">
        Score: <span className="font-medium text-purple-600">{score}</span>/100
      </p>
    </div>
  );
}

export function SatisfactionRadarChart({ data }: SatisfactionRadarChartProps) {
  // Create data for all 8 aspects (even if some have no data)
  const chartData = ALL_ASPECTS.map((aspect) => {
    const aspectData = data.find((d) => d.aspect === aspect);
    return {
      aspect,
      aspectLabel: getAspectLabel(aspect),
      score: aspectData ? Math.round(aspectData.satisfaction_score) : 50, // Default to 50 if no data
      fullMark: 100,
    };
  });

  const hasData = data.length > 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
      <h3 className="text-base font-semibold text-slate-900 mb-4">
        Satisfaction Score
      </h3>

      {!hasData ? (
        <div className="flex items-center justify-center h-[280px] text-slate-400">
          No data available
        </div>
      ) : (
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis
                dataKey="aspectLabel"
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickLine={false}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                tickCount={5}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Radar
                name="Satisfaction"
                dataKey="score"
                stroke="#8b5cf6"
                strokeWidth={2}
                fill="#8b5cf6"
                fillOpacity={0.3}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
