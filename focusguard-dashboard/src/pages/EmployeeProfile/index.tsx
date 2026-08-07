/**
 * Employee Profile Page
 * 360° view of an employee for admins
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import axios from '../../api/axios';
import type { User } from '../../types';
import {
  User as UserIcon,
  Mail,
  Building,
  Calendar,
  Clock,
  Target,
  TrendingUp,
  RefreshCw,
  ArrowLeft,
  Activity,
  Globe,
  BarChart3
} from 'lucide-react';

interface EmployeeProfileData extends User {
  organization?: {
    id: number;
    name: string;
  };
  last_activity?: string | null;
}

export const EmployeeProfilePage: React.FC = () => {
  const { employeeId } = useParams<{ employeeId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [employee, setEmployee] = useState<EmployeeProfileData | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [categories, setCategories] = useState<any>(null);
  const [domains, setDomains] = useState<any>(null);
  const [timeline, setTimeline] = useState<any>(null);
  
  // Date range state
  const [datePreset, setDatePreset] = useState<'today' | 'yesterday' | 'last7days' | 'last30days' | 'custom'>('today');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Helper to format date as YYYY-MM-DD in local timezone
  const formatDateLocal = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Helper to get date range based on preset
  const getDateRange = () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    switch (datePreset) {
      case 'today':
        return {
          start: formatDateLocal(today),
          end: formatDateLocal(today)
        };
      case 'yesterday':
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        return {
          start: formatDateLocal(yesterday),
          end: formatDateLocal(yesterday)
        };
      case 'last7days':
        const weekAgo = new Date(today);
        weekAgo.setDate(weekAgo.getDate() - 6);
        return {
          start: formatDateLocal(weekAgo),
          end: formatDateLocal(today)
        };
      case 'last30days':
        const monthAgo = new Date(today);
        monthAgo.setDate(monthAgo.getDate() - 29);
        return {
          start: formatDateLocal(monthAgo),
          end: formatDateLocal(today)
        };
      case 'custom':
        return {
          start: startDate,
          end: endDate
        };
      default:
        return { start: '', end: '' };
    }
  };


  const fetchEmployeeData = useCallback(async () => {
    if (!employeeId) return;

    try {
      setLoading(true);
      
      // Fetch employee profile
      const employeeResponse = await axios.get(`/admin/employee/${employeeId}`);
      setEmployee(employeeResponse.data);

      // Get date range
      const { start, end } = getDateRange();

      // Fetch analytics data with date range
      const [summaryRes, categoriesRes, domainsRes, timelineRes] = await Promise.all([
        axios.get(`/analytics/user/${employeeId}/summary?start_date=${start}&end_date=${end}`),
        axios.get(`/analytics/user/${employeeId}/categories?start_date=${start}&end_date=${end}`),
        axios.get(`/analytics/user/${employeeId}/domains?limit=10&start_date=${start}&end_date=${end}`),
        axios.get(`/analytics/user/${employeeId}/timeline?limit=20&start_date=${start}&end_date=${end}`),
      ]);

      setSummary(summaryRes.data);
      setCategories(categoriesRes.data);
      setDomains(domainsRes.data);
      setTimeline(timelineRes.data);
    } catch (error) {
      console.error('Failed to fetch employee data:', error);
    } finally {
      setLoading(false);
    }
  }, [employeeId, datePreset, startDate, endDate]);

  useEffect(() => {
    fetchEmployeeData();
  }, [fetchEmployeeData]);

  // Only admins can access this page
  if (user?.role !== 'ADMIN') {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-600">Access denied. Admin only.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-gray-400" size={32} />
      </div>
    );
  }

  if (!employee) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-600">Employee not found.</p>
      </div>
    );
  }

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const formatDateTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  };

  const focusScore = summary?.focus_score?.score || 0;
  const productiveTime = summary?.metrics?.productive_time || 0;
  const idleTime = summary?.metrics?.idle_time || 0;
  const activeTime = summary?.focus_score?.total_active_time || 0;
  const sessions = summary?.metrics?.completed_sessions || 0;
  const tabSwitches = summary?.metrics?.activity_events || 0;

  const topCategory = categories?.categories?.[0]?.category || null;
  const topDomain = domains?.domains?.[0]?.domain || null;
  
  // Calculate productivity percentage
  const totalTime = productiveTime + idleTime;
  const productivityPercent = totalTime > 0 ? (productiveTime / totalTime) * 100 : 0;

  // Check if there's any data
  const hasNoData = focusScore === 0 && productiveTime === 0 && idleTime === 0 && sessions === 0;

  // Helper to check if selected date range is Today
  const isTodaySelected = () => {
    const { start, end } = getDateRange();
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayStr = formatDateLocal(today);
    return start === todayStr && end === todayStr;
  };

  // Determine report type based on date range
  const determineReportType = (): 'daily' | 'weekly' | 'monthly' => {
    const { start, end } = getDateRange();
    const startDate = new Date(start);
    const endDate = new Date(end);
    const diffDays = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 1) return 'daily';
    if (diffDays <= 7) return 'weekly';
    return 'monthly';
  };

  const handleDownloadPDF = async () => {
    // Prevent PDF download for Today (incomplete day)
    const { start, end } = getDateRange();
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayStr = formatDateLocal(today);
    
    if (start === todayStr && end === todayStr) {
      return; // Do not make API request for Today
    }
    
    try {
      const response = await axios.get(
        `/admin/employee/${employeeId}/report/pdf?start_date=${start}&end_date=${end}`,
        { responseType: 'blob' }
      );
      
      // Check if response is an error
      if (response.data.type === 'application/json') {
        const errorText = await response.data.text();
        const errorData = JSON.parse(errorText);
        alert(errorData.error || 'Failed to download PDF report');
        return;
      }
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `productivity_report_${employee?.full_name?.replace(' ', '_')}_${start}_to_${end}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Failed to download PDF:', error);
      alert('Failed to download PDF report');
    }
  };

  return (
    <div className="min-h-0">
      {/* Header */}
      <div className="mb-6 flex items-center gap-4">
        <button
          onClick={() => navigate('/organization-reports')}
          className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          <ArrowLeft size={20} className="text-white" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-white">Employee Profile</h1>
          <p className="text-gray-400">360° view of {employee.full_name}</p>
        </div>
        <button
          onClick={fetchEmployeeData}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          <RefreshCw size={16} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Section 1: Profile */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
        <div className="flex items-start gap-6">
          <div className="w-20 h-20 bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0">
            <UserIcon size={40} className="text-gray-400" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-white mb-2">{employee.full_name}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                <Mail size={16} className="text-gray-400" />
                <span className="text-gray-300">{employee.email}</span>
              </div>
              <div className="flex items-center gap-2">
                <Building size={16} className="text-gray-400" />
                <span className="text-gray-300">{employee.organization?.name || 'N/A'}</span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar size={16} className="text-gray-400" />
                <span className="text-gray-300">Joined {formatDate(employee.created_at)}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  employee.is_active
                    ? 'bg-green-900 text-green-300'
                    : 'bg-gray-700 text-gray-400'
                }`}>
                  {employee.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Date Range Toolbar */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Date Range Presets */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Date Range</label>
            <select
              value={datePreset}
              onChange={(e) => setDatePreset(e.target.value as any)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="last7days">Last 7 Days</option>
              <option value="last30days">Last 30 Days</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>

          {/* Custom Date Range */}
          {datePreset === 'custom' && (
            <>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Section 2: Productivity Overview */}
      {hasNoData ? (
        <div className="bg-gray-800 rounded-lg p-12 border border-gray-700 mb-6 text-center">
          <Activity size={48} className="mx-auto mb-4 text-gray-400" />
          <p className="text-gray-400 text-lg">No activity found for the selected period.</p>
          <p className="text-sm text-gray-500 mt-2">Try selecting a different date range.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <Target className="text-purple-400" size={20} />
                <span className="text-sm text-gray-400">Focus Score</span>
              </div>
              <p className="text-3xl font-bold text-white">{focusScore.toFixed(1)}</p>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="text-emerald-400" size={20} />
                <span className="text-sm text-gray-400">Productive Time</span>
              </div>
              <p className="text-3xl font-bold text-white">{formatTime(productiveTime)}</p>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="text-orange-400" size={20} />
                <span className="text-sm text-gray-400">Idle Time</span>
              </div>
              <p className="text-3xl font-bold text-white">{formatTime(idleTime)}</p>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="text-blue-400" size={20} />
                <span className="text-sm text-gray-400">Sessions</span>
              </div>
              <p className="text-3xl font-bold text-white">{sessions}</p>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="text-purple-400" size={20} />
                <span className="text-sm text-gray-400">Top Category</span>
              </div>
              <p className="text-lg font-bold text-white truncate">{topCategory || 'N/A'}</p>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <Globe className="text-blue-400" size={20} />
                <span className="text-sm text-gray-400">Top Website</span>
              </div>
              <p className="text-lg font-bold text-white truncate">{topDomain || 'N/A'}</p>
            </div>
          </div>

          {/* Section 3: Analytics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Category Breakdown</h3>
              {categories?.categories?.length > 0 ? (
                <div className="space-y-3">
                  {categories.categories.slice(0, 5).map((cat: any, index: number) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-white text-sm">{cat.category}</span>
                          <span className="text-gray-400 text-sm">{cat.percentage.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${cat.percentage}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-4">No category data available</p>
              )}
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Top Websites</h3>
              {domains?.domains?.length > 0 ? (
                <div className="space-y-2">
                  {domains.domains.slice(0, 5).map((domain: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-750 rounded">
                      <span className="text-white text-sm truncate">{domain.domain}</span>
                      <span className="text-gray-400 text-sm">{formatTime(domain.duration_seconds)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-4">No website data available</p>
              )}
            </div>
          </div>
        </>
      )}

      {/* Section 4: Productivity Report */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Productivity Report</h3>
          <div className="flex items-center gap-3">
            {isTodaySelected() && (
              <p className="text-gray-400 text-sm">
                Today's report is still being generated. Download will be available after the day ends.
              </p>
            )}
            <button
              onClick={handleDownloadPDF}
              disabled={isTodaySelected()}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                isTodaySelected()
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-700 hover:bg-gray-600 text-white'
              }`}
            >
              <Activity size={16} />
              <span>Download PDF</span>
            </button>
          </div>
        </div>

        {/* Report Header */}
        <div className="bg-gray-750 rounded-lg p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-400 mb-1">Employee</p>
              <p className="text-white font-medium">{employee.full_name}</p>
              <p className="text-sm text-gray-400">{employee.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Report Type</p>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                determineReportType() === 'daily'
                  ? 'bg-blue-900 text-blue-300'
                  : determineReportType() === 'weekly'
                  ? 'bg-purple-900 text-purple-300'
                  : 'bg-green-900 text-green-300'
              }`}>
                {determineReportType().charAt(0).toUpperCase() + determineReportType().slice(1)} Report
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Date Range</p>
              <p className="text-white font-medium">{formatDate(getDateRange().start)} - {formatDate(getDateRange().end)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Generated</p>
              <p className="text-white font-medium">{formatDateTime(new Date().toISOString())}</p>
            </div>
          </div>
        </div>

        {/* Summary Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-750 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target className="text-purple-400" size={16} />
              <span className="text-sm text-gray-400">Focus Score</span>
            </div>
            <p className="text-2xl font-bold text-white">{focusScore.toFixed(1)}</p>
          </div>
          <div className="bg-gray-750 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="text-emerald-400" size={16} />
              <span className="text-sm text-gray-400">Productive Time</span>
            </div>
            <p className="text-2xl font-bold text-white">{formatTime(productiveTime)}</p>
          </div>
          <div className="bg-gray-750 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="text-orange-400" size={16} />
              <span className="text-sm text-gray-400">Idle Time</span>
            </div>
            <p className="text-2xl font-bold text-white">{formatTime(idleTime)}</p>
          </div>
          <div className="bg-gray-750 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="text-blue-400" size={16} />
              <span className="text-sm text-gray-400">Active Time</span>
            </div>
            <p className="text-2xl font-bold text-white">{formatTime(activeTime)}</p>
          </div>
          <div className="bg-gray-750 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="text-purple-400" size={16} />
              <span className="text-sm text-gray-400">Sessions</span>
            </div>
            <p className="text-2xl font-bold text-white">{sessions}</p>
          </div>
          <div className="bg-gray-750 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="text-green-400" size={16} />
              <span className="text-sm text-gray-400">Productivity %</span>
            </div>
            <p className="text-2xl font-bold text-white">{productivityPercent.toFixed(1)}%</p>
          </div>
          <div className="bg-gray-750 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <RefreshCw className="text-yellow-400" size={16} />
              <span className="text-sm text-gray-400">Tab Switches</span>
            </div>
            <p className="text-2xl font-bold text-white">{tabSwitches}</p>
          </div>
          <div className="bg-gray-750 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="text-blue-400" size={16} />
              <span className="text-sm text-gray-400">Top Category</span>
            </div>
            <p className="text-lg font-bold text-white truncate">{topCategory || 'N/A'}</p>
          </div>
        </div>

        {/* Analytics Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-gray-750 rounded-lg p-6">
            <h4 className="text-md font-semibold text-white mb-4">Category Breakdown</h4>
            {categories?.categories?.length > 0 ? (
              <div className="space-y-3">
                {categories.categories.slice(0, 5).map((cat: any, index: number) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-white text-sm">{cat.category}</span>
                        <span className="text-gray-400 text-sm">{cat.percentage.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${cat.percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-4">No category data available</p>
            )}
          </div>

          <div className="bg-gray-750 rounded-lg p-6">
            <h4 className="text-md font-semibold text-white mb-4">Top Websites</h4>
            {domains?.domains?.length > 0 ? (
              <div className="space-y-2">
                {domains.domains.slice(0, 5).map((domain: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-700 rounded">
                    <span className="text-white text-sm truncate">{domain.domain}</span>
                    <span className="text-gray-400 text-sm">{formatTime(domain.duration_seconds)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-4">No website data available</p>
            )}
          </div>
        </div>

        {/* Activity Summary */}
        <div className="bg-gray-750 rounded-lg p-6">
          <h4 className="text-md font-semibold text-white mb-4">Activity Summary</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-400 mb-1">Websites Visited</p>
              <p className="text-xl font-bold text-white">{domains?.domains?.length || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Categories Used</p>
              <p className="text-xl font-bold text-white">{categories?.categories?.length || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Total Sessions</p>
              <p className="text-xl font-bold text-white">{sessions}</p>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Top Website</p>
              <p className="text-lg font-bold text-white truncate">{topDomain || 'N/A'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Section 5: AI Summary */}
      <div className="bg-gradient-to-r from-purple-900 to-blue-900 rounded-lg p-6 border border-purple-700 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <Activity className="text-purple-300" size={24} />
            <div>
              <h3 className="text-lg font-semibold text-white">AI Summary</h3>
              <p className="text-sm text-purple-200">AI-powered insights for the selected period</p>
            </div>
          </div>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-4">
          <p className="text-gray-300 text-sm">
            AI summary generation will be available after Organization AI is implemented.
            This section will provide concise insights about the employee's productivity,
            patterns, and recommendations for the selected date range.
          </p>
        </div>
      </div>

      {/* Section 6: Recent Activity */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
        {timeline?.items?.length > 0 ? (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {timeline.items.slice(0, 10).map((item: any, index: number) => (
              <div key={index} className="p-3 bg-gray-750 rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-white font-medium text-sm">{item.website_domain || 'Idle Session'}</span>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                        item.type === 'activity'
                          ? 'bg-green-900 text-green-300'
                          : 'bg-orange-900 text-orange-300'
                      }`}>
                        {item.type === 'activity' ? 'Productive' : 'Non-Productive'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400">{item.category || 'Uncategorized'}</p>
                  </div>
                  <span className="text-sm text-gray-400 whitespace-nowrap ml-2">{formatTime(item.duration_seconds)}</span>
                </div>
                <p className="text-xs text-gray-500">{formatDateTime(item.start_time)}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-4">No recent activity</p>
        )}
      </div>
    </div>
  );
};
