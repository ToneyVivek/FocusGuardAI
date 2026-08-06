/**
 * WeeklySummaryCard Component
 * Displays weekly productivity summary from AI
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertCircle, Calendar } from 'lucide-react';
import { aiService } from '../../services/ai';
import { LoadingSkeleton } from './LoadingSkeleton';
import { EmptyState } from './EmptyState';
import { getAssessmentColor, getFocusScoreColor, formatDate } from '../../utils/formatting';

const parseMarkdownSections = (markdown: string) => {
  const sections: { [key: string]: string } = {};
  const lines = markdown.split('\n');
  let currentSection = '';
  let currentContent: string[] = [];

  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (currentSection) {
        sections[currentSection] = currentContent.join('\n').trim();
      }
      currentSection = line.replace('## ', '');
      currentContent = [];
    } else {
      currentContent.push(line);
    }
  }
  if (currentSection) {
    sections[currentSection] = currentContent.join('\n').trim();
  }
  return sections;
};

export const WeeklySummaryCard: React.FC<{
  startDate?: string;
  endDate?: string;
}> = ({ startDate, endDate }) => {
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['ai', 'weekly-summary', startDate, endDate],
    queryFn: () => aiService.getWeeklySummary(startDate, endDate),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Week Overview</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load weekly summary</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Week Overview</h2>
        <EmptyState />
      </div>
    );
  }

  const sections = parseMarkdownSections(summary.summary);

  // Debug: log the raw summary and parsed sections
  console.log('Raw weekly summary:', summary.summary);
  console.log('Parsed weekly sections:', sections);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Week Overview</h2>
        <div className="flex items-center gap-2">
          <span className={`text-2xl font-bold ${getFocusScoreColor(summary.focus_score)}`}>
            {Math.round(summary.focus_score)}%
          </span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getAssessmentColor(summary.assessment)}`}>
            {summary.assessment === 'excellent' ? '🟢 Excellent' : summary.assessment === 'good' ? '🟢 Good' : summary.assessment === 'fair' ? '🟡 Fair' : '🔴 Needs Work'}
          </span>
        </div>
      </div>

      {/* Date Range */}
      {summary.start_date && summary.end_date && (
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
          <Calendar size={16} />
          <span>
            {formatDate(summary.start_date)} - {formatDate(summary.end_date)}
          </span>
        </div>
      )}

      <div className="border-t border-gray-200 my-4" />

      {/* Fallback: Show raw summary if parsing fails */}
      {Object.keys(sections).length === 0 ? (
        <div className="text-sm text-gray-600 whitespace-pre-line leading-relaxed">
          {summary.summary}
        </div>
      ) : (
        /* Parsed Markdown Sections */
        Object.entries(sections).map(([section, content]) => (
          <div key={section} className="mb-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">{section}</h3>
            <div className="text-sm text-gray-600 whitespace-pre-line leading-relaxed">
              {content}
            </div>
          </div>
        ))
      )}

      <div className="border-t border-gray-200 my-4" />

      <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
        View Detailed Report →
      </button>
    </div>
  );
};
