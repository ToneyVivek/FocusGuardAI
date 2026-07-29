/**
 * Token storage and authentication utilities
 * Provides helper functions for managing JWT tokens in localStorage
 */

const TOKEN_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
} as const;

/**
 * Store access token
 */
export const setAccessToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, token);
};

/**
 * Get access token
 */
export const getAccessToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN);
};

/**
 * Remove access token
 */
export const removeAccessToken = (): void => {
  localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN);
};

/**
 * Store refresh token
 */
export const setRefreshToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, token);
};

/**
 * Get refresh token
 */
export const getRefreshToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEYS.REFRESH_TOKEN);
};

/**
 * Remove refresh token
 */
export const removeRefreshToken = (): void => {
  localStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN);
};

/**
 * Store user data
 */
export const setUserData = (userData: string): void => {
  localStorage.setItem(TOKEN_KEYS.USER_DATA, userData);
};

/**
 * Get user data
 */
export const getUserData = (): string | null => {
  return localStorage.getItem(TOKEN_KEYS.USER_DATA);
};

/**
 * Remove user data
 */
export const removeUserData = (): void => {
  localStorage.removeItem(TOKEN_KEYS.USER_DATA);
};

/**
 * Clear all authentication data
 */
export const clearAuthData = (): void => {
  removeAccessToken();
  removeRefreshToken();
  removeUserData();
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  return !!getAccessToken();
};

/**
 * Parse JWT token (without verification - for client-side use only)
 */
export const parseJWT = (token: string): { [key: string]: any } | null => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    return null;
  }
};

/**
 * Check if token is expired
 */
export const isTokenExpired = (token: string): boolean => {
  const payload = parseJWT(token);
  if (!payload || !payload.exp) {
    return true;
  }
  
  const currentTime = Math.floor(Date.now() / 1000);
  return payload.exp < currentTime;
};
