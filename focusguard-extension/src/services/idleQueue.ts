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
  /**
   * Add completed idle session to queue
   */
  async addIdleSession(session: IdleSession): Promise<void> {
    try {
      logger.info(
        `[IDLE QUEUE] Before addIdleSession - Idle ID: ${session.idleId}, Start: ${session.startTime ? new Date(session.startTime).toISOString() : 'null'}, End: ${session.endTime ? new Date(session.endTime).toISOString() : 'null'}, Duration: ${session.durationSeconds}s, Threshold: ${IDLE_CONFIG.MIN_DURATION_SECONDS}s`
      );

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
          `[IDLE QUEUE] Rejecting idle session - Overlaps with existing session: ${overlapping.data.idleId} (${overlapping.data.startTime ? new Date(overlapping.data.startTime).toISOString() : 'null'} - ${overlapping.data.endTime ? new Date(overlapping.data.endTime).toISOString() : 'null'})`
        );
        return;
      }

      logger.info(`[IDLE QUEUE] Idle session validation passed - Adding to queue`);

      logger.info(`[IDLE QUEUE] Current queue size before add: ${queue.length}`);
      
      const queueItem: IdleQueueItem = {
        id: this.generateId(),
        timestamp: Date.now(),
        data: session,
        uploaded: false,
      };

      // Add to beginning of queue (newest first)
      queue.unshift(queueItem);
      logger.info(`[IDLE QUEUE] Queue size after unshift: ${queue.length}`);

      // Enforce maximum queue size
      if (queue.length > QUEUE_CONFIG.MAX_IDLE_SIZE) {
        queue.splice(QUEUE_CONFIG.MAX_IDLE_SIZE);
        logger.warn(`Idle queue truncated to ${QUEUE_CONFIG.MAX_IDLE_SIZE} items`);
      }

      logger.info(`[IDLE QUEUE] Before storageService.set - Key: ${IDLE_QUEUE_KEY}, Queue size: ${queue.length}`);
      await storageService.set(IDLE_QUEUE_KEY, queue);
      logger.info(`[IDLE QUEUE] After storageService.set - SUCCESS - Idle ID: ${session.idleId}`);
      
      // Verify the write
      const verifyQueue = await this.getQueue();
      logger.info(`[IDLE QUEUE] Verification - Queue size after write: ${verifyQueue.length}`);
    } catch (error) {
      logger.error('[IDLE QUEUE] FAILED to add idle session to queue', error);
      logger.error(`[IDLE QUEUE] Error stack: ${error instanceof Error ? error.stack : String(error)}`);
      throw error;
    }
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
    try {
      const queue = await this.getQueue();
      const item = queue.find(item => item.id === itemId);
      
      if (item) {
        item.uploaded = true;
        await storageService.set(IDLE_QUEUE_KEY, queue);
        logger.debug(`Idle session marked as uploaded: ${itemId}`);
      }
    } catch (error) {
      logger.error('[IDLE QUEUE] Failed to mark idle session as uploaded', error);
      throw error;
    }
  }

  /**
   * Remove uploaded idle sessions from queue
   */
  async removeUploadedSessions(): Promise<void> {
    try {
      const queue = await this.getQueue();
      const pendingQueue = queue.filter(item => !item.uploaded);
      
      await storageService.set(IDLE_QUEUE_KEY, pendingQueue);
      logger.debug(`Removed ${queue.length - pendingQueue.length} uploaded idle sessions`);
    } catch (error) {
      logger.error('[IDLE QUEUE] Failed to remove uploaded idle sessions', error);
      throw error;
    }
  }

  /**
   * Clear all idle sessions from queue
   */
  async clearQueue(): Promise<void> {
    try {
      await storageService.remove(IDLE_QUEUE_KEY);
      logger.info('Idle queue cleared');
    } catch (error) {
      logger.error('[IDLE QUEUE] Failed to clear idle queue', error);
      throw error;
    }
  }

  /**
   * Clean up invalid idle sessions from queue
   * Removes sessions that are below the minimum duration threshold
   */
  async cleanupInvalidSessions(): Promise<number> {
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
        logger.info(
          `[IDLE QUEUE] Cleaned up ${removedCount} invalid sessions (${originalSize} -> ${validQueue.length})`
        );
        return removedCount;
      }

      logger.info('[IDLE QUEUE] No invalid sessions found in queue');
      return 0;
    } catch (error) {
      logger.error('[IDLE QUEUE] Failed to cleanup invalid sessions', error);
      return 0;
    }
  }

  /**
   * Clean up overlapping idle sessions from queue
   * Removes sessions that overlap with each other, keeping only the first one
   */
  async cleanupOverlappingSessions(): Promise<number> {
    try {
      const queue = await this.getQueue();
      const originalSize = queue.length;

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
            `[IDLE QUEUE] Removing overlapping session - Idle ID: ${item.data.idleId}, Start: ${item.data.startTime ? new Date(item.data.startTime).toISOString() : 'null'}, End: ${item.data.endTime ? new Date(item.data.endTime).toISOString() : 'null'}`
          );
        } else {
          nonOverlappingQueue.push(item);
        }
      }

      if (removedIds.length > 0) {
        await storageService.set(IDLE_QUEUE_KEY, nonOverlappingQueue);
        logger.info(
          `[IDLE QUEUE] Cleaned up ${removedIds.length} overlapping sessions (${originalSize} -> ${nonOverlappingQueue.length}), Removed IDs: ${removedIds.join(', ')}`
        );
        return removedIds.length;
      }

      logger.info('[IDLE QUEUE] No overlapping sessions found in queue');
      return 0;
    } catch (error) {
      logger.error('[IDLE QUEUE] Failed to cleanup overlapping sessions', error);
      return 0;
    }
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
