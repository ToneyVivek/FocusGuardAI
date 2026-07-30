/**
 * ReportTypeSelector Component
 * Selects report type (Daily, Weekly, Monthly, Custom)
 */
import React from 'react';

export type ReportType = 'daily' | 'weekly' | 'monthly' | 'custom';

interface ReportTypeSelectorProps {
  value: ReportType;
  onChange: (type: ReportType) => void;
}

export const ReportTypeSelector: React.FC<ReportTypeSelectorProps> = ({ value, onChange }) => {
  const options = [
    { value: 'daily' as ReportType, label: 'Daily' },
    { value: 'weekly' as ReportType, label: 'Weekly' },
    { value: 'monthly' as ReportType, label: 'Monthly' },
    { value: 'custom' as ReportType, label: 'Custom Range' },
  ];

  return (
    <div className="flex flex-wrap gap-3">
      {options.map((type) => (
        <button
          key={type.value}
          onClick={() => onChange(type.value)}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            value === type.value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
          aria-label={`Select ${type.label} report`}
        >
          {type.label}
        </button>
      ))}
    </div>
  );
};

/**
 * Get date range for a report type
 */
export function getReportDateRange(type: ReportType): { start_date: string; end_date: string } {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const formatDate = (date: Date) => date.toISOString().split('T')[0];

  switch (type) {
    case 'daily': {
      return {
        start_date: formatDate(today),
        end_date: formatDate(today),
      };
    }

    case 'weekly': {
      const start = new Date(today);
      const dayOfWeek = start.getDay();
      const diff = start.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
      start.setDate(diff);
      return {
        start_date: formatDate(start),
        end_date: formatDate(today),
      };
    }

    case 'monthly': {
      const start = new Date(today.getFullYear(), today.getMonth(), 1);
      return {
        start_date: formatDate(start),
        end_date: formatDate(today),
      };
    }

    case 'custom': {
      // Default to last 30 days for custom
      const start = new Date(today);
      start.setDate(start.getDate() - 29);
      return {
        start_date: formatDate(start),
        end_date: formatDate(today),
      };
    }

    default:
      return {
        start_date: formatDate(today),
        end_date: formatDate(today),
      };
  }
}
