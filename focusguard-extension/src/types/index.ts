/**
 * Type definitions for FocusGuard Extension
 */

/**
 * Extension status interface
 */
export interface ExtensionStatus {
  loaded: boolean;
  version: string;
}

/**
 * Generic API response wrapper
 */
export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  success: boolean;
}

/**
 * API error response
 */
export interface ApiErrorResponse {
  error: string;
  message: string;
  statusCode: number;
  details?: Record<string, unknown>;
}

/**
 * Storage item interface
 */
export interface StorageItem<T = unknown> {
  key: string;
  value: T;
  timestamp?: number;
}

/**
 * Extension state interface
 */
export interface ExtensionState {
  initialized: boolean;
  version: string;
  lastUpdated?: number;
}

/**
 * Configuration interface
 */
export interface Config {
  apiBaseUrl: string;
  version: string;
  environment: 'development' | 'production';
  requestTimeout: number;
  extensionName: string;
  storagePrefix: string;
  enableLogging: boolean;
}

/**
 * HTTP method types
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

/**
 * Request options interface
 */
export interface RequestOptions {
  method?: HttpMethod;
  headers?: Record<string, string>;
  body?: unknown;
  timeout?: number;
  signal?: AbortSignal;
  contentType?: 'json' | 'form-urlencoded';
}

/**
 * Storage operation types
 */
export type StorageOperation = 'get' | 'set' | 'remove' | 'clear' | 'exists' | 'keys';

/**
 * Log level types
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';
