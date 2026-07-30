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
        return;
      }

      // Create repeating alarm (1-minute interval)
      chrome.alarms.create(SYNC_ALARM_NAME, {
        periodInMinutes: 1, // 1 minute = 60 seconds
      }, () => {
        if (chrome.runtime.lastError) {
          logger.error('[SYNC SERVICE] Failed to create periodic sync alarm', chrome.runtime.lastError);
        }
      });
    });
  }

  /**
   * Stop periodic synchronization
   */
  stopPeriodicSync(): void {
    // Clear alarm
    chrome.alarms.clear(SYNC_ALARM_NAME, (_wasCleared) => {
      if (chrome.runtime.lastError) {
        logger.error('[SYNC SERVICE] Failed to clear periodic sync alarm', chrome.runtime.lastError);
      }
    });

    // Clear debounce timer
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }

    // Clear retry timer
    if (this.retryTimer !== null) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
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
        return;
      }

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
    }

    // Set new debounce timer
    this.debounceTimer = setTimeout(() => {
      this.syncSessions().catch(error => {
        logger.error('[SYNC SERVICE] Debounced sync failed', error);
      });
      this.debounceTimer = null;
    }, DEBOUNCE_DELAY_MS);
  }

  /**
   * Synchronize pending sessions to backend
   */
  async syncSessions(): Promise<void> {
    // Prevent concurrent syncs
    if (this.isSyncing) {
      this.pendingSync = true;
      return;
    }

    try {
      this.isSyncing = true;
      this.pendingSync = false;
      logger.info('[SYNC] Started');

      // Check authentication status
      const isAuth = await authService.isAuthenticated();
      if (!isAuth) {
        return;
      }

      // Ensure API client has valid token
      const user = await authService.restoreSession();
      if (!user) {
        return;
      }

      // Sync browser sessions
      const browserCount = await this.syncBrowserSessions();
      if (browserCount > 0) {
        logger.info(`[SYNC] Browser sessions uploaded: ${browserCount}`);
      }

      // Sync idle sessions
      const idleCount = await this.syncIdleSessions();
      if (idleCount > 0) {
        logger.info(`[SYNC] Idle sessions uploaded: ${idleCount}`);
      }

      // Sync activity events
      const activityCount = await this.syncActivities();
      if (activityCount > 0) {
        logger.info(`[SYNC] Activity events uploaded: ${activityCount}`);
      }

      // Reset retry counter on successful sync
      this.retryCounter = 0;
      logger.info('[SYNC] Sync completed');
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
      } else {
        // If it's a date, calculate delay from now
        const retryAfterDate = new Date(retryAfter);
        const now = new Date();
        delayMs = Math.max(0, retryAfterDate.getTime() - now.getTime());
      }
    } else {
      // Use exponential backoff
      const retryIndex = Math.min(this.retryCounter, RETRY_DELAYS_MS.length - 1);
      delayMs = RETRY_DELAYS_MS[retryIndex];
      this.retryCounter++;
    }

    logger.warn('[SYNC] Retry scheduled');

    // Clear existing retry timer
    if (this.retryTimer !== null) {
      clearTimeout(this.retryTimer);
    }

    // Schedule retry
    this.retryTimer = setTimeout(() => {
      this.syncSessions().catch(error => {
        logger.error('[SYNC SERVICE] Retry failed', error);
      });
      this.retryTimer = null;
    }, delayMs);
  }

  /**
   * Synchronize pending browser sessions
   */
  private async syncBrowserSessions(): Promise<number> {
    try {
      const pendingSessions = await sessionQueueService.getPendingSessions();

      if (pendingSessions.length === 0) {
        return 0;
      }

      // Process in batches
      const batches = this.createBatches(pendingSessions, SYNC_CONFIG.BATCH_SIZE);

      let successCount = 0;
      const successfullyUploadedIds: string[] = [];

      for (const batch of batches) {
        try {
          await this.uploadBatch(batch);
          successCount += batch.length;
          // Track successfully uploaded item IDs
          for (const item of batch) {
            successfullyUploadedIds.push(item.id);
          }
        } catch (error) {
          logger.error('[SYNC SERVICE] Browser session batch upload failed', error);
          // Continue with next batch even if this one fails
        }
      }

      // Remove successfully uploaded sessions
      if (successfullyUploadedIds.length > 0) {
        await sessionQueueService.removeUploadedSessionsByIds(successfullyUploadedIds);
      }

      return successCount;
    } catch (error) {
      logger.error('[SYNC SERVICE] Browser session sync failed', error);
      return 0;
    }
  }

  /**
   * Synchronize pending idle sessions
   */
  private async syncIdleSessions(): Promise<number> {
    try {
      const pendingIdleSessions = await idleQueueService.getPendingSessions();

      if (pendingIdleSessions.length === 0) {
        return 0;
      }

      // Process in batches
      const batches = this.createBatches(pendingIdleSessions, SYNC_CONFIG.BATCH_SIZE);

      let successCount = 0;
      const successfullyUploadedIds: string[] = [];

      for (const batch of batches) {
        try {
          await this.uploadIdleBatch(batch);
          successCount += batch.length;
          // Track successfully uploaded item IDs
          for (const item of batch) {
            successfullyUploadedIds.push(item.id);
          }
        } catch (error) {
          logger.error('[SYNC SERVICE] Idle session batch upload failed', error);
          // Continue with next batch even if this one fails
        }
      }

      // Remove successfully uploaded idle sessions
      if (successfullyUploadedIds.length > 0) {
        await idleQueueService.removeUploadedSessionsByIds(successfullyUploadedIds);
      }

      return successCount;
    } catch (error) {
      logger.error('[SYNC SERVICE] Idle session sync failed', error);
      return 0;
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
        } catch (error: any) {
          logger.warn(
            `[SYNC SERVICE] Skipping invalid session - URL: ${item.data.url}, Domain: ${item.data.domain}, Title: ${item.data.title || 'N/A'}, Reason: ${error.message}`
          );
          // Mark invalid sessions as uploaded to remove them from queue
          await sessionQueueService.markAsUploaded(item.id);
        }
      }

      if (validSessions.length === 0) {
        return;
      }

      const payload = {
        sessions: validSessions,
      };

      await apiClient.post(API_ENDPOINTS.ACTIVITY_BATCH, payload);

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
        } catch (error: any) {
          logger.warn(
            `[SYNC SERVICE] Skipping invalid idle session - Idle ID: ${item.data.idleId}, Start: ${item.data.startTime}, End: ${item.data.endTime}, Reason: ${error.message}`
          );
          // Mark invalid sessions as uploaded to remove them from queue
          await idleQueueService.markAsUploaded(item.id);
        }
      }

      if (validSessions.length === 0) {
        return;
      }

      const payload = {
        sessions: validSessions,
      };

      await apiClient.post(API_ENDPOINTS.IDLE_BATCH, payload);

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
          } catch (markError) {
            logger.error('[SYNC SERVICE] Failed to mark session as uploaded', markError);
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
      throw new Error('Session missing required fields: url or domain');
    }

    // Skip sessions with invalid URL protocols (backend requires http:// or https://)
    if (!session.url.startsWith('http://') && !session.url.startsWith('https://')) {
      throw new Error('Session URL must start with http:// or https://');
    }

    // Skip sessions without valid end time
    if (!session.endTime) {
      throw new Error('Session missing end time');
    }

    // Skip sessions with invalid duration (end time must be after start time)
    if (session.endTime <= session.startTime) {
      throw new Error('Session end time must be after start time');
    }

    // Validate domain format to match backend domain_normalization_service
    // Backend rejects: IP addresses, localhost, invalid formats
    const domain = session.domain.toLowerCase().trim().replace(/\.$/, '');
    
    // Reject IP addresses
    if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(domain)) {
      throw new Error(`Invalid domain format: ${session.domain} (IP address not allowed)`);
    }
    
    // Reject localhost
    if (domain === 'localhost' || domain.startsWith('localhost.')) {
      throw new Error(`Invalid domain format: ${session.domain} (localhost not allowed)`);
    }
    
    // Reject common internal/invalid domains
    const invalidDomains = ['127.0.0.1', '0.0.0.0', '[::1]', 'localhost'];
    if (invalidDomains.includes(domain)) {
      throw new Error(`Invalid domain format: ${session.domain} (internal address not allowed)`);
    }
    
    // Reject chrome://, chrome-extension://, edge://, about:, file://, devtools://
    if (session.url.match(/^(chrome|chrome-extension|edge|about|file|devtools):/)) {
      throw new Error(`Invalid URL protocol: ${session.url}`);
    }
    
    // Validate domain format using regex (matches backend validation)
    // Backend pattern: ^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$
    const domainPattern = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$/;
    if (!domainPattern.test(domain)) {
      throw new Error(`Invalid domain format: ${session.domain}`);
    }
    
    // Reject domains starting/ending with hyphen or with consecutive dots
    if (domain.startsWith('-') || domain.endsWith('-')) {
      throw new Error(`Invalid domain format: ${session.domain} (cannot start/end with hyphen)`);
    }
    if (domain.includes('..')) {
      throw new Error(`Invalid domain format: ${session.domain} (consecutive dots not allowed)`);
    }
    
    // Validate domain length (backend requires 3-255 characters)
    if (domain.length < 3 || domain.length > 255) {
      throw new Error(`Invalid domain length: ${session.domain} (must be 3-255 characters)`);
    }

    // Truncate fields to match backend max_length constraints
    const browserName = 'Chrome'; // Could be dynamic in future
    const url = session.url.substring(0, 2048);
    const normalizedDomain = domain.substring(0, 255);
    const title = session.title ? session.title.substring(0, 500) : null;

    return {
      browser_name: browserName,
      website_url: url,
      website_domain: normalizedDomain,
      page_title: title,
      session_start_time: new Date(session.startTime).toISOString(),
      session_end_time: new Date(session.endTime).toISOString(),
    };
  }

  /**
   * Synchronize pending activity events
   */
  private async syncActivities(): Promise<number> {
    try {
      const pendingActivities = await activityQueueService.getPendingActivities();

      if (pendingActivities.length === 0) {
        return 0;
      }

      // Process in batches
      const batches = this.createBatches(pendingActivities, SYNC_CONFIG.BATCH_SIZE);

      let successCount = 0;
      const successfullyUploadedIds: string[] = [];

      for (const batch of batches) {
        try {
          const uploadedCount = await this.uploadActivityBatch(batch);
          successCount += uploadedCount;
          // Track successfully uploaded item IDs
          for (const item of batch) {
            successfullyUploadedIds.push(item.id);
          }
        } catch (error) {
          logger.error('[SYNC SERVICE] Activity event batch upload failed', error);
          // Continue with next batch even if this one fails
        }
      }

      // Remove successfully uploaded activity events
      if (successfullyUploadedIds.length > 0) {
        await activityQueueService.removeUploadedActivitiesByIds(successfullyUploadedIds);
      }

      return successCount;
    } catch (error) {
      logger.error('[SYNC SERVICE] Activity event sync failed', error);
      return 0;
    }
  }

  /**
   * Upload a batch of activity events to backend
   */
  private async uploadActivityBatch(batch: any[]): Promise<number> {
    // Convert activity queue items to backend format, filtering out invalid events
    const validEvents: any[] = [];
    const validItems: any[] = [];

    for (const item of batch) {
      try {
        const eventData = this.convertActivityToBackendFormat(item.data);
        validEvents.push(eventData);
        validItems.push(item);
      } catch (error) {
        logger.warn(`[SYNC SERVICE] Skipping invalid activity event`);
        // Mark invalid events as uploaded to remove them from queue
        await activityQueueService.markAsUploaded(item.id);
      }
    }

    if (validEvents.length === 0) {
      return 0;
    }

    const payload = {
      events: validEvents,
    };

    try {
      await apiClient.post(API_ENDPOINTS.EVENTS_BATCH, payload);

      // Mark valid events as uploaded
      for (const item of validItems) {
        await activityQueueService.markAsUploaded(item.id);
      }

      return validEvents.length;
    } catch (error: any) {
      // Check if error is 409 Conflict (event already exists in database)
      if (error?.status === 409 || error?.response?.status === 409) {
        logger.warn('[SYNC SERVICE] Activity batch upload failed with 409 Conflict - Events may already exist in database');
        // Mark all events in this batch as uploaded since they likely exist in database
        // This prevents infinite retry of events that were already inserted
        for (const item of validItems) {
          try {
            await activityQueueService.markAsUploaded(item.id);
          } catch (markError) {
            logger.error('[SYNC SERVICE] Failed to mark event as uploaded', markError);
          }
        }
        throw error;
      }
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
    }

    // Validate required fields
    if (!activity.eventType) {
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
      throw new Error('Idle session missing end time');
    }

    // Skip sessions with invalid duration (end time must be after start time)
    if (session.endTime <= session.startTime) {
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
