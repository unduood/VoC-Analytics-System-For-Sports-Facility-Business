import { Badge } from '@/components/ui/Badge';
import {
  formatDate,
  getSentimentColor,
  getSentimentLabel,
  getIntentLabel,
  getSourceLabel,
  getSourceBadgeColor,
  getStatusColor,
  getStatusLabel,
  getAspectLabel,
  getAspectColor,
  truncateText,
} from '@/lib/utils';
import type { FeedbackWithAnalysis } from '@/lib/types';

interface FeedbackTableProps {
  data: FeedbackWithAnalysis[];
  onRowClick?: (feedback: FeedbackWithAnalysis) => void;
}

export function FeedbackTable({ data, onRowClick }: FeedbackTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="text-left py-3 px-4 font-medium text-gray-700">วันที่</th>
            <th className="text-left py-3 px-4 font-medium text-gray-700">ข้อความ</th>
            <th className="text-left py-3 px-4 font-medium text-gray-700">แหล่งที่มา</th>
            <th className="text-center py-3 px-4 font-medium text-gray-700">ความรู้สึก</th>
            <th className="text-center py-3 px-4 font-medium text-gray-700">ประเภท</th>
            <th className="text-center py-3 px-4 font-medium text-gray-700">ด้าน</th>
            <th className="text-center py-3 px-4 font-medium text-gray-700">สถานะ</th>
          </tr>
        </thead>
        <tbody>
          {data.length > 0 ? (
            data.map((feedback) => (
              <tr
                key={feedback.id}
                className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => onRowClick?.(feedback)}
              >
                <td className="py-3 px-4 whitespace-nowrap text-gray-600">
                  {formatDate(feedback.created_at_source || feedback.created_at)}
                </td>
                <td className="py-3 px-4 max-w-md">
                  <p className="text-gray-900">{truncateText(feedback.text_content, 100)}</p>
                </td>
                <td className="py-3 px-4 whitespace-nowrap">
                  <Badge className={getSourceBadgeColor(feedback.source_type)}>{getSourceLabel(feedback.source_type)}</Badge>
                </td>
                <td className="py-3 px-4 text-center whitespace-nowrap">
                  {feedback.sentiment_result && !feedback.sentiment_result.is_deleted ? (
                    <Badge className={getSentimentColor(feedback.sentiment_result.sentiment)}>
                      {getSentimentLabel(feedback.sentiment_result.sentiment)}
                    </Badge>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="py-3 px-4 text-center">
                  {feedback.intent_results && feedback.intent_results.filter((i) => !i.is_deleted).length > 0 ? (
                    <div className="flex flex-wrap gap-1 justify-center">
                      {feedback.intent_results
                        .filter((intent) => !intent.is_deleted)
                        .slice(0, 2)
                        .map((intent, idx) => (
                          <Badge key={idx} variant="info" className="text-xs">
                            {getIntentLabel(intent.intent)}
                          </Badge>
                        ))}
                    </div>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="py-3 px-4 text-center">
                  {feedback.aspect_results && feedback.aspect_results.length > 0 ? (
                    <div className="flex flex-wrap gap-1 justify-center">
                      {feedback.aspect_results
                        .filter((aspect) => !aspect.is_deleted)
                        .slice(0, 3)
                        .map((aspect, idx) => (
                          <Badge key={idx} className={`text-xs ${getAspectColor(aspect.sentiment)}`}>
                            {getAspectLabel(aspect.aspect)}
                          </Badge>
                        ))}
                      {feedback.aspect_results.filter((a) => !a.is_deleted).length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{feedback.aspect_results.filter((a) => !a.is_deleted).length - 3}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="py-3 px-4 text-center">
                  <Badge className={getStatusColor(feedback.processing_status)}>
                    {getStatusLabel(feedback.processing_status)}
                  </Badge>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={7} className="py-12 text-center text-gray-500">
                ไม่พบข้อมูล
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
