/**
 * useStorage hook for FocusGuard Extension
 * Provides React hook for Chrome storage operations
 */

import { useState, useEffect, useCallback } from 'react';
import { storageService } from '../services/storage';
import { logger } from '../utils/logger';

/**
 * Hook for Chrome storage operations
 * @param key - Storage key
 * @param initialValue - Initial value if key doesn't exist
 * @returns [value, setValue, isLoading, error]
 */
export function useStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, boolean, Error | null] {
  const [value, setValue] = useState<T>(initialValue);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Load value from storage on mount
  useEffect(() => {
    const loadValue = async () => {
      try {
        setIsLoading(true);
        const storedValue = await storageService.get<T>(key);
        if (storedValue !== null) {
          setValue(storedValue);
        }
      } catch (err) {
        const errorObj = err instanceof Error ? err : new Error('Failed to load storage value');
        setError(errorObj);
        logger.error(`useStorage: Failed to load value for key ${key}`, err);
      } finally {
        setIsLoading(false);
      }
    };

    loadValue();
  }, [key]);

  // Update value in storage
  const updateValue = useCallback(
    (newValue: T | ((prev: T) => T)) => {
      const valueToStore = newValue instanceof Function ? newValue(value) : newValue;
      setValue(valueToStore);

      storageService.set(key, valueToStore).catch((err) => {
        const errorObj = err instanceof Error ? err : new Error('Failed to save storage value');
        setError(errorObj);
        logger.error(`useStorage: Failed to save value for key ${key}`, err);
      });
    },
    [key, value]
  );

  return [value, updateValue, isLoading, error];
}
