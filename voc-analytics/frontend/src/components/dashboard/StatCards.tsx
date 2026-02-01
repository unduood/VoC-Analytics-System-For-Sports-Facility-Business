'use client';

import { MessageSquare, TrendingUp, TrendingDown, AlertTriangle, Star, Sparkles, MinusCircle } from 'lucide-react';
import type { DashboardOverview, TrendInfo } from '@/lib/types';
import { cn } from '@/lib/utils';

interface StatCardsProps {
  data: DashboardOverview;
}

/**
 * Determines the trend display state based on current and previous counts.
 * Handles edge cases for clearer user understanding.
 */
function getTrendDisplayState(trendInfo: TrendInfo | null) {
  if (!trendInfo) {
    return { type: 'unavailable' as const };
  }

  const { current_count, previous_count, percentage, comparison_label } = trendInfo;
  const countChange = current_count - previous_count;

  // Edge case: Both periods have no data
  if (previous_count === 0 && current_count === 0) {
    return {
      type: 'no_data' as const,
      label: comparison_label,
    };
  }

  // Edge case: Previous period was empty, current has data (new activity)
  if (previous_count === 0 && current_count > 0) {
    return {
      type: 'new_activity' as const,
      currentCount: current_count,
      label: comparison_label,
    };
  }

  // Edge case: Current period has no data but previous did
  if (current_count === 0 && previous_count > 0) {
    return {
      type: 'no_activity' as const,
      previousCount: previous_count,
      label: comparison_label,
    };
  }

  // Normal case: Both periods have data
  return {
    type: 'normal' as const,
    percentage,
    countChange,
    label: comparison_label,
  };
}

/**
 * Formats the count change as a string (e.g., "+29" or "-10")
 */
function formatCountChange(change: number): string {
  if (change > 0) return `+${change.toLocaleString()}`;
  if (change < 0) return change.toLocaleString(); // Already has minus sign
  return '0';
}

