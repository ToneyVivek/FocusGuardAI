/**
 * ProductivitySummary Component
 * Displays productive, idle, and non-productive time with progress bars
 * Includes skeleton loading state
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertCircle, TrendingUp } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';

export const ProductivitySummary: React.FC = () => {
  const { data: productivity, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'productivity'],
    queryFn: () => dashboardService.getUserProductivity(),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // Format time
  const formatTime = (seconds: number): string => {
    if (seconds === 0) return '0s';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    if (hours > 0) {
      if (minutes > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${hours}h`;
    }
    if (minutes > 0) {
      if (remainingSeconds > 0) {
        return `${minutes}m ${remainingSeconds}s`;
      }
      return `${minutes}m`;
    }
    return `${remainingSeconds}s`;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Productivity Summary</h2>
        <div className="animate-pulse space-y-6">
          {[...Array(3)].map((_, i) => (
            <div key={i}>
              <div className="flex justify-between mb-2">
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/6"></div>
              </div>
              <div className="h-3 bg-gray-200 rounded w-full"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Productivity Summary</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load productivity data</p>
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

  if (!productivity) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Productivity Summary</h2>
        <div className="text-center py-12">
          <TrendingUp size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No productivity data available yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Productivity Summary</h2>
      <div className="space-y-6">
        {/* Productive Time */}
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Productive Time</span>
            <span className="text-sm text-gray-600">
              {formatTime(productivity.productive.duration_seconds)} ({Math.round(productivity.productive.percentage)}%)
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-green-500 h-2.5 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${productivity.productive.percentage}%` }}
            ></div>
          </div>
        </div>

        {/* Neutral Time */}
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Neutral Time</span>
            <span className="text-sm text-gray-600">
              {formatTime(productivity.neutral.duration_seconds)} ({Math.round(productivity.neutral.percentage)}%)
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-yellow-500 h-2.5 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${productivity.neutral.percentage}%` }}
            ></div>
          </div>
        </div>

        {/* Non-Productive Time */}
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Non-Productive Time</span>
            <span className="text-sm text-gray-600">
              {formatTime(productivity.non_productive.duration_seconds)} ({Math.round(productivity.non_productive.percentage)}%)
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-red-500 h-2.5 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${productivity.non_productive.percentage}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};
