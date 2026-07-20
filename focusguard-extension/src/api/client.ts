/**
 * API Client for FocusGuard Extension
 * Provides reusable HTTP client infrastructure
 */

import { ApiError, NetworkError } from '../utils/errors';
import { logger } from '../utils/logger';
import { config } from '../config';
import { DEFAULT_HEADERS } from '../constants';
import type { ApiResponse, ApiErrorResponse, HttpMethod, RequestOptions } from '../types';

/**
 * API Client class
 * Provides typed HTTP methods for backend communication
 */
class ApiClient {
  private baseUrl: string;
  private defaultTimeout: number;
  private defaultHeaders: Record<string, string>;

  constructor() {
    this.baseUrl = config.apiBaseUrl;
    this.defaultTimeout = config.requestTimeout;
    this.defaultHeaders = DEFAULT_HEADERS;
  }

  /**
   * Set authorization header (for future JWT support)
   */
  setAuthToken(token: string): void {
    this.defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Clear authorization header
   */
  clearAuthToken(): void {
    delete this.defaultHeaders['Authorization'];
  }

  /**
   * Generic request method
   */
  async request<T = unknown>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = this.defaultTimeout,
      signal,
      contentType = 'json',
    } = options;

    const url = this.buildUrl(endpoint);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    // Combine abort signals if provided
    if (signal) {
      signal.addEventListener('abort', () => {
        controller.abort();
      });
    }

    // Prepare request headers and body based on content type
    const requestHeaders: Record<string, string> = { ...this.defaultHeaders, ...headers };
    let requestBody: string | undefined;

    if (body) {
      if (contentType === 'form-urlencoded') {
        requestHeaders['Content-Type'] = 'application/x-www-form-urlencoded';
        requestBody = new URLSearchParams(body as Record<string, string>).toString();
      } else {
        requestHeaders['Content-Type'] = 'application/json';
        requestBody = JSON.stringify(body);
      }
    }

    try {
      const response = await fetch(url, {
        method,
        headers: requestHeaders,
        body: requestBody,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        await this.handleErrorResponse(response, endpoint);
      }

      const data = await response.json();
      
      logger.debug(`API ${method} ${endpoint} success`, data);
      return {
        data,
        success: true,
      };
    } catch (error) {
      clearTimeout(timeoutId);
      this.handleRequestError(error, endpoint, method);
    }
  }

  /**
   * GET request
   */
  async get<T = unknown>(endpoint: string, options?: Omit<RequestOptions, 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T = unknown>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'method'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'POST', body });
  }

  /**
   * PUT request
   */
  async put<T = unknown>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'method'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'PUT', body });
  }

  /**
   * DELETE request
   */
  async delete<T = unknown>(endpoint: string, options?: Omit<RequestOptions, 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  /**
   * PATCH request
   */
  async patch<T = unknown>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'method'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'PATCH', body });
  }

  /**
   * Build full URL from endpoint
   */
  private buildUrl(endpoint: string): string {
    // Remove leading slash if present
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
    // Remove trailing slash from base URL if present
    const cleanBaseUrl = this.baseUrl.endsWith('/') ? this.baseUrl.slice(0, -1) : this.baseUrl;
    return `${cleanBaseUrl}/${cleanEndpoint}`;
  }

  /**
   * Handle error response from API
   */
  private async handleErrorResponse(response: Response, endpoint: string): Promise<never> {
    let errorData: ApiErrorResponse;

    try {
      errorData = await response.json();
    } catch {
      errorData = {
        error: 'Unknown Error',
        message: response.statusText || 'An error occurred',
        statusCode: response.status,
      };
    }

    logger.error(`API Error: ${endpoint}`, errorData);
    throw new ApiError(
      errorData.message,
      errorData.statusCode,
      endpoint
    );
  }

  /**
   * Handle request error (network, timeout, etc.)
   */
  private handleRequestError(error: unknown, endpoint: string, method: HttpMethod): never {
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        logger.error(`API Timeout: ${method} ${endpoint}`);
        throw new ApiError('Request timeout', undefined, endpoint);
      }
      
      logger.error(`Network Error: ${method} ${endpoint}`, error);
      throw new NetworkError(error.message, endpoint);
    }

    logger.error(`Unknown Error: ${method} ${endpoint}`, error);
    throw new NetworkError('An unknown error occurred', endpoint);
  }
}

/**
 * Singleton API client instance
 */
export const apiClient = new ApiClient();
