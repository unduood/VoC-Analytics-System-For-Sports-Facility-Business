'use client';

import { Save, X, Loader2, AlertCircle } from 'lucide-react';
import { SentimentEditor } from './SentimentEditor';
import { IntentEditor } from './IntentEditor';
import { AspectEditor } from './AspectEditor';
import type { UseAnalysisCorrectionReturn } from '@/hooks/useAnalysisCorrection';
import { cn } from '@/lib/utils';

interface AnalysisEditorProps {
  correction: UseAnalysisCorrectionReturn;
}

export function AnalysisEditor({ correction }: AnalysisEditorProps) {
  const {
    editState,
    cancelEditing,
    saveCorrections,
    updateSentiment,
    revertSentiment,
    deleteIntent,
    addIntent,
    revertAllIntents,
    updateAspect,
    deleteAspect,
    addAspect,
    revertAspect,
    revertAllAspects,
    canRevertIntents,
    canRevertAspects,
    canSave,
    validationError,
    isSaving,
    error,
  } = correction;

  if (!editState) return null;

  return (
    <div className="space-y-6">
      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <div>
            <p className="font-medium">เกิดข้อผิดพลาด</p>
            <p>{error.message || 'ไม่สามารถบันทึกการแก้ไขได้'}</p>
          </div>
        </div>
      )}

      {/* Sentiment Section */}
      {editState.sentiment && (
        <div className="border border-gray-200 rounded-lg p-4">
          <SentimentEditor
            state={editState.sentiment}
            onUpdate={updateSentiment}
            onRevert={revertSentiment}
          />
        </div>
      )}

      {/* Intent Section */}
      <div className="border border-gray-200 rounded-lg p-4">
        <IntentEditor
          intents={editState.intents}
          onDelete={deleteIntent}
          onAdd={addIntent}
          onRevertAll={revertAllIntents}
          canRevert={canRevertIntents}
          validationError={validationError}
        />
      </div>

      {/* Aspect Section */}
      <div className="border border-gray-200 rounded-lg p-4">
        <AspectEditor
          aspects={editState.aspects}
          onUpdate={updateAspect}
          onDelete={deleteAspect}
          onAdd={addAspect}
          onRevert={revertAspect}
          onRevertAll={revertAllAspects}
          canRevert={canRevertAspects}
        />
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
        <button
          onClick={cancelEditing}
          disabled={isSaving}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          <X className="w-4 h-4" />
          ยกเลิก
        </button>

        <button
          onClick={saveCorrections}
          disabled={!canSave || isSaving}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
            canSave && !isSaving
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          )}
        >
          {isSaving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              กำลังบันทึก...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              บันทึกการแก้ไข
            </>
          )}
        </button>
      </div>

      {/* Help Text */}
      <div className="text-xs text-gray-500 space-y-1">
        <p>
          <strong>คำแนะนำ:</strong>
        </p>
        <ul className="list-disc list-inside space-y-0.5 pl-2">
          <li>กด &quot;คืนค่าเดิม&quot; ที่มุมขวาของแต่ละหมวดเพื่อรีเซ็ตกลับเป็นผลวิเคราะห์เดิม</li>
          <li>คลิกประเภทข้อความเพื่อเปิด/ปิด (ต้องเลือกอย่างน้อย 1 รายการ)</li>
          <li>&quot;นอกเรื่อง&quot; ไม่สามารถเลือกร่วมกับประเภทอื่นได้</li>
          <li>แง่มุม — เพิ่ม ลบ หรือเปลี่ยนความรู้สึกได้ตามต้องการ</li>
        </ul>
      </div>
    </div>
  );
}
