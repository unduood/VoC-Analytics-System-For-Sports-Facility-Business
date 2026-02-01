'use client';

import { useState } from 'react';
import { Plus, Trash2, RotateCcw } from 'lucide-react';
import type { AspectLabel, SentimentLabel } from '@/lib/types';
import type { AspectEditState } from '@/hooks/useAnalysisCorrection';
import { cn } from '@/lib/utils';

// Helper to check if revert is available for an aspect
function canRevertAspect(aspect: AspectEditState): boolean {
  // Can't revert new items (no original prediction) or deleted items
  if (aspect.isDeleted) return false;
  // Can only revert if there's an original prediction to revert to
  if (!aspect.originalSentiment) return false;
  // Revert available if current value differs from original prediction
  return aspect.sentiment !== aspect.originalSentiment;
}

// Get the label for what we're reverting to
function getRevertTargetLabel(aspect: AspectEditState): string {
  return getSentimentLabel(aspect.originalSentiment || aspect.sentiment);
}

function getOriginalSourceLabel(source: 'model' | 'rating'): string {
  switch (source) {
    case 'rating':
      return 'แปลงจากคะแนนรีวิว';
    case 'model':
    default:
      return 'ประมวลผลด้วย AI';
  }
}

function getSourceBadgeLabel(source: 'model' | 'user' | 'rating'): string {
  switch (source) {
    case 'user':
      return 'แก้ไข';
    case 'rating':
      return 'คะแนน';
    case 'model':
    default:
      return 'AI';
  }
}

interface AspectEditorProps {
  aspects: AspectEditState[];
  onUpdate: (index: number, sentiment: SentimentLabel) => void;
  onDelete: (index: number) => void;
  onAdd: (aspect: AspectLabel, sentiment: SentimentLabel) => void;
  onRevert: (index: number) => void;
  onRevertAll: () => void;
  canRevert: boolean;
}

const aspectOptions: { value: AspectLabel; label: string }[] = [
  { value: 'equipment', label: 'อุปกรณ์' },
  { value: 'staff', label: 'พนักงาน' },
  { value: 'cleanliness', label: 'ความสะอาด' },
  { value: 'atmosphere', label: 'บรรยากาศ' },
  { value: 'price', label: 'ราคา' },
  { value: 'location', label: 'ทำเล' },
  { value: 'programs', label: 'โปรแกรม' },
  { value: 'amenities', label: 'สิ่งอำนวยความสะดวก' },
];

const sentimentOptions: { value: SentimentLabel; label: string; color: string }[] = [
  { value: 'positive', label: 'เชิงบวก', color: 'bg-green-100 text-green-700 border-green-300' },
  { value: 'neutral', label: 'เป็นกลาง', color: 'bg-amber-100 text-amber-700 border-amber-300' },
  { value: 'negative', label: 'เชิงลบ', color: 'bg-red-100 text-red-700 border-red-300' },
];

