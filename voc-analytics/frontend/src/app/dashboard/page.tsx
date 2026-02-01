'use client';

import { Suspense } from 'react';
import { useDashboardOverview } from '@/hooks/useDashboard';
import { DashboardDateProvider, useDashboardDate } from '@/context/DashboardDateContext';
import { DashboardDateFilter } from '@/components/dashboard/DashboardDateFilter';
import { StatCards } from '@/components/dashboard/StatCards';
import { SentimentDonutChart } from '@/components/dashboard/SentimentDonutChart';
import { SentimentTrendChart } from '@/components/dashboard/SentimentTrendChart';
import { AspectStackedBarChart } from '@/components/dashboard/AspectStackedBarChart';
import { SatisfactionRadarChart } from '@/components/dashboard/SatisfactionRadarChart';
import { SourceBarChart } from '@/components/dashboard/SourceBarChart';
import { IntentPieChart } from '@/components/dashboard/IntentPieChart';
import { RecentComplaints } from '@/components/dashboard/RecentComplaints';
import { AlertCircle, Calendar } from 'lucide-react';

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

// Empty State Component
function EmptyState() {
  return (
    <div className="flex items-center justify-center min-h-[300px]">
      <div className="text-center">
        <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">ไม่พบข้อมูลในช่วงเวลานี้</h3>
        <p className="text-slate-500 text-sm">
          ลองปรับช่วงเวลาที่ต้องการดูข้อมูล หรือเลือก &quot;ทั้งหมด&quot; เพื่อดูข้อมูลทั้งหมด
        </p>
      </div>
    </div>
  );
}

// Dashboard Content Component (uses the date context)
function DashboardContent() {
  const { effectiveDates } = useDashboardDate();
  const { data: overview, isLoading, error } = useDashboardOverview(effectiveDates ?? undefined);

  if (error) {
    return <ErrorState />;
  }

  if (isLoading || !overview) {
    return <LoadingSkeleton />;
  }

  // Check if data is empty
  const isEmpty = overview.total_feedbacks === 0;

  if (isEmpty) {
    return <EmptyState />;
  }

  return (
    <>
      {/* Key Metrics */}
      <StatCards data={overview} />

      {/* Sentiment Charts */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-4">
          <SentimentDonutChart data={overview.sentiment_distribution} />
        </div>
        <div className="col-span-12 lg:col-span-8">
          <SentimentTrendChart />
        </div>
      </div>

      {/* Aspect & Source Charts */}
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

      {/* Intent & Complaints */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-3">
          <IntentPieChart data={overview.intent_distribution} />
        </div>
        <div className="col-span-12 lg:col-span-9">
          <RecentComplaints data={overview.recent_complaints} />
        </div>
      </div>
    </>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <DashboardDateProvider>
        <DashboardPageInner />
      </DashboardDateProvider>
    </Suspense>
  );
}

function DashboardPageInner() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="text-slate-500 mt-1">
          Voice of Customer Analytics - Real-time Insights
        </p>
        <p className="text-xs text-slate-400 mt-2">
          All metrics update automatically. Red indicators highlight areas needing attention.
        </p>
      </div>

      {/* Date Filter */}
      <DashboardDateFilter />

      {/* Dashboard Content */}
      <DashboardContent />
    </div>
  );
}
