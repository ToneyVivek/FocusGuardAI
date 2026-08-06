/**
 * ReportTypeSelector Component
 * Selects report type (Daily, Weekly, Monthly, Custom)
 */
import React from 'react';
import { getReportDateRange } from '../../utils/dateUtils';

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

// Re-export getReportDateRange from dateUtils for convenience
export { getReportDateRange };
