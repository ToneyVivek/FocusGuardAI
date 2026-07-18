/**
 * Custom error classes for FocusGuard Extension
 * Provides specific error types for different failure scenarios
 */

/**
 * Base extension error class
 * All custom errors should extend this
 */
export class ExtensionError extends Error {
  code?: string;

  constructor(message: string, code?: string) {
    super(message);
    this.code = code;
    this.name = 'ExtensionError';
    Object.setPrototypeOf(this, ExtensionError.prototype);
  }
}

/**
 * API-related errors
 * Used for network requests, API responses, and communication failures
 */
export class ApiError extends ExtensionError {
  statusCode?: number;
  endpoint?: string;

  constructor(message: string, statusCode?: number, endpoint?: string) {
    super(message, 'API_ERROR');
    this.statusCode = statusCode;
    this.endpoint = endpoint;
    this.name = 'ApiError';
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Storage-related errors
 * Used for Chrome storage operations
 */
export class StorageError extends ExtensionError {
  key?: string;
  operation?: 'get' | 'set' | 'remove' | 'clear';

  constructor(message: string, key?: string, operation?: 'get' | 'set' | 'remove' | 'clear') {
    super(message, 'STORAGE_ERROR');
    this.key = key;
    this.operation = operation;
    this.name = 'StorageError';
    Object.setPrototypeOf(this, StorageError.prototype);
  }
}

/**
 * Validation errors
 * Used for input validation failures
 */
export class ValidationError extends ExtensionError {
  field?: string;
  value?: unknown;

  constructor(message: string, field?: string, value?: unknown) {
    super(message, 'VALIDATION_ERROR');
    this.field = field;
    this.value = value;
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

/**
 * Network errors
 * Used for connectivity issues
 */
export class NetworkError extends ExtensionError {
  url?: string;

  constructor(message: string, url?: string) {
    super(message, 'NETWORK_ERROR');
    this.url = url;
    this.name = 'NetworkError';
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}

/**
 * Authentication errors
 * Reserved for future authentication implementation
 */
export class AuthError extends ExtensionError {
  authType?: string;

  constructor(message: string, authType?: string) {
    super(message, 'AUTH_ERROR');
    this.authType = authType;
    this.name = 'AuthError';
    Object.setPrototypeOf(this, AuthError.prototype);
  }
}
