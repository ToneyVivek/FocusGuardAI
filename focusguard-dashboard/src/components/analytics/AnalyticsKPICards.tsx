/**
 * AnalyticsKPICards Component
 * Displays KPI cards for analytics dashboard
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, TrendingUp, Pause, Percent, Activity, BarChart3 } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import { StatCard } from '../dashboard/StatCard';
import type { DateRange } from './DateRangeFilter';
import { getDateRangeParams } from './DateRangeFilter';

interface AnalyticsKPICardsProps {
  dateRange: DateRange;
  customStartDate?: string;
  customEndDate?: string;
}

export const AnalyticsKPICards: React.FC<AnalyticsKPICardsProps> = ({
  dateRange,
  customStartDate,
  customEndDate,
}) => {
  const { start_date, end_date } = getDateRangeParams(dateRange, customStartDate, customEndDate);

  const { data: summary, isLoading } = useQuery({
    queryKey: ['analytics', 'summary', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserSummary(start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const metrics = summary?.metrics;
  const focusScore = summary?.focus_score;

  // Format time in hours and minutes
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

  // Calculate average session duration
  const averageSessionDuration = metrics?.completed_sessions && metrics.completed_sessions > 0
    ? Math.round((metrics.productive_time + metrics.neutral_time + metrics.non_productive_time) / metrics.completed_sessions)
    : 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
      {/* Total Sessions */}
      <StatCard
        title="Total Sessions"
        value={metrics?.completed_sessions ?? 0}
        icon={Activity}
        isLoading={isLoading}
      />

      {/* Active Time */}
      <StatCard
        title="Active Time"
        value={metrics ? formatTime(metrics.productive_time + metrics.neutral_time + metrics.non_productive_time) : '--'}
        icon={Clock}
        isLoading={isLoading}
      />

      {/* Idle Time */}
      <StatCard
        title="Idle Time"
        value={metrics ? formatTime(metrics.idle_time) : '--'}
        icon={Pause}
        isLoading={isLoading}
      />

      {/* Productive Time */}
      <StatCard
        title="Productive Time"
        value={metrics ? formatTime(metrics.productive_time) : '--'}
        icon={TrendingUp}
        isLoading={isLoading}
      />

      {/* Non-Productive Time */}
      <StatCard
        title="Non-Productive Time"
        value={metrics ? formatTime(metrics.non_productive_time) : '--'}
        icon={BarChart3}
        isLoading={isLoading}
      />

      {/* Focus Score */}
      <StatCard
        title="Focus Score"
        value={focusScore ? `${Math.round(focusScore.score)}%` : '--'}
        icon={Percent}
        isLoading={isLoading}
      />

      {/* Average Session Duration */}
      <StatCard
        title="Avg Session Duration"
        value={averageSessionDuration > 0 ? formatTime(averageSessionDuration) : '--'}
        icon={Clock}
        isLoading={isLoading}
      />
    </div>
  );
};
