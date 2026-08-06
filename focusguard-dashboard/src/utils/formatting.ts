/**
 * Formatting Utilities
 * Shared formatting functions for AI components
 */
import { formatDateForDisplay } from './dateUtils';

/**
 * Format minutes to human-readable time
 */
export const formatMinutes = (minutes: number): string => {
  if (minutes === 0) return '0m';
  
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  
  if (hours > 0) {
    if (mins > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${hours}h`;
  }
  return `${mins}m`;
};

/**
 * Format date to readable string
 * Re-export from dateUtils for convenience
 */
export const formatDate = formatDateForDisplay;

/**
 * Get assessment color class
 */
export const getAssessmentColor = (
  assessment: string
): string => {
  switch (assessment) {
    case 'positive':
    case 'excellent':
      return 'text-green-600 bg-green-50 border-green-200';
    case 'neutral':
    case 'good':
      return 'text-blue-600 bg-blue-50 border-blue-200';
    case 'fair':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'needs_improvement':
      return 'text-red-600 bg-red-50 border-red-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

/**
 * Get impact color class
 */
export const getImpactColor = (impact: string): string => {
  switch (impact) {
    case 'high':
      return 'text-red-600 bg-red-50';
    case 'medium':
      return 'text-yellow-600 bg-yellow-50';
    case 'low':
      return 'text-green-600 bg-green-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
};

/**
 * Get focus score color
 */
export const getFocusScoreColor = (score: number): string => {
  if (score >= 80) return 'text-green-600';
  if (score >= 60) return 'text-blue-600';
  if (score >= 40) return 'text-yellow-600';
  return 'text-red-600';
};
