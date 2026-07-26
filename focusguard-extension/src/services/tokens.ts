/**
 * Token Management Service for FocusGuard Extension
 * Handles JWT token storage and validation
 */

import { storageService } from './storage';
import { logger } from '../utils/logger';
import { STORAGE_KEYS } from '../constants';
import type { TokenPair } from '../types/auth';

/**
 * Token storage interface
 */
interface StoredTokens {
  access_token: string;
  refresh_token: string;
  expires_at: number;
}

/**
 * Token management service
 */
class TokenService {
  /**
   * Save tokens to storage
   */
  async saveTokens(tokenPair: TokenPair, expiresIn: number = 3600): Promise<void> {
    try {
      const expiresAt = Date.now() + expiresIn * 1000;
      const storedTokens: StoredTokens = {
        access_token: tokenPair.access_token,
        refresh_token: tokenPair.refresh_token,
        expires_at: expiresAt,
      };

      await storageService.set(STORAGE_KEYS.ACCESS_TOKEN, tokenPair.access_token);
      await storageService.set(STORAGE_KEYS.REFRESH_TOKEN, tokenPair.refresh_token);
      await storageService.set(STORAGE_KEYS.USER_DATA, storedTokens);
    } catch (error) {
      logger.error('Failed to save tokens', error);
      throw error;
    }
  }

  /**
   * Load tokens from storage
   */
  async loadTokens(): Promise<StoredTokens | null> {
    try {
      const storedTokens = await storageService.get<StoredTokens>(STORAGE_KEYS.USER_DATA);
      return storedTokens;
    } catch (error) {
      logger.error('Failed to load tokens', error);
      return null;
    }
  }

  /**
   * Get access token
   */
  async getAccessToken(): Promise<string | null> {
    try {
      return await storageService.get<string>(STORAGE_KEYS.ACCESS_TOKEN);
    } catch (error) {
      logger.error('Failed to get access token', error);
      return null;
    }
  }

  /**
   * Get refresh token
   */
  async getRefreshToken(): Promise<string | null> {
    try {
      return await storageService.get<string>(STORAGE_KEYS.REFRESH_TOKEN);
    } catch (error) {
      logger.error('Failed to get refresh token', error);
      return null;
    }
  }

  /**
   * Remove all tokens from storage
   */
  async removeTokens(): Promise<void> {
    try {
      await storageService.remove(STORAGE_KEYS.ACCESS_TOKEN);
      await storageService.remove(STORAGE_KEYS.REFRESH_TOKEN);
      await storageService.remove(STORAGE_KEYS.USER_DATA);
    } catch (error) {
      logger.error('Failed to remove tokens', error);
      throw error;
    }
  }

  /**
   * Check if access token is expired
   */
  async isTokenExpired(): Promise<boolean> {
    try {
      const storedTokens = await this.loadTokens();
      if (!storedTokens) {
        return true;
      }
      return Date.now() >= storedTokens.expires_at;
    } catch (error) {
      logger.error('Failed to check token expiration', error);
      return true;
    }
  }

  /**
   * Get token expiration time
   */
  async getExpirationTime(): Promise<number | null> {
    try {
      const storedTokens = await this.loadTokens();
      return storedTokens?.expires_at ?? null;
    } catch (error) {
      logger.error('Failed to get expiration time', error);
      return null;
    }
  }

  /**
   * Check if tokens exist
   */
  async hasTokens(): Promise<boolean> {
    try {
      const accessToken = await this.getAccessToken();
      const refreshToken = await this.getRefreshToken();
      return accessToken !== null && refreshToken !== null;
    } catch (error) {
      logger.error('Failed to check token existence', error);
      return false;
    }
  }
}

/**
 * Singleton token service instance
 */
export const tokenService = new TokenService();
