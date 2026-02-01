'use client';

import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { format } from 'date-fns';
import { th } from 'date-fns/locale';
import {
  Mail,
  Instagram,
  Facebook,
  MapPin,
  FileText,
  PenLine,
  Clock,
  TrendingUp,
  MessageSquare,
  Tag,
  Info,
  Edit3,
  Trash2,
} from 'lucide-react';
import type {
  SourceType,
  SentimentLabel,
  IntentLabel,
  AspectLabel,
  AnalysisSource,
} from '@/lib/types';
import { SourceDetails } from './source-details';
import { AnalysisSourceLabel } from './AnalysisSourceLabel';
import { AnalysisEditor } from './editors';
import { getIntentColor } from '@/lib/utils';
import { useAnalysisCorrection } from '@/hooks/useAnalysisCorrection';
import { useFeedbackDetail, useDeleteFeedback } from '@/hooks/useFeedback';

interface FeedbackDetailModalProps {
  feedbackId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

const sourceIcons: Record<SourceType, React.ReactNode> = {
  email: <Mail className="w-4 h-4" />,
  instagram: <Instagram className="w-4 h-4" />,
  facebook: <Facebook className="w-4 h-4" />,
  google_maps: <MapPin className="w-4 h-4" />,
  google_form: <FileText className="w-4 h-4" />,
  manual: <PenLine className="w-4 h-4" />,
};

const sourceLabels: Record<SourceType, string> = {
  email: 'Email',
  instagram: 'Instagram',
  facebook: 'Facebook',
  google_maps: 'Google Maps',
  google_form: 'Google Forms',
  manual: 'บันทึกเอง',
};

const sentimentConfig: Record<SentimentLabel, { label: string; color: string; bgColor: string }> = {
  positive: { label: 'เชิงบวก', color: 'text-green-700', bgColor: 'bg-green-100' },
  neutral: { label: 'เป็นกลาง', color: 'text-amber-700', bgColor: 'bg-amber-100' },
  negative: { label: 'เชิงลบ', color: 'text-red-700', bgColor: 'bg-red-100' },
};

const intentLabels: Record<IntentLabel, string> = {
  feedback: 'ข้อเสนอแนะ',
  question: 'คำถาม',
  complaint: 'ข้อร้องเรียน',
  off_topic: 'นอกเรื่อง',
};

const aspectLabels: Record<AspectLabel, string> = {
  equipment: 'อุปกรณ์',
  staff: 'พนักงาน',
  cleanliness: 'ความสะอาด',
  atmosphere: 'บรรยากาศ',
  price: 'ราคา',
  location: 'ทำเล',
  programs: 'โปรแกรม',
  amenities: 'สิ่งอำนวยความสะดวก',
};

const statusConfig: Record<string, { label: string; color: string; bgColor: string }> = {
  pending: { label: 'รอดำเนินการ', color: 'text-gray-700', bgColor: 'bg-gray-100' },
  processing: { label: 'กำลังประมวลผล', color: 'text-blue-700', bgColor: 'bg-blue-100' },
  completed: { label: 'เสร็จสิ้น', color: 'text-green-700', bgColor: 'bg-green-100' },
  failed: { label: 'ล้มเหลว', color: 'text-red-700', bgColor: 'bg-red-100' },
};

// Type definitions for analysis_summary JSONB structure
interface AnalysisSummaryAspect {
  aspect: string;
  aspect_thai?: string;
  sentiment: string;
  confidence: number;
  source: AnalysisSource;
  edited: boolean;
}

interface AnalysisSummaryIntent {
  label: string;
  confidence: number;
  source: AnalysisSource;
  edited: boolean;
}

interface AnalysisSummarySentiment {
  label: string;
  confidence: number;
  source: AnalysisSource;
  rating?: number | null;
  edited: boolean;
}

interface AnalysisSummary {
  sentiment?: AnalysisSummarySentiment;
  intents?: AnalysisSummaryIntent[];
  aspects?: AnalysisSummaryAspect[];
  summary_stats?: {
    total_aspects_analyzed?: number;
    aspects_with_sentiment?: number;
    positive_aspects?: number;
    negative_aspects?: number;
    neutral_aspects?: number;
  };
}

export function FeedbackDetailModal({ feedbackId, isOpen, onClose }: FeedbackDetailModalProps) {
  // Fetch detail from React Query cache (seeded by parent on row click,
  // then kept up-to-date by useAnalysisCorrection.onSuccess via setQueryData)
  const { data: feedback } = useFeedbackDetail(feedbackId);

  // Initialize correction hook (always call hooks unconditionally)
  const correction = useAnalysisCorrection(feedbackId || '');

  // Delete state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [passcode, setPasscode] = useState('');
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const deleteMutation = useDeleteFeedback();

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
    setPasscode('');
    setDeleteError(null);
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
    setPasscode('');
    setDeleteError(null);
  };

