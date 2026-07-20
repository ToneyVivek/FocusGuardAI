/**
 * Browser Activity Types for FocusGuard Extension
 * Defines types for tracking browser activity events
 */

/**
 * Browser event type enumeration
 */
export type BrowserEventType = 
  | 'tab_activated'
  | 'tab_created'
  | 'tab_removed'
  | 'tab_updated'
  | 'window_focus_changed'
  | 'browser_startup'
  | 'extension_startup'
  | 'extension_installed';

/**
 * Tab status enumeration
 */
export type TabStatus = 'loading' | 'complete' | 'unloaded';

/**
 * Transition type enumeration
 */
export type TransitionType = 
  | 'link'
  | 'typed'
  | 'auto_bookmark'
  | 'auto_subframe'
  | 'manual_subframe'
  | 'generated'
  | 'start_page'
  | 'form_submit'
  | 'reload'
  | 'keyword'
  | 'keyword_generated'
  | 'other';

/**
 * URL parts interface
 */
export interface UrlParts {
  protocol: string;
  hostname: string;
  domain: string;
  pathname: string;
  query: string;
}

/**
 * Browser event base interface
 */
export interface BrowserEvent {
  id: string;
  timestamp: number;
  timestampIso: string;
  eventType: BrowserEventType;
  tabId: number | null;
  windowId: number | null;
  userId: number | null;
  organizationId: number | null;
}

/**
 * Tab activity interface
 */
export interface TabActivity extends BrowserEvent {
  eventType: 'tab_activated' | 'tab_created' | 'tab_removed' | 'tab_updated';
  url: string | null;
  hostname: string | null;
  domain: string | null;
  title: string | null;
  incognito: boolean;
  active: boolean;
  pinned: boolean;
  audible: boolean;
  discarded: boolean;
  status: TabStatus | null;
  transitionType: TransitionType | null;
  index: number | null;
}

/**
 * Lifecycle activity interface
 */
export interface LifecycleActivity extends BrowserEvent {
  eventType: 'browser_startup' | 'extension_startup' | 'extension_installed';
}

/**
 * Window activity interface
 */
export interface WindowActivity extends BrowserEvent {
  eventType: 'window_focus_changed';
  windowId: number | null;
  focused: boolean;
}

/**
 * Browser state interface
 */
export interface BrowserState {
  activeTabId: number | null;
  activeWindowId: number | null;
  lastActivityTimestamp: number;
}

/**
 * Activity queue item interface
 */
export interface ActivityQueueItem {
  id: string;
  timestamp: number;
  eventType: BrowserEventType;
  data: TabActivity | WindowActivity | LifecycleActivity;
  uploaded: boolean;
}
