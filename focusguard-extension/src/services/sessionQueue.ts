/**
 * Session Queue Service for FocusGuard Extension
 * Manages local storage queue for completed website sessions
 */

import { storageService } from './storage';
import { logger } from '../utils/logger';
import type { SessionQueueItem, WebsiteSession } from '../types/session';

/**
 * Storage key for session queue
 */
const SESSION_QUEUE_KEY = 'activity_sessions';

/**
 * Maximum queue size to prevent storage overflow
 */
const MAX_QUEUE_SIZE = 1000;

/**
 * Session Queue Service
 */
class SessionQueueService {
  /**
   * Add completed session to queue
   */
  async addSession(session: WebsiteSession): Promise<void> {
    try {
      logger.info(`[SESSION QUEUE] Before addSession - Session ID: ${session.sessionId}, Storage key: ${SESSION_QUEUE_KEY}`);
      
      const queue = await this.getQueue();
      logger.info(`[SESSION QUEUE] Current queue size before add: ${queue.length}`);
      
      const queueItem: SessionQueueItem = {
        id: this.generateId(),
        timestamp: Date.now(),
        data: session,
        uploaded: false,
      };

      // Add to beginning of queue (newest first)
      queue.unshift(queueItem);
      logger.info(`[SESSION QUEUE] Queue size after unshift: ${queue.length}`);

      // Enforce maximum queue size
      if (queue.length > MAX_QUEUE_SIZE) {
        queue.splice(MAX_QUEUE_SIZE);
        logger.warn(`Session queue truncated to ${MAX_QUEUE_SIZE} items`);
      }

      logger.info(`[SESSION QUEUE] Before storageService.set - Key: ${SESSION_QUEUE_KEY}, Queue size: ${queue.length}`);
      await storageService.set(SESSION_QUEUE_KEY, queue);
      logger.info(`[SESSION QUEUE] After storageService.set - SUCCESS - Session ID: ${session.sessionId}`);
      
      // Verify the write
      const verifyQueue = await this.getQueue();
      logger.info(`[SESSION QUEUE] Verification - Queue size after write: ${verifyQueue.length}`);
    } catch (error) {
      logger.error('[SESSION QUEUE] FAILED to add session to queue', error);
      logger.error(`[SESSION QUEUE] Error stack: ${error instanceof Error ? error.stack : String(error)}`);
      throw error;
    }
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
    try {
      const queue = await this.getQueue();
      const item = queue.find(item => item.id === itemId);
      
      if (item) {
        item.uploaded = true;
        await storageService.set(SESSION_QUEUE_KEY, queue);
        logger.debug(`Session marked as uploaded: ${itemId}`);
      }
    } catch (error) {
      logger.error('[SESSION QUEUE] Failed to mark session as uploaded', error);
      throw error;
    }
  }

  /**
   * Remove uploaded sessions from queue
   */
  async removeUploadedSessions(): Promise<void> {
    try {
      const queue = await this.getQueue();
      const pendingQueue = queue.filter(item => !item.uploaded);
      
      await storageService.set(SESSION_QUEUE_KEY, pendingQueue);
      logger.debug(`Removed ${queue.length - pendingQueue.length} uploaded sessions`);
    } catch (error) {
      logger.error('[SESSION QUEUE] Failed to remove uploaded sessions', error);
      throw error;
    }
  }

  /**
   * Clear all sessions from queue
   */
  async clearQueue(): Promise<void> {
    try {
      await storageService.remove(SESSION_QUEUE_KEY);
      logger.info('Session queue cleared');
    } catch (error) {
      logger.error('[SESSION QUEUE] Failed to clear session queue', error);
      throw error;
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
