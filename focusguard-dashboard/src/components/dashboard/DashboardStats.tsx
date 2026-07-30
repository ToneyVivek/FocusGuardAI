/**
 * DashboardStats Component
 * Displays 6 statistic cards for the dashboard
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Clock, 
  TrendingUp, 
  Pause, 
  Percent, 
  Users, 
  Globe 
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { dashboardService } from '../../services/dashboard';
import { StatCard } from './StatCard';

export const DashboardStats: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  // Fetch user summary for stats
  const { data: summary, isLoading } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => dashboardService.getUserSummary(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });

  // Fetch domain breakdown for most visited website
  const { data: domains } = useQuery({
    queryKey: ['dashboard', 'domains'],
    queryFn: () => dashboardService.getUserDomains(1),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // Fetch organization summary for admin stats
  const { data: orgSummary } = useQuery({
    queryKey: ['dashboard', 'orgSummary'],
    queryFn: () => dashboardService.getOrgSummary(),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: isAdmin,
  });

  const metrics = summary?.metrics;
  const mostVisitedDomain = domains?.domains[0];

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

  return (
    <div className={`grid gap-6 mb-8 ${isAdmin ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-2'}`}>
      {/* Total Browsing Sessions */}
      <StatCard
        title="Total Browsing Sessions"
        value={metrics?.completed_sessions ?? 0}
        icon={Clock}
        isLoading={isLoading}
      />

      {/* Productive Time */}
      <StatCard
        title="Productive Time"
        value={metrics ? formatTime(metrics.productive_time) : '--'}
        icon={TrendingUp}
        isLoading={isLoading}
      />

      {/* Idle Time */}
      <StatCard
        title="Idle Time"
        value={metrics ? formatTime(metrics.idle_time) : '--'}
        icon={Pause}
        isLoading={isLoading}
      />

      {/* Productivity Percentage */}
      <StatCard
        title="Productivity"
        value={summary?.focus_score ? `${Math.round(summary.focus_score.score)}%` : '--'}
        icon={Percent}
        subtitle="Focus Score"
        isLoading={isLoading}
      />

      {/* Active Users (ADMIN only) */}
      {isAdmin && (
        <StatCard
          title="Active Users"
          value={orgSummary?.employee_count ?? 0}
          icon={Users}
          isLoading={isLoading}
        />
      )}

      {/* Most Visited Website */}
      <StatCard
        title="Most Visited Website"
        value={mostVisitedDomain?.domain ?? '--'}
        icon={Globe}
        subtitle={mostVisitedDomain ? `${mostVisitedDomain.session_count} visits` : undefined}
        isLoading={isLoading}
      />
    </div>
  );
};
