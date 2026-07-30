/**
 * ReportSummary Component
 * Displays summary metrics for a report
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, TrendingUp, Pause, Percent, Activity, BarChart3, Globe, Folder } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';

interface ReportSummaryProps {
  startDate?: string;
  endDate?: string;
}

export const ReportSummary: React.FC<ReportSummaryProps> = ({ startDate, endDate }) => {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['report', 'summary', startDate, endDate],
    queryFn: () => dashboardService.getUserSummary(startDate, endDate),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const { data: domains } = useQuery({
    queryKey: ['report', 'domains', startDate, endDate],
    queryFn: () => dashboardService.getUserDomains(5, startDate, endDate),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const { data: categories } = useQuery({
    queryKey: ['report', 'categories', startDate, endDate],
    queryFn: () => dashboardService.getUserCategories(startDate, endDate),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const metrics = summary?.metrics;
  const focusScore = summary?.focus_score;

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

  const topDomains = domains?.domains.slice(0, 5) || [];
  const topCategories = categories?.categories.slice(0, 5) || [];

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Report Summary</h2>
        <div className="h-32 animate-pulse bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Report Summary</h2>
      
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={18} className="text-blue-600" />
            <span className="text-xs text-gray-500">Sessions</span>
          </div>
          <p className="text-xl font-bold text-gray-900">{metrics?.completed_sessions ?? 0}</p>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={18} className="text-green-600" />
            <span className="text-xs text-gray-500">Active Time</span>
          </div>
          <p className="text-xl font-bold text-gray-900">
            {metrics ? formatTime(metrics.productive_time + metrics.neutral_time + metrics.non_productive_time) : '--'}
          </p>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Pause size={18} className="text-gray-600" />
            <span className="text-xs text-gray-500">Idle Time</span>
          </div>
          <p className="text-xl font-bold text-gray-900">{metrics ? formatTime(metrics.idle_time) : '--'}</p>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={18} className="text-green-600" />
            <span className="text-xs text-gray-500">Productive</span>
          </div>
          <p className="text-xl font-bold text-gray-900">{metrics ? formatTime(metrics.productive_time) : '--'}</p>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 size={18} className="text-red-600" />
            <span className="text-xs text-gray-500">Non-Productive</span>
          </div>
          <p className="text-xl font-bold text-gray-900">{metrics ? formatTime(metrics.non_productive_time) : '--'}</p>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Percent size={18} className="text-purple-600" />
            <span className="text-xs text-gray-500">Focus Score</span>
          </div>
          <p className="text-xl font-bold text-gray-900">{focusScore ? `${Math.round(focusScore.score)}%` : '--'}</p>
        </div>
      </div>

      {/* Top Domains */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Globe size={16} />
          Top Domains
        </h3>
        {topDomains.length > 0 ? (
          <div className="space-y-2">
            {topDomains.map((domain, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="text-sm text-gray-700">{domain.domain}</span>
                <span className="text-sm text-gray-500">{formatTime(domain.duration_seconds)}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No domain data available</p>
        )}
      </div>

      {/* Top Categories */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Folder size={16} />
          Top Categories
        </h3>
        {topCategories.length > 0 ? (
          <div className="space-y-2">
            {topCategories.map((category, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="text-sm text-gray-700">{category.category}</span>
                <span className="text-sm text-gray-500">{formatTime(category.duration_seconds)}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No category data available</p>
        )}
      </div>
    </div>
  );
};
