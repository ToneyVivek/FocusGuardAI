/**
 * Background service worker for FocusGuard Extension
 * Handles extension lifecycle events and browser activity tracking
 */

import { logger } from '../utils/logger';
import { registerTabListeners } from './tabListeners';
import { registerWindowListeners } from './windowListeners';
import { registerLifecycleListeners } from './lifecycleListeners';
import { handleExtensionStartup } from './lifecycleListeners';

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

  logger.info('Background service worker initialized');
}

// Initialize on service worker start
initializeBackground();
