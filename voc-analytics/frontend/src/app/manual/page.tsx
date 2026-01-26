'use client';

import { useState } from 'react';
import { useSubmitFeedback } from '@/hooks/useFeedback';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { CheckCircle, AlertCircle, Send } from 'lucide-react';

const MAX_LENGTH = 5000;

export default function ManualPage() {
  const [text, setText] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [showError, setShowError] = useState(false);

  const { mutate: submitFeedback, isPending } = useSubmitFeedback();

  const trimmedText = text.trim();
  const isTextTooLong = trimmedText.length > MAX_LENGTH;
  const isValidText = trimmedText.length > 0 && trimmedText.length <= MAX_LENGTH;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isValidText) {
      return;
    }

    submitFeedback(trimmedText, {
      onSuccess: () => {
        setText('');
        setShowSuccess(true);
        setShowError(false);
        setTimeout(() => setShowSuccess(false), 5000);
      },
      onError: (error) => {
        if (process.env.NODE_ENV === 'development') {
          console.error('Error submitting feedback:', error);
        }
        setShowError(true);
        setShowSuccess(false);
        setTimeout(() => setShowError(false), 5000);
      },
    });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">บันทึกข้อเสนอแนะ</h1>
        <p className="text-gray-600 mt-2">กรอกข้อเสนอแนะหรือความคิดเห็นของลูกค้า</p>
      </div>

      {/* Success Alert */}
      {showSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center space-x-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-green-900">บันทึกสำเร็จ!</h3>
            <p className="text-sm text-green-700 mt-1">
              ข้อเสนอแนะของคุณถูกบันทึกแล้ว ระบบกำลังประมวลผลด้วย AI
            </p>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {showError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-red-900">เกิดข้อผิดพลาด</h3>
            <p className="text-sm text-red-700 mt-1">
              ไม่สามารถบันทึกข้อเสนอแนะได้ กรุณาลองใหม่อีกครั้ง
            </p>
          </div>
        </div>
      )}

      {/* Form Card */}
      <Card>
        <CardHeader>
          <CardTitle>ข้อเสนอแนะจากลูกค้า</CardTitle>
          <CardDescription>
            กรอกข้อความข้อเสนอแนะ ความคิดเห็น หรือข้อร้องเรียนจากลูกค้า
            ระบบจะวิเคราะห์ความรู้สึก ประเภท และแง่มุมต่างๆ โดยอัตโนมัติ
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="feedback" className="block text-sm font-medium text-gray-700 mb-2">
                ข้อความ
              </label>
              <textarea
                id="feedback"
                rows={8}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="พิมพ์ข้อเสนอแนะหรือความคิดเห็นของลูกค้าที่นี่..."
                className={`w-full px-4 py-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none ${
                  isTextTooLong ? 'border-red-300' : 'border-gray-300'
                }`}
                maxLength={MAX_LENGTH}
                required
              />
              <div className="flex items-center justify-between mt-2">
                <div>
                  {isTextTooLong && (
                    <p className="text-sm text-red-600">
                      ข้อความต้องไม่เกิน {MAX_LENGTH.toLocaleString()} ตัวอักษร (เกินมา {trimmedText.length - MAX_LENGTH})
                    </p>
                  )}
                </div>
                <p className={`text-sm ${isTextTooLong ? 'text-red-600' : 'text-gray-500'}`}>
                  {trimmedText.length.toLocaleString()} / {MAX_LENGTH.toLocaleString()}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setText('')}
                disabled={isPending || !trimmedText}
              >
                ล้างข้อความ
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isPending || !isValidText}
                isLoading={isPending}
              >
                {!isPending && <Send className="w-4 h-4 mr-2" />}
                บันทึกข้อเสนอแนะ
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="p-6">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">
            ระบบจะวิเคราะห์อะไรบ้าง?
          </h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• <strong>ความรู้สึก:</strong> เชิงบวก เป็นกลาง หรือเชิงลบ</li>
            <li>• <strong>ประเภท:</strong> ข้อเสนอแนะ ข้อร้องเรียน คำถาม หรือนอกเรื่อง</li>
            <li>• <strong>แง่มุม:</strong> อุปกรณ์ พนักงาน ความสะอาด บรรยากาศ ราคา ทำเล โปรแกรม สิ่งอำนวยความสะดวก</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
