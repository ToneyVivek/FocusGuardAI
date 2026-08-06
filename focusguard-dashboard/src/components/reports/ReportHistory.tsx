/**
 * ReportHistory Component
 * Displays and manages report history using localStorage
 */
import React, { useState, useEffect } from 'react';
import { Calendar, Clock, History, Download, Trash2 } from 'lucide-react';
import { formatDateForDisplay, getCurrentTimestamp } from '../../utils/dateUtils';

interface SavedReport {
  id: string;
  reportType: string;
  startDate: string;
  endDate: string;
  generatedAt: string;
  summary: any;
}

export const ReportHistory: React.FC = () => {
  const [savedReports, setSavedReports] = useState<SavedReport[]>([]);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = () => {
    try {
      const stored = localStorage.getItem('focusguard-report-history');
      if (stored) {
        const reports = JSON.parse(stored);
        setSavedReports(reports);
      }
    } catch (error) {
      console.error('Failed to load report history:', error);
    }
  };

  const deleteReport = (id: string) => {
    try {
      const updated = savedReports.filter(r => r.id !== id);
      setSavedReports(updated);
      localStorage.setItem('focusguard-report-history', JSON.stringify(updated));
    } catch (error) {
      console.error('Failed to delete report:', error);
    }
  };

  const clearAllHistory = () => {
    try {
      setSavedReports([]);
      localStorage.removeItem('focusguard-report-history');
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  };

  const formatDate = (dateString: string): string => {
    return formatDateForDisplay(dateString);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <History size={24} className="text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Report History</h2>
        </div>
        {savedReports.length > 0 && (
          <button
            onClick={clearAllHistory}
            className="text-sm text-red-600 hover:text-red-700 font-medium"
          >
            Clear All
          </button>
        )}
      </div>

      {savedReports.length === 0 ? (
        <div className="text-center py-12">
          <History size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No saved reports yet</p>
          <p className="text-sm text-gray-400 mt-2">
            Generate a report to save it to history
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {savedReports.map((report) => (
            <div
              key={report.id}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded capitalize">
                    {report.reportType}
                  </span>
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Calendar size={12} />
                    <span>{report.startDate}</span>
                    <span>to</span>
                    <span>{report.endDate}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-400">
                  <Clock size={12} />
                  <span>Generated {formatDate(report.generatedAt)}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    // Would implement reopening the report
                    console.log('Reopen report:', report.id);
                  }}
                  className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="Reopen Report"
                >
                  <Download size={16} />
                </button>
                <button
                  onClick={() => deleteReport(report.id)}
                  className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Delete Report"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-sm text-amber-800">
          <strong>Note:</strong> Report history is stored locally in your browser. 
          Clearing browser data will remove this history. For persistent storage, 
          backend support is required.
        </p>
      </div>
    </div>
  );
};

/**
 * Save a report to history
 */
export function saveReportToHistory(
  reportType: string,
  startDate: string,
  endDate: string,
  summary: any
): void {
  try {
    const report: SavedReport = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      reportType,
      startDate,
      endDate,
      generatedAt: getCurrentTimestamp(),
      summary,
    };

    const stored = localStorage.getItem('focusguard-report-history');
    const reports: SavedReport[] = stored ? JSON.parse(stored) : [];
    
    // Add new report at the beginning
    reports.unshift(report);
    
    // Keep only last 20 reports
    const trimmed = reports.slice(0, 20);
    
    localStorage.setItem('focusguard-report-history', JSON.stringify(trimmed));
  } catch (error) {
    console.error('Failed to save report to history:', error);
  }
}
