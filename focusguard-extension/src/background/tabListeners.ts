/**
 * Tab Event Listeners for FocusGuard Extension
 * Handles tab-related Chrome Extension API events
 */

import { logger } from '../utils/logger';
import { activityQueueService } from '../services/activityQueue';
import { sessionService } from '../services/session';
import { shouldTrackUrl } from '../utils/urlFilter';
import { extractUrlParts } from '../utils/url';
import type { TabActivity, TransitionType, TabStatus } from '../types/browser';

/**
 * In-memory cache for tab state to detect duplicate updates
 * Resets when service worker restarts
 */
interface TabStateCache {
  [tabId: number]: {
    url: string | null;
    title: string | null;
    status: TabStatus | null;
  };
}

const tabStateCache: TabStateCache = {};

/**
 * Generate unique ID for activity
 */
function generateActivityId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Create tab activity object
 */
function createTabActivity(
  eventType: 'tab_activated' | 'tab_created' | 'tab_removed' | 'tab_updated',
  tab: chrome.tabs.Tab,
  windowId: number | null = null
): TabActivity | null {
  // Filter internal URLs
  if (!shouldTrackUrl(tab.url)) {
    return null;
  }

  const urlParts = extractUrlParts(tab.url);

  return {
    id: generateActivityId(),
    timestamp: Date.now(),
    timestampIso: new Date().toISOString(),
    eventType,
    tabId: tab.id ?? null,
    windowId: windowId ?? tab.windowId ?? null,
    url: tab.url ?? null,
    hostname: urlParts?.hostname ?? null,
    domain: urlParts?.domain ?? null,
    title: tab.title ?? null,
    incognito: tab.incognito ?? false,
    active: tab.active ?? false,
    pinned: tab.pinned ?? false,
    audible: tab.audible ?? false,
    discarded: tab.discarded ?? false,
    status: (tab.status as TabStatus) ?? null,
    transitionType: null, // Will be set by onUpdated if available
    index: tab.index ?? null,
    userId: null, // Will be set by activityQueueService
    organizationId: null, // Will be set by activityQueueService
  };
}

/**
 * Handle tab activated event
 */
export function handleTabActivated(activeInfo: any): void {
  logger.info(`[TAB LISTENER] handleTabActivated called - Tab ID: ${activeInfo.tabId}`);
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (chrome.runtime.lastError) {
      logger.error('Error getting tab in onActivated', chrome.runtime.lastError);
      return;
    }

    const activity = createTabActivity('tab_activated', tab, activeInfo.windowId);
    if (activity) {
      logger.info(`[TAB LISTENER] About to call addActivity for tab_activated - Tab ID: ${tab.id}, URL: ${tab.url}`);
      activityQueueService.addActivity(activity);
      logger.info(`Tab activated - Tab ID: ${tab.id}, URL: ${tab.url}`);
      
      // Start session for activated tab
      sessionService.startSession(tab.id ?? null, activeInfo.windowId ?? null, tab.url ?? null, tab.title ?? null);
    } else {
      logger.info(`[TAB LISTENER] Activity is null (filtered URL) - URL: ${tab.url}`);
    }
  });
}

/**
 * Handle tab created event
 */
export function handleTabCreated(tab: chrome.tabs.Tab): void {
  logger.info(`[TAB LISTENER] handleTabCreated called - Tab ID: ${tab.id}, URL: ${tab.url}`);
  
  // Initialize cache entry for this tab
  if (tab.id !== undefined) {
    tabStateCache[tab.id] = {
      url: tab.url ?? null,
      title: tab.title ?? null,
      status: (tab.status as TabStatus) ?? null,
    };
  }
  
  const activity = createTabActivity('tab_created', tab);
  if (activity) {
    logger.info(`[TAB LISTENER] About to call addActivity for tab_created - Tab ID: ${tab.id}, URL: ${tab.url}`);
    activityQueueService.addActivity(activity);
    logger.info(`Tab created - Tab ID: ${tab.id}, URL: ${tab.url}`);
  } else {
    logger.info(`[TAB LISTENER] Activity is null (filtered URL) - URL: ${tab.url}`);
  }
}

/**
 * Handle tab removed event
 */
