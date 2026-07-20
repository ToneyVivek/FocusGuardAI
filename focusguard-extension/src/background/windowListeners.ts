/**
 * Window Event Listeners for FocusGuard Extension
 * Handles window-related Chrome Extension API events
 */

import { logger } from '../utils/logger';
import { activityQueueService } from '../services/activityQueue';
import { sessionService } from '../services/session';
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
  logger.info(`[WINDOW LISTENER] handleWindowFocusChanged called - Window ID: ${windowId}`);
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

    logger.info('[WINDOW LISTENER] About to call addActivity for window_focus_lost');
    activityQueueService.addActivity(activity);
    logger.info('Window focus lost (no window focused)');
    
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

  logger.info('[WINDOW LISTENER] About to call addActivity for window_focus_changed');
  activityQueueService.addActivity(activity);
  logger.info(`Window focus changed - Window ID: ${windowId}, Focused: true`);
}

/**
 * Register all window event listeners
 */
export function registerWindowListeners(): void {
  chrome.windows.onFocusChanged.addListener(handleWindowFocusChanged);
  
  logger.info('Window event listeners registered');
}

/**
 * Unregister all window event listeners
 */
export function unregisterWindowListeners(): void {
  chrome.windows.onFocusChanged.removeListener(handleWindowFocusChanged);
  
  logger.info('Window event listeners unregistered');
}
