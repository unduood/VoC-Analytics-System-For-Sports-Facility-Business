'use client';

import { AlertCircle, RotateCcw } from 'lucide-react';
import type { IntentLabel } from '@/lib/types';
import type { IntentEditState } from '@/hooks/useAnalysisCorrection';
import { cn } from '@/lib/utils';

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

interface IntentEditorProps {
  intents: IntentEditState[];
  onDelete: (index: number) => void;
  onAdd: (intent: IntentLabel) => void;
  onRevertAll: () => void;
  canRevert: boolean;
  validationError: string | null;
}

const intentOptions: { value: IntentLabel; label: string }[] = [
  { value: 'feedback', label: 'ข้อเสนอแนะ' },
  { value: 'question', label: 'คำถาม' },
  { value: 'complaint', label: 'ข้อร้องเรียน' },
  { value: 'off_topic', label: 'นอกเรื่อง' },
];

export function IntentEditor({
  intents,
  onDelete,
  onAdd,
  onRevertAll,
  canRevert,
  validationError,
}: IntentEditorProps) {
  const activeIntents = intents.filter((i) => !i.isDeleted);
  const isLastActive = activeIntents.length <= 1;

  // Lookup: intent label → active edit state item
  const activeIntentMap = new Map(
    activeIntents.map((i) => [i.intent, i])
  );

  const handleToggle = (intentValue: IntentLabel) => {
    const activeItem = activeIntentMap.get(intentValue);

    if (activeItem) {
      // Deactivate: can't remove the last intent
      if (isLastActive) return;
      const index = intents.indexOf(activeItem);
      if (index >= 0) {
        onDelete(index);
      }
    } else {
      // Activate (hook handles off_topic mutual exclusivity & deleted-item restoration)
      onAdd(intentValue);
    }
  };

  const hasOffTopic = activeIntentMap.has('off_topic');

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">ประเภทข้อความ</span>
        <div className="flex items-center gap-3">
          {!canRevert && (
            <span className="text-xs text-gray-500">
              (ขั้นต่ำ 1 รายการ)
            </span>
          )}
          {canRevert && (
            <button
              onClick={onRevertAll}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
              title="คืนค่าประเภทข้อความทั้งหมดเป็นผลวิเคราะห์เดิม"
            >
              <RotateCcw className="w-3 h-3" />
              คืนค่าเดิม
            </button>
          )}
        </div>
      </div>

      {/* Validation Error */}
      {validationError && (
        <div className="flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {validationError}
        </div>
      )}

      {/* Intent Toggle Chips */}
      <div className="grid grid-cols-2 gap-2">
        {intentOptions.map((opt) => {
          const isActive = activeIntentMap.has(opt.value);
          const activeItem = activeIntentMap.get(opt.value);

          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleToggle(opt.value)}
              disabled={isActive && isLastActive}
              className={cn(
                'flex items-center justify-between px-3 py-2.5 rounded-lg border text-sm font-medium transition-all',
                isActive
                  ? 'bg-blue-50 text-blue-700 border-blue-300 ring-1 ring-blue-400'
                  : 'bg-white text-gray-400 border-gray-200 hover:border-gray-300 hover:text-gray-500 hover:bg-gray-50',
                isActive && isLastActive && 'cursor-not-allowed opacity-75',
                !isActive && 'cursor-pointer'
              )}
              title={
                isActive && isLastActive
                  ? 'ไม่สามารถลบได้ — ต้องมีอย่างน้อย 1 รายการ'
                  : isActive
                    ? `คลิกเพื่อลบ "${opt.label}"`
                    : `คลิกเพื่อเพิ่ม "${opt.label}"`
              }
            >
              <span>{opt.label}</span>

              <span className="flex items-center gap-1">
                {/* Source badge for active intents */}
                {isActive && activeItem && (
                  <span
                    className={cn(
                      'text-xs px-1.5 py-0.5 rounded',
                      activeItem.source === 'user'
                        ? 'bg-purple-100 text-purple-700'
                        : activeItem.source === 'rating'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-blue-100 text-blue-700'
                    )}
                  >
                    {getSourceBadgeLabel(activeItem.source)}
                  </span>
                )}

              </span>
            </button>
          );
        })}
      </div>

      {/* Off-topic Warning */}
      {hasOffTopic && activeIntents.length === 1 && (
        <p className="text-xs text-amber-600 bg-amber-50 p-2 rounded">
          &quot;นอกเรื่อง&quot; ไม่สามารถใช้ร่วมกับประเภทอื่นได้ —
          เลือกประเภทอื่นเพื่อแทนที่ &quot;นอกเรื่อง&quot; ได้โดยตรง
        </p>
      )}
    </div>
  );
}
