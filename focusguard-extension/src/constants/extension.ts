/**
 * Extension-related constants for FocusGuard Extension
 */

/**
 * Extension metadata
 */
export const EXTENSION = {
  NAME: 'FocusGuard',
  VERSION: '1.0.0',
  DESCRIPTION: 'FocusGuard Browser Extension - Productivity and time tracking',
} as const;

/**
 * Extension lifecycle events
 */
export const EXTENSION_EVENTS = {
  INSTALLED: 'installed',
  UPDATED: 'updated',
  STARTED: 'started',
  BROWSER_STARTED: 'browser_started',
} as const;

/**
 * Log messages
 */
export const LOG_MESSAGES = {
  EXTENSION_INSTALLED: '[FocusGuard] Extension Installed',
  EXTENSION_STARTED: '[FocusGuard] Extension Started',
  BROWSER_STARTED: '[FocusGuard] Browser Started',
  STORAGE_ERROR: '[FocusGuard] Storage Error',
  API_ERROR: '[FocusGuard] API Error',
  VALIDATION_ERROR: '[FocusGuard] Validation Error',
} as const;

/**
 * Extension permissions
 */
export const PERMISSIONS = {
  STORAGE: 'storage',
  ALARMS: 'alarms',
  ACTIVE_TAB: 'activeTab',
} as const;

/**
 * Host permissions
 */
export const HOST_PERMISSIONS = [
  'http://localhost:8000/*',
] as const;
