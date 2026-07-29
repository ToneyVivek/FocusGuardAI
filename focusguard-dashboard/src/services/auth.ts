/**
 * Authentication Service
 * Handles authentication API calls
 */
import axios from '../api/axios';
import { isAxiosError } from 'axios';
import type { User } from '../types';
import { setAccessToken, setRefreshToken } from '../utils/auth';

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authService = {
  /**
   * Login with email and password
   * Uses OAuth2PasswordRequestForm (form-urlencoded)
   * Email is mapped to username field
   */
  login: async (email: string, password: string): Promise<{ tokens: TokenResponse; user: User }> => {
    try {
      // Send as form-urlencoded for OAuth2PasswordRequestForm
      const formData = new URLSearchParams();
      formData.append('username', email); // OAuth2 uses 'username' field for email
      formData.append('password', password);

      const response = await axios.post<TokenResponse>('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const tokens = response.data;

      // Immediately store tokens so Axios interceptor can attach Authorization header
      setAccessToken(tokens.access_token);
      setRefreshToken(tokens.refresh_token);

      // Now call /auth/me with the access token (interceptor will attach it)
      const userResponse = await axios.get<User>('/auth/me');

      return {
        tokens,
        user: userResponse.data,
      };
    } catch (error) {
      // Handle specific error cases
      if (isAxiosError(error)) {
        if (error.response?.status === 401) {
          throw new Error('Invalid email or password');
        }
        if (error.response?.status === 422) {
          const detail = error.response.data?.detail;
          if (typeof detail === 'string') {
            throw new Error(detail);
          }
          throw new Error('Invalid credentials');
        }
        if (!error.response) {
          throw new Error('Network unavailable. Please check your connection');
        }
        if (error.response?.status >= 500) {
          throw new Error('Server temporarily unavailable. Please try again later');
        }
      }
      throw new Error('Login failed. Please try again');
    }
  },

  /**
   * Get current user
   */
  getCurrentUser: async () => {
    try {
      const response = await axios.get('/auth/me');
      return response.data;
    } catch (error) {
      if (isAxiosError(error)) {
        if (error.response?.status === 401) {
          throw new Error('Session expired');
        }
      }
      throw new Error('Failed to fetch user data');
    }
  },

  /**
   * Logout (if backend supports it)
   */
  logout: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      
      // Send refresh_token in request body if available, otherwise send empty object
      const body = refreshToken ? { refresh_token: refreshToken } : {};
      
      await axios.post('/auth/logout', body);
    } catch (error) {
      // Logout should succeed even if API call fails
      console.error('Logout API call failed:', error);
    }
  },

  /**
   * Refresh token
   */
  refreshToken: async (refreshToken: string) => {
    try {
      const response = await axios.post('/auth/refresh', {
        refresh_token: refreshToken,
      });
      return response.data;
    } catch (error) {
      throw new Error('Session expired. Please log in again');
    }
  },
};
