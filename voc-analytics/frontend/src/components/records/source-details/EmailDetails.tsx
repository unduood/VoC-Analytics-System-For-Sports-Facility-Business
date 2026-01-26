'use client';

import { Mail, User, FileText } from 'lucide-react';
import { isEmailRawData } from '@/lib/types';
import {
  DataField,
  DataGrid,
  DetailSection,
  SectionTitle,
  formatDateTime,
} from './shared';

interface EmailDetailsProps {
  rawData: Record<string, unknown> | null;
}

export function EmailDetails({ rawData }: EmailDetailsProps) {
  if (!rawData || !isEmailRawData(rawData)) {
    return null;
  }

  return (
    <DetailSection>
      <SectionTitle icon={<Mail className="w-4 h-4" />}>
        รายละเอียดอีเมล
      </SectionTitle>
      <DataGrid>
        <DataField
          label="ผู้ส่ง"
          value={
            <span className="flex items-center gap-1">
              <User className="w-3 h-3 text-gray-400" />
              {rawData.sender_email}
            </span>
          }
        />
        <DataField
          label="เวลาที่ได้รับ"
          value={formatDateTime(rawData.received_at)}
        />
        <DataField
          label="หัวข้อ"
          value={
            <span className="flex items-center gap-1">
              <FileText className="w-3 h-3 text-gray-400" />
              {rawData.subject}
            </span>
          }
          className="sm:col-span-2"
        />
      </DataGrid>
    </DetailSection>
  );
}
