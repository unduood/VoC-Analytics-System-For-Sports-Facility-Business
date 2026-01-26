'use client';

import { Facebook, User, Eye, EyeOff, MessageCircle } from 'lucide-react';
import { isFacebookRawData } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import {
  DataField,
  DataFieldLink,
  DataGrid,
  DetailSection,
  SectionTitle,
  formatDateTime,
  TruncatedText,
} from './shared';

interface FacebookDetailsProps {
  rawData: Record<string, unknown> | null;
}

export function FacebookDetails({ rawData }: FacebookDetailsProps) {
  if (!rawData || !isFacebookRawData(rawData)) {
    return null;
  }

  return (
    <DetailSection>
      <SectionTitle icon={<Facebook className="w-4 h-4" />}>
        รายละเอียด Facebook
      </SectionTitle>
      <div className="space-y-4">
        {/* Comment Info */}
        <DataGrid>
          <DataField
            label="ผู้แสดงความคิดเห็น"
            value={
              rawData.name ? (
                <span className="flex items-center gap-1">
                  <User className="w-3 h-3 text-gray-400" />
                  {rawData.name}
                </span>
              ) : (
                <span className="text-gray-400">ไม่ระบุชื่อ</span>
              )
            }
          />
          <DataField
            label="เวลาคอมเมนต์"
            value={formatDateTime(rawData.created_time)}
          />
          <DataField
            label="สถานะการมองเห็น"
            value={
              rawData.is_hidden ? (
                <Badge variant="warning" size="sm" className="inline-flex items-center gap-1">
                  <EyeOff className="w-3 h-3" />
                  ซ่อนอยู่
                </Badge>
              ) : (
                <span className="inline-flex items-center gap-1 text-green-600">
                  <Eye className="w-3 h-3" />
                  แสดงอยู่
                </span>
              )
            }
          />
        </DataGrid>

        {/* Post Info */}
        {(rawData.post_message || rawData.post_permalink_url) && (
          <div className="pt-3 border-t border-gray-200">
            <div className="flex items-center gap-1 text-xs text-gray-500 mb-2">
              <MessageCircle className="w-3 h-3" />
              ข้อมูลโพสต์
            </div>
            <DataGrid>
              {rawData.post_message && (
                <DataField
                  label="เนื้อหาโพสต์"
                  value={<TruncatedText text={rawData.post_message} maxLength={100} />}
                  className="sm:col-span-2"
                />
              )}
              <DataField
                label="เวลาโพสต์"
                value={formatDateTime(rawData.post_created_time)}
              />
              <DataFieldLink
                label="ลิงก์โพสต์"
                href={rawData.post_permalink_url}
                displayText="ดูโพสต์บน Facebook"
              />
            </DataGrid>
          </div>
        )}
      </div>
    </DetailSection>
  );
}
