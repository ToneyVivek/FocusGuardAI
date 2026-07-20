/**
 * API-related constants for FocusGuard Extension
 */

/**
 * HTTP status codes
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
} as const;

/**
 * API endpoints (for future use)
 */
export const API_ENDPOINTS = {
  // Authentication endpoints
  LOGIN: '/auth/login',
  LOGOUT: '/auth/logout',
  REFRESH: '/auth/refresh',
  ME: '/auth/me',
  
  // User endpoints (future)
  USER: '/user',
  USER_PROFILE: '/user/profile',
  
  // Activity endpoints (future)
  ACTIVITY: '/activity',
  ACTIVITY_SUMMARY: '/activity/summary',
} as const;

/**
 * Default headers for API requests
 */
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
} as const;
