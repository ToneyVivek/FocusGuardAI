/**
 * Auth Guard Component for FocusGuard Extension
 * Prevents authenticated-only UI from rendering until authentication state is determined
 */

import { useAuth } from '../../contexts/AuthContext';

/**
 * Auth Guard Props
 */
interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * Auth Guard Component
 */
export function AuthGuard({ children, fallback }: AuthGuardProps) {
  const { loading } = useAuth();

  if (loading) {
    return fallback || <div className="auth-loading">Loading...</div>;
  }

  return <>{children}</>;
}
