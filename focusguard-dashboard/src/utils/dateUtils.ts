/**
 * Date Utilities
 * Centralized date handling using LOCAL timezone
 * All date generation respects the user's local timezone
 */

/**
 * Format a Date object to YYYY-MM-DD string in LOCAL timezone
 */
export function formatDateForAPI(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Get today's date in LOCAL timezone as YYYY-MM-DD
 */
export function getTodayLocal(): string {
  return formatDateForAPI(new Date());
}

/**
 * Get yesterday's date in LOCAL timezone as YYYY-MM-DD
 */
export function getYesterdayLocal(): string {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  return formatDateForAPI(yesterday);
}

/**
 * Get current week range (Monday to today) in LOCAL timezone
 */
export function getCurrentWeekRange(): { start_date: string; end_date: string } {
  const today = new Date();
  const dayOfWeek = today.getDay();
  const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
  const startOfWeek = new Date(today);
  startOfWeek.setDate(diff);
  
  return {
    start_date: formatDateForAPI(startOfWeek),
    end_date: formatDateForAPI(today),
  };
}

/**
 * Get last week range (previous Monday to Sunday) in LOCAL timezone
 */
export function getLastWeekRange(): { start_date: string; end_date: string } {
  const today = new Date();
  const dayOfWeek = today.getDay();
  const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
  const startOfThisWeek = new Date(today);
  startOfThisWeek.setDate(diff);
  
  const startOfLastWeek = new Date(startOfThisWeek);
  startOfLastWeek.setDate(startOfLastWeek.getDate() - 7);
  
  const endOfLastWeek = new Date(startOfThisWeek);
  endOfLastWeek.setDate(endOfLastWeek.getDate() - 1);
  
  return {
    start_date: formatDateForAPI(startOfLastWeek),
    end_date: formatDateForAPI(endOfLastWeek),
  };
}

/**
 * Get current month range (1st to today) in LOCAL timezone
 */
export function getCurrentMonthRange(): { start_date: string; end_date: string } {
  const today = new Date();
  const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  
  return {
    start_date: formatDateForAPI(startOfMonth),
    end_date: formatDateForAPI(today),
  };
}

/**
 * Get last month range in LOCAL timezone
 */
export function getLastMonthRange(): { start_date: string; end_date: string } {
  const today = new Date();
  const startOfThisMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  const startOfLastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
  const endOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
  
  return {
    start_date: formatDateForAPI(startOfLastMonth),
    end_date: formatDateForAPI(endOfLastMonth),
  };
}

/**
 * Get last 7 days range in LOCAL timezone
 */
export function getLast7DaysRange(): { start_date: string; end_date: string } {
  const today = new Date();
  const start = new Date(today);
  start.setDate(start.getDate() - 6);
  
  return {
    start_date: formatDateForAPI(start),
    end_date: formatDateForAPI(today),
  };
}

/**
 * Get last 30 days range in LOCAL timezone
 */
export function getLast30DaysRange(): { start_date: string; end_date: string } {
  const today = new Date();
  const start = new Date(today);
  start.setDate(start.getDate() - 29);
  
  return {
    start_date: formatDateForAPI(start),
    end_date: formatDateForAPI(today),
  };
}

/**
 * Get date range params for analytics filter
 */
export function getDateRangeParams(
  range: 'today' | 'yesterday' | 'last7days' | 'last30days' | 'thisMonth' | 'custom',
  customStart?: string,
  customEnd?: string
): { start_date?: string; end_date?: string } {
  switch (range) {
    case 'today':
      return {
        start_date: getTodayLocal(),
        end_date: getTodayLocal(),
      };
    case 'yesterday':
      return {
        start_date: getYesterdayLocal(),
        end_date: getYesterdayLocal(),
      };
    case 'last7days':
      return getLast7DaysRange();
    case 'last30days':
      return getLast30DaysRange();
    case 'thisMonth':
      return getCurrentMonthRange();
    case 'custom':
      return {
        start_date: customStart,
        end_date: customEnd,
      };
    default:
      return {};
  }
}

/**
 * Get date range for report type
 */
export function getReportDateRange(
  type: 'daily' | 'weekly' | 'monthly' | 'custom'
): { start_date: string; end_date: string } {
  switch (type) {
    case 'daily':
      return {
        start_date: getTodayLocal(),
        end_date: getTodayLocal(),
      };
    case 'weekly':
      return getCurrentWeekRange();
    case 'monthly':
      return getCurrentMonthRange();
    case 'custom':
      return getLast30DaysRange();
    default:
      return {
        start_date: getTodayLocal(),
        end_date: getTodayLocal(),
      };
  }
}

/**
 * Calculate previous period dates for comparison
 */
export function getPreviousPeriodDates(
  type: 'week' | 'month',
  start: string,
  end: string
): { start_date: string; end_date: string } {
  const currentStart = new Date(start);
  const currentEnd = new Date(end);
  const diffDays = Math.floor((currentEnd.getTime() - currentStart.getTime()) / (1000 * 60 * 60 * 24));
  
  const prevStart = new Date(currentStart);
  const prevEnd = new Date(currentEnd);
  
  prevStart.setDate(prevStart.getDate() - diffDays - 1);
  prevEnd.setDate(prevEnd.getDate() - diffDays - 1);
  
  return {
    start_date: formatDateForAPI(prevStart),
    end_date: formatDateForAPI(prevEnd),
  };
}

/**
 * Format date for display (e.g., "Aug 5, 2026")
 */
export function formatDateForDisplay(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/**
 * Format date for short display (e.g., "Aug 5")
 */
export function formatDateShort(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format time for display (e.g., "2:30 PM")
 */
export function formatTimeForDisplay(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format datetime for display (e.g., "Aug 5, 2026, 2:30 PM")
 */
export function formatDateTimeForDisplay(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Get current timestamp in ISO format (for display purposes only)
 */
export function getCurrentTimestamp(): string {
  return new Date().toISOString();
}

/**
 * Parse a date string and return local date string (YYYY-MM-DD)
 * Useful for converting server timestamps to local date for grouping
 */
export function parseToLocalDateString(dateString: string): string {
  const date = new Date(dateString);
  return formatDateForAPI(date);
}
