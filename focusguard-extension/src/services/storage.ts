/**
 * Chrome Storage Service for FocusGuard Extension
 * Provides strongly typed helper methods for chrome.storage.local
 */

import { StorageError } from '../utils/errors';
import { logger } from '../utils/logger';
import { STORAGE_PREFIX } from '../constants';
import type { StorageItem } from '../types';

/**
 * Storage service class
 * Wraps chrome.storage.local with typed methods
 */
class StorageService {
  /**
   * Get a value from storage
   */
  async get<T = unknown>(key: string): Promise<T | null> {
    try {
      const prefixedKey = this.prefixKey(key);
      const result = await chrome.storage.local.get(prefixedKey);
      const value = result[prefixedKey];
      
      logger.debug(`Storage get: ${key}`, value);
      return (value as T) ?? null;
    } catch (error) {
      const message = `Failed to get value for key: ${key}`;
      logger.error(message, error);
      throw new StorageError(message, key, 'get');
    }
  }

  /**
   * Set a value in storage
   */
  async set<T = unknown>(key: string, value: T): Promise<void> {
    try {
      const prefixedKey = this.prefixKey(key);
      const data: Record<string, T> = {
        [prefixedKey]: value,
      };
      
      await chrome.storage.local.set(data);
      logger.debug(`Storage set: ${key}`, value);
    } catch (error) {
      const message = `Failed to set value for key: ${key}`;
      logger.error(message, error);
      throw new StorageError(message, key, 'set');
    }
  }

  /**
   * Remove a value from storage
   */
  async remove(key: string): Promise<void> {
    try {
      const prefixedKey = this.prefixKey(key);
      await chrome.storage.local.remove(prefixedKey);
      logger.debug(`Storage remove: ${key}`);
    } catch (error) {
      const message = `Failed to remove value for key: ${key}`;
      logger.error(message, error);
      throw new StorageError(message, key, 'remove');
    }
  }

  /**
   * Clear all storage values with the extension prefix
   */
  async clear(): Promise<void> {
    try {
      const allKeys = await this.keys();
      await chrome.storage.local.remove(allKeys);
      logger.debug('Storage cleared');
    } catch (error) {
      const message = 'Failed to clear storage';
      logger.error(message, error);
      throw new StorageError(message, undefined, 'clear');
    }
  }

  /**
   * Check if a key exists in storage
   */
  async exists(key: string): Promise<boolean> {
    try {
      const value = await this.get(key);
      return value !== null;
    } catch (error) {
      const message = `Failed to check existence of key: ${key}`;
      logger.error(message, error);
      throw new StorageError(message, key, 'get');
    }
  }

  /**
   * Get all keys with the extension prefix
   */
  async keys(): Promise<string[]> {
    try {
      const result = await chrome.storage.local.get();
      const keys = Object.keys(result).filter(key => 
        key.startsWith(STORAGE_PREFIX)
      );
      logger.debug('Storage keys retrieved', keys);
      return keys;
    } catch (error) {
      const message = 'Failed to get storage keys';
      logger.error(message, error);
      throw new StorageError(message, undefined, 'get');
    }
  }

  /**
   * Get all storage items with the extension prefix
   */
  async getAll<T = unknown>(): Promise<StorageItem<T>[]> {
    try {
      const result = await chrome.storage.local.get();
      const items: StorageItem<T>[] = [];
      
      for (const [key, value] of Object.entries(result)) {
        if (key.startsWith(STORAGE_PREFIX)) {
          items.push({
            key: this.removePrefix(key),
            value: value as T,
          });
        }
      }
      
      logger.debug('Storage items retrieved', items);
      return items;
    } catch (error) {
      const message = 'Failed to get all storage items';
      logger.error(message, error);
      throw new StorageError(message, undefined, 'get');
    }
  }

  /**
   * Get multiple values at once
   */
  async getMultiple<T = unknown>(keys: string[]): Promise<Record<string, T | null>> {
    try {
      const prefixedKeys = keys.map(key => this.prefixKey(key));
      const result = await chrome.storage.local.get(prefixedKeys);
      
      const output: Record<string, T | null> = {};
      for (const key of keys) {
        const prefixedKey = this.prefixKey(key);
        output[key] = (result[prefixedKey] as T) ?? null;
      }
      
      logger.debug(`Storage get multiple: ${keys.join(', ')}`, output);
      return output;
    } catch (error) {
      const message = `Failed to get multiple values for keys: ${keys.join(', ')}`;
      logger.error(message, error);
      throw new StorageError(message, undefined, 'get');
    }
  }

  /**
   * Set multiple values at once
   */
  async setMultiple<T = unknown>(items: Record<string, T>): Promise<void> {
    try {
      const data: Record<string, T> = {};
      for (const [key, value] of Object.entries(items)) {
        data[this.prefixKey(key)] = value;
      }
      
      await chrome.storage.local.set(data);
      logger.debug('Storage set multiple', items);
    } catch (error) {
      const message = 'Failed to set multiple values';
      logger.error(message, error);
      throw new StorageError(message, undefined, 'set');
    }
  }

  /**
   * Prefix a key with the storage prefix
   */
  private prefixKey(key: string): string {
    return key.startsWith(STORAGE_PREFIX) ? key : `${STORAGE_PREFIX}${key}`;
  }

  /**
   * Remove the storage prefix from a key
   */
  private removePrefix(key: string): string {
    return key.startsWith(STORAGE_PREFIX) ? key.slice(STORAGE_PREFIX.length) : key;
  }
}

/**
 * Singleton storage service instance
 */
export const storageService = new StorageService();
