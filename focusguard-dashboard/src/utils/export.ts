/**
 * Export utilities for Reports
 */

/**
 * Format seconds to human-readable time
 */
export function formatTime(seconds: number): string {
  if (seconds === 0) return '0s';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;
  
  if (hours > 0) {
    if (minutes > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${hours}h`;
  }
  if (minutes > 0) {
    if (remainingSeconds > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${minutes}m`;
  }
  return `${remainingSeconds}s`;
}

/**
 * Export data to CSV format
 */
export function exportToCSV(data: any[], filename: string) {
  if (data.length === 0) {
    console.warn('No data to export');
    return;
  }

  // Get headers from first object
  const headers = Object.keys(data[0]);
  
  // Convert data to CSV format
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        // Handle null/undefined
        if (value === null || value === undefined) return '';
        // Handle objects/arrays
        if (typeof value === 'object') return JSON.stringify(value);
        // Escape quotes and wrap in quotes if contains comma
        const stringValue = String(value);
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      }).join(',')
    )
  ].join('\n');

  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', `${filename}.csv`);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
}

/**
 * Export timeline data to CSV
 */
export function exportTimelineToCSV(timeline: any[], filename: string) {
  const csvData = timeline.map(item => ({
    'Session ID': item.session_id,
    'Start Time': new Date(item.start_time).toISOString(),
    'End Time': new Date(item.end_time).toISOString(),
    'Duration (seconds)': item.duration_seconds,
    'Duration (formatted)': formatTime(item.duration_seconds),
    'Website URL': item.website_url || '',
    'Website Domain': item.website_domain || '',
    'Category': item.category || '',
    'Productivity': item.productivity || '',
  }));
  
  exportToCSV(csvData, filename);
}

/**
 * Export category breakdown to CSV
 */
export function exportCategoriesToCSV(categories: any[], filename: string) {
  const csvData = categories.map(item => ({
    'Category': item.category,
    'Duration (seconds)': item.duration_seconds,
    'Duration (formatted)': formatTime(item.duration_seconds),
    'Percentage': item.percentage.toFixed(2),
    'Session Count': item.session_count,
  }));
  
  exportToCSV(csvData, filename);
}

/**
 * Export domain breakdown to CSV
 */
export function exportDomainsToCSV(domains: any[], filename: string) {
  const csvData = domains.map(item => ({
    'Domain': item.domain,
    'Duration (seconds)': item.duration_seconds,
    'Duration (formatted)': formatTime(item.duration_seconds),
    'Session Count': item.session_count,
  }));
  
  exportToCSV(csvData, filename);
}

/**
 * Export summary metrics to CSV
 */
export function exportSummaryToCSV(summary: any, filename: string) {
  const csvData = [{
    'Metric': 'Value',
    'Total Focus Time (seconds)': summary.metrics?.total_focus_time || 0,
    'Productive Time (seconds)': summary.metrics?.productive_time || 0,
    'Neutral Time (seconds)': summary.metrics?.neutral_time || 0,
    'Non-Productive Time (seconds)': summary.metrics?.non_productive_time || 0,
    'Idle Time (seconds)': summary.metrics?.idle_time || 0,
    'Completed Sessions': summary.metrics?.completed_sessions || 0,
    'Idle Sessions': summary.metrics?.idle_sessions || 0,
    'Activity Events': summary.metrics?.activity_events || 0,
    'Focus Score': summary.focus_score?.score || 0,
  }];
  
  exportToCSV(csvData, filename);
}
