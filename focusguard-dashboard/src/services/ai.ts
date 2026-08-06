/**
 * AI Service
 * Handles AI Coach API calls
 */
import axios from '../api/axios';
import type {
  DailySummaryResponse,
  WeeklySummaryResponse,
  InsightsResponse,
  RecommendationsResponse,
  ChatResponse,
  ConversationResponse,
} from '../types/ai';

export const aiService = {
  /**
   * Get daily productivity summary
   */
  getDailySummary: async (targetDate?: string): Promise<DailySummaryResponse> => {
    const params = new URLSearchParams();
    if (targetDate) params.append('target_date', targetDate);

    const response = await axios.get<DailySummaryResponse>(
      `/ai/summary/daily${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },

  /**
   * Get weekly productivity summary
   */
  getWeeklySummary: async (
    startDate?: string,
    endDate?: string
  ): Promise<WeeklySummaryResponse> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await axios.get<WeeklySummaryResponse>(
      `/ai/summary/weekly${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },

  /**
   * Get productivity insights
   */
  getInsights: async (
    startDate?: string,
    endDate?: string
  ): Promise<InsightsResponse> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await axios.get<InsightsResponse>(
      `/ai/insights${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },

  /**
   * Get personalized recommendations
   */
  getRecommendations: async (
    startDate?: string,
    endDate?: string
  ): Promise<RecommendationsResponse> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await axios.get<RecommendationsResponse>(
      `/ai/recommendations${params.toString() ? `?${params.toString()}` : ''}`
    );
    return response.data;
  },

  /**
   * Send chat message to AI
   */
  chat: async (
    message: string,
    conversationHistory?: any[],
    startDate?: string,
    endDate?: string
  ): Promise<ChatResponse> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await axios.post<ChatResponse>(
      `/ai/chat${params.toString() ? `?${params.toString()}` : ''}`,
      {
        message,
        conversation_history: conversationHistory,
      }
    );
    return response.data;
  },

  /**
   * Get the user's latest conversation
   */
  getConversation: async (): Promise<ConversationResponse> => {
    const response = await axios.get<ConversationResponse>('/ai/conversation');
    return response.data;
  },

  /**
   * Clear the user's conversation
   */
  clearConversation: async (): Promise<{ message: string }> => {
    const response = await axios.delete<{ message: string }>('/ai/conversation');
    return response.data;
  },
};
