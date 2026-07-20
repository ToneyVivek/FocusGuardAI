/**
 * Authentication types for FocusGuard Extension
 * Defines all authentication-related interfaces and types
 */

/**
 * Login request interface
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Organization interface
 */
export interface Organization {
  id: number;
  name: string;
  slug: string;
}

/**
 * User interface
 */
export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  role: string;
  organization: Organization;
}

/**
 * Token pair interface
 */
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Login response interface
 * Backend returns only tokens, user is fetched separately via /auth/me
 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Refresh token response interface
 */
export interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Authenticated user session interface
 */
export interface AuthenticatedUser {
  user: User;
  access_token: string;
  refresh_token: string;
  expires_at: number;
}

/**
 * Session state interface
 */
export interface Session {
  authenticated: boolean;
  user: User | null;
  expires_at: number | null;
}

/**
 * Authentication state interface for context
 */
export interface AuthState {
  user: User | null;
  organization: Organization | null;
  loading: boolean;
  isAuthenticated: boolean;
}

/**
 * Authentication context value interface
 */
export interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}
