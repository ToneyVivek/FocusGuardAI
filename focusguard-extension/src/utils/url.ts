/**
 * URL Processing Utilities for FocusGuard Extension
 * Extracts and processes URL components
 */

import type { UrlParts } from '../types/browser';

/**
 * Extract URL parts from a URL string
 * Ignores fragments (#)
 */
export function extractUrlParts(url: string | null | undefined): UrlParts | null {
  if (!url) {
    return null;
  }

  try {
    // Remove fragment if present
    const urlWithoutFragment = url.split('#')[0];
    const parsedUrl = new URL(urlWithoutFragment);

    return {
      protocol: parsedUrl.protocol.replace(':', ''),
      hostname: parsedUrl.hostname,
      domain: extractDomain(parsedUrl.hostname),
      pathname: parsedUrl.pathname,
      query: parsedUrl.search,
    };
  } catch (error) {
    return null;
  }
}

/**
 * Extract domain from hostname
 * Handles subdomains by extracting the main domain
 */
export function extractDomain(hostname: string): string {
  if (!hostname) {
    return '';
  }

  const parts = hostname.split('.');
  
  // Handle localhost
  if (parts.length === 1) {
    return hostname;
  }

  // Handle IP addresses
  if (/^\d+\.\d+\.\d+\.\d+$/.test(hostname)) {
    return hostname;
  }

  // Handle common TLDs (co.uk, com.au, etc.)
  const commonTlds = ['co.uk', 'com.au', 'co.nz', 'co.jp', 'co.in', 'co.za'];
  const lastTwo = parts.slice(-2).join('.');
  
  if (commonTlds.includes(lastTwo) && parts.length >= 3) {
    return parts.slice(-3).join('.');
  }

  // Standard domain extraction
  if (parts.length >= 2) {
    return parts.slice(-2).join('.');
  }

  return hostname;
}

/**
 * Check if URL is valid and parseable
 */
export function isValidUrl(url: string | null | undefined): boolean {
  if (!url) {
    return false;
  }

  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Normalize URL by removing trailing slashes and fragments
 */
export function normalizeUrl(url: string | null | undefined): string | null {
  if (!url) {
    return null;
  }

  try {
    const urlWithoutFragment = url.split('#')[0];
    const parsedUrl = new URL(urlWithoutFragment);
    
    // Remove trailing slash from pathname
    const pathname = parsedUrl.pathname.replace(/\/$/, '');
    
    return `${parsedUrl.protocol}//${parsedUrl.hostname}${pathname}${parsedUrl.search}`;
  } catch {
    return url;
  }
}

/**
 * Get hostname from URL
 */
export function getHostname(url: string | null | undefined): string | null {
  const parts = extractUrlParts(url);
  return parts?.hostname ?? null;
}

/**
 * Get domain from URL
 */
export function getDomain(url: string | null | undefined): string | null {
  const parts = extractUrlParts(url);
  return parts?.domain ?? null;
}

/**
 * Get protocol from URL
 */
export function getProtocol(url: string | null | undefined): string | null {
  const parts = extractUrlParts(url);
  return parts?.protocol ?? null;
}

/**
 * Get pathname from URL
 */
export function getPathname(url: string | null | undefined): string | null {
  const parts = extractUrlParts(url);
  return parts?.pathname ?? null;
}

/**
 * Get query string from URL
 */
export function getQuery(url: string | null | undefined): string | null {
  const parts = extractUrlParts(url);
  return parts?.query ?? null;
}
