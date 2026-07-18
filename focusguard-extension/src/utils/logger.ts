/**
 * Logger utility for FocusGuard Extension
 * Provides structured logging with different log levels
 */

import { config } from '../config';
import type { LogLevel } from '../types';

/**
 * Logger class for structured logging
 */
class Logger {
  private enabled: boolean;

  constructor() {
    this.enabled = config.enableLogging;
  }

  /**
   * Enable or disable logging
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  /**
   * Check if logging is enabled
   */
  isEnabled(): boolean {
    return this.enabled;
  }

  /**
   * Log debug message
   */
  debug(message: string, ...args: unknown[]): void {
    if (this.enabled) {
      console.debug(`[DEBUG] ${message}`, ...args);
    }
  }

  /**
   * Log info message
   */
  info(message: string, ...args: unknown[]): void {
    if (this.enabled) {
      console.info(`[INFO] ${message}`, ...args);
    }
  }

  /**
   * Log warning message
   */
  warn(message: string, ...args: unknown[]): void {
    if (this.enabled) {
      console.warn(`[WARN] ${message}`, ...args);
    }
  }

  /**
   * Log error message
   */
  error(message: string, ...args: unknown[]): void {
    if (this.enabled) {
      console.error(`[ERROR] ${message}`, ...args);
    }
  }

  /**
   * Log message with custom level
   */
  log(level: LogLevel, message: string, ...args: unknown[]): void {
    if (!this.enabled) return;

    switch (level) {
      case 'debug':
        this.debug(message, ...args);
        break;
      case 'info':
        this.info(message, ...args);
        break;
      case 'warn':
        this.warn(message, ...args);
        break;
      case 'error':
        this.error(message, ...args);
        break;
    }
  }
}

/**
 * Singleton logger instance
 */
export const logger = new Logger();
