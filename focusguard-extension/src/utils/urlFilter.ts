/**
 * URL Filtering Utilities for FocusGuard Extension
 * Filters out internal browser URLs that should not be tracked
 */

/**
 * Blocked URL patterns
 */
const BLOCKED_PATTERNS = [
  'chrome://',
  'edge://',
  'about:',
  'devtools://',
  'chrome-extension://',
  'view-source:',
  'file://',
  'moz-extension://',
  'opera://',
  'brave://',
  'vivaldi://',
];

/**
 * Check if a URL should be tracked
 * Returns false for internal browser URLs
 */
export function shouldTrackUrl(url: string | null | undefined): boolean {
  if (!url) {
    return false;
  }

  const lowerUrl = url.toLowerCase();

  // Check against blocked patterns
  for (const pattern of BLOCKED_PATTERNS) {
    if (lowerUrl.startsWith(pattern.toLowerCase())) {
      return false;
    }
  }

  return true;
}

/**
 * Check if URL is an internal browser URL
 */
export function isInternalUrl(url: string | null | undefined): boolean {
  return !shouldTrackUrl(url);
}

/**
 * Get list of blocked patterns
 */
export function getBlockedPatterns(): readonly string[] {
  return BLOCKED_PATTERNS;
}

/**
 * Add custom blocked pattern (for future extensibility)
 */
export function addBlockedPattern(pattern: string): void {
  if (!BLOCKED_PATTERNS.includes(pattern)) {
    BLOCKED_PATTERNS.push(pattern);
  }
}

/**
 * Remove blocked pattern (for future extensibility)
 */
export function removeBlockedPattern(pattern: string): void {
  const index = BLOCKED_PATTERNS.indexOf(pattern);
  if (index > -1) {
    BLOCKED_PATTERNS.splice(index, 1);
  }
}
