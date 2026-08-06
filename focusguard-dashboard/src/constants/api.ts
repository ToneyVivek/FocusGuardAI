/**
 * API Constants
 * Shared constants for API limits and constraints
 */

/**
 * Maximum number of timeline items that can be requested in a single call
 * Backend validation: limit must be <= 500
 */
export const MAX_TIMELINE_LIMIT = 500;

/**
 * Default number of items to request for timeline
 */
export const DEFAULT_TIMELINE_LIMIT = 500;

/**
 * Maximum number of domains that can be requested in a single call
 */
export const MAX_DOMAINS_LIMIT = 50;

/**
 * Default number of domains to request
 */
export const DEFAULT_DOMAINS_LIMIT = 20;
