'use client';

import { Info } from 'lucide-react';
import { DataField, DataGrid, DetailSection, SectionTitle } from './shared';

interface GenericDetailsProps {
  rawData: Record<string, unknown> | null;
}

/**
 * GenericDetails - Fallback renderer for unknown or new source types
 *
 * This component displays raw_data fields in a generic key-value format.
 * It serves as a fallback when no specific renderer is registered for a source type.
 *
 * Useful for:
 * - Debugging new source integrations
 * - Displaying data from sources not yet fully implemented
 * - Handling edge cases gracefully
 */
export function GenericDetails({ rawData }: GenericDetailsProps) {
  if (!rawData || Object.keys(rawData).length === 0) {
    return null;
  }

  // Filter out null/undefined/empty values
  const displayableFields = Object.entries(rawData).filter(
    ([, value]) => value !== null && value !== undefined && value !== ''
  );

  if (displayableFields.length === 0) {
    return null;
  }

  return (
    <DetailSection>
      <SectionTitle icon={<Info className="w-4 h-4" />}>
        ข้อมูลเพิ่มเติม
      </SectionTitle>
      <DataGrid>
        {displayableFields.map(([key, value]) => (
          <DataField
            key={key}
            label={formatLabel(key)}
            value={formatValue(value)}
          />
        ))}
      </DataGrid>
    </DetailSection>
  );
}

/**
 * Convert field keys to readable labels
 */
function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
}

/**
 * Format values for display
 */
function formatValue(value: unknown): React.ReactNode {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'boolean') return value ? 'ใช่' : 'ไม่';
  if (typeof value === 'object') {
    try {
      const str = JSON.stringify(value, null, 2);
      if (str.length > 100) {
        return (
          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto max-h-24 overflow-y-auto">
            {str}
          </pre>
        );
      }
      return <span className="font-mono text-xs">{str}</span>;
    } catch {
      return '[Object]';
    }
  }
  // Truncate long strings
  const strValue = String(value);
  if (strValue.length > 100) {
    return (
      <span title={strValue}>
        {strValue.slice(0, 100)}...
      </span>
    );
  }
  return strValue;
}
