import { useQuery } from '@tanstack/react-query';
import { healthCheck } from '@/lib/api';

export type ApiHealthStatus = 'healthy' | 'unhealthy' | 'checking';

interface UseApiHealthReturn {
  status: ApiHealthStatus;
  isHealthy: boolean;
  lastChecked: Date | null;
  error: Error | null;
  refetch: () => void;
}

/**
 * Hook to check API health status
 * Checks every 30 seconds
 */
export function useApiHealth(): UseApiHealthReturn {
  const { data, error, isLoading, isError, dataUpdatedAt, refetch } = useQuery({
    queryKey: ['api-health'],
    queryFn: healthCheck,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 30 * 1000, // Check every 30 seconds
    retry: 1,
    refetchOnWindowFocus: true,
  });

  let status: ApiHealthStatus = 'checking';
  if (isLoading) {
    status = 'checking';
  } else if (isError || !data) {
    status = 'unhealthy';
  } else if (data.status === 'healthy') {
    status = 'healthy';
  } else {
    status = 'unhealthy';
  }

  return {
    status,
    isHealthy: status === 'healthy',
    lastChecked: dataUpdatedAt ? new Date(dataUpdatedAt) : null,
    error: error as Error | null,
    refetch,
  };
}
