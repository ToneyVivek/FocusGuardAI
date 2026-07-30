/**
 * Dashboard Page
 * Main dashboard with statistics, recent activity, top websites, and productivity summary
 */
import React from 'react';
import { DashboardHeader } from '../../components/dashboard/DashboardHeader';
import { DashboardStats } from '../../components/dashboard/DashboardStats';
import { RecentActivity } from '../../components/dashboard/RecentActivity';
import { TopWebsites } from '../../components/dashboard/TopWebsites';
import { ProductivitySummary } from '../../components/dashboard/ProductivitySummary';

export const DashboardPage: React.FC = () => {
  return (
    <div className="min-h-0">
      <DashboardHeader />
      <DashboardStats />
      
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
        <RecentActivity />
        <TopWebsites />
      </div>
      
      <ProductivitySummary />
    </div>
  );
};
