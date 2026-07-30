/**
 * Activity Queue Service for FocusGuard Extension
 * Manages local storage queue for browser activity events
 */

import { storageService } from './storage';
import { logger } from '../utils/logger';
import { STORAGE_KEYS } from '../constants';
import { QUEUE_CONFIG } from '../config';
import type { ActivityQueueItem, TabActivity, WindowActivity, LifecycleActivity } from '../types/browser';
import type { User } from '../types/auth';

/**
 * Storage key for activity queue
 */
const ACTIVITY_QUEUE_KEY = 'activity_queue';

/**
 * Activity Queue Service
 */
class ActivityQueueService {
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
   * Get user context from storage
   * Returns userId and organizationId if authenticated, null otherwise
   * Uses cached user data for offline-first behavior
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
      logger.warn('[ACTIVITY QUEUE] No cached user data available, using null values');
      return { userId: null, organizationId: null };
    } catch (error) {
      logger.warn('[ACTIVITY QUEUE] Failed to get user context, using null values', error);
      return { userId: null, organizationId: null };
    }
  }

  /**
   * Generate ISO-8601 timestamp
   */
  private generateIsoTimestamp(timestamp: number): string {
    return new Date(timestamp).toISOString();
  }

  /**
   * Add activity to queue
   */
  async addActivity(activity: TabActivity | WindowActivity | LifecycleActivity): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        // Get user context
        const { userId, organizationId } = await this.getUserContext();

        // Attach user context and ISO timestamp to activity
        activity.userId = userId;
        activity.organizationId = organizationId;
        activity.timestampIso = this.generateIsoTimestamp(activity.timestamp);

        const queue = await this.getQueue();

        const queueItem: ActivityQueueItem = {
          id: this.generateId(),
          timestamp: Date.now(),
          eventType: activity.eventType,
          data: activity,
          uploaded: false,
        };

        // Add to beginning of queue (newest first)
        queue.unshift(queueItem);

        // Enforce maximum queue size
        if (queue.length > QUEUE_CONFIG.MAX_ACTIVITY_SIZE) {
          queue.splice(QUEUE_CONFIG.MAX_ACTIVITY_SIZE);
          if (!this.hasWarnedAboutTruncation) {
            logger.warn(`Activity queue truncated to ${QUEUE_CONFIG.MAX_ACTIVITY_SIZE} items`);
            this.hasWarnedAboutTruncation = true;
          }
        } else if (queue.length < QUEUE_CONFIG.MAX_ACTIVITY_SIZE * 0.8) {
          // Reset warning flag when queue drops below 80% of max size
          this.hasWarnedAboutTruncation = false;
        }

        await storageService.set(ACTIVITY_QUEUE_KEY, queue);
      } catch (error) {
        logger.error('[ACTIVITY QUEUE] FAILED to add activity to queue', error);
        throw error;
      }
    });
  }

  /**
   * Get all activities from queue
   */
  async getQueue(): Promise<ActivityQueueItem[]> {
    try {
      const queue = await storageService.get<ActivityQueueItem[]>(ACTIVITY_QUEUE_KEY);
      return queue ?? [];
    } catch (error) {
      logger.error('Failed to get activity queue', error);
      return [];
    }
  }

  /**
   * Get pending (not uploaded) activities
   */
  async getPendingActivities(): Promise<ActivityQueueItem[]> {
    try {
      const queue = await this.getQueue();
      return queue.filter(item => !item.uploaded);
    } catch (error) {
      logger.error('Failed to get pending activities', error);
      return [];
    }
  }

  /**
   * Mark activity as uploaded
   */
  async markAsUploaded(itemId: string): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();
        const item = queue.find(item => item.id === itemId);

        if (item) {
          item.uploaded = true;
          await storageService.set(ACTIVITY_QUEUE_KEY, queue);
        }
      } catch (error) {
        logger.error('Failed to mark activity as uploaded', error);
        throw error;
      }
    });
  }

  /**
   * Remove uploaded activities from queue
   */
  async removeUploadedActivities(): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();
        const pendingQueue = queue.filter(item => !item.uploaded);

        await storageService.set(ACTIVITY_QUEUE_KEY, pendingQueue);
      } catch (error) {
        logger.error('Failed to remove uploaded activities', error);
        throw error;
      }
    });
  }

  /**
   * Remove specific activities from queue by their IDs
   * This is more precise than removeUploadedActivities as it only removes items that were successfully uploaded
   */
  async removeUploadedActivitiesByIds(ids: string[]): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        const queue = await this.getQueue();
        const filteredQueue = queue.filter(item => !ids.includes(item.id));

        await storageService.set(ACTIVITY_QUEUE_KEY, filteredQueue);
      } catch (error) {
        logger.error('Failed to remove activities by IDs', error);
        throw error;
      }
    });
  }

  /**
   * Clear all activities from queue
   */
  async clearQueue(): Promise<void> {
    return this.withWriteLock(async () => {
      try {
        await storageService.remove(ACTIVITY_QUEUE_KEY);
      } catch (error) {
        logger.error('Failed to clear activity queue', error);
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
      logger.error('Failed to get queue size', error);
      return 0;
    }
  }

  /**
   * Get pending queue size
   */
  async getPendingSize(): Promise<number> {
    try {
      const pending = await this.getPendingActivities();
      return pending.length;
    } catch (error) {
      logger.error('Failed to get pending queue size', error);
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
 * Singleton activity queue service instance
 */
export const activityQueueService = new ActivityQueueService();
