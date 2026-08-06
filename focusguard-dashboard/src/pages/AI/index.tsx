/**
 * AI Coach Page
 * Main AI Coach dashboard with daily/weekly summaries, insights, recommendations, and chat
 */
import React, { useState } from 'react';
import { DailySummaryCard } from '../../components/ai/DailySummaryCard';
import { WeeklySummaryCard } from '../../components/ai/WeeklySummaryCard';
import { AIInsights } from '../../components/ai/AIInsights';
import { AIRecommendations } from '../../components/ai/AIRecommendations';
import { AIChat } from '../../components/ai/AIChat';
import { Bot, Lightbulb, MessageSquare, TrendingUp } from 'lucide-react';

export const AIPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'chat'>('dashboard');

  return (
    <div className="min-h-0">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">AI Coach</h1>
        <p className="text-gray-600">Get personalized productivity insights and recommendations</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors ${
            activeTab === 'dashboard'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <Bot size={18} />
          Dashboard
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors ${
            activeTab === 'chat'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <MessageSquare size={18} />
          Chat
        </button>
      </div>

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {/* Daily and Weekly Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <DailySummaryCard />
            <WeeklySummaryCard />
          </div>

          {/* Insights Section */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="text-yellow-500" size={20} />
              <h2 className="text-lg font-semibold text-gray-900">Insights</h2>
            </div>
            <AIInsights />
          </div>

          {/* Recommendations Section */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="text-green-500" size={20} />
              <h2 className="text-lg font-semibold text-gray-900">Recommendations</h2>
            </div>
            <AIRecommendations />
          </div>
        </div>
      )}

      {/* Chat Tab */}
      {activeTab === 'chat' && (
        <AIChat />
      )}
    </div>
  );
};