  const handleDeleteConfirm = () => {
    const expectedPasscode = process.env.NEXT_PUBLIC_DELETE_PASSCODE;

    if (!expectedPasscode) {
      setDeleteError('ไม่ได้ตั้งค่ารหัสผ่านสำหรับลบข้อมูล');
      return;
    }

    if (passcode !== expectedPasscode) {
      setDeleteError('รหัสผ่านไม่ถูกต้อง');
      return;
    }

    // Passcode verified, proceed with delete
    deleteMutation.mutate(feedbackId!, {
      onSuccess: () => {
        setShowDeleteConfirm(false);
        onClose();
      },
      onError: () => {
        setDeleteError('เกิดข้อผิดพลาดในการลบข้อมูล');
      },
    });
  };

  if (!feedback) return null;

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    try {
      return format(new Date(dateString), 'PPpp', { locale: th });
    } catch {
      return dateString;
    }
  };

  const status = statusConfig[feedback.processing_status] || statusConfig.pending;

  // Parse analysis_summary JSONB - this contains the source for EACH label
  const analysisSummary = feedback.analysis_summary as AnalysisSummary | null;

  // Handle close - cancel editing if in edit mode
  const handleClose = () => {
    if (correction.isEditing) {
      correction.cancelEditing();
    }
    onClose();
  };

  const canEdit = feedback.processing_status === 'completed';

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={correction.isEditing ? 'แก้ไขผลการวิเคราะห์' : 'รายละเอียดความคิดเห็น'}
      size="lg"
    >
      <div className="space-y-6">
        {/* Header Info */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-gray-600">
              {sourceIcons[feedback.source_type]}
              <span className="text-sm font-medium">{sourceLabels[feedback.source_type]}</span>
            </div>
            <Badge className={`${status.bgColor} ${status.color}`}>{status.label}</Badge>
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              {formatDate(feedback.created_at_source || feedback.created_at)}
            </div>
          </div>

          {/* Edit Button */}
          {canEdit && !correction.isEditing && (
            <button
              onClick={() => correction.startEditing(feedback)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
            >
              <Edit3 className="w-4 h-4" />
              แก้ไขผลวิเคราะห์
            </button>
          )}
        </div>

        {/* Text Content */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">ข้อความ</h3>
          <p className="text-gray-900 whitespace-pre-wrap">{feedback.text_content}</p>
        </div>

        {/* Source-specific Details */}
        {feedback.raw_data && Object.keys(feedback.raw_data).length > 0 && !correction.isEditing && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Info className="w-4 h-4 text-gray-500" />
              <h3 className="text-sm font-semibold text-gray-700">ข้อมูลจากแหล่งที่มา</h3>
            </div>
            <SourceDetails
              sourceType={feedback.source_type}
              rawData={feedback.raw_data}
            />
          </div>
        )}

        {/* Edit Mode: Show Editor */}
        {correction.isEditing && (
          <AnalysisEditor correction={correction} />
        )}

        {/* View Mode: Show Analysis Results */}
        {!correction.isEditing && feedback.processing_status === 'completed' && (
          <div className="space-y-4">
            {/* Sentiment */}
            {feedback.sentiment_result && !feedback.sentiment_result.is_deleted && (
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-4 h-4 text-gray-600" />
                  <h3 className="text-sm font-semibold text-gray-700">การวิเคราะห์ความรู้สึก</h3>
                </div>
                <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                  <div className="flex items-center gap-3">
                    <Badge
                      className={`${sentimentConfig[feedback.sentiment_result.sentiment].bgColor} ${sentimentConfig[feedback.sentiment_result.sentiment].color}`}
                    >
                      {sentimentConfig[feedback.sentiment_result.sentiment].label}
                    </Badge>
                    <span className="text-sm text-gray-500">
                      ความมั่นใจ: {(feedback.sentiment_result.confidence * 100).toFixed(1)}%
                    </span>
                    {/* Original value tooltip */}
                    {feedback.sentiment_result.original_sentiment && (
                      <span
                        className="text-xs text-gray-400 cursor-help"
                        title={`ค่าเดิม (${feedback.sentiment_result.original_source === 'rating' ? 'แปลงจากคะแนนรีวิว' : 'ประมวลผลด้วย AI'}): ${sentimentConfig[feedback.sentiment_result.original_sentiment]?.label || feedback.sentiment_result.original_sentiment}`}
                      >
                        (แก้ไขแล้ว)
                      </span>
                    )}
                  </div>
                  {/* Use source directly from result, fallback to analysis_summary for rating value */}
                  <AnalysisSourceLabel
                    source={(feedback.sentiment_result.source || analysisSummary?.sentiment?.source || 'model') as AnalysisSource}
                    ratingValue={analysisSummary?.sentiment?.rating}
                    showTooltip={true}
                  />
                </div>
              </div>
            )}

            {/* Intent */}
            {feedback.intent_results && feedback.intent_results.length > 0 && (
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <MessageSquare className="w-4 h-4 text-gray-600" />
                  <h3 className="text-sm font-semibold text-gray-700">ประเภทข้อความ</h3>
                </div>
                <div className="space-y-2">
                  {feedback.intent_results
                    .filter((intent) => !intent.is_deleted)
                    .map((intent) => {
                      // Use source directly from result, fallback to analysis_summary by label match
                      const summaryIntent = analysisSummary?.intents?.find(
                        (i) => i.label.toLowerCase() === intent.intent
                      );
                      const intentSource = intent.source || summaryIntent?.source || 'model';
                      return (
                        <div
                          key={intent.id}
                          className="flex items-center justify-between bg-gray-50 rounded-lg p-3"
                        >
                          <div className="flex items-center gap-3">
                            <Badge className={getIntentColor(intent.intent)}>
                              {intentLabels[intent.intent]}
                            </Badge>
                            <span className="text-sm text-gray-500">
                              ความมั่นใจ: {(intent.confidence * 100).toFixed(0)}%
                            </span>
                            {/* Original value tooltip */}
                            {intent.original_intent && (
                              <span
                                className="text-xs text-gray-400 cursor-help"
                                title={`ค่าเดิม (${intent.original_source === 'rating' ? 'แปลงจากคะแนนรีวิว' : 'ประมวลผลด้วย AI'}): ${intentLabels[intent.original_intent] || intent.original_intent}`}
                              >
                                (แก้ไขแล้ว)
                              </span>
                            )}
                          </div>
                          <AnalysisSourceLabel
                            source={intentSource as AnalysisSource}
                            showTooltip={true}
                          />
                        </div>
                      );
                    })}
                </div>
              </div>
            )}

            {/* Aspects */}
            {feedback.aspect_results && feedback.aspect_results.length > 0 && (
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Tag className="w-4 h-4 text-gray-600" />
                  <h3 className="text-sm font-semibold text-gray-700">แง่มุมที่กล่าวถึง</h3>
                </div>
                <div className="space-y-2">
                  {feedback.aspect_results
                    .filter((aspect) => !aspect.is_deleted)
                    .map((aspect) => {
                      // Use source directly from result, fallback to analysis_summary by aspect match
                      const summaryAspect = analysisSummary?.aspects?.find(
                        (a) => a.aspect.toLowerCase() === aspect.aspect
                      );
                      const aspectSource = aspect.source || summaryAspect?.source || 'model';
                      return (
                        <div
                          key={aspect.id}
                          className="flex items-center justify-between bg-gray-50 rounded-lg p-3"
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-sm text-gray-700">{aspectLabels[aspect.aspect]}</span>
                            <Badge
                              size="sm"
                              className={`${sentimentConfig[aspect.sentiment].bgColor} ${sentimentConfig[aspect.sentiment].color}`}
                            >
                              {sentimentConfig[aspect.sentiment].label}
                            </Badge>
                            <span className="text-sm text-gray-500">
                              ความมั่นใจ: {(aspect.confidence * 100).toFixed(0)}%
                            </span>
                            {/* Original value tooltip */}
                            {aspect.original_sentiment && (
                              <span
                                className="text-xs text-gray-400 cursor-help"
                                title={`ค่าเดิม (${aspect.original_source === 'rating' ? 'แปลงจากคะแนนรีวิว' : 'ประมวลผลด้วย AI'}): ${sentimentConfig[aspect.original_sentiment]?.label || aspect.original_sentiment}`}
                              >
                                (แก้ไขแล้ว)
                              </span>
                            )}
                          </div>
                          <AnalysisSourceLabel
                            source={aspectSource as AnalysisSource}
                            showTooltip={true}
                          />
                        </div>
                      );
                    })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Processing Status Message */}
        {!correction.isEditing && feedback.processing_status === 'pending' && (
          <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500">
            รอการประมวลผล...
          </div>
        )}

        {!correction.isEditing && feedback.processing_status === 'processing' && (
          <div className="bg-blue-50 rounded-lg p-4 text-center text-blue-600">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2" />
            กำลังวิเคราะห์ด้วย AI...
          </div>
        )}

        {!correction.isEditing && feedback.processing_status === 'failed' && (
          <div className="bg-red-50 rounded-lg p-4 text-center text-red-600">
            การวิเคราะห์ล้มเหลว กรุณาลองใหม่อีกครั้ง
          </div>
        )}

        {/* Metadata - only show when not editing */}
        {!correction.isEditing && (
          <div className="pt-4 border-t border-gray-200">
            <div className="text-xs text-gray-500 font-medium mb-2">ข้อมูลอ้างอิง</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="flex flex-col">
                <span className="text-gray-400">ID ในระบบ</span>
                <span className="text-gray-600 font-mono truncate" title={feedback.id}>
                  {feedback.id.slice(0, 8)}...
                </span>
              </div>
              {feedback.source_id && (
                <div className="flex flex-col">
                  <span className="text-gray-400">ID จาก {sourceLabels[feedback.source_type]}</span>
                  <span className="text-gray-600 font-mono truncate" title={feedback.source_id}>
                    {feedback.source_id.length > 20
                      ? `${feedback.source_id.slice(0, 20)}...`
                      : feedback.source_id}
                  </span>
                </div>
              )}
              <div className="flex flex-col sm:col-span-2">
                <span className="text-gray-400">อัปเดตล่าสุด</span>
                <span className="text-gray-600">{formatDate(feedback.updated_at)}</span>
              </div>
            </div>
            <div className="flex justify-end mt-4">
              <button
                onClick={handleDeleteClick}
                disabled={deleteMutation.isPending}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
                ลบข้อมูล
              </button>
            </div>
          </div>
        )}

        {/* Delete Confirmation Dialog */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">ยืนยันการลบข้อมูล</h3>
              <p className="text-sm text-gray-600 mb-4">
                กรุณากรอกรหัสผ่านเพื่อยืนยันการลบความคิดเห็นนี้ การดำเนินการนี้ไม่สามารถย้อนกลับได้
              </p>
              <input
                type="password"
                value={passcode}
                onChange={(e) => {
                  setPasscode(e.target.value);
                  setDeleteError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleDeleteConfirm();
                }}
                placeholder="รหัสผ่าน"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent mb-3"
                autoFocus
              />
              {deleteError && (
                <p className="text-sm text-red-600 mb-3">{deleteError}</p>
              )}
              <div className="flex gap-3">
                <button
                  onClick={handleDeleteCancel}
                  disabled={deleteMutation.isPending}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
                >
                  ยกเลิก
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  disabled={deleteMutation.isPending || !passcode}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50"
                >
                  {deleteMutation.isPending ? 'กำลังลบ...' : 'ยืนยันลบ'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
