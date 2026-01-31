import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getFeedbackList,
  getFeedbackById,
  submitManualFeedback,
  deleteFeedback,
} from '@/lib/api';
import type { FeedbackListParams, DashboardDateParams } from '@/lib/types';

// Query keys (shared across hooks)
export const feedbackKeys = {
  all: ['feedback'] as const,
  lists: () => [...feedbackKeys.all, 'list'] as const,
  list: (params: FeedbackListParams) => [...feedbackKeys.lists(), params] as const,
  details: () => [...feedbackKeys.all, 'detail'] as const,
  detail: (id: string) => [...feedbackKeys.details(), id] as const,
  dashboard: (params?: DashboardDateParams) => [...feedbackKeys.all, 'dashboard', params ?? {}] as const,
  trends: (params?: { start_date?: string; end_date?: string }) => [...feedbackKeys.all, 'trends', params ?? {}] as const,
};

/**
 * Hook to fetch paginated feedback list
 */
export function useFeedbackList(params: FeedbackListParams = {}) {
  return useQuery({
    queryKey: feedbackKeys.list(params),
    queryFn: () => getFeedbackList(params),
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook to fetch a single feedback record by ID
 */
export function useFeedbackDetail(id: string | null) {
  return useQuery({
    queryKey: feedbackKeys.detail(id || ''),
    queryFn: () => getFeedbackById(id!),
    enabled: !!id, // Only run query if id is provided
  });
}

/**
 * Hook to submit manual feedback
 */
export function useSubmitFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (text: string) => submitManualFeedback(text),
    onSuccess: () => {
      // Invalidate and refetch feedback lists, dashboard, and trends
      queryClient.invalidateQueries({ queryKey: feedbackKeys.lists() });
      queryClient.invalidateQueries({ queryKey: feedbackKeys.dashboard() });
      // Invalidate all trend queries (using prefix match)
      queryClient.invalidateQueries({ queryKey: [...feedbackKeys.all, 'trends'] });
    },
  });
}

/**
 * Hook to delete feedback
 */
export function useDeleteFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteFeedback(id),
    onSuccess: () => {
      // Invalidate and refetch feedback lists, dashboard, and trends
      queryClient.invalidateQueries({ queryKey: feedbackKeys.lists() });
      queryClient.invalidateQueries({ queryKey: feedbackKeys.dashboard() });
      // Invalidate all trend queries (using prefix match)
      queryClient.invalidateQueries({ queryKey: [...feedbackKeys.all, 'trends'] });
    },
  });
}
