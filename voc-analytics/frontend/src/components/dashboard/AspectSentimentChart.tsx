'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getAspectLabel } from '@/lib/utils';
import type { AspectSummary } from '@/lib/types';

interface AspectSentimentChartProps {
  data: AspectSummary[];
}

export function AspectSentimentChart({ data }: AspectSentimentChartProps) {
  const chartData = data
    .filter((item) => item.total_mentions > 0)
    .map((item) => ({
      aspect: getAspectLabel(item.aspect),
      positive: item.positive,
      neutral: item.neutral,
      negative: item.negative,
    }))
    .sort((a, b) => (b.positive + b.neutral + b.negative) - (a.positive + a.neutral + a.negative));

  const hasData = chartData.length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Aspect Sentiment Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        {hasData ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                type="number"
                tick={{ fill: '#64748b', fontSize: 12 }}
                tickLine={{ stroke: '#cbd5e1' }}
              />
              <YAxis
                type="category"
                dataKey="aspect"
                tick={{ fill: '#64748b', fontSize: 12 }}
                tickLine={{ stroke: '#cbd5e1' }}
                width={120}
              />
              <Tooltip
                cursor={{ fill: 'rgba(99, 102, 241, 0.05)' }}
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '10px' }}
                formatter={(value) => {
                  const labels: Record<string, string> = {
                    positive: 'เชิงบวก',
                    neutral: 'เป็นกลาง',
                    negative: 'เชิงลบ',
                  };
                  return <span className="text-sm text-slate-700">{labels[value] || value}</span>;
                }}
              />
              <Bar dataKey="positive" stackId="a" fill="#22c55e" radius={[0, 4, 4, 0]} />
              <Bar dataKey="neutral" stackId="a" fill="#f59e0b" />
              <Bar dataKey="negative" stackId="a" fill="#ef4444" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[300px] text-slate-500">
            ไม่มีข้อมูล
          </div>
        )}
      </CardContent>
    </Card>
  );
}
