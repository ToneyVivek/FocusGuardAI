/**
 * Popup component for FocusGuard Extension
 * Displays authentication UI or user information
 */

import { useAuth } from '../contexts/AuthContext';
import { LoginForm } from './auth/LoginForm';
import { AuthenticatedView } from './auth/AuthenticatedView';
import { AuthGuard } from './auth/AuthGuard';

export function Popup() {
  const { isAuthenticated } = useAuth();

  return (
    <AuthGuard>
      {isAuthenticated ? <AuthenticatedView /> : <LoginForm />}
    </AuthGuard>
  );
}