export function AspectEditor({
  aspects,
  onUpdate,
  onDelete,
  onAdd,
  onRevert,
  onRevertAll,
  canRevert,
}: AspectEditorProps) {
  const [newAspect, setNewAspect] = useState<AspectLabel | ''>('');
  const [newSentiment, setNewSentiment] = useState<SentimentLabel>('positive');

  // Get aspects already in use (not deleted)
  const usedAspects = new Set(
    aspects.filter((a) => !a.isDeleted).map((a) => a.aspect)
  );

  // Available aspects to add
  const availableAspects = aspectOptions.filter(
    (opt) => !usedAspects.has(opt.value)
  );

  const handleAdd = () => {
    if (newAspect) {
      onAdd(newAspect, newSentiment);
      setNewAspect('');
      setNewSentiment('positive');
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">แง่มุมที่กล่าวถึง</span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">
            ({aspects.filter((a) => !a.isDeleted).length} รายการ)
          </span>
          {canRevert && (
            <button
              onClick={onRevertAll}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
              title="คืนค่าแง่มุมทั้งหมดเป็นผลวิเคราะห์เดิม"
            >
              <RotateCcw className="w-3 h-3" />
              คืนค่าเดิม
            </button>
          )}
        </div>
      </div>

      {/* Aspect List */}
      {aspects.length > 0 ? (
        <div className="space-y-2">
          {aspects.map((aspect, index) => (
            <div
              key={aspect.id || `new-${index}`}
              className={cn(
                'flex items-center gap-2 p-2 rounded-lg border',
                aspect.isDeleted
                  ? 'bg-red-50 border-red-200 opacity-50'
                  : 'bg-gray-50 border-gray-200'
              )}
            >
              {/* Aspect Label */}
              <span className="w-32 text-sm font-medium text-gray-700 truncate">
                {getAspectLabel(aspect.aspect)}
              </span>

              {/* Sentiment Select */}
              <div className="flex-1 flex gap-1">
                {sentimentOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => onUpdate(index, opt.value)}
                    disabled={aspect.isDeleted}
                    className={cn(
                      'flex-1 px-2 py-1 text-xs font-medium rounded border transition-all',
                      aspect.sentiment === opt.value
                        ? opt.color + ' ring-1 ring-blue-500'
                        : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300',
                      aspect.isDeleted && 'cursor-not-allowed opacity-50'
                    )}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              {/* Source Badge */}
              <span
                className={cn(
                  'text-xs px-2 py-0.5 rounded shrink-0',
                  aspect.source === 'user'
                    ? 'bg-purple-100 text-purple-700'
                    : aspect.source === 'rating'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-blue-100 text-blue-700'
                )}
              >
                {getSourceBadgeLabel(aspect.source)}
              </span>

              {/* Actions */}
              <div className="flex items-center gap-1 shrink-0">
                {/* Revert Button - Show when current value differs from original prediction */}
                {canRevertAspect(aspect) && (
                  <button
                    onClick={() => onRevert(index)}
                    className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                    title={`คืนค่าเดิม → ${getRevertTargetLabel(aspect)} (${getOriginalSourceLabel(aspect.originalSource)})`}
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                )}

                {/* Delete Button */}
                {!aspect.isDeleted && (
                  <button
                    onClick={() => onDelete(index)}
                    className="p-1 text-red-600 hover:bg-red-100 rounded"
                    title="ลบ"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Deleted Badge */}
              {aspect.isDeleted && (
                <span className="text-xs text-red-600 font-medium shrink-0">
                  จะถูกลบ
                </span>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-4 text-sm text-gray-500 bg-gray-50 rounded-lg">
          ไม่มีแง่มุมที่กล่าวถึง
        </div>
      )}

      {/* Add Aspect */}
      {availableAspects.length > 0 && (
        <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg border border-dashed border-gray-300">
          <select
            value={newAspect}
            onChange={(e) => setNewAspect(e.target.value as AspectLabel | '')}
            className="flex-1 px-2 py-1.5 text-sm rounded border border-gray-300 bg-white"
          >
            <option value="">เลือกแง่มุม...</option>
            {availableAspects.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          <select
            value={newSentiment}
            onChange={(e) => setNewSentiment(e.target.value as SentimentLabel)}
            className="w-28 px-2 py-1.5 text-sm rounded border border-gray-300 bg-white"
          >
            {sentimentOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          <button
            onClick={handleAdd}
            disabled={!newAspect}
            className={cn(
              'flex items-center gap-1 px-3 py-1.5 rounded text-sm font-medium transition-colors',
              newAspect
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            )}
          >
            <Plus className="w-4 h-4" />
            เพิ่ม
          </button>
        </div>
      )}

      {availableAspects.length === 0 && aspects.filter((a) => !a.isDeleted).length > 0 && (
        <p className="text-xs text-gray-500 text-center">
          เพิ่มครบทุกแง่มุมแล้ว
        </p>
      )}
    </div>
  );
}

function getAspectLabel(aspect: AspectLabel): string {
  const found = aspectOptions.find((opt) => opt.value === aspect);
  return found ? found.label : aspect;
}

function getSentimentLabel(sentiment: SentimentLabel): string {
  switch (sentiment) {
    case 'positive':
      return 'เชิงบวก';
    case 'neutral':
      return 'เป็นกลาง';
    case 'negative':
      return 'เชิงลบ';
    default:
      return sentiment;
  }
}
