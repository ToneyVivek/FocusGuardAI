/**
 * Lifecycle Event Listeners for FocusGuard Extension
 * Handles extension lifecycle events (startup, install, update)
 */

import { activityQueueService } from '../services/activityQueue';
import { sessionService } from '../services/session';
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
export function handleExtensionInstalled(_details: chrome.runtime.InstalledDetails): void {
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

  activityQueueService.addActivity(activity);
}

/**
 * Handle browser startup event
 */
export function handleBrowserStartup(): void {
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

  activityQueueService.addActivity(activity);
}

/**
 * Handle browser shutdown event
 */
export async function handleBrowserShutdown(): Promise<void> {
  // End all active sessions
  await sessionService.endAllSessions();
}

/**
 * Handle extension startup event
 */
export function handleExtensionStartup(): void {
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

  activityQueueService.addActivity(activity);
}

/**
 * Register all lifecycle event listeners
 */
export function registerLifecycleListeners(): void {
  chrome.runtime.onInstalled.addListener(handleExtensionInstalled);
  
  // Browser startup is handled by chrome.runtime.onStartup
  chrome.runtime.onStartup.addListener(handleBrowserStartup);
}

/**
 * Unregister all lifecycle event listeners
 */
export function unregisterLifecycleListeners(): void {
  chrome.runtime.onInstalled.removeListener(handleExtensionInstalled);
  chrome.runtime.onStartup.removeListener(handleBrowserStartup);
}
