/**
 * AIInsights Component
 * Displays AI-powered productivity insights
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertCircle, Lightbulb, TrendingUp, AlertTriangle, Target } from 'lucide-react';
import { aiService } from '../../services/ai';
import { CardSkeleton } from './LoadingSkeleton';
import { EmptyState } from './EmptyState';

export const AIInsights: React.FC<{
  startDate?: string;
  endDate?: string;
}> = ({ startDate, endDate }) => {
  const { data: insights, isLoading, error } = useQuery({
    queryKey: ['ai', 'insights', startDate, endDate],
    queryFn: () => aiService.getInsights(startDate, endDate),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Insights</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load insights</p>
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

  if (!insights) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Insights</h2>
        <EmptyState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Productivity Insights</h2>

      {/* Patterns */}
      {insights.patterns.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="text-blue-600" size={20} />
            <h3 className="font-semibold text-gray-900">Patterns</h3>
          </div>
          <ul className="space-y-2">
            {insights.patterns.map((pattern, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>{pattern}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Distractions */}
      {insights.distractions.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="text-amber-600" size={20} />
            <h3 className="font-semibold text-gray-900">Distractions</h3>
          </div>
          <ul className="space-y-2">
            {insights.distractions.map((distraction, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="text-amber-500 mt-0.5">⚠</span>
                <span>{distraction}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Category Balance */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Target className="text-green-600" size={20} />
          <h3 className="font-semibold text-gray-900">Category Balance</h3>
        </div>
        <p className="text-sm text-gray-600">{insights.category_balance}</p>
      </div>

      {/* Individual Insights */}
      {insights.insights.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {insights.insights.map((insight, index) => (
            <div
              key={index}
              className="bg-white rounded-xl shadow-sm border border-gray-100 p-5"
            >
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="text-yellow-500" size={18} />
                <span className="text-xs font-medium text-gray-500 uppercase">
                  {insight.category}
                </span>
              </div>
              <p className="text-sm text-gray-700 mb-2">{insight.insight}</p>
              {insight.data_point && (
                <p className="text-xs text-gray-500">{insight.data_point}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Focus Score Recommendations */}
      {insights.focus_score_recommendations.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Focus Score Tips</h3>
          <ul className="space-y-2">
            {insights.focus_score_recommendations.map((tip, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Time Allocation Suggestions */}
      {insights.time_allocation_suggestions.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Time Allocation</h3>
          <ul className="space-y-2">
            {insights.time_allocation_suggestions.map((suggestion, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="text-blue-500 mt-0.5">→</span>
                <span>{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
