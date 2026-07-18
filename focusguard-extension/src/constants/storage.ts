/**
 * Storage-related constants for FocusGuard Extension
 */

/**
 * Storage key prefixes
 */
export const STORAGE_PREFIX = 'focusguard_';

/**
 * Storage keys
 */
export const STORAGE_KEYS = {
  // Authentication keys (future)
  ACCESS_TOKEN: `${STORAGE_PREFIX}access_token`,
  REFRESH_TOKEN: `${STORAGE_PREFIX}refresh_token`,
  USER_DATA: `${STORAGE_PREFIX}user_data`,
  
  // Extension state
  EXTENSION_STATE: `${STORAGE_PREFIX}extension_state`,
  LAST_SYNC: `${STORAGE_PREFIX}last_sync`,
  
  // Settings (future)
  SETTINGS: `${STORAGE_PREFIX}settings`,
  PREFERENCES: `${STORAGE_PREFIX}preferences`,
} as const;

/**
 * Storage defaults
 */
export const STORAGE_DEFAULTS = {
  extensionState: {
    initialized: false,
    version: '1.0.0',
  },
} as const;
