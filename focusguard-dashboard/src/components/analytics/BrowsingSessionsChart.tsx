/**
 * BrowsingSessionsChart Component
 * Displays browsing sessions per day as a bar chart
 * Aggregates data from timeline in frontend
 */
import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from 'recharts';
import { parseToLocalDateString, formatDateShort } from '../../utils/dateUtils';
import { AlertCircle, Activity } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import type { DateRange } from './DateRangeFilter';
import { getDateRangeParams } from './DateRangeFilter';
import { DEFAULT_TIMELINE_LIMIT } from '../../constants/api';

interface BrowsingSessionsChartProps {
  dateRange: DateRange;
  customStartDate?: string;
  customEndDate?: string;
}

export const BrowsingSessionsChart: React.FC<BrowsingSessionsChartProps> = ({
  dateRange,
  customStartDate,
  customEndDate,
}) => {
  const { start_date, end_date } = getDateRangeParams(dateRange, customStartDate, customEndDate);

  const { data: timeline, isLoading, error } = useQuery({
    queryKey: ['analytics', 'timeline', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserTimeline(DEFAULT_TIMELINE_LIMIT, start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const chartData = useMemo(() => {
    if (!timeline?.items || timeline.items.length === 0) return [];

    // Aggregate timeline data by date
    const dateMap = new Map<string, number>();

    timeline.items.forEach((item) => {
      const date = parseToLocalDateString(item.start_time);
      dateMap.set(date, (dateMap.get(date) || 0) + 1);
    });

    // Convert to array and sort by date
    const sortedData = Array.from(dateMap.entries())
      .map(([date, sessions]) => ({
        date: formatDateShort(date),
        fullDate: date,
        sessions,
      }))
      .sort((a, b) => new Date(a.fullDate).getTime() - new Date(b.fullDate).getTime());

    return sortedData;
  }, [timeline]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          <p className="text-sm text-gray-600">
            Sessions: {payload[0].value}
          </p>
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Browsing Sessions per Day</h2>
        <div className="h-64 animate-pulse bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Browsing Sessions per Day</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load sessions data</p>
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

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Browsing Sessions per Day</h2>
        <div className="text-center py-12">
          <Activity size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No session data available for the selected period</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Browsing Sessions per Day</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} role="img" aria-label="Browsing sessions per day bar chart">
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="sessions" fill="#3b82f6" radius={[4, 4, 0, 0]}>
            <LabelList dataKey="sessions" position="top" fontSize={12} fill="#6b7280" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
