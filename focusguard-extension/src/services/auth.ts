/**
 * Authentication Service for FocusGuard Extension
 * Handles all authentication operations using the API client
 * with offline-first behavior to preserve session during network failures
 */

import { apiClient } from '../api/client';
import { tokenService } from './tokens';
import { storageService } from './storage';
import { logger } from '../utils/logger';
import { AuthError, ApiError } from '../utils/errors';
import { API_ENDPOINTS, STORAGE_KEYS } from '../constants';
import type { LoginResponse, RefreshResponse, User } from '../types/auth';

/**
 * Authentication service
 */
class AuthService {
  /**
   * Determine if an error is a network failure (vs authentication failure)
   * Network failures should preserve session, auth failures should clear it
   */
  private isNetworkError(error: any): boolean {
    // TypeError with "Failed to fetch" indicates network failure
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      return true;
    }

    // No response object typically indicates network failure
    if (!error.response && error.message) {
      const message = error.message.toLowerCase();
      if (message.includes('network') ||
          message.includes('connection') ||
          message.includes('timeout') ||
          message.includes('fetch')) {
        return true;
      }
    }

    return false;
  }

  /**
   * Determine if an error is an authentication failure
   * Auth failures should clear the session
   */
  private isAuthError(error: any): boolean {
    // HTTP 401 Unauthorized
    if (error.status === 401 || error.response?.status === 401) {
      return true;
    }

    // HTTP 403 Forbidden
    if (error.status === 403 || error.response?.status === 403) {
      return true;
    }

    // ApiError with auth-related status
    if (error instanceof ApiError && (error.statusCode === 401 || error.statusCode === 403)) {
      return true;
    }

    return false;
  }
  /**
   * Login with email and password
   * Uses OAuth2PasswordRequestForm (form-urlencoded)
   * Fetches user data separately via /auth/me
   */
  async login(email: string, password: string): Promise<User> {
    try {
      logger.info('[AUTH] Attempting login', { email, endpoint: API_ENDPOINTS.LOGIN });

      // Send login request as form-urlencoded (OAuth2PasswordRequestForm format)
      const formData = {
        username: email,
        password: password,
      };

      logger.info('[AUTH] Sending login request', {
        endpoint: API_ENDPOINTS.LOGIN,
        contentType: 'form-urlencoded',
        formData: { username: email, password: '***' },
      });

      const response = await apiClient.post<LoginResponse>(
        API_ENDPOINTS.LOGIN,
        formData,
        { contentType: 'form-urlencoded' }
      );

      logger.info('[AUTH] Login API response received', {
        hasAccessToken: !!response.data.access_token,
        hasRefreshToken: !!response.data.refresh_token,
        tokenType: response.data.token_type,
      });

      // Save tokens with 1 hour expiration (default)
      await tokenService.saveTokens({
        access_token: response.data.access_token,
        refresh_token: response.data.refresh_token,
        token_type: response.data.token_type,
      });

      logger.info('[AUTH] Tokens saved successfully');

      // Set auth token in API client
      apiClient.setAuthToken(response.data.access_token);

      logger.info('[AUTH] Auth token set in API client');

      // Fetch user data from /auth/me
      logger.info('[AUTH] Fetching user data from /auth/me');
      const userResponse = await apiClient.get<User>(API_ENDPOINTS.ME);
      const user = userResponse.data;

      logger.info('[AUTH] User data received', { userId: user.id, email: user.email });

      // Save user data
      await storageService.set(STORAGE_KEYS.USER_DATA, user);

      logger.info('[AUTH] User data saved to storage', { userId: user.id });
      logger.info('Login successful', { userId: user.id });
      return user;
    } catch (error) {
      logger.error('[AUTH] Login failed', {
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      });
      if (error instanceof ApiError) {
        throw new AuthError(error.message, 'login');
      }
      throw new AuthError('Login failed', 'login');
    }
  }

  /**
   * Logout and clear session
   */
  async logout(): Promise<void> {
    try {
      const accessToken = await tokenService.getAccessToken();
      
      if (accessToken) {
        try {
          const refreshToken = await tokenService.getRefreshToken();
          const requestBody = refreshToken ? { refresh_token: refreshToken } : {};
          await apiClient.post(API_ENDPOINTS.LOGOUT, requestBody);
          logger.info('Logout successful');
        } catch (error) {
          // Continue with logout even if API call fails
          logger.warn('Logout API call failed, clearing local session', error);
        }
      }

      // Clear tokens and user data
      await this.clearSession();
    } catch (error) {
      logger.error('Logout failed', error);
      throw new AuthError('Logout failed', 'logout');
    }
  }

  /**
   * Refresh access token
   */
  async refresh(): Promise<string> {
    try {
      const refreshToken = await tokenService.getRefreshToken();

      if (!refreshToken) {
        throw new AuthError('No refresh token available', 'refresh');
      }

      const response = await apiClient.post<RefreshResponse>(API_ENDPOINTS.REFRESH, {
        refresh_token: refreshToken,
      });

      // Update tokens
      await tokenService.saveTokens({
        access_token: response.data.access_token,
        refresh_token: response.data.refresh_token,
        token_type: response.data.token_type,
      });

      // Update auth token in API client
      apiClient.setAuthToken(response.data.access_token);

      logger.info('Token refresh successful');
      return response.data.access_token;
    } catch (error) {
      logger.error('Token refresh failed', error);

      // Preserve session on network errors
      if (this.isNetworkError(error)) {
        logger.warn('[AUTH] Network unavailable during token refresh - keeping existing session');
        throw new AuthError('Network unavailable during token refresh', 'network');
      }

      // Clear session on authentication errors
      if (this.isAuthError(error)) {
        logger.warn('[AUTH] Authentication invalid during token refresh - clearing session');
        await this.clearSession();
        throw new AuthError('Token refresh failed - authentication invalid', 'refresh');
      }

      // Clear session on other errors
      await this.clearSession();
      throw new AuthError('Token refresh failed', 'refresh');
    }
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User | null> {
    try {
      const user = await storageService.get<User>(STORAGE_KEYS.USER_DATA);
      return user;
    } catch (error) {
      logger.error('Failed to get current user', error);
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    try {
      const hasTokens = await tokenService.hasTokens();
      const isExpired = await tokenService.isTokenExpired();
      return hasTokens && !isExpired;
    } catch (error) {
      logger.error('Failed to check authentication status', error);
      return false;
    }
  }

  /**
   * Clear session data
   */
  async clearSession(): Promise<void> {
    try {
      await tokenService.removeTokens();
      await storageService.remove(STORAGE_KEYS.USER_DATA);
      apiClient.clearAuthToken();
      logger.info('Session cleared');
    } catch (error) {
      logger.error('Failed to clear session', error);
      throw error;
    }
  }

  /**
   * Restore session from storage
   * Fetches fresh user data via /auth/me after obtaining valid access token
   * Preserves session on network errors to enable offline-first behavior
   */
  async restoreSession(): Promise<User | null> {
    try {
      const isAuth = await this.isAuthenticated();

      if (!isAuth) {
        // Try to refresh if expired but refresh token exists
        const hasRefreshToken = await tokenService.getRefreshToken();
        if (hasRefreshToken) {
          await this.refresh();
          // Fetch fresh user data after refresh
          const userResponse = await apiClient.get<User>(API_ENDPOINTS.ME);
          const user = userResponse.data;
          await storageService.set(STORAGE_KEYS.USER_DATA, user);
          return user;
        }
        return null;
      }

      // Set auth token in API client
      const accessToken = await tokenService.getAccessToken();
      if (accessToken) {
        apiClient.setAuthToken(accessToken);
      }

      // Fetch fresh user data from /auth/me
      const userResponse = await apiClient.get<User>(API_ENDPOINTS.ME);
      const user = userResponse.data;
      await storageService.set(STORAGE_KEYS.USER_DATA, user);

      return user;
    } catch (error) {
      logger.error('Failed to restore session', error);

      // Preserve session on network errors - return cached user data
      if (this.isNetworkError(error)) {
        logger.warn('[AUTH] Network unavailable during session restore - keeping existing session');
        const cachedUser = await this.getCurrentUser();
        if (cachedUser) {
          logger.info('[AUTH] Returning cached user data for offline mode');
          return cachedUser;
        }
        return null;
      }

      // Clear session on authentication errors
      if (this.isAuthError(error)) {
        logger.warn('[AUTH] Authentication invalid during session restore - clearing session');
        await this.clearSession();
        return null;
      }

      // Clear session on other errors
      await this.clearSession();
      return null;
    }
  }
}

/**
 * Singleton authentication service instance
 */
export const authService = new AuthService();
