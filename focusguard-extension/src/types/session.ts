/**
 * Session Types for FocusGuard Extension
 * Defines types for website activity sessions
 */

/**
 * Website category enumeration
 */
export type WebsiteCategory =
  | 'DEVELOPMENT'
  | 'PRODUCTIVITY'
  | 'SOCIAL_MEDIA'
  | 'ENTERTAINMENT'
  | 'COMMUNICATION'
  | 'SHOPPING'
  | 'NEWS'
  | 'EDUCATION'
  | 'SEARCH'
  | 'OTHER';

/**
 * Website activity session interface
 */
export interface WebsiteSession {
  sessionId: string;
  userId: number | null;
  organizationId: number | null;
  tabId: number | null;
  windowId: number | null;
  url: string | null;
  hostname: string | null;
  domain: string | null;
  title: string | null;
  category: WebsiteCategory;
  startTime: number;
  endTime: number | null;
  durationMs: number | null;
  durationSeconds: number | null;
  durationMinutes: number | null;
  uploaded: boolean;
}

/**
 * Session queue item interface
 */
export interface SessionQueueItem {
  id: string;
  timestamp: number;
  data: WebsiteSession;
  uploaded: boolean;
}

/**
 * Current active session state
 */
export interface ActiveSessionState {
  sessionId: string;
  tabId: number | null;
  windowId: number | null;
  url: string | null;
  hostname: string | null;
  domain: string | null;
  title: string | null;
  category: WebsiteCategory;
  startTime: number;
  userId: number | null;
  organizationId: number | null;
}
