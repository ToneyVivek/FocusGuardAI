/**
 * Application Routes Configuration
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { PublicRoute } from './PublicRoute';
import { ProtectedLayout } from '../components/layout/ProtectedLayout';

// Pages
import { LoginPage } from '../pages/Login';
import { DashboardPage } from '../pages/Dashboard';
import { AnalyticsPage } from '../pages/Analytics';
import { OrganizationPage } from '../pages/Organization';
import { ProfilePage } from '../pages/Profile';
import { SettingsPage } from '../pages/Settings';
import { NotFoundPage } from '../pages/NotFound';

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
        element: <AnalyticsPage />,
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
