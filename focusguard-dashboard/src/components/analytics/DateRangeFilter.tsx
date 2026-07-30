/**
 * DateRangeFilter Component
 * Provides date range selection for analytics
 */
import React from 'react';
import { Calendar, ChevronDown } from 'lucide-react';

export type DateRange = 'today' | 'yesterday' | 'last7days' | 'last30days' | 'thisMonth' | 'custom';

interface DateRangeFilterProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  customStartDate?: string;
  customEndDate?: string;
  onCustomStartChange?: (date: string) => void;
  onCustomEndChange?: (date: string) => void;
}

export const DateRangeFilter: React.FC<DateRangeFilterProps> = ({
  value,
  onChange,
  customStartDate,
  customEndDate,
  onCustomStartChange,
  onCustomEndChange,
}) => {
  const dateOptions = [
    { value: 'today' as DateRange, label: 'Today' },
    { value: 'yesterday' as DateRange, label: 'Yesterday' },
    { value: 'last7days' as DateRange, label: 'Last 7 Days' },
    { value: 'last30days' as DateRange, label: 'Last 30 Days' },
    { value: 'thisMonth' as DateRange, label: 'This Month' },
    { value: 'custom' as DateRange, label: 'Custom Range' },
  ];

  return (
    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
      <div className="relative">
        <label htmlFor="date-range-select" className="sr-only">Select date range</label>
        <select
          id="date-range-select"
          value={value}
          onChange={(e) => onChange(e.target.value as DateRange)}
          className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-10 text-sm font-medium text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
          aria-label="Select date range"
        >
          {dateOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" aria-hidden="true" />
      </div>

      {value === 'custom' && (
        <div className="flex items-center gap-2">
          <div className="relative">
            <label htmlFor="custom-start-date" className="sr-only">Start date</label>
            <input
              id="custom-start-date"
              type="date"
              value={customStartDate}
              onChange={(e) => onCustomStartChange?.(e.target.value)}
              className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-10 text-sm text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="Start date"
            />
            <Calendar size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" aria-hidden="true" />
          </div>
          <span className="text-gray-500" aria-hidden="true">to</span>
          <div className="relative">
            <label htmlFor="custom-end-date" className="sr-only">End date</label>
            <input
              id="custom-end-date"
              type="date"
              value={customEndDate}
              onChange={(e) => onCustomEndChange?.(e.target.value)}
              className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-10 text-sm text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="End date"
            />
            <Calendar size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" aria-hidden="true" />
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Get start and end dates for a given date range
 */
export function getDateRangeParams(range: DateRange, customStart?: string, customEnd?: string): { start_date?: string; end_date?: string } {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const formatDate = (date: Date) => date.toISOString().split('T')[0];

  switch (range) {
    case 'today':
      return {
        start_date: formatDate(today),
        end_date: formatDate(today),
      };

    case 'yesterday': {
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      return {
        start_date: formatDate(yesterday),
        end_date: formatDate(yesterday),
      };
    }

    case 'last7days': {
      const start = new Date(today);
      start.setDate(start.getDate() - 6);
      return {
        start_date: formatDate(start),
        end_date: formatDate(today),
      };
    }

    case 'last30days': {
      const start = new Date(today);
      start.setDate(start.getDate() - 29);
      return {
        start_date: formatDate(start),
        end_date: formatDate(today),
      };
    }

    case 'thisMonth': {
      const start = new Date(today.getFullYear(), today.getMonth(), 1);
      return {
        start_date: formatDate(start),
        end_date: formatDate(today),
      };
    }

    case 'custom':
      return {
        start_date: customStart,
        end_date: customEnd,
      };

    default:
      return {};
  }
}
