/**
 * Navbar Component
 * Top navigation bar with application title, profile menu, and placeholders
 */
import React from 'react';
import { Bell, Sun } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

export const Navbar: React.FC = () => {
  const { user } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Application Title */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900">FocusGuard Dashboard</h2>
          <p className="text-sm text-gray-500">Welcome back, {user?.full_name || 'User'}</p>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center gap-4">
          {/* Theme Toggle Placeholder */}
          <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors" title="Toggle Theme">
            <Sun size={20} />
          </button>

          {/* Notifications Placeholder */}
          <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors" title="Notifications">
            <Bell size={20} />
          </button>

          {/* Profile Menu Placeholder */}
          <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium">
              {user?.full_name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="hidden md:block">
              <p className="text-sm font-medium text-gray-900">{user?.full_name || 'User'}</p>
              <p className="text-xs text-gray-500">{user?.role || 'EMPLOYEE'}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
