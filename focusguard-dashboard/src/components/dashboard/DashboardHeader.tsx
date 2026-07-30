/**
 * DashboardHeader Component
 * Displays welcome message, organization name, and current date
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const DashboardHeader: React.FC = () => {
  const { user } = useAuth();
  
  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <div className="mb-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Welcome back, {user?.full_name || 'User'}
      </h1>
      <div className="flex items-center justify-between">
        <span className="text-gray-600">{currentDate}</span>
      </div>
    </div>
  );
};
