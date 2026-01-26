'use client';

import { format } from 'date-fns';
import { th } from 'date-fns/locale';
import { ExternalLink } from 'lucide-react';

/**
 * Format a date string to Thai locale
 */
export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return '-';
  try {
    return format(new Date(dateString), 'PPpp', { locale: th });
  } catch {
    return dateString;
  }
}

/**
 * Format a date string to short format
 */
export function formatDateShort(dateString: string | null | undefined): string {
  if (!dateString) return '-';
  try {
    return format(new Date(dateString), 'PP', { locale: th });
  } catch {
    return dateString;
  }
}

/**
 * DataField - Reusable component for displaying labeled data
 */
interface DataFieldProps {
  label: string;
  value: React.ReactNode;
  className?: string;
}

export function DataField({ label, value, className = '' }: DataFieldProps) {
  if (value === null || value === undefined || value === '') return null;

  return (
    <div className={`flex flex-col ${className}`}>
      <span className="text-xs text-gray-500 mb-0.5">{label}</span>
      <span className="text-sm text-gray-800">{value}</span>
    </div>
  );
}

/**
 * DataFieldLink - Data field with external link
 */
interface DataFieldLinkProps {
  label: string;
  href: string | null | undefined;
  displayText?: string;
}

export function DataFieldLink({ label, href, displayText }: DataFieldLinkProps) {
  if (!href) return null;

  return (
    <div className="flex flex-col">
      <span className="text-xs text-gray-500 mb-0.5">{label}</span>
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
      >
        {displayText || 'ดูลิงก์'}
        <ExternalLink className="w-3 h-3" />
      </a>
    </div>
  );
}

/**
 * DataGrid - Grid layout for data fields
 */
interface DataGridProps {
  children: React.ReactNode;
  columns?: 2 | 3;
}

export function DataGrid({ children, columns = 2 }: DataGridProps) {
  const gridCols = columns === 3 ? 'grid-cols-1 sm:grid-cols-3' : 'grid-cols-1 sm:grid-cols-2';
  return <div className={`grid ${gridCols} gap-3`}>{children}</div>;
}

/**
 * SectionTitle - Title for detail sections
 */
interface SectionTitleProps {
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export function SectionTitle({ icon, children }: SectionTitleProps) {
  return (
    <div className="flex items-center gap-2 mb-3">
      {icon && <span className="text-gray-500">{icon}</span>}
      <h4 className="text-sm font-semibold text-gray-700">{children}</h4>
    </div>
  );
}

/**
 * DetailSection - Container for a group of related data fields
 */
interface DetailSectionProps {
  children: React.ReactNode;
  className?: string;
}

export function DetailSection({ children, className = '' }: DetailSectionProps) {
  return (
    <div className={`bg-slate-50 rounded-lg p-4 ${className}`}>
      {children}
    </div>
  );
}

/**
 * StarRating - Display star rating
 */
interface StarRatingProps {
  rating: number | null | undefined;
  maxRating?: number;
}

export function StarRating({ rating, maxRating = 5 }: StarRatingProps) {
  if (rating === null || rating === undefined) return <span className="text-gray-400">-</span>;

  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: maxRating }, (_, i) => (
        <span
          key={i}
          className={i < rating ? 'text-yellow-400' : 'text-gray-300'}
        >
          ★
        </span>
      ))}
      <span className="text-sm text-gray-600 ml-1">({rating})</span>
    </div>
  );
}

/**
 * TruncatedText - Display text with optional truncation
 */
interface TruncatedTextProps {
  text: string | null | undefined;
  maxLength?: number;
  className?: string;
}

export function TruncatedText({ text, maxLength = 100, className = '' }: TruncatedTextProps) {
  if (!text) return <span className="text-gray-400">-</span>;

  const truncated = text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;

  return (
    <span className={`text-sm text-gray-700 ${className}`} title={text}>
      {truncated}
    </span>
  );
}
