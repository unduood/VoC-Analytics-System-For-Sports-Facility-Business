'use client';

import { Instagram, User, Image, Film, MessageCircle } from 'lucide-react';
import { isInstagramRawData } from '@/lib/types';
import {
  DataField,
  DataGrid,
  DetailSection,
  SectionTitle,
  formatDateTime,
  TruncatedText,
} from './shared';

interface InstagramDetailsProps {
  rawData: Record<string, unknown> | null;
}

const mediaTypeLabels: Record<string, { label: string; icon: React.ReactNode }> = {
  photo: { label: 'รูปภาพ', icon: <Image className="w-3 h-3" /> },
  video: { label: 'วิดีโอ', icon: <Film className="w-3 h-3" /> },
  carousel_album: { label: 'อัลบั้ม', icon: <Image className="w-3 h-3" /> },
  reel: { label: 'Reel', icon: <Film className="w-3 h-3" /> },
};

export function InstagramDetails({ rawData }: InstagramDetailsProps) {
  if (!rawData || !isInstagramRawData(rawData)) {
    return null;
  }

  const mediaInfo = mediaTypeLabels[rawData.media_type] || {
    label: rawData.media_type,
    icon: <Image className="w-3 h-3" />,
  };

  return (
    <DetailSection>
      <SectionTitle icon={<Instagram className="w-4 h-4" />}>
        รายละเอียด Instagram
      </SectionTitle>
      <div className="space-y-4">
        {/* Comment Info */}
        <DataGrid>
          <DataField
            label="ชื่อผู้ใช้"
            value={
              <span className="flex items-center gap-1">
                <User className="w-3 h-3 text-gray-400" />
                @{rawData.username}
              </span>
            }
          />
          <DataField
            label="เวลาคอมเมนต์"
            value={formatDateTime(rawData.comment_timestamp)}
          />
        </DataGrid>

        {/* Post Info */}
        <div className="pt-3 border-t border-gray-200">
          <div className="flex items-center gap-1 text-xs text-gray-500 mb-2">
            <MessageCircle className="w-3 h-3" />
            ข้อมูลโพสต์
          </div>
          <DataGrid>
            <DataField
              label="ประเภทสื่อ"
              value={
                <span className="flex items-center gap-1 text-gray-600">
                  {mediaInfo.icon}
                  {mediaInfo.label}
                </span>
              }
            />
            <DataField
              label="เวลาโพสต์"
              value={formatDateTime(rawData.post_timestamp)}
            />
            {rawData.caption && (
              <DataField
                label="แคปชั่น"
                value={<TruncatedText text={rawData.caption} maxLength={80} />}
                className="sm:col-span-2"
              />
            )}
          </DataGrid>
        </div>
      </div>
    </DetailSection>
  );
}
