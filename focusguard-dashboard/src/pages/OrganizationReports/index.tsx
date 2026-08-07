/**
 * Organization Reports Page
 * Displays all employees in the organization with their report summary
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { organizationService } from '../../services/organization';
import axios from '../../api/axios';
import type { User } from '../../types';
import {
  Search,
  User as UserIcon,
  RefreshCw,
  TrendingUp,
  FileText,
  Target
} from 'lucide-react';

interface EmployeeWithStats extends User {
  focus_score?: number;
  total_reports?: number;
}

export const OrganizationReportsPage: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [employees, setEmployees] = useState<EmployeeWithStats[]>([]);
  const [filteredEmployees, setFilteredEmployees] = useState<EmployeeWithStats[]>([]);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const fetchEmployees = useCallback(async () => {
    try {
      setLoading(true);
      const response = await organizationService.getEmployees({ limit: 100 });
      const employeesWithStats = await Promise.all(
        response.employees.map(async (emp) => {
          try {
            // Fetch employee summary for focus score
            const summaryResponse = await axios.get(`/analytics/user/${emp.id}/summary`);
            // Fetch report count
            const reportsResponse = await axios.get(`/admin/employee/${emp.id}/reports`);
            
            return {
              ...emp,
              focus_score: summaryResponse.data.focus_score?.score || 0,
              total_reports: reportsResponse.data.length || 0,
            };
          } catch (error) {
            return {
              ...emp,
              focus_score: 0,
              total_reports: 0,
            };
          }
        })
      );
      setEmployees(employeesWithStats);
      setFilteredEmployees(employeesWithStats);
    } catch (error) {
      console.error('Failed to fetch employees:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  useEffect(() => {
    let filtered = [...employees];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(emp =>
        emp.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        emp.email?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(emp => {
        if (statusFilter === 'active') return emp.is_active;
        if (statusFilter === 'inactive') return !emp.is_active;
        return true;
      });
    }

    setFilteredEmployees(filtered);
  }, [searchTerm, statusFilter, employees]);

  // Only admins can access this page
  if (user?.role !== 'ADMIN') {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-600">Access denied. Admin only.</p>
      </div>
    );
  }


  const handleViewProfile = (employeeId: number) => {
    window.location.href = `/employee-profile/${employeeId}`;
  };

  return (
    <div className="min-h-0">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Organization Reports</h1>
            <p className="text-gray-400">View employee profiles and reports</p>
          </div>
          <button
            onClick={fetchEmployees}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Employees Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="animate-spin text-gray-400" size={32} />
        </div>
      ) : filteredEmployees.length === 0 ? (
        <div className="bg-gray-800 rounded-lg p-12 border border-gray-700 text-center">
          <UserIcon size={48} className="mx-auto mb-4 text-gray-400" />
          <p className="text-gray-400 mb-2">No employees found</p>
          <p className="text-sm text-gray-500">Try adjusting your filters or check back later</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredEmployees.map((employee) => (
            <div
              key={employee.id}
              className="bg-gray-800 rounded-lg p-5 border border-gray-700 hover:border-gray-600 transition-colors cursor-pointer"
              onClick={() => handleViewProfile(employee.id)}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center">
                    <UserIcon size={24} className="text-gray-400" />
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">{employee.full_name}</h3>
                    <p className="text-sm text-gray-400">{employee.email}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  employee.is_active
                    ? 'bg-green-900 text-green-300'
                    : 'bg-gray-700 text-gray-400'
                }`}>
                  {employee.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <Target size={14} className="text-purple-400" />
                    <span className="text-xs text-gray-400">Focus</span>
                  </div>
                  <p className="text-lg font-bold text-white">{employee.focus_score?.toFixed(1) || '0.0'}</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <FileText size={14} className="text-blue-400" />
                    <span className="text-xs text-gray-400">Reports</span>
                  </div>
                  <p className="text-lg font-bold text-white">{employee.total_reports || 0}</p>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-700">
                <span className="text-sm text-gray-400">View Profile →</span>
                <TrendingUp size={18} className="text-gray-400" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
