/**
 * AnalyticsInsights Component
 * Displays computed insights from analytics data
 */
import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Lightbulb, TrendingUp, AlertTriangle, Clock, Target, Award } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';
import type { DateRange } from './DateRangeFilter';
import { getDateRangeParams } from './DateRangeFilter';
import { normalizeProductivity } from '../../utils/productivity';

interface AnalyticsInsightsProps {
  dateRange: DateRange;
  customStartDate?: string;
  customEndDate?: string;
}

interface Insight {
  icon: React.ReactNode;
  title: string;
  value: string;
  description: string;
  color: string;
}

export const AnalyticsInsights: React.FC<AnalyticsInsightsProps> = ({
  dateRange,
  customStartDate,
  customEndDate,
}) => {
  const { start_date, end_date } = getDateRangeParams(dateRange, customStartDate, customEndDate);

  const { data: summary } = useQuery({
    queryKey: ['analytics', 'summary', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserSummary(start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const { data: categories } = useQuery({
    queryKey: ['analytics', 'categories', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserCategories(start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const { data: domains } = useQuery({
    queryKey: ['analytics', 'domains', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserDomains(10, start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const { data: timeline } = useQuery({
    queryKey: ['analytics', 'timeline', dateRange, customStartDate, customEndDate],
    queryFn: () => dashboardService.getUserTimeline(500, start_date, end_date),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const insights: Insight[] = useMemo(() => {
    if (!summary || !categories || !domains || !timeline) return [];

    const focusScore = summary.focus_score;
    const items = timeline.items || [];

    const insightsList: Insight[] = [];

    // Most productive website
    if (domains.domains.length > 0) {
      const productiveDomains = domains.domains
        .filter(d => {
          const domainTimeline = items.filter(i => i.website_domain === d.domain);
          return domainTimeline.some(i => normalizeProductivity(i.productivity) === 'PRODUCTIVE');
        })
        .sort((a, b) => b.duration_seconds - a.duration_seconds);

      if (productiveDomains.length > 0) {
        insightsList.push({
          icon: <TrendingUp size={20} />,
          title: 'Most Productive Website',
          value: productiveDomains[0].domain,
          description: `${productiveDomains[0].session_count} sessions, ${Math.round(productiveDomains[0].duration_seconds / 60)} min`,
          color: 'text-green-600',
        });
      }
    }

    // Most distracting website
    if (domains.domains.length > 0) {
      const nonProductiveDomains = domains.domains
        .filter(d => {
          const domainTimeline = items.filter(i => i.website_domain === d.domain);
          return domainTimeline.some(i => normalizeProductivity(i.productivity) === 'NON_PRODUCTIVE');
        })
        .sort((a, b) => b.duration_seconds - a.duration_seconds);

      if (nonProductiveDomains.length > 0) {
        insightsList.push({
          icon: <AlertTriangle size={20} />,
          title: 'Most Distracting Website',
          value: nonProductiveDomains[0].domain,
          description: `${nonProductiveDomains[0].session_count} sessions, ${Math.round(nonProductiveDomains[0].duration_seconds / 60)} min`,
          color: 'text-red-600',
        });
      }
    }

    // Longest focus session
    if (items.length > 0) {
      const productiveSessions = items.filter(i => normalizeProductivity(i.productivity) === 'PRODUCTIVE');
      if (productiveSessions.length > 0) {
        const longest = productiveSessions.sort((a, b) => b.duration_seconds - a.duration_seconds)[0];
        const duration = Math.round(longest.duration_seconds / 60);
        insightsList.push({
          icon: <Clock size={20} />,
          title: 'Longest Focus Session',
          value: `${duration} min`,
          description: `on ${longest.website_domain || 'Unknown'}`,
          color: 'text-blue-600',
        });
      }
    }

    // Total coding time (DEVELOPMENT category)
    const devCategory = categories.categories.find(c => c.category === 'DEVELOPMENT');
    if (devCategory && devCategory.duration_seconds > 0) {
      const devMinutes = Math.round(devCategory.duration_seconds / 60);
      insightsList.push({
        icon: <Target size={20} />,
        title: 'Total Coding Time',
        value: `${devMinutes} min`,
        description: `${Math.round(devCategory.percentage)}% of total time`,
        color: 'text-purple-600',
      });
    }

    // Average daily productivity
    if (focusScore) {
      insightsList.push({
        icon: <Award size={20} />,
        title: 'Focus Score',
        value: `${Math.round(focusScore.score)}%`,
        description: 'Based on productive vs total active time',
        color: 'text-amber-600',
      });
    }

    // Most visited category
    if (categories.categories.length > 0) {
      const topCategory = categories.categories.sort((a, b) => b.duration_seconds - a.duration_seconds)[0];
      insightsList.push({
        icon: <Lightbulb size={20} />,
        title: 'Most Visited Category',
        value: topCategory.category,
        description: `${Math.round(topCategory.percentage)}% of time, ${topCategory.session_count} sessions`,
        color: 'text-cyan-600',
      });
    }

    return insightsList;
  }, [summary, categories, domains, timeline]);

  if (insights.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Insights</h2>
        <div className="text-center py-12">
          <Lightbulb size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Not enough data to generate insights</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Insights</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {insights.map((insight, index) => (
          <div
            key={index}
            className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className={`p-2 rounded-lg bg-white ${insight.color}`}>
              {insight.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-500 mb-1">{insight.title}</p>
              <p className="text-sm font-semibold text-gray-900 truncate">{insight.value}</p>
              <p className="text-xs text-gray-600 truncate">{insight.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
