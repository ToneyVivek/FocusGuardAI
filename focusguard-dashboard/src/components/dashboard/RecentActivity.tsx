/**
 * RecentActivity Component
 * Displays recent browsing sessions in a table format
 * Includes skeleton loading state and empty state
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, AlertCircle } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import { getProductivityBadgeColor, getProductivityLabel } from '../../utils/productivity';
import { formatTimeForDisplay } from '../../utils/dateUtils';

export const RecentActivity: React.FC = () => {
  const { data: timeline, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'timeline'],
    queryFn: () => dashboardService.getUserTimeline(10),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const activities = timeline?.items || [];

  // Format duration
  const formatDuration = (seconds: number): string => {
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

  // Format time
  const formatTime = (dateString: string): string => {
    return formatTimeForDisplay(dateString);
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4">
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/6"></div>
              <div className="h-4 bg-gray-200 rounded w-1/5"></div>
              <div className="h-4 bg-gray-200 rounded w-1/6"></div>
              <div className="h-4 bg-gray-200 rounded w-1/8"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load recent activity</p>
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

  if (activities.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="text-center py-12">
          <Clock size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No browsing activity available yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-white">
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Website</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Category</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Productivity</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Duration</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Time</th>
            </tr>
          </thead>
          <tbody>
            {activities.slice(0, 10).map((activity, index) => (
              <tr 
                key={activity.session_id} 
                className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
              >
                <td className="py-3 px-4 text-sm text-gray-900">
                  {activity.website_domain || 'Unknown'}
                </td>
                <td className="py-3 px-4 text-sm text-gray-600">
                  {activity.category || 'Uncategorized'}
                </td>
                <td className="py-3 px-4">
                  <span
                    className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium ${getProductivityBadgeColor(
                      activity.productivity
                    )}`}
                  >
                    {getProductivityLabel(activity.productivity)}
                  </span>
                </td>
                <td className="py-3 px-4 text-sm text-gray-600">
                  {formatDuration(activity.duration_seconds)}
                </td>
                <td className="py-3 px-4 text-sm text-gray-600">
                  {formatTime(activity.start_time)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
