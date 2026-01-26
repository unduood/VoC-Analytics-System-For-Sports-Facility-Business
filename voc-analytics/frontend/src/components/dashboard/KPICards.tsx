import { Card } from '@/components/ui/Card';
import { MessageSquare, TrendingUp, Users, Star } from 'lucide-react';
import type { DashboardOverview } from '@/lib/types';

interface KPICardsProps {
  data: DashboardOverview;
}

export function KPICards({ data }: KPICardsProps) {
  const totalFeedbacks = data.total_feedbacks;
  const sentimentTotal =
    data.sentiment_distribution.positive +
    data.sentiment_distribution.neutral +
    data.sentiment_distribution.negative;

  const positiveRatio = sentimentTotal > 0
    ? (data.sentiment_distribution.positive / sentimentTotal) * 100
    : 0;

  const totalSources = Object.values(data.source_distribution).filter(count => count > 0).length;
  const avgConfidence = data.avg_confidence * 100; // Convert to percentage

  const kpis = [
    {
      label: 'Total Feedbacks',
      value: totalFeedbacks.toLocaleString(),
      icon: MessageSquare,
      iconBg: 'bg-indigo-100',
      iconColor: 'text-indigo-600',
    },
    {
      label: 'Positive Ratio',
      value: `${positiveRatio.toFixed(1)}%`,
      icon: TrendingUp,
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
    },
    {
      label: 'Total Sources',
      value: totalSources.toString(),
      icon: Users,
      iconBg: 'bg-cyan-100',
      iconColor: 'text-cyan-600',
    },
    {
      label: 'Avg Confidence',
      value: `${avgConfidence.toFixed(1)}%`,
      icon: Star,
      iconBg: 'bg-amber-100',
      iconColor: 'text-amber-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi, index) => {
        const Icon = kpi.icon;
        return (
          <Card key={index} className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">{kpi.label}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{kpi.value}</p>
              </div>
              <div className={`p-3 rounded-xl ${kpi.iconBg}`}>
                <Icon className={`w-6 h-6 ${kpi.iconColor}`} />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
