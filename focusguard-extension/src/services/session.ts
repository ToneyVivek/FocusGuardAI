/**
 * Session Service for FocusGuard Extension
 * Manages website activity sessions
 */

import { logger } from '../utils/logger';
import { sessionQueueService } from './sessionQueue';
import { classificationService } from './classification';
import { storageService } from './storage';
import { STORAGE_KEYS } from '../constants';
import { extractUrlParts } from '../utils/url';
import type { WebsiteSession, ActiveSessionState } from '../types/session';
import type { User } from '../types/auth';

/**
 * Session Service
 */
class SessionService {
  private currentSession: ActiveSessionState | null = null;

  /**
   * Get user context from storage
   */
  private async getUserContext(): Promise<{ userId: number | null; organizationId: number | null }> {
    try {
      const user = await storageService.get<User>(STORAGE_KEYS.USER_DATA);
      if (user) {
        return {
          userId: user.id,
          organizationId: user.organization?.id ?? null,
        };
      }
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
      };

      logger.info(`[SESSION SERVICE] Session started - Session ID: ${this.currentSession.sessionId}, Tab ID: ${tabId}, URL: ${url}, Category: ${category}`);
    } catch (error) {
      logger.error('[SESSION SERVICE] Failed to start session', error);
      throw error;
    }
  }

  /**
   * End the current session
   */
  async endSession(reason: string): Promise<void> {
    if (!this.currentSession) {
      logger.info('[SESSION SERVICE] No active session to end');
      return;
    }

    try {
      const endTime = Date.now();
      const { durationMs, durationSeconds, durationMinutes } = this.calculateDuration(
        this.currentSession.startTime,
        endTime
      );

      const completedSession: WebsiteSession = {
        sessionId: this.currentSession.sessionId,
        userId: this.currentSession.userId,
        organizationId: this.currentSession.organizationId,
        tabId: this.currentSession.tabId,
        windowId: this.currentSession.windowId,
        url: this.currentSession.url,
        hostname: this.currentSession.hostname,
        domain: this.currentSession.domain,
        title: this.currentSession.title,
        category: this.currentSession.category,
        startTime: this.currentSession.startTime,
        endTime,
        durationMs,
        durationSeconds,
        durationMinutes,
        uploaded: false,
      };

      logger.info(`[SESSION SERVICE] Session ended - Session ID: ${this.currentSession.sessionId}, Reason: ${reason}, Duration: ${durationSeconds}s (${durationMinutes}m)`);

      // Save completed session to queue
      await sessionQueueService.addSession(completedSession);

      // Clear current session
      this.currentSession = null;
    } catch (error) {
      logger.error('[SESSION SERVICE] Failed to end session', error);
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
