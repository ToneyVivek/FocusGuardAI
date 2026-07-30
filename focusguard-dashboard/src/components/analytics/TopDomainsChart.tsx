/**
 * TopDomainsChart Component
 * Displays top domains as a vertical bar chart
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';
import { AlertCircle, Globe } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import type { DateRange } from './DateRangeFilter';
import { getDateRangeParams } from './DateRangeFilter';

interface TopDomainsChartProps {
  dateRange: DateRange;
  customStartDate?: string;
  customEndDate?: string;
}

export const TopDomainsChart: React.FC<TopDomainsChartProps> = ({
  dateRange,
  customStartDate,
  customEndDate,
}) => {
  const { start_date, end_date } = getDateRangeParams(dateRange, customStartDate, customEndDate);

  const { data: domains, isLoading, error } = useQuery({
    queryKey: ['analytics', 'domains', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserDomains(10, start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const chartData = domains?.domains
    .sort((a, b) => b.duration_seconds - a.duration_seconds)
    .slice(0, 10)
    .map((domain) => ({
      name: domain.domain.length > 20 ? domain.domain.substring(0, 20) + '...' : domain.domain,
      fullName: domain.domain,
      duration: domain.duration_seconds,
      sessions: domain.session_count,
    })) || [];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-medium text-gray-900">{data.fullName}</p>
          <p className="text-sm text-gray-600">Duration: {formatTime(data.duration)}</p>
          <p className="text-sm text-gray-600">Sessions: {data.sessions}</p>
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Domains</h2>
        <div className="h-64 animate-pulse bg-gray-100 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Domains</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load domain data</p>
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

  if (!domains || chartData.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Domains</h2>
        <div className="text-center py-12">
          <Globe size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No domain data available for the selected period</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Domains</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} role="img" aria-label="Top 10 domains vertical bar chart">
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis 
            dataKey="name" 
            tick={{ fontSize: 11 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis tickFormatter={(value) => formatTime(value)} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="duration" fill="#3b82f6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
