/**
 * React Query (TanStack Query) configuration
 * Provides global QueryClient with sensible defaults
 */
import { QueryClient } from '@tanstack/react-query';

/**
 * Create and configure QueryClient
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Time in milliseconds that data remains fresh
      staleTime: 5 * 60 * 1000, // 5 minutes
      
      // Time in milliseconds that inactive queries remain in cache
      gcTime: 10 * 60 * 1000, // 10 minutes
      
      // Number of times to retry failed queries
      retry: 1,
      
      // Retry delay
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      
      // Refetch on window focus
      refetchOnWindowFocus: false,
      
      // Refetch on reconnect
      refetchOnReconnect: true,
      
      // Refetch on mount
      refetchOnMount: true,
    },
    mutations: {
      // Number of times to retry failed mutations
      retry: 1,
      
      // Retry delay
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
});
