/**
 * Employee Report Viewer Component
 * Reusable component for viewing employee reports
 */
import React from 'react';
import { User, Clock, Target, TrendingUp, Activity, Download, X } from 'lucide-react';

interface ReportViewerProps {
  employee: {
    full_name: string;
    email: string;
  };
  report: {
    report_type: string;
    start_date: string;
    end_date: string;
    created_at: string;
  };
  metrics?: {
    focus_score: number;
    productive_time: number;
    idle_time: number;
    completed_sessions: number;
  };
  aiSummary?: string;
  recommendations?: string[];
  onClose: () => void;
}

export const EmployeeReportViewer: React.FC<ReportViewerProps> = ({
  employee,
  report,
  metrics,
  aiSummary,
  recommendations,
  onClose,
}) => {
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-gray-700">
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <User className="text-blue-400" size={24} />
              <div>
                <h2 className="text-xl font-bold text-white">{employee.full_name}</h2>
                <p className="text-sm text-gray-400">{employee.email}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="text-gray-400" size={20} />
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 text-sm font-medium rounded-full ${
              report.report_type === 'daily'
                ? 'bg-blue-900 text-blue-300'
                : report.report_type === 'weekly'
                ? 'bg-purple-900 text-purple-300'
                : 'bg-green-900 text-green-300'
            }`}>
              {report.report_type.charAt(0).toUpperCase() + report.report_type.slice(1)} Report
            </span>
            <span className="text-gray-400">
              {formatDate(report.start_date)} - {formatDate(report.end_date)}
            </span>
          </div>
        </div>

        {/* Metrics */}
        {metrics && (
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-750 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="text-purple-400" size={16} />
                  <span className="text-sm text-gray-400">Focus Score</span>
                </div>
                <p className="text-2xl font-bold text-white">{metrics.focus_score.toFixed(1)}</p>
              </div>
              <div className="bg-gray-750 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="text-emerald-400" size={16} />
                  <span className="text-sm text-gray-400">Productive</span>
                </div>
                <p className="text-2xl font-bold text-white">{formatTime(metrics.productive_time)}</p>
              </div>
              <div className="bg-gray-750 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="text-orange-400" size={16} />
                  <span className="text-sm text-gray-400">Idle</span>
                </div>
                <p className="text-2xl font-bold text-white">{formatTime(metrics.idle_time)}</p>
              </div>
              <div className="bg-gray-750 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="text-blue-400" size={16} />
                  <span className="text-sm text-gray-400">Sessions</span>
                </div>
                <p className="text-2xl font-bold text-white">{metrics.completed_sessions}</p>
              </div>
            </div>
          </div>
        )}

        {/* AI Summary */}
        {aiSummary && (
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-3">AI Summary</h3>
            <div className="bg-gray-750 rounded-lg p-4">
              <p className="text-gray-300 text-sm leading-relaxed">{aiSummary}</p>
            </div>
          </div>
        )}

        {/* Recommendations */}
        {recommendations && recommendations.length > 0 && (
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-3">Recommendations</h3>
            <ul className="space-y-2">
              {recommendations.map((rec, index) => (
                <li key={index} className="flex items-start gap-2 text-gray-300 text-sm">
                  <span className="text-blue-400 mt-1">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Footer */}
        <div className="p-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            Close
          </button>
          <button
            onClick={() => alert('Download PDF functionality to be implemented')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Download size={16} />
            <span>Download PDF</span>
          </button>
        </div>
      </div>
    </div>
  );
};
