/**
 * Shared TypeScript interfaces for FocusGuard Dashboard
 */

// User types
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'EMPLOYEE';
  organization_id: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserProfile extends User {
  organization?: Organization;
}

// Organization types
export interface Organization {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

// Auth types
export interface JWTPayload {
  sub: number; // user_id
  email: string;
  role: string;
  organization_id: number | null;
  exp: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  organization_name?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// API Response types
export interface APIResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface APIError {
  detail: string;
  status_code?: number;
}

// Analytics types (placeholder - will be expanded in Phase 1)
export interface AnalyticsSummary {
  total_focus_time: number;
  productive_time: number;
  neutral_time: number;
  non_productive_time: number;
  idle_time: number;
  completed_sessions: number;
  idle_sessions: number;
  activity_events: number;
}

export interface ProductivityBreakdown {
  productive: {
    duration_seconds: number;
    percentage: number;
  };
  neutral: {
    duration_seconds: number;
    percentage: number;
  };
  non_productive: {
    duration_seconds: number;
    percentage: number;
  };
}

export interface CategoryBreakdownItem {
  category: string;
  duration_seconds: number;
  percentage: number;
  session_count: number;
}

export interface CategoryBreakdown {
  categories: CategoryBreakdownItem[];
}

export interface DomainBreakdownItem {
  domain: string;
  duration_seconds: number;
  session_count: number;
}

export interface DomainBreakdown {
  domains: DomainBreakdownItem[];
}

export interface FocusScore {
  score: number;
  productive_time: number;
  total_active_time: number;
}

// Navigation types
export interface NavItem {
  label: string;
  path: string;
  icon?: string;
  roles?: ('ADMIN' | 'EMPLOYEE')[];
}

// Employee management types
export interface EmployeeListResponse {
  employees: User[];
  total: number;
  limit: number;
  offset: number;
}

export interface Invitation {
  id: number;
  email: string;
  organization_id: number;
  invited_by: number;
  expires_at: string;
  is_used: boolean;
  created_at: string;
  updated_at: string;
}

export interface InvitationListResponse {
  invitations: Invitation[];
  total: number;
  limit: number;
  offset: number;
}

// Organization Dashboard types
export interface OrganizationSummaryMetrics {
  total_focus_time: number;
  productive_time: number;
  neutral_time: number;
  non_productive_time: number;
  idle_time: number;
  completed_sessions: number;
  idle_sessions: number;
  activity_events: number;
}

export interface OrganizationProductivityBreakdown {
  productive: { duration_seconds: number; percentage: number };
  neutral: { duration_seconds: number; percentage: number };
  non_productive: { duration_seconds: number; percentage: number };
}

export interface OrganizationSummaryResponse {
  metrics: OrganizationSummaryMetrics;
  productivity: OrganizationProductivityBreakdown;
  categories: { categories: Array<{ category: string; duration_seconds: number; percentage: number; session_count: number }> };
  domains: { domains: Array<{ domain: string; duration_seconds: number; session_count: number }> };
  employee_count: number;
}

export interface EmployeeRankingItem {
  user_id: number;
  username: string;
  focus_score: number;
  productive_time: number;
  total_active_time: number;
}

export interface EmployeeRankings {
  rankings: EmployeeRankingItem[];
}

export interface TimelineItem {
  session_id: number;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  website_url: string | null;
  website_domain: string | null;
  category: string | null;
  productivity: string | null;
  type: 'activity' | 'idle';
  user_id?: number;
  user_name?: string;
  employee_name?: string;
  employee_email?: string;
}
