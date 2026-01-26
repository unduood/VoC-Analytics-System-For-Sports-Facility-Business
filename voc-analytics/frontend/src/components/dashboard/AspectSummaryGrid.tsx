import { Card } from '@/components/ui/Card';
import { getAspectLabel } from '@/lib/utils';
import type { AspectSummary } from '@/lib/types';

interface AspectSummaryGridProps {
  data: AspectSummary[];
}

export function AspectSummaryGrid({ data }: AspectSummaryGridProps) {
  // Sort by total mentions descending
  const sortedData = [...data]
    .filter((item) => item.total_mentions > 0)
    .sort((a, b) => b.total_mentions - a.total_mentions);

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Aspect Summary</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {sortedData.length > 0 ? (
          sortedData.map((item) => {
            const total = item.positive + item.neutral + item.negative;
            const positivePercent = total > 0 ? (item.positive / total) * 100 : 0;

            return (
              <Card key={item.aspect} className="p-5">
                <div className="space-y-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">
                      {getAspectLabel(item.aspect)}
                    </h3>
                    <p className="text-sm text-slate-600 mt-1">
                      {item.total_mentions} การกล่าวถึง
                    </p>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-1">
                    <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                      <div
                        className="bg-green-500 h-2.5 rounded-full transition-all duration-300"
                        style={{ width: `${positivePercent}%` }}
                      />
                    </div>
                    <p className="text-sm font-medium text-green-600">
                      {positivePercent.toFixed(0)}% positive
                    </p>
                  </div>

                  {/* Sentiment Breakdown */}
                  <div className="flex items-center justify-between text-xs text-slate-600">
                    <span className="flex items-center">
                      <span className="w-2 h-2 rounded-full bg-green-500 mr-1"></span>
                      {item.positive}
                    </span>
                    <span className="flex items-center">
                      <span className="w-2 h-2 rounded-full bg-amber-500 mr-1"></span>
                      {item.neutral}
                    </span>
                    <span className="flex items-center">
                      <span className="w-2 h-2 rounded-full bg-red-500 mr-1"></span>
                      {item.negative}
                    </span>
                  </div>
                </div>
              </Card>
            );
          })
        ) : (
          <div className="col-span-full flex items-center justify-center py-12 text-slate-500">
            ไม่มีข้อมูล Aspect
          </div>
        )}
      </div>
    </div>
  );
}
