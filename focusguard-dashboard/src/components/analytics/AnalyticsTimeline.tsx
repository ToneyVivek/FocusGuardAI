/**
 * AnalyticsTimeline Component
 * Displays timeline with pagination
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Clock, Globe, AlertCircle } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import type { DateRange } from './DateRangeFilter';
import { getDateRangeParams } from './DateRangeFilter';
import { getProductivityBadgeColor, getProductivityLabel } from '../../utils/productivity';
import { formatDateTimeForDisplay } from '../../utils/dateUtils';
import { DEFAULT_TIMELINE_LIMIT } from '../../constants/api';

interface AnalyticsTimelineProps {
  dateRange: DateRange;
  customStartDate?: string;
  customEndDate?: string;
}

const ITEMS_PER_PAGE = 20;

export const AnalyticsTimeline: React.FC<AnalyticsTimelineProps> = ({
  dateRange,
  customStartDate,
  customEndDate,
}) => {
  const [currentPage, setCurrentPage] = useState(1);

  const { start_date, end_date } = getDateRangeParams(dateRange, customStartDate, customEndDate);

  const { data: timeline, isLoading, error } = useQuery({
    queryKey: ['analytics', 'timeline', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserTimeline(DEFAULT_TIMELINE_LIMIT, start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const items = timeline?.items || [];
  const totalPages = Math.ceil(items.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentItems = items.slice(startIndex, endIndex);

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

  const formatTime = (dateString: string): string => {
    return formatDateTimeForDisplay(dateString);
  };

  const getFaviconUrl = (domain: string): string => {
    return `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
  };

  const handlePreviousPage = () => {
    setCurrentPage((prev) => Math.max(1, prev - 1));
  };

  const handleNextPage = () => {
    setCurrentPage((prev) => Math.min(totalPages, prev + 1));
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Timeline</h2>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
              <div className="w-8 h-8 bg-gray-200 rounded"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                <div className="h-3 bg-gray-200 rounded w-1/4"></div>
              </div>
              <div className="h-4 bg-gray-200 rounded w-16"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Timeline</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load timeline data</p>
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

  if (items.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Timeline</h2>
        <div className="text-center py-12">
          <Clock size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No browsing history found for the selected period</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Timeline</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePreviousPage}
            disabled={currentPage === 1}
            className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Previous page"
            aria-disabled={currentPage === 1}
          >
            <ChevronLeft size={20} />
          </button>
          <span className="text-sm text-gray-600" aria-live="polite">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
            className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Next page"
            aria-disabled={currentPage === totalPages}
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {currentItems.map((item) => (
          <div
            key={item.session_id}
            className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="relative shrink-0">
              {item.website_domain ? (
                <img
                  src={getFaviconUrl(item.website_domain)}
                  alt={item.website_domain}
                  className="w-8 h-8 rounded"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                    (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                  }}
                />
              ) : null}
              <Globe size={32} className="text-gray-400 hidden" />
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {item.website_domain || 'Unknown'}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {item.category || 'Uncategorized'}
              </p>
            </div>

            <div className="shrink-0">
              <span
                className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getProductivityBadgeColor(
                  item.productivity
                )}`}
              >
                {getProductivityLabel(item.productivity)}
              </span>
            </div>

            <div className="text-right shrink-0">
              <p className="text-sm text-gray-600">{formatDuration(item.duration_seconds)}</p>
              <p className="text-xs text-gray-500">{formatTime(item.start_time)}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
