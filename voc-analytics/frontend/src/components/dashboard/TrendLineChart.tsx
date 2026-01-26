'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';
import { th } from 'date-fns/locale';
import { useDashboardTrends } from '@/hooks/useDashboard';

export function TrendLineChart() {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('7d');
  const { data: trendData, isLoading } = useDashboardTrends(period);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    if (period === '7d') {
      return format(date, 'EEE', { locale: th });
    } else if (period === '30d') {
      return format(date, 'dd MMM', { locale: th });
    } else {
      return format(date, 'dd/MM', { locale: th });
    }
  };

  const chartData = (trendData || []).map((item) => ({
    ...item,
    dateFormatted: formatDate(item.date),
  }));

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Sentiment Trends</CardTitle>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as '7d' | '30d' | '90d')}
            className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="7d">7 วัน</option>
            <option value="30d">30 วัน</option>
            <option value="90d">90 วัน</option>
          </select>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center h-[250px]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          </div>
        ) : chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="dateFormatted"
                tick={{ fill: '#64748b', fontSize: 12 }}
                tickLine={{ stroke: '#cbd5e1' }}
              />
              <YAxis
                tick={{ fill: '#64748b', fontSize: 12 }}
                tickLine={{ stroke: '#cbd5e1' }}
              />
              <Tooltip
                labelFormatter={(label, payload) => {
                  if (payload && payload.length > 0) {
                    return format(new Date(payload[0].payload.date), 'dd MMMM yyyy', {
                      locale: th,
                    });
                  }
                  return label;
                }}
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '10px' }}
                formatter={(value) => (
                  <span className="text-sm text-slate-700">{value}</span>
                )}
              />
              <Line
                type="monotone"
                dataKey="positive"
                name="เชิงบวก"
                stroke="#22c55e"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="neutral"
                name="เป็นกลาง"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="negative"
                name="เชิงลบ"
                stroke="#ef4444"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
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
