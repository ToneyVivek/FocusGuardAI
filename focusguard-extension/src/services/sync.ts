/**
 * Sync Service for FocusGuard Extension
 * Handles batch synchronization of completed sessions to backend
 * with debounced batching and intelligent retry logic
 */

import { apiClient } from '../api/client';
import { authService } from './auth';
import { sessionQueueService } from './sessionQueue';
import { idleQueueService } from './idleQueue';
import { activityQueueService } from './activityQueue';
import { logger } from '../utils/logger';
import { API_ENDPOINTS } from '../constants';
import { SYNC_CONFIG } from '../config';
import type { WebsiteSession } from '../types/session';
import type { IdleSession } from '../types/idle';

/**
 * Sync Service Configuration
 */
const DEBOUNCE_DELAY_MS = 5000; // 5 seconds
const RETRY_DELAYS_MS = [10000, 20000, 40000, 80000, 300000]; // 10s, 20s, 40s, 80s, 5min
const SYNC_ALARM_NAME = 'focusguard-sync-alarm';

/**
 * Sync Service
 */
class SyncService {
  private isSyncing: boolean = false;
  private pendingSync: boolean = false;
  private debounceTimer: number | null = null;
  private retryCounter: number = 0;
  private retryTimer: number | null = null;

  /**
   * Start periodic synchronization using Chrome Alarms API
   * Creates a repeating alarm for MV3 compliance
   */
  startPeriodicSync(): void {
    // Check if alarm already exists to avoid duplicates
    chrome.alarms.get(SYNC_ALARM_NAME, (alarm) => {
      if (chrome.runtime.lastError) {
        logger.error('[SYNC SERVICE] Failed to check alarm existence', chrome.runtime.lastError);
        return;
      }

      if (alarm) {
        logger.info('[SYNC SERVICE] Periodic sync alarm already exists');
        return;
      }

      // Create repeating alarm (1-minute interval)
      chrome.alarms.create(SYNC_ALARM_NAME, {
        periodInMinutes: 1, // 1 minute = 60 seconds
      }, () => {
        if (chrome.runtime.lastError) {
          logger.error('[SYNC SERVICE] Failed to create periodic sync alarm', chrome.runtime.lastError);
        } else {
          logger.info('[SYNC SERVICE] Periodic sync alarm created (1-minute interval)');
        }
      });
    });
  }

  /**
   * Stop periodic synchronization
   */
  stopPeriodicSync(): void {
    // Clear alarm
    chrome.alarms.clear(SYNC_ALARM_NAME, (wasCleared) => {
      if (chrome.runtime.lastError) {
        logger.error('[SYNC SERVICE] Failed to clear periodic sync alarm', chrome.runtime.lastError);
      } else if (wasCleared) {
        logger.info('[SYNC SERVICE] Periodic sync alarm cleared');
      } else {
        logger.info('[SYNC SERVICE] Periodic sync alarm was not found or already cleared');
      }
    });

    // Clear debounce timer
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
      logger.info('[SYNC SERVICE] Debounce timer cleared');
    }

