'use client';

import { AlertTriangle, Mail, MessageCircle } from 'lucide-react';
import type { RecentComplaint, SourceType } from '@/lib/types';
import { formatRelativeTime, getSourceLabel, getSourceBadgeColor, getAspectLabel, truncateText } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface RecentComplaintsProps {
  data: RecentComplaint[];
}

// Source icons mapping
function SourceIcon({ source, className }: { source: SourceType; className?: string }) {
  switch (source) {
    case 'email':
      return <Mail className={className} />;
    case 'instagram':
      return (
        <svg className={className} viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
        </svg>
      );
    case 'facebook':
      return (
        <svg className={className} viewBox="0 0 24 24" fill="currentColor">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
        </svg>
      );
    case 'google_maps':
      return (
        <svg className={className} viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0C7.802 0 4 3.403 4 7.602c0 .86.194 1.666.459 2.434l7.199 13.323a.39.39 0 00.684 0l7.199-13.323c.265-.768.459-1.574.459-2.434C20 3.403 16.198 0 12 0zm0 10.5c-1.657 0-3-1.343-3-3s1.343-3 3-3 3 1.343 3 3-1.343 3-3 3z" />
        </svg>
      );
    default:
      return <MessageCircle className={className} />;
  }
}

function ComplaintCard({ complaint }: { complaint: RecentComplaint }) {
  return (
    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 hover:border-slate-300 transition-colors">
      {/* Header with source badge */}
      <div className="flex items-center justify-between mb-2">
        <div
          className={cn(
            'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
            getSourceBadgeColor(complaint.source_type)
          )}
        >
          <SourceIcon source={complaint.source_type} className="w-3.5 h-3.5 shrink-0" />
          <span>{getSourceLabel(complaint.source_type)}</span>
        </div>
        {complaint.created_at && (
          <span className="text-xs text-slate-400">
            {formatRelativeTime(complaint.created_at)}
          </span>
        )}
      </div>

      {/* Feedback text */}
      <p className="text-sm text-slate-700 leading-relaxed mb-3">
        {truncateText(complaint.text_content, 120)}
      </p>

      {/* Negative aspect tags */}
      {complaint.negative_aspects.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {complaint.negative_aspects.map((aspect) => (
            <span
              key={aspect}
              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700"
            >
              {getAspectLabel(aspect)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export function RecentComplaints({ data }: RecentComplaintsProps) {
  if (data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          <h3 className="text-base font-semibold text-slate-900">
            Recent Complaints
          </h3>
        </div>
        <div className="flex items-center justify-center h-[300px] text-slate-400">
          No complaints found
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm h-full">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-amber-500" />
        <h3 className="text-base font-semibold text-slate-900">
          Recent Complaints
        </h3>
        <span className="ml-auto text-xs text-slate-400">
          {data.length} items
        </span>
      </div>

      {/* 2-column grid for complaint cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data.map((complaint) => (
          <ComplaintCard key={complaint.id} complaint={complaint} />
        ))}
      </div>
    </div>
  );
}
