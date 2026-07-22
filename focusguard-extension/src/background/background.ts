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
  logger.info('Background service worker initializing');

  try {
    // Register all event listeners
    registerTabListeners();
    registerWindowListeners();
    registerLifecycleListeners();

    // Handle extension startup
    handleExtensionStartup();

    // Clean up invalid idle sessions from queue (stale data from before validation fix)
    idleQueueService.cleanupInvalidSessions().then(removedCount => {
      if (removedCount > 0) {
        logger.info(`[BACKGROUND] Cleaned up ${removedCount} invalid idle sessions from queue on startup`);
      }
    }).catch(error => {
      logger.error('[BACKGROUND] Failed to cleanup invalid idle sessions', error);
    });

    // Clean up overlapping idle sessions from queue
    idleQueueService.cleanupOverlappingSessions().then(removedCount => {
      if (removedCount > 0) {
        logger.info(`[BACKGROUND] Cleaned up ${removedCount} overlapping idle sessions from queue on startup`);
      }
    }).catch(error => {
      logger.error('[BACKGROUND] Failed to cleanup overlapping idle sessions', error);
    });

    // Start periodic sync
    syncService.startPeriodicSync();

    // Start idle detection (may fail if chrome.idle is not available)
    try {
      idleService.startIdleDetection();
    } catch (error) {
      logger.error('[BACKGROUND] Failed to start idle detection', error);
      // Continue initialization even if idle detection fails
    }

    logger.info('Background service worker initialized');
  } catch (error) {
    logger.error('[BACKGROUND] Failed to initialize background service worker', error);
    // Don't throw - allow service worker to start even if some features fail
  }
}

// Handle browser shutdown
chrome.runtime.onSuspend.addListener(async () => {
  logger.info('Browser shutdown detected, ending all sessions');
  await handleBrowserShutdown();
  await sessionService.endAllSessions();
  await idleService.endAllIdleSessions();
});

// Initialize on service worker start
initializeBackground();
