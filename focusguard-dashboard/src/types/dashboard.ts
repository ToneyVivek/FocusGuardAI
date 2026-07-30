/**
 * Dashboard Types
 * Types for analytics data from backend
 */

export interface SummaryMetrics {
  total_focus_time: number;
  productive_time: number;
  neutral_time: number;
  non_productive_time: number;
  idle_time: number;
  completed_sessions: number;
  idle_sessions: number;
  activity_events: number;
}

export interface ProductivityType {
  duration_seconds: number;
  percentage: number;
}

export interface ProductivityBreakdown {
  productive: ProductivityType;
  neutral: ProductivityType;
  non_productive: ProductivityType;
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

export interface TimelineItem {
  session_id: number;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  website_url: string | null;
  website_domain: string | null;
  category: string | null;
  productivity: string | null;
}

export interface Timeline {
  items: TimelineItem[];
}

export interface FocusScore {
  score: number;
  productive_time: number;
  total_active_time: number;
}

export interface UserSummaryResponseV2 {
  metrics: SummaryMetrics;
  productivity: ProductivityBreakdown;
  categories: CategoryBreakdown;
  domains: DomainBreakdown;
  focus_score: FocusScore;
}

export interface OrganizationSummaryResponseV2 {
  metrics: SummaryMetrics;
  productivity: ProductivityBreakdown;
  categories: CategoryBreakdown;
  domains: DomainBreakdown;
  employee_count: number;
}
