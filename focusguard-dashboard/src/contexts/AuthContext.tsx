/**
 * Authentication Context
 * Provides authentication state and methods to the application
 */
import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { type User } from '../types';
import { 
  getAccessToken, 
  getUserData, 
  clearAuthData,
  isTokenExpired 
} from '../utils/auth';
import { authService } from '../services/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing authentication on mount and validate with backend
    const checkAuth = async () => {
      const token = getAccessToken();
      const userData = getUserData();

      if (token && userData) {
        // Check if token is expired
        if (isTokenExpired(token)) {
          clearAuthData();
          setUser(null);
          setIsLoading(false);
          return;
        }

        try {
          // Validate token by fetching current user from backend
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
          // Update stored user data with fresh data from backend
          localStorage.setItem('user_data', JSON.stringify(currentUser));
        } catch (error) {
          // Token is invalid or expired
          console.error('Session validation failed:', error);
          clearAuthData();
          setUser(null);
        }
      }
      
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = (user: User, accessToken: string, refreshToken: string) => {
    setUser(user);
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('user_data', JSON.stringify(user));
  };

  const logout = async () => {
    try {
      // Call backend logout endpoint if available
      await authService.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      // Always clear local data regardless of API call success
      setUser(null);
      clearAuthData();
    }
  };

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
    localStorage.setItem('user_data', JSON.stringify(updatedUser));
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
