'use client';

import { useMemo } from 'react';
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
import { useDashboardDate } from '@/context/DashboardDateContext';

// Granularity display labels (Thai)
const GRANULARITY_LABELS = {
  daily: 'รายวัน',
  weekly: 'รายสัปดาห์',
  monthly: 'รายเดือน',
  quarterly: 'รายไตรมาส',
} as const;

export function TrendLineChart() {
  // Get dashboard date context
  const { effectiveDates } = useDashboardDate();

  // Fetch trend data using dashboard's date range
  const { data: trendResponse, isLoading } = useDashboardTrends(
    effectiveDates ? { start_date: effectiveDates.start_date, end_date: effectiveDates.end_date } : undefined
  );

  // Extract granularity and data from response
  const granularity = trendResponse?.granularity ?? 'daily';
  const trendData = trendResponse?.data ?? [];

  const formatDate = useMemo(() => {
    return (dateStr: string) => {
      const date = new Date(dateStr);
      switch (granularity) {
        case 'daily':
          return format(date, 'EEE d', { locale: th });
        case 'weekly':
          return format(date, 'd MMM', { locale: th });
        case 'monthly':
          return format(date, 'MMM yy', { locale: th });
        case 'quarterly':
          const quarter = Math.ceil((date.getMonth() + 1) / 3);
          return `Q${quarter} ${format(date, 'yy', { locale: th })}`;
        default:
          return format(date, 'dd/MM', { locale: th });
      }
    };
  }, [granularity]);

  const chartData = trendData.map((item) => ({
    ...item,
    dateFormatted: formatDate(item.date),
  }));

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Sentiment Trends</CardTitle>
          <span className="px-3 py-1.5 text-sm font-medium text-slate-600 bg-slate-100 rounded-lg">
            {GRANULARITY_LABELS[granularity]}
          </span>
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
