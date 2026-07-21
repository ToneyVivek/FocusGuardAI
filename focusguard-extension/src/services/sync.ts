/**
 * Sync Service for FocusGuard Extension
 * Handles batch synchronization of completed sessions to backend
 */

import { apiClient } from '../api/client';
import { authService } from './auth';
import { sessionQueueService } from './sessionQueue';
import { logger } from '../utils/logger';
import { API_ENDPOINTS } from '../constants';
import type { WebsiteSession } from '../types/session';

/**
 * Batch size for session uploads
 */
const BATCH_SIZE = 50;

/**
 * Sync interval in milliseconds (60 seconds)
 */
const SYNC_INTERVAL_MS = 60 * 1000;

/**
 * Sync Service
 */
class SyncService {
  private isSyncing: boolean = false;
  private syncTimer: number | null = null;

  /**
   * Start periodic synchronization
   */
  startPeriodicSync(): void {
    if (this.syncTimer !== null) {
      logger.info('[SYNC SERVICE] Periodic sync already running');
      return;
    }

    logger.info('[SYNC SERVICE] Starting periodic sync (60s interval)');
    this.syncTimer = setInterval(() => {
      this.syncSessions().catch(error => {
        logger.error('[SYNC SERVICE] Periodic sync failed', error);
      });
    }, SYNC_INTERVAL_MS);
  }

