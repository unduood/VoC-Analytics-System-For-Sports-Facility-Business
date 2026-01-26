import { useQuery } from '@tanstack/react-query';
import { getDashboardOverview, getTrendData } from '@/lib/api';
import { feedbackKeys } from './useFeedback';

/**
 * Hook to fetch dashboard overview data with auto-refresh
 */
export function useDashboardOverview() {
  return useQuery({
    queryKey: feedbackKeys.dashboard(),
    queryFn: getDashboardOverview,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto refetch every 60 seconds (WebSocket handles real-time)
    refetchOnWindowFocus: true,
    retry: 2,
  });
}

/**
 * Hook to fetch sentiment trend data
 * @param period - Time period: '7d', '30d', or '90d'
 */
export function useDashboardTrends(period: '7d' | '30d' | '90d' = '7d') {
  return useQuery({
    queryKey: feedbackKeys.trends(period),
    queryFn: () => getTrendData(period),
    staleTime: 60 * 1000, // 1 minute
    refetchOnWindowFocus: true,
    retry: 2,
  });
}
