/**
 * TopWebsites Component
 * Displays top 5 most visited websites
 * Includes skeleton loading state and empty state
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Globe, AlertCircle } from 'lucide-react';
import { dashboardService } from '../../services/dashboard';

export const TopWebsites: React.FC = () => {
  const { data: domains, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'topDomains'],
    queryFn: () => dashboardService.getUserDomains(5),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const topDomains = domains?.domains || [];

  // Sort domains by duration DESC (defensive sort)
  const sortedDomains = [...topDomains].sort((a, b) => b.duration_seconds - a.duration_seconds);

  // Format duration
  const formatDuration = (seconds: number): string => {
    if (seconds === 0) return '0s';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    if (hours > 0) {
      if (minutes > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${hours}h`;
    }
    if (minutes > 0) {
      if (remainingSeconds > 0) {
        return `${minutes}m ${remainingSeconds}s`;
      }
      return `${minutes}m`;
    }
    return `${remainingSeconds}s`;
  };

  // Get title from domain
  const getTitleFromDomain = (domain: string): string => {
    // Remove .com, .org, etc. and capitalize
    const cleanDomain = domain.replace(/\.(com|org|net|io|co|app|dev|ai)$/, '');
    return cleanDomain
      .split('.')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Get favicon URL
  const getFaviconUrl = (domain: string): string => {
    return `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Websites</h2>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4">
              <div className="h-8 w-8 bg-gray-200 rounded"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/3"></div>
              </div>
              <div className="h-4 bg-gray-200 rounded w-1/6"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Websites</h2>
        <div className="text-center py-12">
          <AlertCircle size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">Unable to load top websites</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (topDomains.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Websites</h2>
        <div className="text-center py-12">
          <Globe size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No website data available yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Websites</h2>
      <div className="space-y-4">
        {sortedDomains.map((domain) => (
          <div key={domain.domain} className="flex items-center space-x-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
            <div className="relative shrink-0">
              <img
                src={getFaviconUrl(domain.domain)}
                alt={domain.domain}
                className="w-8 h-8 rounded"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                  (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                }}
              />
              <Globe size={32} className="text-gray-400 hidden" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{getTitleFromDomain(domain.domain)}</p>
              <p className="text-xs text-gray-500 truncate">{domain.domain}</p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-sm text-gray-600">{formatDuration(domain.duration_seconds)}</p>
              <p className="text-xs text-gray-500">{domain.session_count} visits</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
