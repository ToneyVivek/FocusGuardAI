/**
 * DailyTrendChart Component
 * Displays daily productivity trend as a line chart
 * Aggregates data from timeline in frontend
 */
import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { parseToLocalDateString, formatDateShort } from '../../utils/dateUtils';
import { AlertCircle, TrendingUp } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import type { DateRange } from './DateRangeFilter';
import { getDateRangeParams } from './DateRangeFilter';
import { DEFAULT_TIMELINE_LIMIT } from '../../constants/api';
import { normalizeProductivity } from '../../utils/productivity';

interface DailyTrendChartProps {
  dateRange: DateRange;
  customStartDate?: string;
  customEndDate?: string;
}

export const DailyTrendChart: React.FC<DailyTrendChartProps> = ({
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
    const dateMap = new Map<string, {
      productive: number;
      neutral: number;
      non_productive: number;
      sessions: number;
    }>();

    timeline.items.forEach((item) => {
      const date = parseToLocalDateString(item.start_time);
      const existing = dateMap.get(date) || { productive: 0, neutral: 0, non_productive: 0, sessions: 0 };

      const productivity = normalizeProductivity(item.productivity);
      
      if (productivity === 'PRODUCTIVE') {
        existing.productive += item.duration_seconds;
      } else if (productivity === 'NON_PRODUCTIVE') {
        existing.non_productive += item.duration_seconds;
      } else {
        existing.neutral += item.duration_seconds;
      }
      
      existing.sessions += 1;
      dateMap.set(date, existing);
    });

    // Convert to array and sort by date
    const sortedData = Array.from(dateMap.entries())
      .map(([date, values]) => ({
        date: formatDateShort(date),
        fullDate: date,
        productive: Math.round(values.productive / 60), // Convert to minutes
        neutral: Math.round(values.neutral / 60),
        non_productive: Math.round(values.non_productive / 60),
        sessions: values.sessions,
      }))
      .sort((a, b) => new Date(a.fullDate).getTime() - new Date(b.fullDate).getTime());

    return sortedData;
  }, [timeline]);

  const formatMinutes = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm text-gray-600" style={{ color: entry.color }}>
              {entry.name}: {formatMinutes(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Productivity Trend</h2>
        <div className="h-64 animate-pulse bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Productivity Trend</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load trend data</p>
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
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Productivity Trend</h2>
        <div className="text-center py-12">
          <TrendingUp size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No trend data available for the selected period</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Productivity Trend</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} role="img" aria-label="Daily productivity trend line chart">
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={(value) => formatMinutes(value)} />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            verticalAlign="top" 
            height={36}
            wrapperStyle={{ paddingBottom: '8px' }}
          />
          <Line 
            type="monotone" 
            dataKey="productive" 
            stroke="#22c55e" 
            strokeWidth={2}
            dot={{ r: 5, fill: '#22c55e', strokeWidth: 2 }}
            activeDot={{ r: 7, fill: '#22c55e', strokeWidth: 2 }}
            name="Productive"
          />
          <Line 
            type="monotone" 
            dataKey="neutral" 
            stroke="#eab308" 
            strokeWidth={2}
            dot={{ r: 5, fill: '#eab308', strokeWidth: 2 }}
            activeDot={{ r: 7, fill: '#eab308', strokeWidth: 2 }}
            name="Neutral"
          />
          <Line 
            type="monotone" 
            dataKey="non_productive" 
            stroke="#ef4444" 
            strokeWidth={2}
            dot={{ r: 5, fill: '#ef4444', strokeWidth: 2 }}
            activeDot={{ r: 7, fill: '#ef4444', strokeWidth: 2 }}
            name="Non-Productive"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
