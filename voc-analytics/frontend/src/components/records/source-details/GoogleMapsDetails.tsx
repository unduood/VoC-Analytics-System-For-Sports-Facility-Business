'use client';

import { MapPin, User, Calendar, Edit } from 'lucide-react';
import { isGoogleMapsRawData } from '@/lib/types';
import {
  DataField,
  DataFieldLink,
  DataGrid,
  DetailSection,
  SectionTitle,
  StarRating,
  formatDateShort,
} from './shared';

interface GoogleMapsDetailsProps {
  rawData: Record<string, unknown> | null;
}

export function GoogleMapsDetails({ rawData }: GoogleMapsDetailsProps) {
  if (!rawData || !isGoogleMapsRawData(rawData)) {
    return null;
  }

  const wasEdited = rawData.iso_date_of_last_edit && rawData.iso_date_of_last_edit !== rawData.iso_date;

  return (
    <DetailSection>
      <SectionTitle icon={<MapPin className="w-4 h-4" />}>
        รายละเอียดรีวิว Google Maps
      </SectionTitle>
      <div className="space-y-4">
        {/* Rating and Reviewer */}
        <DataGrid columns={3}>
          <DataField
            label="คะแนน"
            value={<StarRating rating={rawData.rating} />}
          />
          <DataField
            label="ผู้รีวิว"
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
          <DataFieldLink
            label="ลิงก์รีวิว"
            href={rawData.link}
            displayText="ดูบน Google Maps"
          />
        </DataGrid>

        {/* Dates */}
        <div className="pt-3 border-t border-gray-200">
          <DataGrid>
            <DataField
              label="วันที่รีวิว"
              value={
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-gray-400" />
                  {formatDateShort(rawData.iso_date)}
                </span>
              }
            />
            {wasEdited && (
              <DataField
                label="แก้ไขล่าสุด"
                value={
                  <span className="flex items-center gap-1 text-amber-600">
                    <Edit className="w-3 h-3" />
                    {formatDateShort(rawData.iso_date_of_last_edit)}
                  </span>
                }
              />
            )}
          </DataGrid>
        </div>

        {/* Original text if different from snippet */}
        {rawData.original && rawData.original !== rawData.snippet && (
          <div className="pt-3 border-t border-gray-200">
            <DataField
              label="ข้อความต้นฉบับ"
              value={
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {rawData.original}
                </p>
              }
            />
          </div>
        )}
      </div>
    </DetailSection>
  );
}
