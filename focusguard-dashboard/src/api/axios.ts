/**
 * Axios client configuration for FocusGuard Dashboard
 * Provides a reusable Axios instance with authentication and error handling
 */
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { authService } from '../services/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Create and configure Axios instance
 */
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

/**
 * Request interceptor
 * Automatically adds Authorization header with access token
 */
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get access token from localStorage
    const token = localStorage.getItem('access_token');
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor
 * Handles common error scenarios and token refresh
 */
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // Handle 401 Unauthorized - attempt token refresh
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (refreshToken) {
          // Attempt to refresh token using authService
          const response = await authService.refreshToken(refreshToken);
          
          const { access_token, refresh_token: new_refresh_token } = response;
          
          // Store new tokens
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', new_refresh_token);
          
          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          
          return axiosInstance(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed - clear all auth data and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    // Handle other errors
    return Promise.reject(error);
  }
);

/**
 * Centralized error handler
 */
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      // Server responded with error status
      const data = error.response.data as { detail?: string };
      return data.detail || 'An error occurred on the server';
    } else if (error.request) {
      // Request made but no response
      return 'Network error. Please check your connection';
    } else {
      // Error in request setup
      return 'An error occurred while making the request';
    }
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
};

export default axiosInstance;
