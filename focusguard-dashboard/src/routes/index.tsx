/**
 * Application Routes Configuration
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { PublicRoute } from './PublicRoute';
import { ProtectedLayout } from '../components/layout/ProtectedLayout';
import { lazy, Suspense } from 'react';

// Pages
import { LoginPage } from '../pages/Login';
import { DashboardPage } from '../pages/Dashboard';
import { OrganizationPage } from '../pages/Organization';
import { ProfilePage } from '../pages/Profile';
import { SettingsPage } from '../pages/Settings';
import { NotFoundPage } from '../pages/NotFound';

// Lazy load Analytics and Reports pages to reduce bundle size
const AnalyticsPage = lazy(() => import('../pages/Analytics').then(m => ({ default: m.AnalyticsPage })));
const ReportsPage = lazy(() => import('../pages/Reports').then(m => ({ default: m.ReportsPage })));

const AnalyticsPageWrapper = () => (
  <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Analytics...</div>}>
    <AnalyticsPage />
  </Suspense>
);

const ReportsPageWrapper = () => (
  <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Reports...</div>}>
    <ReportsPage />
  </Suspense>
);

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/login',
    element: (
      <PublicRoute>
        <LoginPage />
      </PublicRoute>
    ),
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <ProtectedLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'analytics',
        element: <AnalyticsPageWrapper />,
      },
      {
        path: 'reports',
        element: <ReportsPageWrapper />,
      },
      {
        path: 'organization',
        element: (
          <ProtectedRoute requiereRoles={['ADMIN']}>
            <OrganizationPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
