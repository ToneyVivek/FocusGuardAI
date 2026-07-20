/**
 * Authenticated View Component for FocusGuard Extension
 * Displays user information when logged in
 */

import { useAuth } from '../../contexts/AuthContext';

/**
 * Authenticated View Component
 */
export function AuthenticatedView() {
  const { user, logout, loading } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className="authenticated-view">
      <div className="user-info">
        <h2 className="user-name">{user.full_name || user.username}</h2>
        <p className="user-email">{user.email}</p>
        <div className="user-organization">
          <span className="organization-label">Organization:</span>
          <span className="organization-name">{user.organization.name}</span>
        </div>
        <div className="user-role">
          <span className="role-label">Role:</span>
          <span className="role-name">{user.role}</span>
        </div>
      </div>

      <div className="auth-status">
        <span className="status-indicator authenticated"></span>
        <span className="status-text">Authenticated</span>
      </div>

      <button
        onClick={handleLogout}
        disabled={loading}
        className="logout-button"
      >
        {loading ? 'Logging out...' : 'Logout'}
      </button>
    </div>
  );
}
