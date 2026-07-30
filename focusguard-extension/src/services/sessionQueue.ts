/**
 * Session Queue Service for FocusGuard Extension
 * Manages local storage queue for completed website sessions
 */

import { storageService } from './storage';
import { logger } from '../utils/logger';
import { QUEUE_CONFIG } from '../config';
import type { SessionQueueItem, WebsiteSession } from '../types/session';

/**
 * Storage key for session queue
 */
const SESSION_QUEUE_KEY = 'activity_sessions';

/**
 * Session Queue Service
 */
class SessionQueueService {
  private writeLock: Promise<void> = Promise.resolve();
  private hasWarnedAboutTruncation: boolean = false;

  /**
   * Execute a queue write operation with a lock to prevent concurrent writes
   */
  private async withWriteLock<T>(operation: () => Promise<T>): Promise<T> {
    // Wait for any existing write to complete
    await this.writeLock;

    // Create a new lock for this operation
    let resolveLock: () => void;
    this.writeLock = new Promise(resolve => {
      resolveLock = resolve;
    });

    try {
      // Execute the operation
      return await operation();
    } finally {
      // Release the lock
      resolveLock!();
    }
  }
  /**
   * Add completed session to queue
   */
  async addSession(session: WebsiteSession): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();

        const queueItem: SessionQueueItem = {
          id: this.generateId(),
          timestamp: Date.now(),
          data: session,
          uploaded: false,
        };

        // Add to beginning of queue (newest first)
        queue.unshift(queueItem);

        // Enforce maximum queue size
        if (queue.length > QUEUE_CONFIG.MAX_SESSION_SIZE) {
          queue.splice(QUEUE_CONFIG.MAX_SESSION_SIZE);
          if (!this.hasWarnedAboutTruncation) {
            logger.warn(`Session queue truncated to ${QUEUE_CONFIG.MAX_SESSION_SIZE} items`);
            this.hasWarnedAboutTruncation = true;
          }
        } else if (queue.length < QUEUE_CONFIG.MAX_SESSION_SIZE * 0.8) {
          // Reset warning flag when queue drops below 80% of max size
          this.hasWarnedAboutTruncation = false;
        }

        await storageService.set(SESSION_QUEUE_KEY, queue);
      } catch (error) {
        logger.error('[SESSION QUEUE] FAILED to add session to queue', error);
        throw error;
      }
    });
  }

  /**
   * Get all sessions from queue
   */
  async getQueue(): Promise<SessionQueueItem[]> {
    try {
      const queue = await storageService.get<SessionQueueItem[]>(SESSION_QUEUE_KEY);
      return queue ?? [];
    } catch (error) {
      logger.error('[SESSION QUEUE] Failed to get session queue', error);
      return [];
    }
  }

  /**
   * Get pending (not uploaded) sessions
   */
  async getPendingSessions(): Promise<SessionQueueItem[]> {
    try {
      const queue = await this.getQueue();
      return queue.filter(item => !item.uploaded);
    } catch (error) {
      logger.error('[SESSION QUEUE] Failed to get pending sessions', error);
      return [];
    }
  }

  /**
   * Mark session as uploaded
   */
  async markAsUploaded(itemId: string): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();
        const item = queue.find(item => item.id === itemId);

        if (item) {
          item.uploaded = true;
          await storageService.set(SESSION_QUEUE_KEY, queue);
        }
      } catch (error) {
        logger.error('[SESSION QUEUE] Failed to mark session as uploaded', error);
        throw error;
      }
    });
  }

  /**
   * Remove uploaded sessions from queue
   */
  async removeUploadedSessions(): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();
        const pendingQueue = queue.filter(item => !item.uploaded);

        await storageService.set(SESSION_QUEUE_KEY, pendingQueue);
      } catch (error) {
        logger.error('[SESSION QUEUE] Failed to remove uploaded sessions', error);
        throw error;
      }
    });
  }

  /**
   * Remove specific sessions from queue by their IDs
   * This is more precise than removeUploadedSessions as it only removes items that were successfully uploaded
   */
  async removeUploadedSessionsByIds(ids: string[]): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();
        const filteredQueue = queue.filter(item => !ids.includes(item.id));

        await storageService.set(SESSION_QUEUE_KEY, filteredQueue);
      } catch (error) {
        logger.error('[SESSION QUEUE] Failed to remove sessions by IDs', error);
        throw error;
      }
    });
  }

  /**
   * Clear all sessions from queue
   */
  async clearQueue(): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        await storageService.remove(SESSION_QUEUE_KEY);
      } catch (error) {
        logger.error('[SESSION QUEUE] Failed to clear session queue', error);
        throw error;
      }
    });
  }

  /**
   * Get queue size
   */
  async getQueueSize(): Promise<number> {
    try {
      const queue = await this.getQueue();
      return queue.length;
    } catch (error) {
      logger.error('[SESSION QUEUE] Failed to get queue size', error);
      return 0;
    }
  }

  /**
   * Get pending queue size
   */
  async getPendingSize(): Promise<number> {
    try {
      const pending = await this.getPendingSessions();
      return pending.length;
    } catch (error) {
      logger.error('[SESSION QUEUE] Failed to get pending queue size', error);
      return 0;
    }
  }

  /**
   * Generate unique ID for queue item
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

/**
 * Singleton session queue service instance
 */
export const sessionQueueService = new SessionQueueService();
