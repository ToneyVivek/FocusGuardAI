/**
 * AI Types
 * Type definitions for AI Coach endpoints
 */

export interface DailySummaryResponse {
  title: string;
  summary: string;
  highlights: string[];
  recommendations: string[];
  assessment: 'positive' | 'neutral' | 'needs_improvement';
  focus_score: number;
  date: string;
}

export interface WeeklySummaryResponse {
  title: string;
  summary: string;
  highlights: string[];
  recommendations: string[];
  assessment: 'excellent' | 'good' | 'fair' | 'needs_improvement';
  next_week_goal: string;
  focus_score: number;
  start_date: string;
  end_date: string;
}

export interface InsightItem {
  category: string;
  insight: string;
  data_point?: string;
}

export interface InsightsResponse {
  title: string;
  insights: InsightItem[];
  patterns: string[];
  distractions: string[];
  category_balance: string;
  focus_score_recommendations: string[];
  time_allocation_suggestions: string[];
}

export interface RecommendationItem {
  title: string;
  impact: 'high' | 'medium' | 'low';
  implementation_steps: string[];
  expected_outcome: string;
}

export interface RecommendationsResponse {
  title: string;
  recommendations: RecommendationItem[];
  priority_order: string[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  conversation_history?: ChatMessage[];
}

export interface ChatResponse {
  message: string;
  context_used: boolean;
  suggestions: string[];
}

export interface ConversationResponse {
  messages: ChatMessage[];
  suggested_questions: string[];
  last_message_at: string | null;
}
