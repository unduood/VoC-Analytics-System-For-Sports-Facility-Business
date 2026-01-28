'use client';

import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useFeedbackList, feedbackKeys } from '@/hooks/useFeedback';
import { FeedbackTable } from '@/components/records/FeedbackTable';
import { FeedbackFilters } from '@/components/records/FeedbackFilters';
import { FeedbackDetailModal } from '@/components/records/FeedbackDetailModal';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import type { FeedbackListParams, FeedbackWithAnalysis } from '@/lib/types';

export default function RecordsPage() {
  const [filters, setFilters] = useState<FeedbackListParams>({
    page: 1,
    page_size: 20,
  });
  const queryClient = useQueryClient();
  const [selectedFeedbackId, setSelectedFeedbackId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data, isLoading, error } = useFeedbackList(filters);

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
  };

  const handleRowClick = (feedback: FeedbackWithAnalysis) => {
    // Seed the detail cache with list data so the modal renders instantly
    queryClient.setQueryData(feedbackKeys.detail(feedback.id), feedback);
    setSelectedFeedbackId(feedback.id);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedFeedbackId(null);
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">เกิดข้อผิดพลาด</h3>
          <p className="text-gray-600">ไม่สามารถโหลดข้อมูลได้ กรุณาลองใหม่อีกครั้ง</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">ข้อมูลความคิดเห็น</h1>
        <p className="text-gray-600 mt-2">ดูและค้นหาความคิดเห็นทั้งหมด</p>
      </div>

      {/* Filters */}
      <FeedbackFilters filters={filters} onFiltersChange={setFilters} />

      {/* Results Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>รายการความคิดเห็น</CardTitle>
              {data && (
                <p className="text-sm text-gray-500 mt-1">
                  แสดง {(data.page - 1) * data.page_size + 1} -{" "}
                  {Math.min(data.page * data.page_size, data.total)} จากทั้งหมด{" "}
                  {data.total} รายการ
                </p>
              )}
            </div>
            {data && data.total > 0 && (
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(filters.page! - 1)}
                  disabled={!data || data.page <= 1 || isLoading}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-sm text-gray-600">
                  หน้า {data.page} / {data.total_pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(filters.page! + 1)}
                  disabled={!data || data.page >= data.total_pages || isLoading}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
                <p className="text-gray-600">กำลังโหลดข้อมูล...</p>
              </div>
            </div>
          ) : (
            <FeedbackTable
              data={data?.items || []}
              onRowClick={handleRowClick}
            />
          )}
        </CardContent>
      </Card>

      {/* Pagination at bottom */}
      {data && data.total > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            แสดง {(data.page - 1) * data.page_size + 1} -{" "}
            {Math.min(data.page * data.page_size, data.total)} จากทั้งหมด{" "}
            {data.total} รายการ
          </p>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(filters.page! - 1)}
              disabled={data.page <= 1 || isLoading}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              ก่อนหน้า
            </Button>
            <span className="text-sm text-gray-600">
              หน้า {data.page} / {data.total_pages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(filters.page! + 1)}
              disabled={data.page >= data.total_pages || isLoading}
            >
              ถัดไป
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      <FeedbackDetailModal
        feedbackId={selectedFeedbackId}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
}
