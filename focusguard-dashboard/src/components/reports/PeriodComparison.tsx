/**
 * PeriodComparison Component
 * Compares two periods (e.g., This Week vs Last Week)
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, Minus, ArrowUp, ArrowDown } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import { getPreviousPeriodDates } from '../../utils/dateUtils';

export type ComparisonType = 'week' | 'month';

interface PeriodComparisonProps {
  startDate?: string;
  endDate?: string;
}

export const PeriodComparison: React.FC<PeriodComparisonProps> = ({ startDate, endDate }) => {
  const [comparisonType, setComparisonType] = useState<ComparisonType>('week');

  const { start_date: prevStart, end_date: prevEnd } = getPreviousPeriodDates(comparisonType, startDate || '', endDate || '');

  // Fetch current period data
  const { data: currentSummary, isLoading: currentLoading } = useQuery({
    queryKey: ['comparison', 'current', startDate, endDate],
    queryFn: () => dashboardService.getUserSummary(startDate, endDate),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // Fetch previous period data
  const { data: prevSummary, isLoading: prevLoading } = useQuery({
    queryKey: ['comparison', 'previous', prevStart, prevEnd],
    queryFn: () => dashboardService.getUserSummary(prevStart, prevEnd),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const isLoading = currentLoading || prevLoading;

  const calculateChange = (current: number, previous: number): { value: number; percentage: number } => {
    if (previous === 0) {
      return { value: current, percentage: current > 0 ? 100 : 0 };
    }
    const value = current - previous;
    const percentage = ((current - previous) / previous) * 100;
    return { value, percentage };
  };

  const formatTime = (seconds: number): string => {
    if (seconds === 0) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const currentMetrics = currentSummary?.metrics;
  const prevMetrics = prevSummary?.metrics;
  const currentFocusScore = currentSummary?.focus_score?.score || 0;
  const prevFocusScore = prevSummary?.focus_score?.score || 0;

  const productiveChange = calculateChange(currentMetrics?.productive_time || 0, prevMetrics?.productive_time || 0);
  const focusScoreChange = calculateChange(currentFocusScore, prevFocusScore);
  const sessionsChange = calculateChange(currentMetrics?.completed_sessions || 0, prevMetrics?.completed_sessions || 0);

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Period Comparison</h2>
        <div className="h-32 animate-pulse bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Period Comparison</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setComparisonType('week')}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              comparisonType === 'week'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Week vs Week
          </button>
          <button
            onClick={() => setComparisonType('month')}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              comparisonType === 'month'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Month vs Month
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Productive Time Comparison */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-medium text-gray-600 mb-3">Productive Time</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Current</span>
              <span className="font-semibold text-gray-900">{formatTime(currentMetrics?.productive_time || 0)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Previous</span>
              <span className="text-gray-600">{formatTime(prevMetrics?.productive_time || 0)}</span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-gray-200">
              <span className="text-xs text-gray-500">Change</span>
              <div className="flex items-center gap-1">
                {productiveChange.percentage > 0 ? (
                  <ArrowUp size={14} className="text-green-600" />
                ) : productiveChange.percentage < 0 ? (
                  <ArrowDown size={14} className="text-red-600" />
                ) : (
                  <Minus size={14} className="text-gray-400" />
                )}
                <span className={`text-sm font-medium ${
                  productiveChange.percentage > 0 ? 'text-green-600' : 
                  productiveChange.percentage < 0 ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {Math.abs(productiveChange.percentage).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Focus Score Comparison */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-medium text-gray-600 mb-3">Focus Score</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Current</span>
              <span className="font-semibold text-gray-900">{Math.round(currentFocusScore)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Previous</span>
              <span className="text-gray-600">{Math.round(prevFocusScore)}%</span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-gray-200">
              <span className="text-xs text-gray-500">Change</span>
              <div className="flex items-center gap-1">
                {focusScoreChange.percentage > 0 ? (
                  <ArrowUp size={14} className="text-green-600" />
                ) : focusScoreChange.percentage < 0 ? (
                  <ArrowDown size={14} className="text-red-600" />
                ) : (
                  <Minus size={14} className="text-gray-400" />
                )}
                <span className={`text-sm font-medium ${
                  focusScoreChange.percentage > 0 ? 'text-green-600' : 
                  focusScoreChange.percentage < 0 ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {Math.abs(focusScoreChange.percentage).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Sessions Comparison */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-medium text-gray-600 mb-3">Sessions</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Current</span>
              <span className="font-semibold text-gray-900">{currentMetrics?.completed_sessions ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">Previous</span>
              <span className="text-gray-600">{prevMetrics?.completed_sessions ?? 0}</span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-gray-200">
              <span className="text-xs text-gray-500">Change</span>
              <div className="flex items-center gap-1">
                {sessionsChange.percentage > 0 ? (
                  <ArrowUp size={14} className="text-green-600" />
                ) : sessionsChange.percentage < 0 ? (
                  <ArrowDown size={14} className="text-red-600" />
                ) : (
                  <Minus size={14} className="text-gray-400" />
                )}
                <span className={`text-sm font-medium ${
                  sessionsChange.percentage > 0 ? 'text-green-600' : 
                  sessionsChange.percentage < 0 ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {Math.abs(sessionsChange.percentage).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Overall Trend */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg flex items-center justify-between">
        <div className="flex items-center gap-3">
          {productiveChange.percentage > 0 ? (
            <TrendingUp size={24} className="text-green-600" />
          ) : productiveChange.percentage < 0 ? (
            <TrendingDown size={24} className="text-red-600" />
          ) : (
            <Minus size={24} className="text-gray-400" />
          )}
          <div>
            <p className="text-sm font-medium text-gray-900">
              {productiveChange.percentage > 0 ? 'More Productive' : 
               productiveChange.percentage < 0 ? 'Less Productive' : 'Same Productivity'}
            </p>
            <p className="text-xs text-gray-600">
              Compared to previous {comparisonType}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
