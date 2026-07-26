/**
 * Idle Queue Service for FocusGuard Extension
 * Manages local storage queue for completed idle sessions
 */

import { storageService } from './storage';
import { logger } from '../utils/logger';
import { QUEUE_CONFIG, IDLE_CONFIG } from '../config';
import type { IdleQueueItem, IdleSession } from '../types/idle';

/**
 * Storage key for idle queue
 */
const IDLE_QUEUE_KEY = 'idle_sessions';

/**
 * Idle Queue Service
 */
class IdleQueueService {
  private writeLock: Promise<void> = Promise.resolve();

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
   * Add completed idle session to queue
   */
  async addIdleSession(session: IdleSession): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        // Validate idle duration before adding to queue
        if (session.durationSeconds === null || session.durationSeconds < IDLE_CONFIG.MIN_DURATION_SECONDS) {
          logger.warn(
            `[IDLE QUEUE] Rejecting idle session - Duration (${session.durationSeconds}s) is below threshold (${IDLE_CONFIG.MIN_DURATION_SECONDS}s). Not adding to queue.`
          );
          return;
        }

        // Check for overlapping sessions in queue
        const queue = await this.getQueue();
        const overlapping = queue.find(item => {
          const existing = item.data;
          return (
            session.startTime !== null &&
            session.endTime !== null &&
            existing.startTime !== null &&
            existing.endTime !== null &&
            session.startTime < existing.endTime &&
            session.endTime > existing.startTime
          );
        });

        if (overlapping) {
          logger.warn(
            `[IDLE QUEUE] Rejecting idle session - Overlaps with existing session: ${overlapping.data.idleId}`
          );
          return;
        }

        const queueItem: IdleQueueItem = {
          id: this.generateId(),
          timestamp: Date.now(),
          data: session,
          uploaded: false,
        };

        // Add to beginning of queue (newest first)
        queue.unshift(queueItem);

        // Enforce maximum queue size
        if (queue.length > QUEUE_CONFIG.MAX_IDLE_SIZE) {
          queue.splice(QUEUE_CONFIG.MAX_IDLE_SIZE);
          logger.warn(`Idle queue truncated to ${QUEUE_CONFIG.MAX_IDLE_SIZE} items`);
        }

        await storageService.set(IDLE_QUEUE_KEY, queue);
      } catch (error) {
        logger.error('[IDLE QUEUE] FAILED to add idle session to queue', error);
        throw error;
      }
    });
  }

  /**
   * Get all idle sessions from queue
   */
  async getQueue(): Promise<IdleQueueItem[]> {
    try {
      const queue = await storageService.get<IdleQueueItem[]>(IDLE_QUEUE_KEY);
      return queue ?? [];
    } catch (error) {
      logger.error('[IDLE QUEUE] Failed to get idle queue', error);
      return [];
    }
  }

  /**
   * Get pending (not uploaded) idle sessions
   */
  async getPendingSessions(): Promise<IdleQueueItem[]> {
    try {
      const queue = await this.getQueue();
      return queue.filter(item => !item.uploaded);
    } catch (error) {
      logger.error('[IDLE QUEUE] Failed to get pending idle sessions', error);
      return [];
    }
  }

  /**
   * Mark idle session as uploaded
   */
  async markAsUploaded(itemId: string): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();
        const item = queue.find(item => item.id === itemId);

        if (item) {
          item.uploaded = true;
          await storageService.set(IDLE_QUEUE_KEY, queue);
        }
      } catch (error) {
        logger.error('[IDLE QUEUE] Failed to mark idle session as uploaded', error);
        throw error;
      }
    });
  }

  /**
   * Remove uploaded idle sessions from queue
   */
  async removeUploadedSessions(): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();
        const pendingQueue = queue.filter(item => !item.uploaded);

        await storageService.set(IDLE_QUEUE_KEY, pendingQueue);
      } catch (error) {
        logger.error('[IDLE QUEUE] Failed to remove uploaded idle sessions', error);
        throw error;
      }
    });
  }

  /**
   * Clear all idle sessions from queue
   */
  async clearQueue(): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        await storageService.remove(IDLE_QUEUE_KEY);
      } catch (error) {
        logger.error('[IDLE QUEUE] Failed to clear idle queue', error);
        throw error;
      }
    });
  }

  /**
   * Clean up invalid idle sessions from queue
   * Removes sessions that are below the minimum duration threshold
   */
  async cleanupInvalidSessions(): Promise<number> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();
        const originalSize = queue.length;

        const validQueue = queue.filter(item => {
          const isValid = item.data.durationSeconds !== null && item.data.durationSeconds >= IDLE_CONFIG.MIN_DURATION_SECONDS;
          if (!isValid) {
            logger.warn(
              `[IDLE QUEUE] Removing invalid session - Idle ID: ${item.data.idleId}, Duration: ${item.data.durationSeconds}s, Threshold: ${IDLE_CONFIG.MIN_DURATION_SECONDS}s`
            );
          }
          return isValid;
        });

        if (validQueue.length !== originalSize) {
          await storageService.set(IDLE_QUEUE_KEY, validQueue);
          const removedCount = originalSize - validQueue.length;
          return removedCount;
        }

        return 0;
      } catch (error) {
        logger.error('[IDLE QUEUE] Failed to cleanup invalid sessions', error);
        return 0;
      }
    });
  }

  /**
   * Clean up overlapping idle sessions from queue
   * Removes sessions that overlap with each other, keeping only the first one
   */
  async cleanupOverlappingSessions(): Promise<number> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();

        // Sort by start time to process in chronological order
        const sortedQueue = [...queue].sort((a, b) => {
          const aTime = a.data.startTime ?? 0;
          const bTime = b.data.startTime ?? 0;
          return aTime - bTime;
        });

        const nonOverlappingQueue: typeof queue = [];
        const removedIds: string[] = [];

        for (const item of sortedQueue) {
          const overlaps = nonOverlappingQueue.some(existing => {
            return (
              item.data.startTime !== null &&
              item.data.endTime !== null &&
              existing.data.startTime !== null &&
              existing.data.endTime !== null &&
              item.data.startTime < existing.data.endTime &&
              item.data.endTime > existing.data.startTime
            );
          });

          if (overlaps) {
            removedIds.push(item.data.idleId);
            logger.warn(
              `[IDLE QUEUE] Removing overlapping session - Idle ID: ${item.data.idleId}`
            );
          } else {
            nonOverlappingQueue.push(item);
          }
        }

        if (removedIds.length > 0) {
          await storageService.set(IDLE_QUEUE_KEY, nonOverlappingQueue);
          return removedIds.length;
        }

        return 0;
      } catch (error) {
        logger.error('[IDLE QUEUE] Failed to cleanup overlapping sessions', error);
        return 0;
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
      logger.error('[IDLE QUEUE] Failed to get queue size', error);
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
      logger.error('[IDLE QUEUE] Failed to get pending queue size', error);
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
 * Singleton idle queue service instance
 */
export const idleQueueService = new IdleQueueService();
