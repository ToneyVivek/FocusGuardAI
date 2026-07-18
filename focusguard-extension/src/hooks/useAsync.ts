/**
 * useAsync hook for FocusGuard Extension
 * Provides React hook for async operations
 */

import { useState, useCallback, useEffect } from 'react';
import { logger } from '../utils/logger';

/**
 * Hook for async operations
 * @param asyncFunction - Async function to execute
 * @param immediate - Whether to execute immediately on mount
 * @returns { data, error, loading, execute, reset }
 */
export function useAsync<T>(
  asyncFunction: () => Promise<T>,
  immediate = true
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);

  const execute = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await asyncFunction();
      setData(result);
      return result;
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error('Async operation failed');
      setError(errorObj);
      logger.error('useAsync: Operation failed', err);
      throw errorObj;
    } finally {
      setLoading(false);
    }
  }, [asyncFunction]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  return {
    data,
    error,
    loading,
    execute,
    reset,
  };
}
