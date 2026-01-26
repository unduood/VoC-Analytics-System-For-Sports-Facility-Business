'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { PieLabelRenderProps } from 'recharts';
import type { SentimentDistribution } from '@/lib/types';

interface SentimentPieChartProps {
  data: SentimentDistribution;
}

const COLORS = {
  positive: '#22c55e', // green-500
  neutral: '#f59e0b', // amber-500
  negative: '#ef4444', // red-500
};

export function SentimentPieChart({ data }: SentimentPieChartProps) {
  const chartData = [
    { name: 'เชิงบวก', value: data.positive, color: COLORS.positive },
    { name: 'เป็นกลาง', value: data.neutral, color: COLORS.neutral },
    { name: 'เชิงลบ', value: data.negative, color: COLORS.negative },
  ].filter((item) => item.value > 0);

  const total = data.positive + data.neutral + data.negative;

  const renderLabel = (props: PieLabelRenderProps) => {
    const { cx, cy, midAngle, innerRadius, outerRadius, percent } = props;

    // Handle optional values with defaults
    const cxNum = typeof cx === 'number' ? cx : 0;
    const cyNum = typeof cy === 'number' ? cy : 0;
    const midAngleNum = typeof midAngle === 'number' ? midAngle : 0;
    const innerRadiusNum = typeof innerRadius === 'number' ? innerRadius : 0;
    const outerRadiusNum = typeof outerRadius === 'number' ? outerRadius : 0;
    const percentNum = typeof percent === 'number' ? percent : 0;

    const RADIAN = Math.PI / 180;
    const radius = innerRadiusNum + (outerRadiusNum - innerRadiusNum) * 0.5;
    const x = cxNum + radius * Math.cos(-midAngleNum * RADIAN);
    const y = cyNum + radius * Math.sin(-midAngleNum * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cxNum ? 'start' : 'end'}
        dominantBaseline="central"
        className="font-semibold text-sm"
      >
        {`${(percentNum * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sentiment Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {total > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderLabel}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => [`${value} รายการ`, '']}
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                }}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value) => <span className="text-sm text-slate-700">{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[250px] text-slate-500">
            ไม่มีข้อมูล
          </div>
        )}
      </CardContent>
    </Card>
  );
}
