/**
 * CategoryBreakdownChart Component
 * Displays category breakdown as a horizontal bar chart
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts';
import { AlertCircle, Folder } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import type { DateRange } from './DateRangeFilter';
import { getDateRangeParams } from './DateRangeFilter';

interface CategoryBreakdownChartProps {
  dateRange: DateRange;
  customStartDate?: string;
  customEndDate?: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  DEVELOPMENT: '#3b82f6',
  EDUCATION: '#22c55e',
  AI_TOOL: '#8b5cf6',
  ENTERTAINMENT: '#ef4444',
  SEARCH_ENGINE: '#f97316',
  COMMUNICATION: '#06b6d4',
  NEWS: '#6366f1',
  SOCIAL_MEDIA: '#ec4899',
  SHOPPING: '#f59e0b',
  PRODUCTIVITY: '#10b981',
  OTHER: '#94a3b8',
};

export const CategoryBreakdownChart: React.FC<CategoryBreakdownChartProps> = ({
  dateRange,
  customStartDate,
  customEndDate,
}) => {
  const { start_date, end_date } = getDateRangeParams(dateRange, customStartDate, customEndDate);

  const { data: categories, isLoading, error } = useQuery({
    queryKey: ['analytics', 'categories', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserCategories(start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const chartData = categories?.categories
    .sort((a, b) => b.duration_seconds - a.duration_seconds)
    .map((cat) => ({
      name: cat.category,
      duration: cat.duration_seconds,
      percentage: cat.percentage,
      sessions: cat.session_count,
      color: CATEGORY_COLORS[cat.category] || CATEGORY_COLORS.OTHER,
    })) || [];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-medium text-gray-900">{data.name}</p>
          <p className="text-sm text-gray-600">Duration: {formatTime(data.duration)}</p>
          <p className="text-sm text-gray-600">Percentage: {Math.round(data.percentage)}%</p>
          <p className="text-sm text-gray-600">Sessions: {data.sessions}</p>
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Breakdown</h2>
        <div className="h-64 animate-pulse bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Breakdown</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load category data</p>
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

  if (!categories || chartData.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Breakdown</h2>
        <div className="text-center py-12">
          <Folder size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No category data available for the selected period</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Breakdown</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} layout="vertical" role="img" aria-label="Category breakdown horizontal bar chart">
          <XAxis type="number" tickFormatter={(value) => formatTime(value)} />
          <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 12 }} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="duration" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
