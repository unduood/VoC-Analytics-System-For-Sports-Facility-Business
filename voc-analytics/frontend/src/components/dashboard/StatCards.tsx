'use client';

import { MessageSquare, TrendingUp, TrendingDown, AlertTriangle, Star } from 'lucide-react';
import type { DashboardOverview } from '@/lib/types';
import { cn } from '@/lib/utils';

interface StatCardsProps {
  data: DashboardOverview;
}

export function StatCards({ data }: StatCardsProps) {
  const stats = [
    {
      title: 'Total Feedback',
      value: data.total_feedbacks.toLocaleString(),
      trend: data.trend_percentage,
      icon: MessageSquare,
      iconBg: 'bg-indigo-100',
      iconColor: 'text-indigo-600',
    },
    {
      title: 'Positive Rate',
      value: `${data.positive_rate}%`,
      subtitle: 'of all feedback',
      icon: TrendingUp,
      iconBg: 'bg-emerald-100',
      iconColor: 'text-emerald-600',
    },
    {
      title: 'Complaints',
      value: data.complaint_count.toLocaleString(),
      subtitle: 'need attention',
      icon: AlertTriangle,
      iconBg: 'bg-amber-100',
      iconColor: 'text-amber-600',
    },
    {
      title: 'Avg Score',
      value: data.avg_satisfaction.toFixed(1),
      subtitle: 'satisfaction score',
      icon: Star,
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <div
            key={index}
            className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-500">{stat.title}</p>
                <div className="mt-2 flex items-baseline gap-2">
                  <p className="text-2xl font-bold text-slate-900">{stat.value}</p>
                  {stat.trend !== undefined && (
                    <span
                      className={cn(
                        'flex items-center text-sm font-medium',
                        stat.trend >= 0 ? 'text-emerald-600' : 'text-red-600'
                      )}
                    >
                      {stat.trend >= 0 ? (
                        <TrendingUp className="w-4 h-4 mr-0.5" />
                      ) : (
                        <TrendingDown className="w-4 h-4 mr-0.5" />
                      )}
                      {Math.abs(stat.trend)}%
                    </span>
                  )}
                </div>
                {stat.subtitle && (
                  <p className="mt-1 text-xs text-slate-400">{stat.subtitle}</p>
                )}
              </div>
              <div className={cn('p-3 rounded-xl', stat.iconBg)}>
                <Icon className={cn('w-6 h-6', stat.iconColor)} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
