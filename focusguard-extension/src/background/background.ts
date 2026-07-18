/**
 * Background service worker for FocusGuard Extension
 * Handles extension lifecycle events
 */

import { LOG_MESSAGES } from '../constants';

console.log(LOG_MESSAGES.EXTENSION_STARTED);

/**
 * Handle extension installation
 */
chrome.runtime.onInstalled.addListener(() => {
  console.log(LOG_MESSAGES.EXTENSION_INSTALLED);
});

/**
 * Handle browser startup
 */
chrome.runtime.onStartup.addListener(() => {
  console.log(LOG_MESSAGES.BROWSER_STARTED);
});
