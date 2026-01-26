'use client';

import { FileText, Calendar, Hash } from 'lucide-react';
import { isGoogleFormRawData } from '@/lib/types';
import {
  DataField,
  DataGrid,
  DetailSection,
  SectionTitle,
  formatDateTime,
} from './shared';

interface GoogleFormDetailsProps {
  rawData: Record<string, unknown> | null;
}

/**
 * GoogleFormDetails - Renderer for Google Forms feedback
 *
 * This component is designed to be extensible for the upcoming
 * Google Forms integration. It currently supports common fields
 * and will display any additional fields dynamically.
 */
export function GoogleFormDetails({ rawData }: GoogleFormDetailsProps) {
  if (!rawData || !isGoogleFormRawData(rawData)) {
    return null;
  }

  // Known fields to display with special formatting
  const knownFields = ['form_id', 'response_id', 'submitted_at'];

  // Get any additional custom fields from the form response
  const additionalFields = Object.entries(rawData).filter(
    ([key, value]) =>
      !knownFields.includes(key) &&
      value !== null &&
      value !== undefined &&
      value !== ''
  );

  return (
    <DetailSection>
      <SectionTitle icon={<FileText className="w-4 h-4" />}>
        รายละเอียด Google Forms
      </SectionTitle>
      <div className="space-y-4">
        {/* Standard Form Fields */}
        <DataGrid>
          {rawData.form_id && (
            <DataField
              label="Form ID"
              value={
                <span className="flex items-center gap-1 font-mono text-xs">
                  <Hash className="w-3 h-3 text-gray-400" />
                  {String(rawData.form_id)}
                </span>
              }
            />
          )}
          {rawData.response_id && (
            <DataField
              label="Response ID"
              value={
                <span className="flex items-center gap-1 font-mono text-xs">
                  <Hash className="w-3 h-3 text-gray-400" />
                  {String(rawData.response_id)}
                </span>
              }
            />
          )}
          {rawData.submitted_at && (
            <DataField
              label="เวลาที่ส่ง"
              value={
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-gray-400" />
                  {formatDateTime(String(rawData.submitted_at))}
                </span>
              }
            />
          )}
        </DataGrid>

        {/* Additional Form Response Fields */}
        {additionalFields.length > 0 && (
          <div className="pt-3 border-t border-gray-200">
            <div className="text-xs text-gray-500 mb-2">ข้อมูลเพิ่มเติมจากแบบฟอร์ม</div>
            <DataGrid>
              {additionalFields.map(([key, value]) => (
                <DataField
                  key={key}
                  label={formatFieldLabel(key)}
                  value={formatFieldValue(value)}
                />
              ))}
            </DataGrid>
          </div>
        )}
      </div>
    </DetailSection>
  );
}

/**
 * Convert snake_case or camelCase field names to readable labels
 */
function formatFieldLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
}

/**
 * Format field values for display
 */
function formatFieldValue(value: unknown): React.ReactNode {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'boolean') return value ? 'ใช่' : 'ไม่';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
