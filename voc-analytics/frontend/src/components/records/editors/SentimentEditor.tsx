'use client';

import { RotateCcw } from 'lucide-react';
import type { SentimentLabel } from '@/lib/types';
import type { SentimentEditState } from '@/hooks/useAnalysisCorrection';
import { cn } from '@/lib/utils';

interface SentimentEditorProps {
  state: SentimentEditState;
  onUpdate: (sentiment: SentimentLabel) => void;
  onRevert: () => void;
}

const sentimentOptions: { value: SentimentLabel; label: string; color: string }[] = [
  { value: 'positive', label: 'เชิงบวก', color: 'text-green-700 bg-green-100 border-green-300' },
  { value: 'neutral', label: 'เป็นกลาง', color: 'text-amber-700 bg-amber-100 border-amber-300' },
  { value: 'negative', label: 'เชิงลบ', color: 'text-red-700 bg-red-100 border-red-300' },
];

export function SentimentEditor({ state, onUpdate, onRevert }: SentimentEditorProps) {
  // Revert target: original prediction value (before any user edit)
  const revertTarget = state.originalSentiment;
  // Show revert if current value differs from original prediction
  const canRevert = state.sentiment !== revertTarget;
  // Show "edited" indicator if source is 'user'
  const isEdited = state.source === 'user';

  // Source-aware label for the original prediction origin
  const originalSourceLabel = getOriginalSourceLabel(state.originalSource);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">ความรู้สึกโดยรวม</span>
        {canRevert && (
          <button
            onClick={onRevert}
            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
            title={`คืนค่าเดิม → ${getSentimentLabel(revertTarget)} (${originalSourceLabel})`}
          >
            <RotateCcw className="w-3 h-3" />
            คืนค่าเดิม
          </button>
        )}
      </div>

      <div className="flex gap-2">
        {sentimentOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => onUpdate(option.value)}
            className={cn(
              'flex-1 px-3 py-2 rounded-lg border-2 text-sm font-medium transition-all',
              state.sentiment === option.value
                ? option.color + ' ring-2 ring-offset-1 ring-blue-500'
                : 'bg-gray-50 text-gray-600 border-gray-200 hover:border-gray-300'
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      {isEdited && (
        <p className="text-xs text-gray-500">
          ผลวิเคราะห์เดิม ({originalSourceLabel}): {getSentimentLabel(state.originalSentiment)}
        </p>
      )}
    </div>
  );
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

function getOriginalSourceLabel(source: 'model' | 'rating'): string {
  switch (source) {
    case 'rating':
      return 'แปลงจากคะแนนรีวิว';
    case 'model':
    default:
      return 'ประมวลผลด้วย AI';
  }
}
