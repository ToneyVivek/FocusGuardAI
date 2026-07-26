/**
 * Background service worker for FocusGuard Extension
 * Handles extension lifecycle events and browser activity tracking
 */

import { logger } from '../utils/logger';
import { registerTabListeners } from './tabListeners';
import { registerWindowListeners } from './windowListeners';
import { registerLifecycleListeners } from './lifecycleListeners';
import { handleExtensionStartup, handleBrowserShutdown } from './lifecycleListeners';
import { syncService } from '../services/sync';
import { idleService } from '../services/idle';
import { sessionService } from '../services/session';
import { idleQueueService } from '../services/idleQueue';

/**
 * Initialize background service worker
 */
function initializeBackground(): void {
  try {
    // Register all event listeners
    registerTabListeners();
    registerWindowListeners();
    registerLifecycleListeners();

    // Handle extension startup
    handleExtensionStartup();

    // Clean up invalid idle sessions from queue (stale data from before validation fix)
    idleQueueService.cleanupInvalidSessions().catch(error => {
      logger.error('[BACKGROUND] Failed to cleanup invalid idle sessions', error);
    });

    // Clean up overlapping idle sessions from queue
    idleQueueService.cleanupOverlappingSessions().catch(error => {
      logger.error('[BACKGROUND] Failed to cleanup overlapping idle sessions', error);
    });

    // Start periodic sync using Chrome Alarms API
    syncService.startPeriodicSync();

    // Start idle detection (may fail if chrome.idle is not available)
    try {
      idleService.startIdleDetection();
    } catch (error) {
      logger.error('[BACKGROUND] Failed to start idle detection', error);
      // Continue initialization even if idle detection fails
    }
  } catch (error) {
    logger.error('[BACKGROUND] Failed to initialize background service worker', error);
    // Don't throw - allow service worker to start even if some features fail
  }
}

// Handle alarm events for periodic sync
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'focusguard-sync-alarm') {
    logger.info('[BACKGROUND] Sync alarm triggered');
    syncService.checkAndSync().catch(error => {
      logger.error('[BACKGROUND] Sync alarm handler failed', error);
    });
  }
});

// Handle browser shutdown (best-effort only)
// Chrome MV3 does not guarantee async operations complete before termination
// All sessions are already persisted to chrome.storage.local as they end, so data is safe
chrome.runtime.onSuspend.addListener(() => {
  // Fire and forget - don't await since Chrome may terminate before completion
  handleBrowserShutdown().catch(error => {
    logger.error('[BACKGROUND] Failed to handle browser shutdown', error);
  });
  sessionService.endAllSessions().catch(error => {
    logger.error('[BACKGROUND] Failed to end sessions on shutdown', error);
  });
  idleService.endAllIdleSessions().catch(error => {
    logger.error('[BACKGROUND] Failed to end idle sessions on shutdown', error);
  });
});

// Initialize on service worker start
initializeBackground();
