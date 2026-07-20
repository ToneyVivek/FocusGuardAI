/**
 * Authentication Context for FocusGuard Extension
 * Provides authentication state and methods to the application
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/auth';
import { logger } from '../utils/logger';
import type { AuthContextValue, AuthState } from '../types/auth';

/**
 * Default authentication state
 */
const defaultAuthState: AuthState = {
  user: null,
  organization: null,
  loading: true,
  isAuthenticated: false,
};

/**
 * Authentication Context
 */
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Auth Provider Props
 */
interface AuthProviderProps {
  children: React.ReactNode;
}

/**
 * Authentication Provider Component
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>(defaultAuthState);

  /**
   * Restore session on mount
   */
  useEffect(() => {
    const restoreSession = async () => {
      try {
        setState(prev => ({ ...prev, loading: true }));
        const user = await authService.restoreSession();
        
        if (user) {
          setState({
            user,
            organization: user.organization,
            loading: false,
            isAuthenticated: true,
          });
        } else {
          setState({
            user: null,
            organization: null,
            loading: false,
            isAuthenticated: false,
          });
        }
      } catch (error) {
        logger.error('Failed to restore session', error);
        setState({
          user: null,
          organization: null,
          loading: false,
          isAuthenticated: false,
        });
      }
    };

    restoreSession();
  }, []);

  /**
   * Login function
   */
  const login = useCallback(async (email: string, password: string) => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      const user = await authService.login(email, password);
      
      setState({
        user,
        organization: user.organization,
        loading: false,
        isAuthenticated: true,
      });
    } catch (error) {
      setState(prev => ({ ...prev, loading: false }));
      throw error;
    }
  }, []);

  /**
   * Logout function
   */
  const logout = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      await authService.logout();
      
      setState({
        user: null,
        organization: null,
        loading: false,
        isAuthenticated: false,
      });
    } catch (error) {
      logger.error('Logout failed', error);
      // Force logout even if API call fails
      setState({
        user: null,
        organization: null,
        loading: false,
        isAuthenticated: false,
      });
      throw error;
    }
  }, []);

  /**
   * Refresh function
   */
  const refresh = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      await authService.refresh();
      const user = await authService.getCurrentUser();
      
      if (user) {
        setState({
          user,
          organization: user.organization,
          loading: false,
          isAuthenticated: true,
        });
      } else {
        setState({
          user: null,
          organization: null,
          loading: false,
          isAuthenticated: false,
        });
      }
    } catch (error) {
      logger.error('Refresh failed', error);
      setState({
        user: null,
        organization: null,
        loading: false,
        isAuthenticated: false,
      });
      throw error;
    }
  }, []);

  /**
   * Context value
   */
  const contextValue: AuthContextValue = {
    ...state,
    login,
    logout,
    refresh,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use authentication context
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}
