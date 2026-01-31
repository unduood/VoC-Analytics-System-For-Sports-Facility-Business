import { useState, useEffect, useCallback, useRef } from 'react';
import { Search, AlertCircle } from 'lucide-react';
import type { FeedbackListParams } from '@/lib/types';

interface FeedbackFiltersProps {
  filters: FeedbackListParams;
  onFiltersChange: (filters: FeedbackListParams) => void;
}

// Custom debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function FeedbackFilters({ filters, onFiltersChange }: FeedbackFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search || '');
  const [dateError, setDateError] = useState<string | null>(null);
  const debouncedSearch = useDebounce(searchInput, 300);

  // Use refs to always have latest values without causing effect re-runs
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  const onFiltersChangeRef = useRef(onFiltersChange);
  onFiltersChangeRef.current = onFiltersChange;

  // Apply debounced search
  useEffect(() => {
    const currentFilters = filtersRef.current;
    if (debouncedSearch !== currentFilters.search) {
      onFiltersChangeRef.current({
        ...currentFilters,
        search: debouncedSearch || undefined,
        page: 1,
      });
    }
  }, [debouncedSearch]);

  const updateFilter = useCallback((key: keyof FeedbackListParams, value: string) => {
    // Date validation
    if (key === 'start_date' && value && filters.end_date) {
      if (new Date(value) > new Date(filters.end_date)) {
        setDateError('วันที่เริ่มต้นต้องไม่มากกว่าวันที่สิ้นสุด');
        return;
      }
    }
    if (key === 'end_date' && value && filters.start_date) {
      if (new Date(value) < new Date(filters.start_date)) {
        setDateError('วันที่สิ้นสุดต้องไม่น้อยกว่าวันที่เริ่มต้น');
        return;
      }
    }

    setDateError(null);
    onFiltersChange({
      ...filters,
      [key]: value || undefined,
      page: 1,
    });
  }, [filters, onFiltersChange]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Search */}
        <div className="lg:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ค้นหา
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="ค้นหาข้อความ..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Source Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            แหล่งที่มา
          </label>
          <select
            value={filters.source_type || ''}
            onChange={(e) => updateFilter('source_type', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">ทั้งหมด</option>
            <option value="email">Email</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
            <option value="google_maps">Google Maps</option>
            <option value="manual">บันทึกเอง</option>
            <option value="google_form">Google Forms</option>
          </select>
        </div>

        {/* Sentiment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ความรู้สึก
          </label>
          <select
            value={filters.sentiment || ''}
            onChange={(e) => updateFilter('sentiment', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">ทั้งหมด</option>
            <option value="positive">เชิงบวก</option>
            <option value="neutral">เป็นกลาง</option>
            <option value="negative">เชิงลบ</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Intent */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ประเภท
          </label>
          <select
            value={filters.intent || ''}
            onChange={(e) => updateFilter('intent', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">ทั้งหมด</option>
            <option value="feedback">ข้อเสนอแนะ</option>
            <option value="complaint">ข้อร้องเรียน</option>
            <option value="question">คำถาม</option>
            <option value="off_topic">นอกเรื่อง</option>
          </select>
        </div>

        {/* Start Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            วันที่เริ่มต้น
          </label>
          <input
            type="date"
            value={filters.start_date || ''}
            max={filters.end_date || undefined}
            onChange={(e) => updateFilter('start_date', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              dateError ? 'border-red-300' : 'border-gray-300'
            }`}
          />
        </div>

        {/* End Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            วันที่สิ้นสุด
          </label>
          <input
            type="date"
            value={filters.end_date || ''}
            min={filters.start_date || undefined}
            onChange={(e) => updateFilter('end_date', e.target.value)}
            className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              dateError ? 'border-red-300' : 'border-gray-300'
            }`}
          />
        </div>
      </div>

      {/* Date Error Message */}
      {dateError && (
        <div className="flex items-center gap-2 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>{dateError}</span>
        </div>
      )}
    </div>
  );
}
