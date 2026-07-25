/**
 * Session Service for FocusGuard Extension
 * Manages website activity sessions
 */

import { logger } from '../utils/logger';
import { sessionQueueService } from './sessionQueue';
import { classificationService } from './classification';
import { storageService } from './storage';
import { syncService } from './sync';
import { STORAGE_KEYS } from '../constants';
import { extractUrlParts } from '../utils/url';
import { shouldTrackUrl } from '../utils/urlFilter';
import { SessionLifecycleState } from '../types/session';
import type { WebsiteSession, ActiveSessionState } from '../types/session';
import type { User } from '../types/auth';

/**
 * Session Service
 */
class SessionService {
  private currentSession: ActiveSessionState | null = null;

  /**
   * Get user context from storage
   * Uses cached user data for offline-first behavior
   */
  private async getUserContext(): Promise<{ userId: number | null; organizationId: number | null }> {
    try {
      const user = await storageService.get<User>(STORAGE_KEYS.USER_DATA);
      if (user) {
        logger.info(`[SESSION SERVICE] Using cached user context - User ID: ${user.id}, Organization ID: ${user.organization?.id}`);
        return {
          userId: user.id,
          organizationId: user.organization?.id ?? null,
        };
      }
      logger.warn('[SESSION SERVICE] No cached user data available, using null values');
      return { userId: null, organizationId: null };
    } catch (error) {
      logger.warn('[SESSION SERVICE] Failed to get user context, using null values', error);
      return { userId: null, organizationId: null };
    }
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Calculate duration metrics
   */
  private calculateDuration(startTime: number, endTime: number): {
    durationMs: number;
    durationSeconds: number;
    durationMinutes: number;
  } {
    const durationMs = endTime - startTime;
    const durationSeconds = Math.floor(durationMs / 1000);
    const durationMinutes = Math.floor(durationSeconds / 60);

    return { durationMs, durationSeconds, durationMinutes };
  }

  /**
   * Start a new session
   */
  async startSession(
    tabId: number | null,
    windowId: number | null,
    url: string | null,
    title: string | null
  ): Promise<void> {
    // Validate URL before creating session
    if (!shouldTrackUrl(url)) {
      logger.info(`[SESSION SERVICE] Ignoring invalid URL: ${url}`);
      return;
    }

    try {
      // End current session if exists
      if (this.currentSession) {
        await this.endSession('tab_switch');
      }

      const urlParts = extractUrlParts(url);
      const category = classificationService.classify(url);
      const { userId, organizationId } = await this.getUserContext();

      this.currentSession = {
        sessionId: this.generateSessionId(),
        tabId,
        windowId,
        url,
        hostname: urlParts?.hostname ?? null,
        domain: urlParts?.domain ?? null,
        title,
        category,
        startTime: Date.now(),
        userId,
        organizationId,
        lifecycleState: SessionLifecycleState.ACTIVE,
      };

      logger.info(`[SESSION SERVICE] Session started - Session ID: ${this.currentSession.sessionId}, Tab ID: ${tabId}, URL: ${url}, Category: ${category}`);
    } catch (error) {
      logger.error('[SESSION SERVICE] Failed to start session', error);
      throw error;
    }
  }

  /**
   * End the current session (idempotent)
   * Uses session lifecycle state to prevent duplicate termination
   * Clears session synchronously before async work to eliminate race window
   */
  async endSession(reason: string): Promise<void> {
    // Return early if no active session
    if (!this.currentSession) {
      logger.info(`[SESSION SERVICE] No active session to end (reason: ${reason})`);
      return;
    }

    // Check session lifecycle state - prevent duplicate termination
    if (this.currentSession.lifecycleState !== SessionLifecycleState.ACTIVE) {
      logger.info(`[SESSION SERVICE] Session already ${this.currentSession.lifecycleState}, ignoring duplicate request (reason: ${reason})`);
      return;
    }

    // Transition to ENDING state synchronously
    this.currentSession.lifecycleState = SessionLifecycleState.ENDING;

    // Capture session data and clear currentSession synchronously
    // This eliminates the race window where concurrent events can terminate the same session
    const sessionToTerminate = this.currentSession;
    this.currentSession = null;

    try {
      const endTime = Date.now();
      const { durationMs, durationSeconds, durationMinutes } = this.calculateDuration(
        sessionToTerminate.startTime,
        endTime
      );

      const completedSession: WebsiteSession = {
        sessionId: sessionToTerminate.sessionId,
        userId: sessionToTerminate.userId,
        organizationId: sessionToTerminate.organizationId,
        tabId: sessionToTerminate.tabId,
        windowId: sessionToTerminate.windowId,
        url: sessionToTerminate.url,
        hostname: sessionToTerminate.hostname,
        domain: sessionToTerminate.domain,
        title: sessionToTerminate.title,
        category: sessionToTerminate.category,
        startTime: sessionToTerminate.startTime,
        endTime,
        durationMs,
        durationSeconds,
        durationMinutes,
        uploaded: false,
      };

      logger.info(`[SESSION SERVICE] Session ended - Session ID: ${sessionToTerminate.sessionId}, Reason: ${reason}, Duration: ${durationSeconds}s (${durationMinutes}m)`);

      // Save completed session to queue
      await sessionQueueService.addSession(completedSession);

      // Trigger debounced sync after session completion
      syncService.triggerSync();

      // Transition to ENDED state (for completeness, though session is already detached)
      sessionToTerminate.lifecycleState = SessionLifecycleState.ENDED;
    } catch (error) {
      logger.error('[SESSION SERVICE] Failed to end session', error);
      // Even on error, session remains detached (currentSession is already null)
      throw error;
    }
  }

  /**
   * Switch to a new session (end current, start new)
   */
  async switchSession(
    tabId: number | null,
    windowId: number | null,
    url: string | null,
    title: string | null
  ): Promise<void> {
    logger.info(`[SESSION SERVICE] Switching session - Tab ID: ${tabId}, URL: ${url}`);
    
    // End current session
    await this.endSession('tab_switch');
    
    // Start new session
    await this.startSession(tabId, windowId, url, title);
  }

  /**
   * Close session for a specific tab
   */
  async closeSession(tabId: number): Promise<void> {
    if (!this.currentSession) {
      logger.info('[SESSION SERVICE] No active session to close');
      return;
    }

    if (this.currentSession.tabId === tabId) {
      logger.info(`[SESSION SERVICE] Closing session for tab - Tab ID: ${tabId}`);
      await this.endSession('tab_closed');
    }
  }

  /**
   * Save completed session to queue
   */
  async saveCompletedSession(session: WebsiteSession): Promise<void> {
    try {
      await sessionQueueService.addSession(session);
      logger.info(`[SESSION SERVICE] Saved completed session - Session ID: ${session.sessionId}`);
    } catch (error) {
      logger.error('[SESSION SERVICE] Failed to save completed session', error);
      throw error;
    }
  }

  /**
   * Get current active session
   */
  getCurrentSession(): ActiveSessionState | null {
    return this.currentSession;
  }

  /**
   * Clear current session without saving
   */
  clearCurrentSession(): void {
    if (this.currentSession) {
      logger.info(`[SESSION SERVICE] Clearing current session - Session ID: ${this.currentSession.sessionId}`);
      this.currentSession = null;
    }
  }

  /**
   * End all sessions on browser shutdown
   */
  async endAllSessions(): Promise<void> {
    if (this.currentSession) {
      logger.info('[SESSION SERVICE] Ending all sessions on browser shutdown');
      await this.endSession('browser_shutdown');
    }
  }
}

/**
 * Singleton session service instance
 */
export const sessionService = new SessionService();
