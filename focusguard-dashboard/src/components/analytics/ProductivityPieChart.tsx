/**
 * ProductivityPieChart Component
 * Displays productivity distribution as a pie chart
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { AlertCircle, TrendingUp } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import type { DateRange } from './DateRangeFilter';
import { getDateRangeParams } from './DateRangeFilter';

interface ProductivityPieChartProps {
  dateRange: DateRange;
  customStartDate?: string;
  customEndDate?: string;
}

const COLORS = {
  productive: '#22c55e',
  neutral: '#eab308',
  non_productive: '#ef4444',
};

export const ProductivityPieChart: React.FC<ProductivityPieChartProps> = ({
  dateRange,
  customStartDate,
  customEndDate,
}) => {
  const { start_date, end_date } = getDateRangeParams(dateRange, customStartDate, customEndDate);

  const { data: productivity, isLoading, error } = useQuery({
    queryKey: ['analytics', 'productivity', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserProductivity(start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const chartData = productivity ? [
    {
      name: 'Productive',
      value: productivity.productive.duration_seconds,
      percentage: productivity.productive.percentage,
      color: COLORS.productive,
    },
    {
      name: 'Neutral',
      value: productivity.neutral.duration_seconds,
      percentage: productivity.neutral.percentage,
      color: COLORS.neutral,
    },
    {
      name: 'Non-Productive',
      value: productivity.non_productive.duration_seconds,
      percentage: productivity.non_productive.percentage,
      color: COLORS.non_productive,
    },
  ] : [];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-medium text-gray-900">{data.name}</p>
          <p className="text-sm text-gray-600">Duration: {formatTime(data.value)}</p>
          <p className="text-sm text-gray-600">Percentage: {Math.round(data.percentage)}%</p>
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Productivity Distribution</h2>
        <div className="h-64 animate-pulse bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Productivity Distribution</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load productivity data</p>
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

  if (!productivity || chartData.every(d => d.value === 0)) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Productivity Distribution</h2>
        <div className="text-center py-12">
          <TrendingUp size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No productivity data available for the selected period</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Productivity Distribution</h2>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart role="img" aria-label="Productivity distribution pie chart">
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, payload }) => `${name} (${Math.round(payload?.percentage || 0)}%)`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            layout="vertical" 
            verticalAlign="middle" 
            align="right"
            wrapperStyle={{ paddingLeft: '20px' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
