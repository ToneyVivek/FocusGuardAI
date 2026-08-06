/**
 * Reports Page
 * Full reporting system with export, comparison, and history
 */
import React, { useState } from 'react';
import { Download, TrendingUp, History, Building } from 'lucide-react';
import { ReportTypeSelector, getReportDateRange } from '../../components/reports/ReportTypeSelector';
import type { ReportType } from '../../components/reports/ReportTypeSelector';
import { ReportSummary } from '../../components/reports/ReportSummary';
import { PeriodComparison } from '../../components/reports/PeriodComparison';
import { OrganizationReports } from '../../components/reports/OrganizationReports';
import { ReportHistory, saveReportToHistory } from '../../components/reports/ReportHistory';
import { ProductivityPieChart } from '../../components/analytics/ProductivityPieChart';
import { CategoryBreakdownChart } from '../../components/analytics/CategoryBreakdownChart';
import { TopDomainsChart } from '../../components/analytics/TopDomainsChart';
import { DailyTrendChart } from '../../components/analytics/DailyTrendChart';
import { BrowsingSessionsChart } from '../../components/analytics/BrowsingSessionsChart';
import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../../services/dashboard';
import { exportTimelineToCSV, exportCategoriesToCSV, exportDomainsToCSV, exportSummaryToCSV } from '../../utils/export';
import { useAuth } from '../../contexts/AuthContext';
import { DEFAULT_TIMELINE_LIMIT, DEFAULT_DOMAINS_LIMIT } from '../../constants/api';

export const ReportsPage: React.FC = () => {
  const [reportType, setReportType] = useState<ReportType>('weekly');
  const [showComparison, setShowComparison] = useState(false);
  const [showOrgReport, setShowOrgReport] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');

  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  const { start_date, end_date } = getReportDateRange(reportType);

  // Fetch data for export
  const { data: summary } = useQuery({
    queryKey: ['report', 'summary', start_date, end_date],
    queryFn: () => dashboardService.getUserSummary(start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const { data: categories } = useQuery({
    queryKey: ['report', 'categories', start_date, end_date],
    queryFn: () => dashboardService.getUserCategories(start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const { data: domains } = useQuery({
    queryKey: ['report', 'domains', start_date, end_date],
    queryFn: () => dashboardService.getUserDomains(DEFAULT_DOMAINS_LIMIT, start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const { data: timeline } = useQuery({
    queryKey: ['report', 'timeline', start_date, end_date],
    queryFn: () => dashboardService.getUserTimeline(DEFAULT_TIMELINE_LIMIT, start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const handleExportCSV = () => {
    const filename = `focusguard-report-${reportType}-${start_date}-to-${end_date}`;
    
    // Export summary
    if (summary) {
      exportSummaryToCSV(summary, `${filename}-summary`);
    }
    
    // Export categories
    if (categories?.categories) {
      exportCategoriesToCSV(categories.categories, `${filename}-categories`);
    }
    
    // Export domains
    if (domains?.domains) {
      exportDomainsToCSV(domains.domains, `${filename}-domains`);
    }
    
    // Export timeline
    if (timeline?.items) {
      exportTimelineToCSV(timeline.items, `${filename}-timeline`);
    }
  };

  const handleExportPDF = () => {
    // PDF export will be implemented separately
    alert('PDF export will be implemented with a library like jsPDF or html2pdf');
  };

  return (
    <div className="min-h-0">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Reports</h1>
        <p className="text-gray-600">Generate, export, and compare productivity reports</p>
      </div>

      {/* Report Type Selector */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Report Type</h2>
        <ReportTypeSelector value={reportType} onChange={setReportType} />
        
        {reportType === 'custom' && (
          <div className="flex items-center gap-2 mt-4">
            <div className="relative">
              <label htmlFor="report-start-date" className="sr-only">Start date</label>
              <input
                id="report-start-date"
                type="date"
                value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)}
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-10 text-sm text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                aria-label="Start date"
              />
            </div>
            <span className="text-gray-500">to</span>
            <div className="relative">
              <label htmlFor="report-end-date" className="sr-only">End date</label>
              <input
                id="report-end-date"
                type="date"
                value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)}
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-10 text-sm text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                aria-label="End date"
              />
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-4 mb-6">
        <button 
          onClick={handleExportPDF}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Download size={18} />
          Export PDF
        </button>
        <button 
          onClick={handleExportCSV}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <Download size={18} />
          Export CSV
        </button>
        <button
          onClick={() => setShowComparison(!showComparison)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            showComparison
              ? 'bg-purple-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <TrendingUp size={18} />
          Compare Periods
        </button>
        {isAdmin && (
          <button
            onClick={() => setShowOrgReport(!showOrgReport)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              showOrgReport
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <Building size={18} />
            Organization Report
          </button>
        )}
        <button 
          onClick={() => {
            setShowHistory(!showHistory);
            if (summary && !showHistory) {
              saveReportToHistory(reportType, start_date, end_date, summary);
            }
          }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            showHistory
              ? 'bg-gray-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <History size={18} />
          Report History
        </button>
      </div>

      {/* Report Summary */}
      <ReportSummary startDate={start_date} endDate={end_date} />

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <ProductivityPieChart
          dateRange="custom"
          customStartDate={start_date}
          customEndDate={end_date}
        />
        <CategoryBreakdownChart
          dateRange="custom"
          customStartDate={start_date}
          customEndDate={end_date}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <DailyTrendChart
          dateRange="custom"
          customStartDate={start_date}
          customEndDate={end_date}
        />
        <BrowsingSessionsChart
          dateRange="custom"
          customStartDate={start_date}
          customEndDate={end_date}
        />
      </div>

      {/* Top Domains */}
      <div className="mb-6">
        <TopDomainsChart
          dateRange="custom"
          customStartDate={start_date}
          customEndDate={end_date}
        />
      </div>

      {/* Placeholder for comparison and history */}
      {showComparison && (
        <PeriodComparison startDate={start_date} endDate={end_date} />
      )}

      {/* Organization Report (ADMIN only) */}
      {showOrgReport && (
        <OrganizationReports startDate={start_date} endDate={end_date} />
      )}

      {/* Report History */}
      {showHistory && (
        <ReportHistory />
      )}
    </div>
  );
};
