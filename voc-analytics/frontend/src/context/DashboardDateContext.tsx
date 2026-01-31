'use client';

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
  type ReactNode,
} from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import type { DatePreset, DashboardDateParams } from '@/lib/types';

// Helper to format date to ISO string (YYYY-MM-DD)
function formatDateISO(date: Date): string {
  return format(date, 'yyyy-MM-dd');
}

// Calculate date range from preset
function getDateRangeFromPreset(preset: DatePreset): { start_date: string; end_date: string } | null {
  const today = new Date();
  const endDate = formatDateISO(endOfDay(today));

  switch (preset) {
    case 'today':
      return { start_date: formatDateISO(startOfDay(today)), end_date: endDate };
    case '7d':
      return { start_date: formatDateISO(subDays(today, 6)), end_date: endDate };
    case '30d':
      return { start_date: formatDateISO(subDays(today, 29)), end_date: endDate };
    case '90d':
      return { start_date: formatDateISO(subDays(today, 89)), end_date: endDate };
    case 'all':
      return null; // No date filter for "all"
    default:
      return { start_date: formatDateISO(subDays(today, 6)), end_date: endDate };
  }
}

// Calculate the span in days from date params
export function getDateSpanDays(params: DashboardDateParams | null): number | null {
  if (!params) return null;

  if (params.preset === 'all') return null;

  if (params.preset) {
    switch (params.preset) {
      case 'today': return 1;
      case '7d': return 7;
      case '30d': return 30;
      case '90d': return 90;
      default: return null;
    }
  }

  if (params.start_date && params.end_date) {
    const start = new Date(params.start_date);
    const end = new Date(params.end_date);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
  }

  return null;
}

interface DashboardDateContextValue {
  dateParams: DashboardDateParams;
  setDateParams: (params: DashboardDateParams) => void;
  clearDateParams: () => void;
  effectiveDates: { start_date: string; end_date: string } | null;
  activePreset: DatePreset | null;
  spanDays: number | null;
}

const DashboardDateContext = createContext<DashboardDateContextValue | null>(null);

// Default preset
const DEFAULT_PRESET: DatePreset = '7d';

interface DashboardDateProviderProps {
  children: ReactNode;
}

export function DashboardDateProvider({ children }: DashboardDateProviderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Initialize state from URL or defaults
  const [dateParams, setDateParamsState] = useState<DashboardDateParams>(() => {
    const presetParam = searchParams.get('preset') as DatePreset | null;
    const startParam = searchParams.get('start');
    const endParam = searchParams.get('end');

    // If custom dates in URL
    if (startParam && endParam) {
      return { start_date: startParam, end_date: endParam };
    }

    // If preset in URL
    if (presetParam && ['today', '7d', '30d', '90d', 'all'].includes(presetParam)) {
      return { preset: presetParam };
    }

    // Default to 7 days
    return { preset: DEFAULT_PRESET };
  });

  // Compute effective dates from params
  const effectiveDates = useMemo((): { start_date: string; end_date: string } | null => {
    if (dateParams.preset) {
      return getDateRangeFromPreset(dateParams.preset);
    }
    if (dateParams.start_date && dateParams.end_date) {
      return { start_date: dateParams.start_date, end_date: dateParams.end_date };
    }
    return null;
  }, [dateParams]);

  // Get active preset (null if custom range)
  const activePreset = useMemo((): DatePreset | null => {
    return dateParams.preset ?? null;
  }, [dateParams]);

  // Get span in days
  const spanDays = useMemo(() => getDateSpanDays(dateParams), [dateParams]);

  // Sync to URL
  useEffect(() => {
    const params = new URLSearchParams();

    if (dateParams.preset) {
      if (dateParams.preset !== DEFAULT_PRESET) {
        params.set('preset', dateParams.preset);
      }
    } else if (dateParams.start_date && dateParams.end_date) {
      params.set('start', dateParams.start_date);
      params.set('end', dateParams.end_date);
    }

    const queryString = params.toString();
    const newUrl = queryString ? `${pathname}?${queryString}` : pathname;

    // Only update if URL actually changed
    const currentUrl = searchParams.toString() ? `${pathname}?${searchParams.toString()}` : pathname;
    if (newUrl !== currentUrl) {
      router.replace(newUrl, { scroll: false });
    }
  }, [dateParams, pathname, router, searchParams]);

  const setDateParams = useCallback((params: DashboardDateParams) => {
    setDateParamsState(params);
  }, []);

  const clearDateParams = useCallback(() => {
    setDateParamsState({ preset: DEFAULT_PRESET });
  }, []);

  const value = useMemo(
    () => ({
      dateParams,
      setDateParams,
      clearDateParams,
      effectiveDates,
      activePreset,
      spanDays,
    }),
    [dateParams, setDateParams, clearDateParams, effectiveDates, activePreset, spanDays]
  );

  return (
    <DashboardDateContext.Provider value={value}>
      {children}
    </DashboardDateContext.Provider>
  );
}

export function useDashboardDate() {
  const context = useContext(DashboardDateContext);
  if (!context) {
    throw new Error('useDashboardDate must be used within a DashboardDateProvider');
  }
  return context;
}
