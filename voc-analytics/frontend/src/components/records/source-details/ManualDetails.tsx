'use client';

import { PenLine, CheckCircle } from 'lucide-react';
import { isManualRawData } from '@/lib/types';
import { DetailSection, SectionTitle } from './shared';

interface ManualDetailsProps {
  rawData: Record<string, unknown> | null;
}

export function ManualDetails({ rawData }: ManualDetailsProps) {
  if (!rawData || !isManualRawData(rawData)) {
    return null;
  }

  return (
    <DetailSection>
      <SectionTitle icon={<PenLine className="w-4 h-4" />}>
        รายละเอียดการบันทึก
      </SectionTitle>
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <CheckCircle className="w-4 h-4 text-green-500" />
        <span>บันทึกด้วยตนเองผ่านระบบ</span>
      </div>
    </DetailSection>
  );
}