  /**
   * Stop periodic synchronization
   */
  stopPeriodicSync(): void {
    if (this.syncTimer !== null) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
      logger.info('[SYNC SERVICE] Periodic sync stopped');
    }
  }

  /**
   * Synchronize pending sessions to backend
   */
  async syncSessions(): Promise<void> {
    // Prevent concurrent syncs
    if (this.isSyncing) {
      logger.info('[SYNC SERVICE] Sync already in progress, skipping');
      return;
    }

    try {
      this.isSyncing = true;
      logger.info('[SYNC SERVICE] Sync started');

      // Check authentication status
      const isAuth = await authService.isAuthenticated();
      if (!isAuth) {
        logger.info('[SYNC SERVICE] User not authenticated, skipping sync');
        return;
      }

      // Ensure API client has valid token
      const accessToken = await authService.restoreSession();
      if (!accessToken) {
        logger.info('[SYNC SERVICE] Failed to restore session, skipping sync');
        return;
      }

      // Get pending sessions
      const pendingSessions = await sessionQueueService.getPendingSessions();
      logger.info(`[SYNC SERVICE] Pending sessions: ${pendingSessions.length}`);

      if (pendingSessions.length === 0) {
        logger.info('[SYNC SERVICE] No pending sessions to sync');
        return;
      }

      // Process in batches
      const batches = this.createBatches(pendingSessions, BATCH_SIZE);
      logger.info(`[SYNC SERVICE] Created ${batches.length} batches for upload`);

      let successCount = 0;
      let failureCount = 0;

      for (let i = 0; i < batches.length; i++) {
        const batch = batches[i];
        logger.info(`[SYNC SERVICE] Processing batch ${i + 1}/${batches.length} - Size: ${batch.length}`);

        try {
          await this.uploadBatch(batch);
          successCount += batch.length;
          logger.info(`[SYNC SERVICE] Batch ${i + 1} uploaded successfully - Sessions: ${batch.length}`);
        } catch (error) {
          failureCount += batch.length;
          logger.error(`[SYNC SERVICE] Batch ${i + 1} upload failed - Sessions: ${batch.length}`, error);
          // Continue with next batch even if this one fails
        }
      }

      logger.info(`[SYNC SERVICE] Sync completed - Success: ${successCount}, Failure: ${failureCount}`);

      // Remove successfully uploaded sessions
      if (successCount > 0) {
        await sessionQueueService.removeUploadedSessions();
        logger.info(`[SYNC SERVICE] Removed ${successCount} uploaded sessions from queue`);
      }
    } catch (error) {
      logger.error('[SYNC SERVICE] Sync failed', error);
    } finally {
      this.isSyncing = false;
    }
  }

  /**
   * Create batches from sessions
   */
  private createBatches(sessions: any[], batchSize: number): any[][] {
    const batches: any[][] = [];
    for (let i = 0; i < sessions.length; i += batchSize) {
      batches.push(sessions.slice(i, i + batchSize));
    }
    return batches;
  }

  /**
   * Upload a batch of sessions to backend
   */
  private async uploadBatch(batch: any[]): Promise<void> {
    try {
      // Convert session queue items to backend format, filtering out invalid sessions
      const validSessions: any[] = [];
      const validItems: any[] = [];
      
      for (const item of batch) {
        try {
          const sessionData = this.convertSessionToBackendFormat(item.data);
          validSessions.push(sessionData);
          validItems.push(item);
        } catch (error) {
          logger.warn(`[SYNC SERVICE] Skipping invalid session - Session ID: ${item.data.sessionId}`, error);
          // Mark invalid sessions as uploaded to remove them from queue
          await sessionQueueService.markAsUploaded(item.id);
        }
      }

      if (validSessions.length === 0) {
        logger.info('[SYNC SERVICE] No valid sessions in batch to upload');
        return;
      }

      const payload = {
        sessions: validSessions,
      };

      logger.info(`[SYNC SERVICE] Uploading batch - Size: ${validSessions.length}`);
      logger.info(`[SYNC SERVICE] Payload: ${JSON.stringify(payload, null, 2)}`);
      await apiClient.post(API_ENDPOINTS.ACTIVITY_BATCH, payload);
      logger.info('[SYNC SERVICE] Batch upload successful');

      // Mark valid sessions as uploaded
      for (const item of validItems) {
        await sessionQueueService.markAsUploaded(item.id);
      }
    } catch (error) {
      logger.error('[SYNC SERVICE] Batch upload failed', error);
      throw error;
    }
  }

  /**
   * Convert session to backend format
   */
  private convertSessionToBackendFormat(session: WebsiteSession): any {
    // Skip sessions without required fields
    if (!session.url || !session.domain) {
      logger.warn(`[SYNC SERVICE] Skipping session with missing required data - Session ID: ${session.sessionId}, URL: ${session.url}, Domain: ${session.domain}`);
      throw new Error('Session missing required fields: url or domain');
    }

    // Skip sessions with invalid URL protocols (backend requires http:// or https://)
    if (!session.url.startsWith('http://') && !session.url.startsWith('https://')) {
      logger.warn(`[SYNC SERVICE] Skipping session with invalid URL protocol - Session ID: ${session.sessionId}, URL: ${session.url}`);
      throw new Error('Session URL must start with http:// or https://');
    }

    // Skip sessions without valid end time
    if (!session.endTime) {
      logger.warn(`[SYNC SERVICE] Skipping session without end time - Session ID: ${session.sessionId}`);
      throw new Error('Session missing end time');
    }

    // Skip sessions with invalid duration (end time must be after start time)
    if (session.endTime <= session.startTime) {
      logger.warn(`[SYNC SERVICE] Skipping session with invalid duration - Session ID: ${session.sessionId}, Start: ${session.startTime}, End: ${session.endTime}`);
      throw new Error('Session end time must be after start time');
    }

    return {
      browser_name: 'Chrome', // Could be dynamic in future
      website_url: session.url,
      website_domain: session.domain,
      page_title: session.title,
      session_start_time: new Date(session.startTime).toISOString(),
      session_end_time: new Date(session.endTime).toISOString(),
    };
  }

  /**
   * Trigger sync immediately (called after session completion)
   */
  async triggerSync(): Promise<void> {
    logger.info('[SYNC SERVICE] Immediate sync triggered');
    await this.syncSessions();
  }

  /**
   * Get sync status
   */
  isSyncInProgress(): boolean {
    return this.isSyncing;
  }
}

/**
 * Singleton sync service instance
 */
export const syncService = new SyncService();
