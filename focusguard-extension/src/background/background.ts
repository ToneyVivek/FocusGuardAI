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

/**
 * Initialize background service worker
 */
function initializeBackground(): void {
  logger.info('Background service worker initializing');

  // Register all event listeners
  registerTabListeners();
  registerWindowListeners();
  registerLifecycleListeners();

  // Handle extension startup
  handleExtensionStartup();

  // Start periodic sync
  syncService.startPeriodicSync();

  logger.info('Background service worker initialized');
}

// Handle browser shutdown
chrome.runtime.onSuspend.addListener(async () => {
  logger.info('Browser shutdown detected, ending all sessions');
  await handleBrowserShutdown();
});

// Initialize on service worker start
initializeBackground();
