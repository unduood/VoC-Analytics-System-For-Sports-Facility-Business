'use client';

import { FileText, User, Calendar, Star, MessageSquare } from 'lucide-react';
import { GoogleFormRawData, isGoogleFormRawData } from '@/lib/types';
import {
  DataField,
  DataGrid,
  DetailSection,
  SectionTitle,
  StarRating,
  formatDateTime,
} from './shared';

interface GoogleFormDetailsProps {
  rawData: Record<string, unknown> | null;
}

/**
 * Aspect rating configuration in the correct order:
 * equipment → staff → cleanliness → atmosphere → price → location → programs → amenities
 */
const ASPECT_RATINGS: Array<{
  field: keyof GoogleFormRawData;
  label: string;
  thaiLabel: string;
}> = [
  { field: 'equipment_rating', label: 'Equipment', thaiLabel: 'อุปกรณ์' },
  { field: 'staff_rating', label: 'Staff', thaiLabel: 'พนักงาน' },
  { field: 'cleanliness_rating', label: 'Cleanliness', thaiLabel: 'ความสะอาด' },
  { field: 'atmosphere_rating', label: 'Atmosphere', thaiLabel: 'บรรยากาศ' },
  { field: 'price_rating', label: 'Price', thaiLabel: 'ราคา' },
  { field: 'location_rating', label: 'Location', thaiLabel: 'ทำเล' },
  { field: 'program_rating', label: 'Programs', thaiLabel: 'โปรแกรม' },
  { field: 'amenities_rating', label: 'Amenities', thaiLabel: 'สิ่งอำนวยความสะดวก' },
];

/**
 * Parse comma-separated string and display as a list
 */
function MultiValueList({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="text-gray-400">-</span>;

  const items = value.split(',').map((item) => item.trim()).filter(Boolean);

  if (items.length === 0) return <span className="text-gray-400">-</span>;
  if (items.length === 1) return <span>{items[0]}</span>;

  return (
    <ul className="space-y-0.5">
      {items.map((item, index) => (
        <li key={index} className="text-sm text-gray-800 flex items-start gap-1">
          <span className="text-gray-400">•</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

/**
 * Compact star display for aspect rating cards
 */
function CompactStars({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          className={`text-xs ${i < rating ? 'text-yellow-400' : 'text-gray-300'}`}
        >
          ★
        </span>
      ))}
    </div>
  );
}

/**
 * GoogleFormDetails - Renderer for Google Forms survey feedback
 *
 * Displays:
 * 1. Overall Rating - Prominent display with stars
 * 2. Demographics Section - gender, age_group, membership_type, visit_frequency, preferred_period, timestamp
 * 3. Aspect Ratings Grid - All 8 ratings in compact cards with stars
 * 4. Additional Suggestions - If provided, show in text box
 */
export function GoogleFormDetails({ rawData }: GoogleFormDetailsProps) {
  if (!rawData || !isGoogleFormRawData(rawData)) {
    return null;
  }

  const data = rawData as GoogleFormRawData;

  return (
    <div className="space-y-4">
      {/* Overall Rating - Prominent Display */}
      <DetailSection>
        <SectionTitle icon={<Star className="w-4 h-4" />}>
          คะแนนความพึงพอใจโดยรวม
        </SectionTitle>
        <div className="flex items-center justify-center py-2">
          <div className="flex flex-col items-center">
            <StarRating rating={data.overall_rating} />
            <span className="text-xs text-gray-500 mt-1">จาก 5 คะแนน</span>
          </div>
        </div>
      </DetailSection>

      {/* Demographics Section */}
      <DetailSection>
        <SectionTitle icon={<User className="w-4 h-4" />}>
          ข้อมูลผู้ตอบแบบสอบถาม
        </SectionTitle>
        <DataGrid columns={3}>
          <DataField label="เพศ" value={data.gender} />
          <DataField label="กลุ่มอายุ" value={data.age_group} />
          <DataField label="ประเภทสมาชิก" value={data.membership_type} />
          <DataField label="ความถี่ในการมาใช้บริการ" value={data.visit_frequency} />
          <DataField
            label="ช่วงเวลาที่ชอบ"
            value={<MultiValueList value={data.preferred_period} />}
          />
          <DataField
            label="วันที่ส่งแบบสอบถาม"
            value={
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3 text-gray-400" />
                {formatDateTime(data.timestamp)}
              </span>
            }
          />
        </DataGrid>
      </DetailSection>

      {/* Aspect Ratings Grid */}
      <DetailSection>
        <SectionTitle icon={<FileText className="w-4 h-4" />}>
          คะแนนรายด้าน
        </SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {ASPECT_RATINGS.map(({ field, thaiLabel }) => {
            const rating = data[field] as number;
            return (
              <div
                key={field}
                className="bg-white border border-gray-200 rounded-lg p-2 flex flex-col items-center"
              >
                <span className="text-xs text-gray-600 mb-1">{thaiLabel}</span>
                <CompactStars rating={rating} />
                <span className="text-sm font-medium text-gray-700 mt-0.5">
                  {rating}/5
                </span>
              </div>
            );
          })}
        </div>
      </DetailSection>

      {/* Additional Suggestions */}
      {data.additional_suggestions && (
        <DetailSection>
          <SectionTitle icon={<MessageSquare className="w-4 h-4" />}>
            ข้อเสนอแนะเพิ่มเติม
          </SectionTitle>
          <div className="bg-white border border-gray-200 rounded-lg p-3">
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {data.additional_suggestions}
            </p>
          </div>
        </DetailSection>
      )}
    </div>
  );
}
