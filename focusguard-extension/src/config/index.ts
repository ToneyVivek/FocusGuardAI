/**
 * Environment configuration for FocusGuard Extension
 * Centralized configuration management
 */

export const config = {
  /**
   * API Base URL
   * Backend API endpoint for future communication
   */
  apiBaseUrl: 'http://localhost:8000/api/v1',

  /**
   * Extension Version
   * Current version of the extension
   */
  version: '1.0.0',

  /**
   * Environment
   * Current environment (development, production)
   */
  environment: 'development' as const,

  /**
   * Request Timeout
   * Default timeout for API requests in milliseconds
   */
  requestTimeout: 30000,

  /**
   * Extension Name
   * Display name of the extension
   */
  extensionName: 'FocusGuard',

  /**
   * Storage Prefix
   * Prefix for all storage keys to avoid conflicts
   */
  storagePrefix: 'focusguard_',

  /**
   * Enable Logging
   * Whether logging is enabled (can be disabled in production)
   */
  enableLogging: true,
} as const;

export type Config = typeof config;
