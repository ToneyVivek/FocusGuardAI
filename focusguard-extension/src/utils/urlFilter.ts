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
  'data:',
  'javascript:',
];

/**
 * Supported protocols for tracking
 */
const SUPPORTED_PROTOCOLS = ['http://', 'https://'];

/**
 * Blocked domains (localhost, IP addresses, etc.)
 */
const BLOCKED_DOMAINS = [
  'localhost',
  '127.0.0.1',
  '0.0.0.0',
  '[::1]',
];

/**
 * Check if a URL should be tracked
 * Returns false for internal browser URLs, empty URLs, unsupported protocols, and invalid domains
 */
export function shouldTrackUrl(url: string | null | undefined): boolean {
  if (!url || url.trim() === '') {
    return false;
  }

  const lowerUrl = url.toLowerCase();

  // Check against blocked patterns
  for (const pattern of BLOCKED_PATTERNS) {
    if (lowerUrl.startsWith(pattern.toLowerCase())) {
      return false;
    }
  }

  // Check if URL starts with supported protocol
  const hasSupportedProtocol = SUPPORTED_PROTOCOLS.some(protocol =>
    lowerUrl.startsWith(protocol.toLowerCase())
  );

  if (!hasSupportedProtocol) {
    return false;
  }

  // Extract domain and validate
  try {
    const urlObj = new URL(url);
    const domain = urlObj.hostname.toLowerCase().trim().replace(/\.$/, '');

    // Check against blocked domains
    if (BLOCKED_DOMAINS.includes(domain)) {
      return false;
    }

    // Reject localhost subdomains
    if (domain.startsWith('localhost.')) {
      return false;
    }

    // Reject IP addresses (IPv4)
    if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(domain)) {
      return false;
    }

    // Validate domain format using regex (matches backend validation)
    // Backend pattern: ^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$
    const domainPattern = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$/;
    if (!domainPattern.test(domain)) {
      return false;
    }

    // Reject domains starting/ending with hyphen or with consecutive dots
    if (domain.startsWith('-') || domain.endsWith('-')) {
      return false;
    }
    if (domain.includes('..')) {
      return false;
    }

    // Validate domain length (backend requires 3-255 characters)
    if (domain.length < 3 || domain.length > 255) {
      return false;
    }
  } catch (error) {
    // Invalid URL format
    return false;
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
