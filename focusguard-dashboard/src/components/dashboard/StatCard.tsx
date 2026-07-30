/**
 * StatCard Component
 * Displays a statistic with title, value, icon, and optional subtitle
 * Includes skeleton loading state
 */
import React from 'react';
import { type LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  subtitle?: string;
  isLoading?: boolean;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon: Icon,
  subtitle,
  isLoading = false,
  className = '',
}) => {
  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl shadow-sm border border-gray-100 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-4">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-10 w-10 bg-gray-200 rounded-lg"></div>
          </div>
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
          {subtitle && <div className="h-3 bg-gray-200 rounded w-1/3"></div>}
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow duration-200 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        <div className="p-2.5 bg-blue-50 rounded-lg">
          <Icon size={20} className="text-blue-600" />
        </div>
      </div>
      <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
      {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
    </div>
  );
};
