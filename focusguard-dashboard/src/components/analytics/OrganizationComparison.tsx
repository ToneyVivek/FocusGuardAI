/**
 * OrganizationComparison Component
 * Displays user vs organization comparison (ADMIN only)
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, TrendingUp, AlertCircle } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import { useAuth } from '../../contexts/AuthContext';
import type { DateRange } from './DateRangeFilter';
import { getDateRangeParams } from './DateRangeFilter';

interface OrganizationComparisonProps {
  dateRange: DateRange;
  customStartDate?: string;
  customEndDate?: string;
}

export const OrganizationComparison: React.FC<OrganizationComparisonProps> = ({
  dateRange,
  customStartDate,
  customEndDate,
}) => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  // Early return if not ADMIN
  if (!isAdmin) {
    return null;
  }

  const { start_date, end_date } = getDateRangeParams(dateRange, customStartDate, customEndDate);

  const { data: userSummary, isLoading: userLoading } = useQuery({
    queryKey: ['analytics', 'summary', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserSummary(start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: isAdmin,
  });

  const { data: orgSummary, isLoading: orgLoading } = useQuery({
    queryKey: ['analytics', 'orgSummary', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getOrgSummary(start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const isLoading = userLoading || orgLoading;

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const userProductiveTime = userSummary?.metrics?.productive_time || 0;
  const orgProductiveTime = orgSummary?.metrics?.productive_time || 0;
  const orgEmployeeCount = orgSummary?.employee_count || 1;
  const avgOrgProductiveTime = orgProductiveTime / orgEmployeeCount;

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Organization Comparison</h2>
        <div className="h-32 animate-pulse bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  if (!userSummary || !orgSummary) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Organization Comparison</h2>
        <div className="text-center py-8">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Unable to load comparison data</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Organization Comparison</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Productive Time Comparison */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <TrendingUp size={20} className="text-green-600" />
            <p className="text-sm text-gray-600">Productive Time</p>
          </div>
          <div className="space-y-2">
            <div>
              <p className="text-2xl font-bold text-gray-900">{formatTime(userProductiveTime)}</p>
              <p className="text-xs text-gray-500">Your Time</p>
            </div>
            <div className="border-t border-gray-200 pt-2">
              <p className="text-lg font-semibold text-gray-700">{formatTime(avgOrgProductiveTime)}</p>
              <p className="text-xs text-gray-500">Avg per Employee</p>
            </div>
            <div className={`text-sm font-medium ${userProductiveTime >= avgOrgProductiveTime ? 'text-green-600' : 'text-red-600'}`}>
              {userProductiveTime >= avgOrgProductiveTime ? 'Above average' : 'Below average'}
            </div>
          </div>
        </div>

        {/* Organization Size */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Users size={20} className="text-blue-600" />
            <p className="text-sm text-gray-600">Organization Size</p>
          </div>
          <div className="space-y-2">
            <div>
              <p className="text-2xl font-bold text-gray-900">{orgEmployeeCount}</p>
              <p className="text-xs text-gray-500">Total Employees</p>
            </div>
            <div className="border-t border-gray-200 pt-2">
              <p className="text-lg font-semibold text-gray-700">Active</p>
              <p className="text-xs text-gray-500">Status</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
