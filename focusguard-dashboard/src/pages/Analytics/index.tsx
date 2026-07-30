/**
 * Analytics Page
 * Comprehensive analytics dashboard with charts, filters, and insights
 */
import React, { useState } from 'react';
import { DateRangeFilter } from '../../components/analytics/DateRangeFilter';
import type { DateRange } from '../../components/analytics/DateRangeFilter';
import { AnalyticsKPICards } from '../../components/analytics/AnalyticsKPICards';
import { ProductivityPieChart } from '../../components/analytics/ProductivityPieChart';
import { DailyTrendChart } from '../../components/analytics/DailyTrendChart';
import { BrowsingSessionsChart } from '../../components/analytics/BrowsingSessionsChart';
import { CategoryBreakdownChart } from '../../components/analytics/CategoryBreakdownChart';
import { TopDomainsChart } from '../../components/analytics/TopDomainsChart';
import { AnalyticsTimeline } from '../../components/analytics/AnalyticsTimeline';
import { AnalyticsInsights } from '../../components/analytics/AnalyticsInsights';
import { OrganizationComparison } from '../../components/analytics/OrganizationComparison';

export const AnalyticsPage: React.FC = () => {
  const [dateRange, setDateRange] = useState<DateRange>('last7days');
  const [customStartDate, setCustomStartDate] = useState<string>('');
  const [customEndDate, setCustomEndDate] = useState<string>('');

  return (
    <div className="min-h-0">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics</h1>
        <p className="text-gray-600">Analyze your browsing behavior and productivity over time</p>
      </div>

      {/* Date Range Filter */}
      <div className="mb-6">
        <DateRangeFilter
          value={dateRange}
          onChange={setDateRange}
          customStartDate={customStartDate}
          customEndDate={customEndDate}
          onCustomStartChange={setCustomStartDate}
          onCustomEndChange={setCustomEndDate}
        />
      </div>

      {/* KPI Cards */}
      <AnalyticsKPICards
        dateRange={dateRange}
        customStartDate={customStartDate}
        customEndDate={customEndDate}
      />

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <ProductivityPieChart
          dateRange={dateRange}
          customStartDate={customStartDate}
          customEndDate={customEndDate}
        />
        <CategoryBreakdownChart
          dateRange={dateRange}
          customStartDate={customStartDate}
          customEndDate={customEndDate}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <DailyTrendChart
          dateRange={dateRange}
          customStartDate={customStartDate}
          customEndDate={customEndDate}
        />
        <BrowsingSessionsChart
          dateRange={dateRange}
          customStartDate={customStartDate}
          customEndDate={customEndDate}
        />
      </div>

      {/* Top Domains */}
      <div className="mb-6">
        <TopDomainsChart
          dateRange={dateRange}
          customStartDate={customStartDate}
          customEndDate={customEndDate}
        />
      </div>

      {/* Organization Comparison (ADMIN only) */}
      <div className="mb-6">
        <OrganizationComparison
          dateRange={dateRange}
          customStartDate={customStartDate}
          customEndDate={customEndDate}
        />
      </div>

      {/* Insights */}
      <div className="mb-6">
        <AnalyticsInsights
          dateRange={dateRange}
          customStartDate={customStartDate}
          customEndDate={customEndDate}
        />
      </div>

      {/* Timeline */}
      <div>
        <AnalyticsTimeline
          dateRange={dateRange}
          customStartDate={customStartDate}
          customEndDate={customEndDate}
        />
      </div>
    </div>
  );
};