export function StatCards({ data }: StatCardsProps) {
  // Get trend display state for Total Feedback card
  const trendState = getTrendDisplayState(data.trend_info);

  const stats = [
    {
      title: 'Total Feedback',
      value: data.total_feedbacks.toLocaleString(),
      // Custom rendering handled separately for this card
      isTotalFeedback: true,
      icon: MessageSquare,
      iconBg: 'bg-indigo-100',
      iconColor: 'text-indigo-600',
    },
    {
      title: 'Positive Rate',
      value: `${data.positive_rate}%`,
      subtitle: 'positive sentiment detected',
      benchmark: data.positive_rate >= 70 ? 'above' : data.positive_rate >= 50 ? 'average' : 'below',
      progress: data.positive_rate,
      progressColor: data.positive_rate >= 70 ? 'bg-emerald-500' : data.positive_rate >= 50 ? 'bg-amber-500' : 'bg-red-500',
      icon: TrendingUp,
      iconBg: 'bg-emerald-100',
      iconColor: 'text-emerald-600',
    },
    {
      title: 'Complaints',
      value: data.complaint_count.toLocaleString(),
      subtitle: 'require follow-up',
      alertLevel: data.complaint_count > 10 ? 'high' : data.complaint_count > 5 ? 'medium' : 'low',
      icon: AlertTriangle,
      iconBg: 'bg-amber-100',
      iconColor: 'text-amber-600',
    },
    {
      title: 'Avg Score',
      value: data.avg_satisfaction.toFixed(1),
      subtitle: 'out of 100 points',
      progress: data.avg_satisfaction,
      progressColor: data.avg_satisfaction >= 70 ? 'bg-purple-500' : data.avg_satisfaction >= 50 ? 'bg-amber-500' : 'bg-red-500',
      icon: Star,
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
    },
  ];

  // Render trend info for Total Feedback card based on state
  const renderTotalFeedbackTrend = () => {
    switch (trendState.type) {
      case 'unavailable':
        return (
          <p className="mt-1 text-xs text-slate-400">Trend data unavailable</p>
        );

      case 'no_data':
        return (
          <div className="mt-1">
            <div className="inline-flex items-center gap-1 text-xs text-slate-400">
              <MinusCircle className="w-3 h-3" />
              <span>No data in either period</span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">{trendState.label}</p>
          </div>
        );

      case 'new_activity':
        return (
          <div className="mt-1">
            <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-xs font-medium">
              <Sparkles className="w-3 h-3" />
              <span>New: {trendState.currentCount.toLocaleString()} feedback{trendState.currentCount !== 1 ? 's' : ''}</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">{trendState.label}</p>
          </div>
        );

      case 'no_activity':
        return (
          <div className="mt-1">
            <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-xs font-medium">
              <MinusCircle className="w-3 h-3" />
              <span>No activity this period</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Previously: {trendState.previousCount.toLocaleString()} · {trendState.label}
            </p>
          </div>
        );

      case 'normal':
        const isPositive = trendState.percentage >= 0;
        const isZeroChange = trendState.countChange === 0;
        return (
          <div className="mt-1">
            {/* Percentage with icon */}
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  'flex items-center text-sm font-medium',
                  isZeroChange ? 'text-slate-500' :
                  isPositive ? 'text-emerald-600' : 'text-red-600'
                )}
              >
                {isZeroChange ? null : isPositive ? (
                  <TrendingUp className="w-4 h-4 mr-0.5" />
                ) : (
                  <TrendingDown className="w-4 h-4 mr-0.5" />
                )}
                {isZeroChange ? 'No change' : `${Math.abs(trendState.percentage)}%`}
              </span>
              {/* Count change */}
              {!isZeroChange && (
                <span className={cn(
                  'text-xs',
                  isPositive ? 'text-emerald-600' : 'text-red-600'
                )}>
                  ({formatCountChange(trendState.countChange)})
                </span>
              )}
            </div>
            {/* Comparison label */}
            <p className="text-xs text-slate-400 mt-0.5">{trendState.label}</p>
          </div>
        );
    }
  };

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

                {/* Value display */}
                <p className="mt-2 text-2xl font-bold text-slate-900">{stat.value}</p>

                {/* Total Feedback card: custom trend rendering */}
                {stat.isTotalFeedback && renderTotalFeedbackTrend()}

                {/* Other cards: standard subtitle */}
                {!stat.isTotalFeedback && stat.subtitle && (
                  <p className="mt-1 text-xs text-slate-400">{stat.subtitle}</p>
                )}

                {/* Benchmark indicator (Positive Rate) */}
                {stat.benchmark && (
                  <p className={cn(
                    'mt-0.5 text-xs font-medium',
                    stat.benchmark === 'above' ? 'text-emerald-600' :
                    stat.benchmark === 'below' ? 'text-red-500' : 'text-slate-500'
                  )}>
                    {stat.benchmark === 'above' ? 'Above target (70%)' :
                     stat.benchmark === 'below' ? 'Below target (70%)' : 'Near target (70%)'}
                  </p>
                )}

                {/* Alert level badge (Complaints) */}
                {stat.alertLevel && (
                  <div className={cn(
                    'mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                    stat.alertLevel === 'high' ? 'bg-red-100 text-red-700' :
                    stat.alertLevel === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
                  )}>
                    {stat.alertLevel === 'high' ? 'High priority' :
                     stat.alertLevel === 'medium' ? 'Moderate' : 'Under control'}
                  </div>
                )}

                {/* Progress bar (Positive Rate, Avg Score) */}
                {stat.progress !== undefined && (
                  <div className="mt-2 w-full bg-slate-100 rounded-full h-1.5">
                    <div
                      className={cn('h-1.5 rounded-full transition-all', stat.progressColor)}
                      style={{ width: `${Math.min(stat.progress, 100)}%` }}
                    />
                  </div>
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