    // Clear retry timer
    if (this.retryTimer !== null) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
      logger.info('[SYNC SERVICE] Retry timer cleared');
    }
  }

  /**
   * Check if queues have pending items and sync if needed
   * Used by periodic sync to avoid unnecessary syncs
   * Public method to allow chrome.alarms.onAlarm listener to call it
   */
  async checkAndSync(): Promise<void> {
    try {
      const pendingSessions = await sessionQueueService.getPendingSessions();
      const pendingIdle = await idleQueueService.getPendingSessions();
      const pendingActivities = await activityQueueService.getPendingActivities();

      const totalPending = pendingSessions.length + pendingIdle.length + pendingActivities.length;

      if (totalPending === 0) {
        logger.debug('[SYNC SERVICE] No pending items, skipping periodic sync');
        return;
      }

      logger.info(`[SYNC SERVICE] Periodic sync triggered - Pending: ${totalPending} (sessions: ${pendingSessions.length}, idle: ${pendingIdle.length}, activities: ${pendingActivities.length})`);
      await this.syncSessions();
    } catch (error) {
      logger.error('[SYNC SERVICE] Periodic sync check failed', error);
    }
  }

  /**
   * Trigger debounced sync
   * Resets debounce timer on each call
   * This method is synchronous and handles errors internally
   */
  triggerSync(): void {
    // Clear existing debounce timer
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
      logger.debug('[SYNC SERVICE] Debounce timer reset');
    }

    // Set new debounce timer
    this.debounceTimer = setTimeout(() => {
      logger.info('[SYNC SERVICE] Debounced sync triggered');
      this.syncSessions().catch(error => {
        logger.error('[SYNC SERVICE] Debounced sync failed', error);
      });
      this.debounceTimer = null;
    }, DEBOUNCE_DELAY_MS);

    logger.debug('[SYNC SERVICE] Debounced sync scheduled in 5s');
  }

  /**
   * Synchronize pending sessions to backend
   */
  async syncSessions(): Promise<void> {
    // Prevent concurrent syncs
    if (this.isSyncing) {
      logger.info('[SYNC SERVICE] Sync already in progress, marking as pending');
      this.pendingSync = true;
      return;
    }

    try {
      this.isSyncing = true;
      this.pendingSync = false;
      logger.info('[SYNC SERVICE] Sync started');

      // Check authentication status
      const isAuth = await authService.isAuthenticated();
      if (!isAuth) {
        logger.info('[SYNC SERVICE] User not authenticated, skipping sync');
        return;
      }

      // Ensure API client has valid token
      const user = await authService.restoreSession();
      if (!user) {
        logger.info('[SYNC SERVICE] Failed to restore session, skipping sync');
        return;
      }

      logger.info(`[SYNC SERVICE] Session restored - User ID: ${user.id}, Organization ID: ${user.organization?.id}`);

      // Sync browser sessions
      await this.syncBrowserSessions();

      // Sync idle sessions
      await this.syncIdleSessions();

      // Sync activity events
      await this.syncActivities();

      // Reset retry counter on successful sync
      this.retryCounter = 0;
      logger.info('[SYNC SERVICE] Sync completed successfully');
    } catch (error: any) {
      logger.error('[SYNC SERVICE] Sync failed', error);

      // Handle retry logic for rate limiting or temporary failures
      if (this.shouldRetry(error)) {
        this.scheduleRetry(error);
      }
    } finally {
      this.isSyncing = false;

      // Check if another sync was requested during this sync
      if (this.pendingSync) {
        logger.info('[SYNC SERVICE] Pending sync detected, triggering immediately');
        this.pendingSync = false;
        this.syncSessions().catch(error => {
          logger.error('[SYNC SERVICE] Pending sync failed', error);
        });
      }
    }
  }

  /**
   * Determine if error should trigger retry
   */
  private shouldRetry(error: any): boolean {
    // Retry on HTTP 429 (Too Many Requests)
    if (error?.status === 429 || error?.response?.status === 429) {
      return true;
    }

    // Retry on network errors (no response)
    if (!error?.response && error?.message?.includes('network')) {
      return true;
    }

    // Retry on 5xx server errors
    if (error?.status >= 500 || error?.response?.status >= 500) {
      return true;
    }

    return false;
  }

  /**
   * Schedule retry with exponential backoff or Retry-After header
   */
  private scheduleRetry(error: any): void {
    let delayMs: number;

    // Check for Retry-After header
    const retryAfter = error?.response?.headers?.['retry-after'];
    if (retryAfter) {
      // Retry-After can be seconds or HTTP date
      const retryAfterSeconds = parseInt(retryAfter, 10);
      if (!isNaN(retryAfterSeconds)) {
        delayMs = retryAfterSeconds * 1000;
        logger.info(`[SYNC SERVICE] Retry-After header honored: ${retryAfterSeconds}s`);
      } else {
        // If it's a date, calculate delay from now
        const retryAfterDate = new Date(retryAfter);
        const now = new Date();
        delayMs = Math.max(0, retryAfterDate.getTime() - now.getTime());
        logger.info(`[SYNC SERVICE] Retry-After date honored: ${retryAfter}`);
      }
    } else {
      // Use exponential backoff
      const retryIndex = Math.min(this.retryCounter, RETRY_DELAYS_MS.length - 1);
      delayMs = RETRY_DELAYS_MS[retryIndex];
      this.retryCounter++;
      logger.info(`[SYNC SERVICE] Retry scheduled in ${delayMs / 1000}s (attempt ${this.retryCounter})`);
    }

    // Clear existing retry timer
    if (this.retryTimer !== null) {
      clearTimeout(this.retryTimer);
    }

    // Schedule retry
    this.retryTimer = setTimeout(() => {
      logger.info('[SYNC SERVICE] Retry executing');
      this.syncSessions().catch(error => {
        logger.error('[SYNC SERVICE] Retry failed', error);
      });
      this.retryTimer = null;
    }, delayMs);
  }

  /**
   * Synchronize pending browser sessions
   */
  private async syncBrowserSessions(): Promise<void> {
    try {
      const pendingSessions = await sessionQueueService.getPendingSessions();
      logger.info(`[SYNC SERVICE] Pending browser sessions: ${pendingSessions.length}`);

      if (pendingSessions.length === 0) {
        logger.info('[SYNC SERVICE] No pending browser sessions to sync');
        return;
      }

      // Process in batches
      const batches = this.createBatches(pendingSessions, SYNC_CONFIG.BATCH_SIZE);
      logger.info(`[SYNC SERVICE] Created ${batches.length} browser session batches for upload`);

      let successCount = 0;
      let failureCount = 0;

      for (let i = 0; i < batches.length; i++) {
        const batch = batches[i];
        logger.info(`[SYNC SERVICE] Processing browser session batch ${i + 1}/${batches.length} - Size: ${batch.length}`);

        // Log batch payload for debugging
        logger.info(
          `[SYNC SERVICE] Browser batch payload - Session IDs: ${batch.map(item => item.data.sessionId).join(', ')}, URLs: ${batch.map(item => item.data.url?.substring(0, 50) + '...').join(', ')}, Title lengths: ${batch.map(item => item.data.title?.length ?? 0).join(', ')}`
        );

        try {
          await this.uploadBatch(batch);
          successCount += batch.length;
          logger.info(`[SYNC SERVICE] Browser session batch ${i + 1} uploaded successfully - Sessions: ${batch.length}`);
        } catch (error) {
          failureCount += batch.length;
          logger.error(`[SYNC SERVICE] Browser session batch ${i + 1} upload failed - Sessions: ${batch.length}`, error);
          // Continue with next batch even if this one fails
        }
      }

      logger.info(`[SYNC SERVICE] Browser session sync completed - Success: ${successCount}, Failure: ${failureCount}`);

      // Remove successfully uploaded sessions
      if (successCount > 0) {
        await sessionQueueService.removeUploadedSessions();
        logger.info(`[SYNC SERVICE] Removed ${successCount} uploaded browser sessions from queue`);
      }
    } catch (error) {
      logger.error('[SYNC SERVICE] Browser session sync failed', error);
    }
  }

  /**
   * Synchronize pending idle sessions
   */
  private async syncIdleSessions(): Promise<void> {
    try {
      const pendingIdleSessions = await idleQueueService.getPendingSessions();
      logger.info(`[SYNC SERVICE] Pending idle sessions: ${pendingIdleSessions.length}`);

      if (pendingIdleSessions.length === 0) {
        logger.info('[SYNC SERVICE] No pending idle sessions to sync');
        return;
      }

      // Process in batches
      const batches = this.createBatches(pendingIdleSessions, SYNC_CONFIG.BATCH_SIZE);
      logger.info(`[SYNC SERVICE] Created ${batches.length} idle session batches for upload`);

      let successCount = 0;
      let failureCount = 0;

      for (let i = 0; i < batches.length; i++) {
        const batch = batches[i];
        logger.info(`[SYNC SERVICE] Processing idle session batch ${i + 1}/${batches.length} - Size: ${batch.length}`);

        // Log batch payload for debugging
        logger.info(
          `[SYNC SERVICE] Idle batch payload - Session IDs: ${batch.map(item => item.data.idleId).join(', ')}, Start times: ${batch.map(item => item.data.startTime ? new Date(item.data.startTime).toISOString() : 'null').join(', ')}, End times: ${batch.map(item => item.data.endTime ? new Date(item.data.endTime).toISOString() : 'null').join(', ')}, Durations: ${batch.map(item => `${item.data.durationSeconds}s`).join(', ')}`
        );

        try {
          await this.uploadIdleBatch(batch);
          successCount += batch.length;
          logger.info(`[SYNC SERVICE] Idle session batch ${i + 1} uploaded successfully - Sessions: ${batch.length}`);
        } catch (error) {
          failureCount += batch.length;
          logger.error(`[SYNC SERVICE] Idle session batch ${i + 1} upload failed - Sessions: ${batch.length}`, error);
          // Continue with next batch even if this one fails
        }
      }

      logger.info(`[SYNC SERVICE] Idle session sync completed - Success: ${successCount}, Failure: ${failureCount}`);

      // Remove successfully uploaded idle sessions
      if (successCount > 0) {
        await idleQueueService.removeUploadedSessions();
        logger.info(`[SYNC SERVICE] Removed ${successCount} uploaded idle sessions from queue`);
      }
    } catch (error) {
      logger.error('[SYNC SERVICE] Idle session sync failed', error);
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
   * Upload a batch of idle sessions to backend
   */
  private async uploadIdleBatch(batch: any[]): Promise<void> {
    try {
      // Convert idle queue items to backend format, filtering out invalid sessions
      const validSessions: any[] = [];
      const validItems: any[] = [];

      for (const item of batch) {
        try {
          const sessionData = this.convertIdleSessionToBackendFormat(item.data);
          validSessions.push(sessionData);
          validItems.push(item);
        } catch (error) {
          logger.warn(`[SYNC SERVICE] Skipping invalid idle session - Idle ID: ${item.data.idleId}`, error);
          // Mark invalid sessions as uploaded to remove them from queue
          await idleQueueService.markAsUploaded(item.id);
        }
      }

      if (validSessions.length === 0) {
        logger.info('[SYNC SERVICE] No valid idle sessions in batch to upload');
        return;
      }

      const payload = {
        sessions: validSessions,
      };

      logger.info(`[SYNC SERVICE] Uploading idle batch - Size: ${validSessions.length}`);
      await apiClient.post(API_ENDPOINTS.IDLE_BATCH, payload);
      logger.info('[SYNC SERVICE] Idle batch upload successful');

      // Mark valid sessions as uploaded
      for (const item of validItems) {
        await idleQueueService.markAsUploaded(item.id);
      }
    } catch (error: any) {
      // Check if error is 409 Conflict (session already exists in database)
      if (error?.status === 409 || error?.response?.status === 409) {
        logger.warn('[SYNC SERVICE] Idle batch upload failed with 409 Conflict - Sessions may already exist in database');
        // Mark all sessions in this batch as uploaded since they likely exist in database
        // This prevents infinite retry of sessions that were already inserted
        for (const item of batch) {
          try {
            await idleQueueService.markAsUploaded(item.id);
            logger.info(`[SYNC SERVICE] Marked session as uploaded due to 409 conflict - Idle ID: ${item.data.idleId}`);
          } catch (markError) {
            logger.error(`[SYNC SERVICE] Failed to mark session as uploaded - Idle ID: ${item.data.idleId}`, markError);
          }
        }
        throw error;
      }
      logger.error('[SYNC SERVICE] Idle batch upload failed', error);
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

    // Truncate fields to match backend max_length constraints
    const browserName = 'Chrome'; // Could be dynamic in future
    const url = session.url.substring(0, 2048);
    const domain = session.domain.substring(0, 255);
    const title = session.title ? session.title.substring(0, 500) : null;

    // Log if truncation occurred
    if (session.url.length > 2048) {
      logger.warn(`[SYNC SERVICE] Truncating URL from ${session.url.length} to 2048 chars - Session ID: ${session.sessionId}`);
    }
    if (session.title && session.title.length > 500) {
      logger.warn(`[SYNC SERVICE] Truncating title from ${session.title.length} to 500 chars - Session ID: ${session.sessionId}`);
    }
    if (session.domain.length > 255) {
      logger.warn(`[SYNC SERVICE] Truncating domain from ${session.domain.length} to 255 chars - Session ID: ${session.sessionId}`);
    }

    return {
      browser_name: browserName,
      website_url: url,
      website_domain: domain,
      page_title: title,
      session_start_time: new Date(session.startTime).toISOString(),
      session_end_time: new Date(session.endTime).toISOString(),
    };
  }

  /**
   * Synchronize pending activity events
   */
  private async syncActivities(): Promise<void> {
    try {
      const pendingActivities = await activityQueueService.getPendingActivities();
      logger.info(`[SYNC SERVICE] Pending activity events: ${pendingActivities.length}`);

      if (pendingActivities.length === 0) {
        logger.info('[SYNC SERVICE] No pending activity events to sync');
        return;
      }

      // Process in batches
      const batches = this.createBatches(pendingActivities, SYNC_CONFIG.BATCH_SIZE);
      logger.info(`[SYNC SERVICE] Created ${batches.length} activity event batches for upload`);

      let successCount = 0;
      let failureCount = 0;

      for (let i = 0; i < batches.length; i++) {
        const batch = batches[i];
        logger.info(`[SYNC SERVICE] Processing activity event batch ${i + 1}/${batches.length} - Size: ${batch.length}`);

        // Log batch payload for debugging
        logger.info(
          `[SYNC SERVICE] Activity batch payload - Event IDs: ${batch.map(item => item.data.id).join(', ')}, Event types: ${batch.map(item => item.data.eventType).join(', ')}`
        );

        try {
          const uploadedCount = await this.uploadActivityBatch(batch);
          successCount += uploadedCount;
          failureCount += batch.length - uploadedCount;
          logger.info(`[SYNC SERVICE] Activity event batch ${i + 1} uploaded successfully - Uploaded: ${uploadedCount}, Failed: ${batch.length - uploadedCount}`);
        } catch (error) {
          failureCount += batch.length;
          logger.error(`[SYNC SERVICE] Activity event batch ${i + 1} upload failed - Events: ${batch.length}`, error);
          // Continue with next batch even if this one fails
        }
      }

      logger.info(`[SYNC SERVICE] Activity event sync completed - Success: ${successCount}, Failure: ${failureCount}`);

      // Remove successfully uploaded activity events
      if (successCount > 0) {
        await activityQueueService.removeUploadedActivities();
        logger.info(`[SYNC SERVICE] Removed ${successCount} uploaded activity events from queue`);
      }
    } catch (error) {
      logger.error('[SYNC SERVICE] Activity event sync failed', error);
    }
  }

  /**
   * Upload a batch of activity events to backend
   */
  private async uploadActivityBatch(batch: any[]): Promise<number> {
    try {
      // Convert activity queue items to backend format, filtering out invalid events
      const validEvents: any[] = [];
      const validItems: any[] = [];

      for (const item of batch) {
        try {
          const eventData = this.convertActivityToBackendFormat(item.data);
          validEvents.push(eventData);
          validItems.push(item);
        } catch (error) {
          logger.warn(`[SYNC SERVICE] Skipping invalid activity event - Event ID: ${item.data.id}`, error);
          // Mark invalid events as uploaded to remove them from queue
          await activityQueueService.markAsUploaded(item.id);
        }
      }

      if (validEvents.length === 0) {
        logger.info('[SYNC SERVICE] No valid activity events in batch to upload');
        return 0;
      }

      const payload = {
        events: validEvents,
      };

      logger.info(`[SYNC SERVICE] Uploading activity batch - Size: ${validEvents.length}`);
      const response = await apiClient.post(API_ENDPOINTS.EVENTS_BATCH, payload);
      logger.info(`[SYNC SERVICE] Activity batch upload successful - Response: ${JSON.stringify(response.data)}`);

      // Mark valid events as uploaded
      for (const item of validItems) {
        await activityQueueService.markAsUploaded(item.id);
      }

      return validEvents.length;
    } catch (error: any) {
      logger.error('[SYNC SERVICE] Activity batch upload failed', error);
      throw error;
    }
  }

  /**
   * Convert activity event to backend format
   */
  private convertActivityToBackendFormat(activity: any): any {
    // Handle old queue entries without activity.id - generate one
    let eventId = activity.id;
    if (!eventId) {
      eventId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      logger.info(`[SYNC SERVICE] Generated event ID for old activity: ${eventId}`);
    }

    // Validate required fields
    if (!activity.eventType) {
      logger.warn(`[SYNC SERVICE] Skipping activity with missing required data - Event ID: ${eventId}, Event type: ${activity.eventType}`);
      throw new Error('Activity missing required field: eventType');
    }

    // Convert event type to uppercase to match backend validation
    const eventType = this.convertEventTypeToBackendFormat(activity.eventType);

    // Truncate fields to match backend constraints
    const browserName = (activity.browserName || 'Chrome').substring(0, 100);
    const websiteUrl = activity.url ? activity.url.substring(0, 2048) : null;
    const websiteDomain = activity.domain ? activity.domain.substring(0, 255) : null;
    const pageTitle = activity.title ? activity.title.substring(0, 500) : null;
    const previousUrl = activity.previousUrl ? activity.previousUrl.substring(0, 2048) : null;
    const previousDomain = activity.previousDomain ? activity.previousDomain.substring(0, 255) : null;

    // Log if truncation occurred
    if (activity.url && activity.url.length > 2048) {
      logger.warn(`[SYNC SERVICE] Truncating websiteUrl from ${activity.url.length} to 2048 chars - Event ID: ${eventId}`);
    }
    if (activity.title && activity.title.length > 500) {
      logger.warn(`[SYNC SERVICE] Truncating pageTitle from ${activity.title.length} to 500 chars - Event ID: ${eventId}`);
    }
    if (activity.domain && activity.domain.length > 255) {
      logger.warn(`[SYNC SERVICE] Truncating websiteDomain from ${activity.domain.length} to 255 chars - Event ID: ${eventId}`);
    }

    return {
      event_id: eventId,
      event_type: eventType,
      browser_name: browserName,
      tab_id: activity.tabId || null,
      window_id: activity.windowId || null,
      website_url: websiteUrl,
      website_domain: websiteDomain,
      page_title: pageTitle,
      previous_url: previousUrl,
      previous_domain: previousDomain,
      timestamp: activity.timestampIso || new Date(activity.timestamp).toISOString(),
      metadata: activity.metadata || null,  // Backend expects 'metadata', not 'event_metadata'
    };
  }

  /**
   * Convert extension event type to backend format (uppercase with underscores)
   */
  private convertEventTypeToBackendFormat(eventType: string): string {
    // Mapping from extension format to backend format
    const typeMapping: Record<string, string> = {
      'tab_activated': 'TAB_ACTIVATED',
      'tab_created': 'TAB_CREATED',
      'tab_removed': 'TAB_CLOSED',
      'tab_updated': 'TAB_UPDATED',
      'window_focus_changed': 'WINDOW_FOCUS_GAINED',
      'browser_startup': 'BROWSER_STARTUP',
      'extension_startup': 'BROWSER_STARTUP',
      'extension_installed': 'BROWSER_STARTUP',
    };

    // If mapping exists, use it; otherwise convert to uppercase with underscores
    if (typeMapping[eventType]) {
      return typeMapping[eventType];
    }

    // Fallback: convert to uppercase and replace hyphens with underscores
    return eventType.toUpperCase().replace(/-/g, '_');
  }

  /**
   * Convert idle session to backend format
   */
  private convertIdleSessionToBackendFormat(session: IdleSession): any {
    // Skip sessions without valid end time
    if (!session.endTime) {
      logger.warn(`[SYNC SERVICE] Skipping idle session without end time - Idle ID: ${session.idleId}`);
      throw new Error('Idle session missing end time');
    }

    // Skip sessions with invalid duration (end time must be after start time)
    if (session.endTime <= session.startTime) {
      logger.warn(`[SYNC SERVICE] Skipping idle session with invalid duration - Idle ID: ${session.idleId}, Start: ${session.startTime}, End: ${session.endTime}`);
      throw new Error('Idle session end time must be after start time');
    }

    return {
      idle_start_time: new Date(session.startTime).toISOString(),
      idle_end_time: new Date(session.endTime).toISOString(),
    };
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