export function handleTabRemoved(tabId: number, removeInfo: any): void {
  logger.info(`[TAB LISTENER] handleTabRemoved called - Tab ID: ${tabId}, Window ID: ${removeInfo.windowId}`);
  
  // Clean up cache entry
  delete tabStateCache[tabId];
  
  // Close session for this tab
  sessionService.closeSession(tabId);
  
  // For tab removed, we can't get the tab object as it's already closed
  // We create a minimal activity record
  const activity: TabActivity = {
    id: generateActivityId(),
    timestamp: Date.now(),
    timestampIso: new Date().toISOString(),
    eventType: 'tab_removed',
    tabId: tabId,
    windowId: removeInfo.windowId ?? null,
    url: null,
    hostname: null,
    domain: null,
    title: null,
    incognito: false,
    active: false,
    pinned: false,
    audible: false,
    discarded: false,
    status: null,
    transitionType: null,
    index: null,
    userId: null,
    organizationId: null,
  };

  logger.info(`[TAB LISTENER] About to call addActivity for tab_removed - Tab ID: ${tabId}`);
  activityQueueService.addActivity(activity);
  logger.info(`Tab removed - Tab ID: ${tabId}, Window ID: ${removeInfo.windowId}`);
}

/**
 * Handle tab updated event
 */
export function handleTabUpdated(
  tabId: number,
  changeInfo: any,
  tab: chrome.tabs.Tab
): void {
  logger.info(`[TAB LISTENER] handleTabUpdated called - Tab ID: ${tabId}`);
  
  // Get current state from cache
  const cachedState = tabStateCache[tabId];
  const currentUrl = tab.url ?? null;
  const currentTitle = tab.title ?? null;
  const currentStatus = (tab.status as TabStatus) ?? null;
  
  // Check if this is a meaningful change
  const urlChanged = changeInfo.url && currentUrl !== cachedState?.url;
  const titleChanged = changeInfo.title && currentTitle !== cachedState?.title;
  const statusBecameComplete = changeInfo.status === 'complete' && currentStatus === 'complete' && cachedState?.status !== 'complete';
  
  // Only track if URL changed, title changed, or status became complete
  if (!urlChanged && !titleChanged && !statusBecameComplete) {
    logger.info(`[TAB LISTENER] Skipping tab update (no meaningful change) - URL changed: ${urlChanged}, Title changed: ${titleChanged}, Status became complete: ${statusBecameComplete}`);
    logger.info(`[TAB LISTENER] Cache state - Cached URL: ${cachedState?.url}, Current URL: ${currentUrl}, Cached title: ${cachedState?.title}, Current title: ${currentTitle}, Cached status: ${cachedState?.status}, Current status: ${currentStatus}`);
    
    // Update cache even if we skip the event
    if (tabId !== undefined) {
      tabStateCache[tabId] = {
        url: currentUrl,
        title: currentTitle,
        status: currentStatus,
      };
    }
    return;
  }

  // Update cache
  if (tabId !== undefined) {
    tabStateCache[tabId] = {
      url: currentUrl,
      title: currentTitle,
      status: currentStatus,
    };
  }

  // Handle URL change - switch session
  if (urlChanged) {
    logger.info(`[TAB LISTENER] URL changed, switching session - Tab ID: ${tabId}, New URL: ${currentUrl}`);
    sessionService.switchSession(tabId, tab.windowId ?? null, currentUrl, currentTitle);
  }

  const activity = createTabActivity('tab_updated', tab);
  if (activity) {
    // Set transition type if available from changeInfo
    if (changeInfo.url && 'transitionType' in changeInfo) {
      activity.transitionType = (changeInfo as any).transitionType as TransitionType;
    }
    
    logger.info(`[TAB LISTENER] About to call addActivity for tab_updated - Tab ID: ${tabId}, URL: ${tab.url}`);
    activityQueueService.addActivity(activity);
    logger.info(`Tab updated - Tab ID: ${tabId}, URL: ${tab.url}`);
  } else {
    logger.info(`[TAB LISTENER] Activity is null (filtered URL) - URL: ${tab.url}`);
  }
}

/**
 * Register all tab event listeners
 */
export function registerTabListeners(): void {
  chrome.tabs.onActivated.addListener(handleTabActivated);
  chrome.tabs.onCreated.addListener(handleTabCreated);
  chrome.tabs.onRemoved.addListener(handleTabRemoved);
  chrome.tabs.onUpdated.addListener(handleTabUpdated);
  
  logger.info('Tab event listeners registered');
}

/**
 * Unregister all tab event listeners
 */
export function unregisterTabListeners(): void {
  chrome.tabs.onActivated.removeListener(handleTabActivated);
  chrome.tabs.onCreated.removeListener(handleTabCreated);
  chrome.tabs.onRemoved.removeListener(handleTabRemoved);
  chrome.tabs.onUpdated.removeListener(handleTabUpdated);
  
  logger.info('Tab event listeners unregistered');
}
