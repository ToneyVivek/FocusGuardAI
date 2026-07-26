/**
 * Window Event Listeners for FocusGuard Extension
 * Handles window-related Chrome Extension API events
 */

import { activityQueueService } from '../services/activityQueue';
import { sessionService } from '../services/session';
import { syncService } from '../services/sync';
import type { WindowActivity } from '../types/browser';

/**
 * Generate unique ID for activity
 */
function generateActivityId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Handle window focus changed event
 */
export function handleWindowFocusChanged(windowId: number): void {
  // chrome.windows.WINDOW_ID_NONE (-1) indicates no window is focused
  if (windowId === chrome.windows.WINDOW_ID_NONE) {
    // No window is focused, we can still log this event
    const activity: WindowActivity = {
      id: generateActivityId(),
      timestamp: Date.now(),
      timestampIso: new Date().toISOString(),
      eventType: 'window_focus_changed',
      tabId: null,
      windowId: null,
      focused: false,
      userId: null, // Will be set by activityQueueService
      organizationId: null, // Will be set by activityQueueService
    };

    activityQueueService.addActivity(activity);
    
    // End current session when window loses focus
    sessionService.endSession('window_focus_lost');
    return;
  }

  const activity: WindowActivity = {
    id: generateActivityId(),
    timestamp: Date.now(),
    timestampIso: new Date().toISOString(),
    eventType: 'window_focus_changed',
    tabId: null,
    windowId: windowId,
    focused: true,
    userId: null, // Will be set by activityQueueService
    organizationId: null, // Will be set by activityQueueService
  };

  activityQueueService.addActivity(activity);

  // Trigger debounced sync when browser regains focus
  syncService.triggerSync();
}

/**
 * Register all window event listeners
 */
export function registerWindowListeners(): void {
  chrome.windows.onFocusChanged.addListener(handleWindowFocusChanged);
}

/**
 * Unregister all window event listeners
 */
export function unregisterWindowListeners(): void {
  chrome.windows.onFocusChanged.removeListener(handleWindowFocusChanged);
}
