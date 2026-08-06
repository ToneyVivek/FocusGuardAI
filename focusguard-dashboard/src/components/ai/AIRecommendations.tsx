/**
 * AIRecommendations Component
 * Displays personalized AI recommendations
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';
import { aiService } from '../../services/ai';
import { CardSkeleton } from './LoadingSkeleton';
import { EmptyState } from './EmptyState';
import { getImpactColor } from '../../utils/formatting';

export const AIRecommendations: React.FC<{
  startDate?: string;
  endDate?: string;
}> = ({ startDate, endDate }) => {
  const { data: recommendations, isLoading, error } = useQuery({
    queryKey: ['ai', 'recommendations', startDate, endDate],
    queryFn: () => aiService.getRecommendations(startDate, endDate),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load recommendations</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!recommendations || recommendations.recommendations.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h2>
        <EmptyState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Personalized Recommendations</h2>

      {/* Priority Order */}
      {recommendations.priority_order.length > 0 && (
        <div className="bg-blue-50 rounded-xl border border-blue-200 p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="text-blue-600" size={18} />
            <h3 className="font-semibold text-blue-900 text-sm">Priority Order</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {recommendations.priority_order.map((title, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-white border border-blue-300 rounded-full text-sm text-blue-700"
              >
                {index + 1}. {title}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {recommendations.recommendations.map((rec, index) => (
          <div
            key={index}
            className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"
          >
            <div className="flex items-start justify-between mb-4">
              <h3 className="font-semibold text-gray-900">{rec.title}</h3>
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${getImpactColor(rec.impact)}`}
              >
                {rec.impact}
              </span>
            </div>

            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Implementation Steps</h4>
              <ol className="space-y-2">
                {rec.implementation_steps.map((step, stepIndex) => (
                  <li key={stepIndex} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-blue-500 mt-0.5">{stepIndex + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="pt-4 border-t border-gray-100">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <CheckCircle className="text-green-500" size={16} />
                <span className="font-medium">Expected Outcome:</span>
                <span>{rec.expected_outcome}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
