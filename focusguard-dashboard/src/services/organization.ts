/**
 * Organization Service
 * Handles organization and employee management API calls
 */
import axios from '../api/axios';
import type { EmployeeListResponse, Invitation, InvitationListResponse, User } from '../types';

export const organizationService = {
  /**
   * Get organization employees with optional search and filtering
   */
  getEmployees: async (params?: {
    search?: string;
    status_filter?: 'active' | 'inactive';
    limit?: number;
    offset?: number;
  }): Promise<EmployeeListResponse> => {
    const response = await axios.get<EmployeeListResponse>('/admin/employees', { params });
    return response.data;
  },

  /**
   * Get employee details
   */
  getEmployee: async (employeeId: number): Promise<User> => {
    const response = await axios.get<User>(`/admin/employees/${employeeId}`);
    return response.data;
  },

  /**
   * Toggle employee status (enable/disable)
   */
  toggleEmployeeStatus: async (employeeId: number): Promise<User> => {
    const response = await axios.patch<User>(`/admin/employees/${employeeId}/toggle-status`);
    return response.data;
  },

  /**
   * Remove employee (soft delete)
   */
  removeEmployee: async (employeeId: number): Promise<void> => {
    await axios.delete(`/admin/employees/${employeeId}`);
  },

  /**
   * Invite a new employee
   */
  inviteEmployee: async (email: string): Promise<Invitation> => {
    const response = await axios.post<Invitation>('/admin/invite-user', { email });
    return response.data;
  },

  /**
   * Get pending invitations
   */
  getInvitations: async (params?: {
    limit?: number;
    offset?: number;
  }): Promise<InvitationListResponse> => {
    const response = await axios.get<InvitationListResponse>('/admin/invitations', { params });
    return response.data;
  },

  /**
   * Resend invitation
   */
  resendInvitation: async (invitationId: number): Promise<Invitation> => {
    const response = await axios.post<Invitation>(`/admin/invitations/${invitationId}/resend`);
    return response.data;
  },
};
