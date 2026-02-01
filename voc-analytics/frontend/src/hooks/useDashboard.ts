import { useQuery } from '@tanstack/react-query';
import { getDashboardOverview, getTrendData } from '@/lib/api';
import { feedbackKeys } from './useFeedback';
import type { DashboardDateParams } from '@/lib/types';

/**
 * Hook to fetch dashboard overview data with auto-refresh
 * @param params - Optional date filter parameters
 */
export function useDashboardOverview(params?: DashboardDateParams) {
  return useQuery({
    queryKey: feedbackKeys.dashboard(params),
    queryFn: () => getDashboardOverview(params),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto refetch every 60 seconds (WebSocket handles real-time)
    refetchOnWindowFocus: true,
    retry: 2,
  });
}

/**
 * Hook to fetch sentiment trend data
 * @param params - Optional date filter parameters (start_date, end_date)
 */
export function useDashboardTrends(params?: { start_date?: string; end_date?: string }) {
  return useQuery({
    queryKey: feedbackKeys.trends(params),
    queryFn: () => getTrendData(params),
    staleTime: 60 * 1000, // 1 minute
    refetchOnWindowFocus: true,
    retry: 2,
  });
}
