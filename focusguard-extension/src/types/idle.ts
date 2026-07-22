/**
 * Idle Session Types for FocusGuard Extension
 * Defines types for idle detection and tracking
 */

/**
 * Idle state enumeration
 */
export type IdleState = 'active' | 'idle' | 'locked';

/**
 * Idle session interface
 */
export interface IdleSession {
  idleId: string;
  userId: number | null;
  organizationId: number | null;
  startTime: number;
  endTime: number | null;
  durationMs: number | null;
  durationSeconds: number | null;
  durationMinutes: number | null;
  uploaded: boolean;
}

/**
 * Idle queue item interface
 */
export interface IdleQueueItem {
  id: string;
  timestamp: number;
  data: IdleSession;
  uploaded: boolean;
}

/**
 * Current idle state
 */
export interface CurrentIdleState {
  idleId: string | null;
  state: IdleState;
  startTime: number | null;
}
