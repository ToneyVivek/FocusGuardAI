/**
 * Idle Detection Service for FocusGuard Extension
 * Manages idle state tracking using Chrome Idle API
 */

import { logger } from '../utils/logger';
import { idleQueueService } from './idleQueue';
import { sessionService } from './session';
import { storageService } from './storage';
import { syncService } from './sync';
import { STORAGE_KEYS } from '../constants';
import { IDLE_CONFIG } from '../config';
import type { IdleSession, CurrentIdleState } from '../types/idle';
import type { User } from '../types/auth';

/**
 * Idle Service
 */
class IdleService {
  private currentState: CurrentIdleState = {
    idleId: null,
    state: 'active',
    startTime: null,
  };

  private idleDetectionInterval: number | null = null;

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
      logger.warn('[IDLE SERVICE] Failed to get user context, using null values', error);
      return { userId: null, organizationId: null };
    }
  }

  /**
   * Generate unique idle session ID
   */
  private generateIdleId(): string {
    return `idle-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
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
   * Start idle period
   */
  private async startIdlePeriod(): Promise<void> {
    try {
      // Check if already idle
      if (this.currentState.state === 'idle' && this.currentState.idleId) {
        logger.warn(
          `[IDLE SERVICE] Already in idle state - Idle ID: ${this.currentState.idleId}, Start time: ${this.currentState.startTime}. Ignoring duplicate start.`
        );
        return;
      }

      // End active browsing session if exists
      await sessionService.endSession('user_idle');

      // Start idle tracking
      const idleId = this.generateIdleId();
      const startTime = Date.now();

      this.currentState = {
        idleId,
        state: 'idle',
        startTime,
      };

      logger.info(
        `[IDLE SERVICE] Idle started - Idle ID: ${idleId}, Start time: ${new Date(startTime).toISOString()}, State: ${this.currentState.state}`
      );
    } catch (error) {
      logger.error('[IDLE SERVICE] Failed to start idle period', error);
    }
  }

  /**
   * End idle period
   */
  private async endIdlePeriod(): Promise<void> {
    try {
      if (!this.currentState.idleId || !this.currentState.startTime) {
        logger.info('[IDLE SERVICE] No active idle period to end');
        return;
      }

      const endTime = Date.now();
      const { durationMs, durationSeconds, durationMinutes } = this.calculateDuration(
        this.currentState.startTime,
        endTime
      );

      logger.info(
        `[IDLE SERVICE] Idle session ending - Idle ID: ${this.currentState.idleId}, Start: ${new Date(this.currentState.startTime).toISOString()}, End: ${new Date(endTime).toISOString()}, Duration: ${durationSeconds}s, Threshold: ${IDLE_CONFIG.MIN_DURATION_SECONDS}s, Valid: ${durationSeconds >= IDLE_CONFIG.MIN_DURATION_SECONDS}`
      );

      // Validate idle duration against minimum threshold
      if (durationSeconds < IDLE_CONFIG.MIN_DURATION_SECONDS) {
        logger.warn(
          `[IDLE SERVICE] Idle session duration (${durationSeconds}s) is below minimum threshold (${IDLE_CONFIG.MIN_DURATION_SECONDS}s). Discarding idle session.`
        );

        // Clear current idle state without saving
        this.currentState = {
          idleId: null,
          state: 'active',
          startTime: null,
        };

        // Resume browsing session with current active tab
        await this.resumeBrowsingSession();
        return;
      }

      const { userId, organizationId } = await this.getUserContext();

      const completedIdleSession: IdleSession = {
        idleId: this.currentState.idleId,
        userId,
        organizationId,
        startTime: this.currentState.startTime,
        endTime,
        durationMs,
        durationSeconds,
        durationMinutes,
        uploaded: false,
      };

      logger.info(
        `[IDLE SERVICE] Idle session created for queue - Idle ID: ${completedIdleSession.idleId}, Duration: ${durationSeconds}s, User ID: ${userId}`
      );

      // Save completed idle session to queue
      await idleQueueService.addIdleSession(completedIdleSession);

      // Trigger sync after idle session completion
      syncService.triggerSync().catch(error => {
        logger.warn('[IDLE SERVICE] Failed to trigger sync after idle session completion', error);
      });

      // Clear current idle state
      this.currentState = {
        idleId: null,
        state: 'active',
        startTime: null,
      };

      // Resume browsing session with current active tab
      await this.resumeBrowsingSession();
    } catch (error) {
      logger.error('[IDLE SERVICE] Failed to end idle period', error);
    }
  }

  /**
   * Resume browsing session after idle period
   */
  private async resumeBrowsingSession(): Promise<void> {
    try {
      // Get the current active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (tab && tab.url && tab.id) {
        logger.info(`[IDLE SERVICE] Resuming browsing session - Tab ID: ${tab.id}, URL: ${tab.url}`);
        await sessionService.startSession(tab.id, tab.windowId ?? null, tab.url, tab.title ?? null);
      }
    } catch (error) {
      logger.error('[IDLE SERVICE] Failed to resume browsing session', error);
    }
  }

  /**
   * Handle idle state change from Chrome Idle API
   */
  private async handleIdleStateChange(newState: chrome.idle.IdleState): Promise<void> {
    try {
      logger.info(`[IDLE SERVICE] Idle state changed - New state: ${newState}`);

      if (newState === 'idle' || newState === 'locked') {
        // User became idle or locked - start idle period
        if (this.currentState.state === 'active') {
          await this.startIdlePeriod();
        }
        this.currentState.state = newState as 'idle' | 'locked';
      } else if (newState === 'active') {
        // User became active - end idle period
        if (this.currentState.state !== 'active') {
          await this.endIdlePeriod();
        }
        this.currentState.state = 'active';
      }
    } catch (error) {
      logger.error('[IDLE SERVICE] Failed to handle idle state change', error);
    }
  }

  /**
   * Start idle detection
   */
  startIdleDetection(): void {
    if (this.idleDetectionInterval !== null) {
      logger.info('[IDLE SERVICE] Idle detection already running');
      return;
    }

    // Defensive check: Ensure chrome.idle API is available
    if (!chrome.idle) {
      logger.warn('[IDLE SERVICE] chrome.idle API is not available. Idle detection will be skipped.');
      return;
    }

    logger.info('[IDLE SERVICE] Starting idle detection');
    
    // Set up Chrome Idle API listener
    chrome.idle.setDetectionInterval(IDLE_CONFIG.THRESHOLD_SECONDS);
    
    chrome.idle.onStateChanged.addListener((newState: string) => {
      this.handleIdleStateChange(newState as chrome.idle.IdleState).catch(error => {
        logger.error('[IDLE SERVICE] Error in idle state change handler', error);
      });
    });

    logger.info('[IDLE SERVICE] Idle detection started');
  }

  /**
   * Stop idle detection
   */
  stopIdleDetection(): void {
    if (this.idleDetectionInterval !== null) {
      clearInterval(this.idleDetectionInterval);
      this.idleDetectionInterval = null;
      logger.info('[IDLE SERVICE] Idle detection stopped');
    }

    // Note: Chrome Idle API listeners are automatically removed on service worker restart
    // No need to manually remove the listener
  }

  /**
   * Get current idle state
   */
  getCurrentState(): CurrentIdleState {
    return this.currentState;
  }

  /**
   * End all idle sessions on browser shutdown
   */
  async endAllIdleSessions(): Promise<void> {
    if (this.currentState.state !== 'active' && this.currentState.idleId) {
      logger.info('[IDLE SERVICE] Ending idle session on browser shutdown');
      await this.endIdlePeriod();
    }
  }
}

/**
 * Singleton idle service instance
 */
export const idleService = new IdleService();
