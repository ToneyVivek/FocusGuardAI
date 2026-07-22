/**
 * Centralized Configuration for FocusGuard Extension
 * DEVELOPMENT MODE: Values are set for testing (change for production)
 */

/**
 * Application Configuration
 */
export const config = {
  /**
   * Enable logging
   */
  enableLogging: true,

  /**
   * API base URL
   * Includes /api/v1 prefix for all API routes
   */
  apiBaseUrl: 'http://localhost:8000/api/v1',

  /**
   * Request timeout in milliseconds
   */
  requestTimeout: 30000,
} as const;

/**
 * Idle Detection Configuration
 */
export const IDLE_CONFIG = {
  /**
   * Idle detection threshold in seconds
   * Chrome Idle API will fire after this many seconds of inactivity
   * DEVELOPMENT: 15 seconds for testing
   * PRODUCTION: Change to 60 seconds
   */
  THRESHOLD_SECONDS: 15,

  /**
   * Minimum idle duration in seconds to be considered valid
   * Idle sessions shorter than this will be discarded
   * DEVELOPMENT: 15 seconds for testing
   * PRODUCTION: Change to 60 seconds
   */
  MIN_DURATION_SECONDS: 15,
} as const;

/**
 * Synchronization Configuration
 */
export const SYNC_CONFIG = {
  /**
   * Sync interval in milliseconds
   * How often to check for pending sessions to upload
   */
  INTERVAL_MS: 60 * 1000, // 60 seconds

  /**
   * Batch size for session uploads
   * Maximum number of sessions per API request
   */
  BATCH_SIZE: 50,
} as const;

/**
 * Queue Configuration
 */
export const QUEUE_CONFIG = {
  /**
   * Maximum activity queue size
   * Maximum number of activities to store locally
   */
  MAX_ACTIVITY_SIZE: 1000,

  /**
   * Maximum session queue size
   * Maximum number of completed sessions to store locally
   */
  MAX_SESSION_SIZE: 1000,

  /**
   * Maximum idle queue size
   * Maximum number of idle sessions to store locally
   */
  MAX_IDLE_SIZE: 1000,
} as const;
