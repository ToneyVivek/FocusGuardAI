/**
 * Dashboard Service
 * Handles dashboard-specific API calls
 */
import axios from '../api/axios';
import type { 
  UserSummaryResponseV2, 
  OrganizationSummaryResponseV2,
  Timeline,
  ProductivityBreakdown,
  DomainBreakdown,
  CategoryBreakdown
} from '../types/dashboard';
import { DEFAULT_TIMELINE_LIMIT, DEFAULT_DOMAINS_LIMIT } from '../constants/api';

export const dashboardService = {
  /**
   * Get user summary for dashboard
   */
  getUserSummary: async (startDate?: string, endDate?: string): Promise<UserSummaryResponseV2> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await axios.get<UserSummaryResponseV2>(
      `/analytics/me/v2/summary${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },

  /**
   * Get organization summary for dashboard (ADMIN only)
   */
  getOrgSummary: async (startDate?: string, endDate?: string): Promise<OrganizationSummaryResponseV2> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await axios.get<OrganizationSummaryResponseV2>(
      `/analytics/org/v2/summary${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },

  /**
   * Get user productivity breakdown
   */
  getUserProductivity: async (startDate?: string, endDate?: string): Promise<ProductivityBreakdown> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await axios.get<ProductivityBreakdown>(
      `/analytics/me/v2/productivity${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },

  /**
   * Get user domain breakdown (top websites)
   */
  getUserDomains: async (limit: number = DEFAULT_DOMAINS_LIMIT, startDate?: string, endDate?: string): Promise<DomainBreakdown> => {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await axios.get<DomainBreakdown>(
      `/analytics/me/v2/domains${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },

  /**
   * Get user timeline (recent activity)
   */
  getUserTimeline: async (limit: number = DEFAULT_TIMELINE_LIMIT, startDate?: string, endDate?: string): Promise<Timeline> => {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await axios.get<Timeline>(
      `/analytics/me/v2/timeline${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },

  /**
   * Get user category breakdown
   */
  getUserCategories: async (startDate?: string, endDate?: string): Promise<CategoryBreakdown> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await axios.get<CategoryBreakdown>(
      `/analytics/me/v2/categories${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },
};
