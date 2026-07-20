/**
 * Lifecycle Event Listeners for FocusGuard Extension
 * Handles extension lifecycle events (startup, install, update)
 */

import { logger } from '../utils/logger';
import { activityQueueService } from '../services/activityQueue';
import type { LifecycleActivity } from '../types/browser';

/**
 * Generate unique ID for activity
 */
function generateActivityId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Handle extension installed event
 */
export function handleExtensionInstalled(details: chrome.runtime.InstalledDetails): void {
  logger.info(`[LIFECYCLE LISTENER] handleExtensionInstalled called - Reason: ${details.reason}`);

  // Create lifecycle activity record
  const activity: LifecycleActivity = {
    id: generateActivityId(),
    timestamp: Date.now(),
    timestampIso: new Date().toISOString(),
    eventType: 'extension_installed',
    tabId: null,
    windowId: null,
    userId: null, // Will be set by activityQueueService
    organizationId: null, // Will be set by activityQueueService
  };

  logger.info('[LIFECYCLE LISTENER] About to call addActivity for extension_installed');
  activityQueueService.addActivity(activity);

  // Log installation reason
  switch (details.reason) {
    case 'install':
      logger.info('Extension installed for the first time');
      break;
    case 'update':
      logger.info(`Extension updated - Previous version: ${details.previousVersion}`);
      break;
    case 'chrome_update':
      logger.info('Chrome updated, extension reloaded');
      break;
    case 'shared_module_update':
      logger.info('Shared module updated, extension reloaded');
      break;
    default:
      logger.info(`Extension installed with unknown reason - Reason: ${details.reason}`);
  }
}

/**
 * Handle browser startup event
 */
export function handleBrowserStartup(): void {
  logger.info('[LIFECYCLE LISTENER] handleBrowserStartup called');

  // Create lifecycle activity record
  const activity: LifecycleActivity = {
    id: generateActivityId(),
    timestamp: Date.now(),
    timestampIso: new Date().toISOString(),
    eventType: 'browser_startup',
    tabId: null,
    windowId: null,
    userId: null, // Will be set by activityQueueService
    organizationId: null, // Will be set by activityQueueService
  };

  logger.info('[LIFECYCLE LISTENER] About to call addActivity for browser_startup');
  activityQueueService.addActivity(activity);
}

/**
 * Handle extension startup event
 */
export function handleExtensionStartup(): void {
  logger.info('[LIFECYCLE LISTENER] handleExtensionStartup called');

  // Create lifecycle activity record
  const activity: LifecycleActivity = {
    id: generateActivityId(),
    timestamp: Date.now(),
    timestampIso: new Date().toISOString(),
    eventType: 'extension_startup',
    tabId: null,
    windowId: null,
    userId: null, // Will be set by activityQueueService
    organizationId: null, // Will be set by activityQueueService
  };

  logger.info('[LIFECYCLE LISTENER] About to call addActivity for extension_startup');
  activityQueueService.addActivity(activity);
}

/**
 * Register all lifecycle event listeners
 */
export function registerLifecycleListeners(): void {
  chrome.runtime.onInstalled.addListener(handleExtensionInstalled);
  
  // Browser startup is handled by chrome.runtime.onStartup
  chrome.runtime.onStartup.addListener(handleBrowserStartup);
  
  logger.info('Lifecycle event listeners registered');
}

/**
 * Unregister all lifecycle event listeners
 */
export function unregisterLifecycleListeners(): void {
  chrome.runtime.onInstalled.removeListener(handleExtensionInstalled);
  chrome.runtime.onStartup.removeListener(handleBrowserStartup);
  
  logger.info('Lifecycle event listeners unregistered');
}
