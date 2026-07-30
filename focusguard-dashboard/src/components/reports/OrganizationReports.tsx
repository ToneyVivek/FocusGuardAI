/**
 * OrganizationReports Component
 * Organization-level reports for ADMIN users
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Building, Users, TrendingUp, AlertCircle } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import { useAuth } from '../../contexts/AuthContext';

interface OrganizationReportsProps {
  startDate?: string;
  endDate?: string;
}

export const OrganizationReports: React.FC<OrganizationReportsProps> = ({ startDate, endDate }) => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  // Early return if not ADMIN
  if (!isAdmin) {
    return null;
  }

  const { data: orgSummary, isLoading, error } = useQuery({
    queryKey: ['org-report', 'summary', startDate, endDate],
    queryFn: () => dashboardService.getOrgSummary(startDate, endDate),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const formatTime = (seconds: number): string => {
    if (seconds === 0) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Organization Report</h2>
        <div className="h-32 animate-pulse bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Organization Report</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load organization data</p>
        </div>
      </div>
    );
  }

  const metrics = orgSummary?.metrics;
  const employeeCount = orgSummary?.employee_count || 0;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center gap-2 mb-6">
        <Building size={24} className="text-blue-600" />
        <h2 className="text-lg font-semibold text-gray-900">Organization Report</h2>
      </div>

      {/* Organization Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Users size={18} className="text-blue-600" />
            <span className="text-xs text-gray-500">Employees</span>
          </div>
          <p className="text-xl font-bold text-gray-900">{employeeCount}</p>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={18} className="text-green-600" />
            <span className="text-xs text-gray-500">Total Productive Time</span>
          </div>
          <p className="text-xl font-bold text-gray-900">
            {metrics ? formatTime(metrics.productive_time) : '--'}
          </p>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={18} className="text-purple-600" />
            <span className="text-xs text-gray-500">Total Active Time</span>
          </div>
          <p className="text-xl font-bold text-gray-900">
            {metrics ? formatTime(metrics.total_focus_time) : '--'}
          </p>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={18} className="text-blue-600" />
            <span className="text-xs text-gray-500">Total Sessions</span>
          </div>
          <p className="text-xl font-bold text-gray-900">
            {metrics?.completed_sessions ?? 0}
          </p>
        </div>
      </div>

      {/* Average Metrics */}
      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Average per Employee</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="p-3 bg-blue-50 rounded-lg">
            <p className="text-xs text-gray-600 mb-1">Avg Productive Time</p>
            <p className="text-lg font-semibold text-gray-900">
              {metrics && employeeCount > 0 ? formatTime(metrics.productive_time / employeeCount) : '--'}
            </p>
          </div>
          <div className="p-3 bg-green-50 rounded-lg">
            <p className="text-xs text-gray-600 mb-1">Avg Active Time</p>
            <p className="text-lg font-semibold text-gray-900">
              {metrics && employeeCount > 0 ? formatTime(metrics.total_focus_time / employeeCount) : '--'}
            </p>
          </div>
          <div className="p-3 bg-purple-50 rounded-lg">
            <p className="text-xs text-gray-600 mb-1">Avg Sessions</p>
            <p className="text-lg font-semibold text-gray-900">
              {metrics && employeeCount > 0 ? Math.round(metrics.completed_sessions / employeeCount) : '--'}
            </p>
          </div>
        </div>
      </div>

      {/* Note about user ranking */}
      <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-sm text-amber-800">
          <strong>Note:</strong> User ranking and top performers require additional backend endpoints 
          for individual user data comparison. This report shows organization-wide aggregates.
        </p>
      </div>
    </div>
  );
};
