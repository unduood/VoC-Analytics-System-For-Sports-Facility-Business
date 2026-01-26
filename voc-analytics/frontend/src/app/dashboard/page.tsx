'use client';

import { useDashboardOverview } from '@/hooks/useDashboard';
import { StatCards } from '@/components/dashboard/StatCards';
import { SentimentDonutChart } from '@/components/dashboard/SentimentDonutChart';
import { SentimentTrendChart } from '@/components/dashboard/SentimentTrendChart';
import { AspectStackedBarChart } from '@/components/dashboard/AspectStackedBarChart';
import { SatisfactionRadarChart } from '@/components/dashboard/SatisfactionRadarChart';
import { SourceBarChart } from '@/components/dashboard/SourceBarChart';
import { IntentPieChart } from '@/components/dashboard/IntentPieChart';
import { RecentComplaints } from '@/components/dashboard/RecentComplaints';
import { AlertCircle } from 'lucide-react';

// Loading Skeleton Component
function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Row 1: Stat Cards Skeleton */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 h-28" />
        ))}
      </div>

      {/* Row 2: Donut + Trend Skeleton */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-4 bg-white rounded-xl border border-slate-200 h-[350px]" />
        <div className="col-span-12 lg:col-span-8 bg-white rounded-xl border border-slate-200 h-[350px]" />
      </div>

      {/* Row 3: Aspect + Radar + Source Skeleton */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-5 bg-white rounded-xl border border-slate-200 h-[380px]" />
        <div className="col-span-12 lg:col-span-4 bg-white rounded-xl border border-slate-200 h-[380px]" />
        <div className="col-span-12 lg:col-span-3 bg-white rounded-xl border border-slate-200 h-[380px]" />
      </div>

      {/* Row 4: Intent + Complaints Skeleton */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-3 bg-white rounded-xl border border-slate-200 h-[350px]" />
        <div className="col-span-12 lg:col-span-9 bg-white rounded-xl border border-slate-200 h-[350px]" />
      </div>
    </div>
  );
}

// Error Component
function ErrorState() {
  return (
    <div className="flex items-center justify-center min-h-[500px]">
      <div className="text-center">
        <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Data</h3>
        <p className="text-slate-600">
          Unable to load data. Please check your connection and try again.
        </p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: overview, isLoading, error } = useDashboardOverview();

  if (error) {
    return <ErrorState />;
  }

  if (isLoading || !overview) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="text-slate-500 mt-1">
          Voice of Customer Analytics - Real-time Insights
        </p>
      </div>

      {/* Row 1: Stat Cards (full width, 2 cols mobile, 4 cols desktop) */}
      <StatCards data={overview} />

      {/* Row 2: Sentiment Donut (4 cols) + Sentiment Trend (8 cols) */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-4">
          <SentimentDonutChart data={overview.sentiment_distribution} />
        </div>
        <div className="col-span-12 lg:col-span-8">
          <SentimentTrendChart />
        </div>
      </div>

      {/* Row 3: Aspect Stacked Bar (5 cols) + Satisfaction Radar (4 cols) + Source Bar (3 cols) */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-5">
          <AspectStackedBarChart data={overview.aspect_summary} />
        </div>
        <div className="col-span-12 md:col-span-6 lg:col-span-4">
          <SatisfactionRadarChart data={overview.aspect_summary} />
        </div>
        <div className="col-span-12 md:col-span-6 lg:col-span-3">
          <SourceBarChart data={overview.source_distribution} />
        </div>
      </div>

      {/* Row 4: Intent Pie (3 cols) + Recent Complaints (9 cols) */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-3">
          <IntentPieChart data={overview.intent_distribution} />
        </div>
        <div className="col-span-12 lg:col-span-9">
          <RecentComplaints data={overview.recent_complaints} />
        </div>
      </div>
    </div>
  );
}
