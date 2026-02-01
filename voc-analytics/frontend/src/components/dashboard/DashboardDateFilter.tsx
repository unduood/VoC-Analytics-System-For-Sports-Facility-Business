'use client';

import { useState, useCallback } from 'react';
import { format, parseISO, isValid, isAfter, startOfDay } from 'date-fns';
import { th } from 'date-fns/locale';
import { Calendar, X } from 'lucide-react';
import { useDashboardDate } from '@/context/DashboardDateContext';
import { cn } from '@/lib/utils';
import type { DatePreset } from '@/lib/types';

// Thai localization for presets
const PRESET_LABELS: Record<DatePreset, { en: string; th: string }> = {
  today: { en: 'Today', th: 'วันนี้' },
  '7d': { en: '7 Days', th: '7 วันที่ผ่านมา' },
  '30d': { en: '30 Days', th: '30 วันที่ผ่านมา' },
  '90d': { en: '90 Days', th: '90 วันที่ผ่านมา' },
  all: { en: 'All Time', th: 'ทั้งหมด' },
};

const PRESETS: DatePreset[] = ['today', '7d', '30d', '90d', 'all'];

export function DashboardDateFilter() {
  const { dateParams, setDateParams, clearDateParams, effectiveDates, activePreset } = useDashboardDate();

  // Local state for custom date inputs
  const [customStart, setCustomStart] = useState(dateParams.start_date || '');
  const [customEnd, setCustomEnd] = useState(dateParams.end_date || '');
  const [error, setError] = useState<string | null>(null);

  // Handle preset click
  const handlePresetClick = useCallback((preset: DatePreset) => {
    setDateParams({ preset });
    setCustomStart('');
    setCustomEnd('');
    setError(null);
  }, [setDateParams]);

  // Validate and apply custom date range
  const applyCustomRange = useCallback(() => {
    if (!customStart || !customEnd) {
      setError('กรุณาเลือกวันที่เริ่มต้นและสิ้นสุด');
      return;
    }

    const startDate = parseISO(customStart);
    const endDate = parseISO(customEnd);

    if (!isValid(startDate) || !isValid(endDate)) {
      setError('รูปแบบวันที่ไม่ถูกต้อง');
      return;
    }

    if (isAfter(startDate, endDate)) {
      setError('วันที่เริ่มต้นต้องไม่เกินวันที่สิ้นสุด');
      return;
    }

    const today = startOfDay(new Date());
    if (isAfter(startDate, today)) {
      setError('วันที่เริ่มต้นต้องไม่เกินวันนี้');
      return;
    }

    setError(null);
    setDateParams({ start_date: customStart, end_date: customEnd });
  }, [customStart, customEnd, setDateParams]);

  // Handle clear
  const handleClear = useCallback(() => {
    clearDateParams();
    setCustomStart('');
    setCustomEnd('');
    setError(null);
  }, [clearDateParams]);

  // Format the active date range for display
  const formatDateRange = (): string => {
    if (!effectiveDates) {
      return 'ทุกช่วงเวลา';
    }
    const start = parseISO(effectiveDates.start_date);
    const end = parseISO(effectiveDates.end_date);
    return `${format(start, 'd MMM yyyy', { locale: th })} - ${format(end, 'd MMM yyyy', { locale: th })}`;
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center gap-4">
        {/* Preset Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {PRESETS.map((preset) => (
            <button
              key={preset}
              onClick={() => handlePresetClick(preset)}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors',
                activePreset === preset
                  ? 'bg-emerald-500 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900'
              )}
            >
              {PRESET_LABELS[preset].th}
            </button>
          ))}
        </div>

        {/* Divider */}
        <div className="hidden lg:block w-px h-8 bg-slate-200" />

        {/* Custom Date Range */}
        <div className="flex flex-wrap items-center gap-2">
          <Calendar className="w-4 h-4 text-slate-400" />
          <input
            type="date"
            value={customStart}
            onChange={(e) => {
              setCustomStart(e.target.value);
              setError(null);
            }}
            className={cn(
              'px-3 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500',
              error ? 'border-red-300' : 'border-slate-200'
            )}
            placeholder="เริ่มต้น"
            max={format(new Date(), 'yyyy-MM-dd')}
          />
          <span className="text-slate-400 text-sm">ถึง</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => {
              setCustomEnd(e.target.value);
              setError(null);
            }}
            className={cn(
              'px-3 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500',
              error ? 'border-red-300' : 'border-slate-200'
            )}
            placeholder="สิ้นสุด"
            max={format(new Date(), 'yyyy-MM-dd')}
          />
          <button
            onClick={applyCustomRange}
            disabled={!customStart || !customEnd}
            className="px-3 py-1.5 text-sm font-medium bg-slate-900 text-white rounded-lg hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            ใช้งาน
          </button>
          {(activePreset !== '7d' || customStart || customEnd) && (
            <button
              onClick={handleClear}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              title="ล้าง"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <p className="mt-2 text-sm text-red-500">{error}</p>
      )}

      {/* Active Range Display */}
      <div className="mt-3 pt-3 border-t border-slate-100">
        <p className="text-sm text-slate-500">
          แสดงข้อมูล: <span className="font-medium text-slate-700">{formatDateRange()}</span>
        </p>
      </div>
    </div>
  );
}
