/**
 * EmptyState Component
 * Displays when no data is available
 */
import React from 'react';
import { Clock } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No activity yet',
  description = 'Browse normally today. We\'ll generate AI insights automatically.',
  icon,
}) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
      <div className="flex justify-center mb-4">
        {icon || <Clock size={48} className="text-gray-300" />}
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500">{description}</p>
    </div>
  );
};
