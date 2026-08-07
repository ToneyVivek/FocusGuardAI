/**
 * Organization Dashboard Page
 * Admin-only dashboard showing organization-wide metrics and activity
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { organizationService } from '../../services/organization';
import axios from '../../api/axios';
import type {
  OrganizationSummaryResponse,
  EmployeeRankings,
  TimelineItem,
  InvitationListResponse,
  EmployeeListResponse
} from '../../types';
import {
  Users,
  Target,
  TrendingUp,
  Activity,
  RefreshCw,
  Plus,
  Settings,
  FileText,
  UserCheck,
  Clock,
  Mail
} from 'lucide-react';

export const OrganizationDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<OrganizationSummaryResponse | null>(null);
  const [employeeRankings, setEmployeeRankings] = useState<EmployeeRankings | null>(null);
  const [recentActivity, setRecentActivity] = useState<TimelineItem[]>([]);
  const [employees, setEmployees] = useState<EmployeeListResponse | null>(null);
  const [invitations, setInvitations] = useState<InvitationListResponse | null>(null);

  const fetchOrganizationSummary = useCallback(async () => {
    try {
      const response = await axios.get<OrganizationSummaryResponse>('/analytics/org/v2/summary');
      setSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch organization summary:', error);
    }
  }, []);

  const fetchEmployeeRankings = useCallback(async () => {
    try {
      const response = await axios.get<EmployeeRankings>('/analytics/org/v2/employees?limit=5');
      setEmployeeRankings(response.data);
    } catch (error) {
      console.error('Failed to fetch employee rankings:', error);
    }
  }, []);

  const fetchRecentActivity = useCallback(async () => {
    try {
      const response = await axios.get<TimelineItem[]>('/analytics/activity/organization?limit=10');
      setRecentActivity(response.data);
    } catch (error) {
      console.error('Failed to fetch recent activity:', error);
    }
  }, []);

  const fetchEmployeesAndInvitations = useCallback(async () => {
    try {
      const [employeesRes, invitationsRes] = await Promise.all([
        organizationService.getEmployees({ limit: 100 }),
        organizationService.getInvitations({ limit: 100 })
      ]);
      setEmployees(employeesRes);
      setInvitations(invitationsRes);
    } catch (error) {
      console.error('Failed to fetch employees and invitations:', error);
    }
  }, []);

  useEffect(() => {
    const loadAllData = async () => {
      setLoading(true);
      await Promise.all([
        fetchOrganizationSummary(),
        fetchEmployeeRankings(),
        fetchRecentActivity(),
        fetchEmployeesAndInvitations()
      ]);
      setLoading(false);
    };
    loadAllData();
  }, [fetchOrganizationSummary, fetchEmployeeRankings, fetchRecentActivity, fetchEmployeesAndInvitations]);

  // Only admins can access this page
  if (user?.role !== 'ADMIN') {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-600">Access denied. Admin only.</p>
      </div>
    );
  }

  const totalEmployees = employees?.total || 0;
  const activeEmployees = employees?.employees.filter(e => e.is_active).length || 0;
  const pendingInvitations = invitations?.total || 0;
  const orgFocusScore = summary ? 
    (summary.metrics.productive_time / (summary.metrics.productive_time + summary.metrics.neutral_time + summary.metrics.non_productive_time || 1)) * 100 : 0;
  const totalProductiveTime = summary?.metrics.productive_time || 0;
  const totalIdleTime = summary?.metrics.idle_time || 0;

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatScore = (score: number): string => {
    return score.toFixed(1);
  };

  const quickActions = [
    { icon: Plus, label: 'Invite Employee', path: '/organization' },
    { icon: Settings, label: 'Manage Organization', path: '/organization' },
    { icon: FileText, label: 'View Reports', path: '/organization-reports' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-gray-400" size={32} />
      </div>
    );
  }

  return (
    <div className="min-h-0">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Organization Dashboard</h1>
        <p className="text-gray-400">Overview of your team's productivity and activity</p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-24 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <Users className="text-blue-400" size={20} />
            <span className="text-2xl font-bold text-white">{totalEmployees}</span>
          </div>
          <p className="text-sm text-gray-400">Total Employees</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-24 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <UserCheck className="text-green-400" size={20} />
            <span className="text-2xl font-bold text-white">{activeEmployees}</span>
          </div>
          <p className="text-sm text-gray-400">Active Today</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-24 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <Target className="text-purple-400" size={20} />
            <span className="text-2xl font-bold text-white">{formatScore(orgFocusScore)}</span>
          </div>
          <p className="text-sm text-gray-400">Focus Score</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-24 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <TrendingUp className="text-emerald-400" size={20} />
            <span className="text-2xl font-bold text-white">{formatTime(totalProductiveTime)}</span>
          </div>
          <p className="text-sm text-gray-400">Productive Time</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-24 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <Clock className="text-orange-400" size={20} />
            <span className="text-2xl font-bold text-white">{formatTime(totalIdleTime)}</span>
          </div>
          <p className="text-sm text-gray-400">Idle Time</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-24 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <Mail className="text-cyan-400" size={20} />
            <span className="text-2xl font-bold text-white">{pendingInvitations}</span>
          </div>
          <p className="text-sm text-gray-400">Pending Invitations</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        {/* Top Employees */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Top Employees</h2>
            <TrendingUp className="text-gray-400" size={20} />
          </div>
          {employeeRankings && employeeRankings.rankings.length > 0 ? (
            <div className="space-y-3">
              {employeeRankings.rankings.map((employee, index) => (
                <div key={employee.user_id} className="flex items-center justify-between p-3 bg-gray-750 rounded-lg hover:bg-gray-700 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-900 rounded-full flex items-center justify-center text-blue-300 font-bold text-sm flex-shrink-0">
                      {index + 1}
                    </div>
                    <div className="min-w-0">
                      <p className="text-white font-medium truncate">{employee.username}</p>
                      <p className="text-sm text-gray-400">{formatTime(employee.productive_time)} productive</p>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-lg font-bold text-emerald-400">{formatScore(employee.focus_score)}</p>
                    <p className="text-xs text-gray-400">Focus Score</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              <Users size={48} className="mx-auto mb-4 opacity-50" />
              <p>No employee data available</p>
            </div>
          )}
        </div>

        {/* Recent Organization Activity */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Recent Activity</h2>
            <Activity className="text-gray-400" size={20} />
          </div>
          {recentActivity.length > 0 ? (
            <div className="space-y-2 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
              {recentActivity.slice(0, 10).map((activity) => (
                <div key={activity.session_id} className="flex items-center gap-3 p-3 bg-gray-750 rounded-lg hover:bg-gray-700 transition-colors">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    activity.type === 'activity' ? 'bg-blue-400' : 'bg-orange-400'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm truncate">
                      {activity.website_domain || 'Idle Session'}
                    </p>
                    <p className="text-xs text-gray-400">
                      {activity.employee_name || activity.user_name || 'Unknown'} • {activity.website_domain || ''} • {activity.category || ''} • {new Date(activity.start_time).toLocaleString()}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400 whitespace-nowrap flex-shrink-0">
                    {formatTime(activity.duration_seconds)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              <Activity size={48} className="mx-auto mb-4 opacity-50" />
              <p>No recent activity</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <button
              key={action.label}
              onClick={() => window.location.href = action.path}
              className="flex items-center gap-3 p-4 bg-gray-750 hover:bg-gray-700 rounded-lg transition-colors border border-gray-700 hover:border-gray-600"
            >
              <action.icon className="text-blue-400" size={24} />
              <span className="text-white font-medium">{action.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
