/**
 * AIChat Component
 * Chat interface for AI productivity coach
 */
import React, { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Send, Bot, User, Loader2, Trash2, AlertCircle } from 'lucide-react';
import { aiService } from '../../services/ai';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export const AIChat: React.FC<{
  startDate?: string;
  endDate?: string;
}> = ({ startDate, endDate }) => {
  const [message, setMessage] = useState('');
  const [conversation, setConversation] = useState<Array<{ role: 'user' | 'assistant'; content: string; error?: boolean }>>([]);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [lastUserMessage, setLastUserMessage] = useState<string>('');

  const queryClient = useQueryClient();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const isUserNearBottom = useRef(true);

  // Load conversation on mount
  const { data: savedConversation } = useQuery({
    queryKey: ['ai-conversation'],
    queryFn: () => aiService.getConversation(),
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000, // 5 minutes - allows cache invalidation to work
  });

  useEffect(() => {
    console.log('[FRONTEND RESTORE] useEffect triggered');
    console.log('[FRONTEND RESTORE] savedConversation:', savedConversation);
    console.log('[FRONTEND RESTORE] conversation.length:', conversation.length);
    // Only load from saved conversation if local state is empty (first mount)
    if (savedConversation && conversation.length === 0) {
      console.log('[FRONTEND RESTORE] Loading from saved conversation');
      console.log('[FRONTEND RESTORE] Saved messages count:', savedConversation.messages.length);
      setConversation(savedConversation.messages.map(msg => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content
      })));
      setSuggestedQuestions(savedConversation.suggested_questions || []);
      // Scroll to bottom after loading
      setTimeout(() => scrollToBottom(), 100);
      console.log('[FRONTEND RESTORE] Final restored message count:', savedConversation.messages.length);
    } else if (conversation.length > 0) {
      console.log('[FRONTEND RESTORE] Skipping load - local state has messages');
    }
  }, [savedConversation, conversation.length]);

  const chatMutation = useMutation({
    mutationFn: (msg: string) => aiService.chat(msg, conversation.filter(m => !m.error), startDate, endDate),
    onSuccess: (response) => {
      console.log('[FRONTEND SUCCESS] AI response received');
      console.log('[FRONTEND SUCCESS] Message count after AI response:', conversation.length);
      console.log('[FRONTEND SUCCESS] Adding assistant message to local state');
      console.log('[FRONTEND SUCCESS] Current conversation length before update:', conversation.length);
      setConversation((prev) => [
        ...prev,
        { role: 'assistant', content: response.message },
      ]);
      setSuggestedQuestions(response.suggestions || []);
      setMessage('');
      setLastUserMessage('');
      scrollToBottom();
      console.log('[FRONTEND SUCCESS] Local state updated');
      console.log('[FRONTEND SUCCESS] Final message count:', conversation.length + 1);
      // Invalidate conversation query to refetch updated data from backend
      console.log('[FRONTEND SUCCESS] Invalidating conversation query cache');
      queryClient.invalidateQueries({ queryKey: ['ai-conversation'] });
    },
    onError: () => {
      console.log('[CHAT MUTATION] Error - adding error message');
      setConversation((prev) => [
        ...prev,
        { role: 'assistant', content: '', error: true },
      ]);
    },
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleScroll = () => {
    if (chatContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
      isUserNearBottom.current = scrollHeight - scrollTop - clientHeight < 100;
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    console.log('[FRONTEND SEND] Starting message send');
    console.log('[FRONTEND SEND] Message count before sending:', conversation.length);
    console.log('[FRONTEND SEND] User message:', message);

    setLastUserMessage(message);
    setConversation((prev) => [...prev, { role: 'user', content: message }]);
    chatMutation.mutate(message);
  };

  const handleSuggestedQuestion = (question: string) => {
    setMessage(question);
  };

  const handleClearConversation = () => {
    setShowClearConfirm(true);
  };

  const confirmClearConversation = async () => {
    console.log('[CLEAR CONVERSATION] Clearing conversation');
    await aiService.clearConversation();
    setConversation([]);
    setSuggestedQuestions([]);
    setShowClearConfirm(false);
    console.log('[CLEAR CONVERSATION] Invalidating conversation query cache');
    queryClient.invalidateQueries({ queryKey: ['ai-conversation'] });
  };

  const handleRetry = () => {
    if (lastUserMessage) {
      // Remove the error message
      setConversation((prev) => prev.slice(0, -1));
      chatMutation.mutate(lastUserMessage);
    }
  };

  const handleDismissError = () => {
    setConversation((prev) => prev.slice(0, -1));
    setLastUserMessage('');
  };

  // Auto-scroll when new messages arrive
  useEffect(() => {
    if (isUserNearBottom.current) {
      scrollToBottom();
    }
  }, [conversation.length]);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col h-[600px]">
      {/* Header */}
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="text-blue-600" size={20} />
          <h2 className="font-semibold text-gray-900">AI Productivity Coach</h2>
        </div>
        <button
          onClick={handleClearConversation}
          className="text-gray-400 hover:text-red-600 transition-colors"
          title="Clear conversation"
        >
          <Trash2 size={18} />
        </button>
      </div>

      {/* Chat Messages */}
      <div
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {conversation.length === 0 ? (
          <div className="text-center py-12">
            <Bot size={48} className="text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-2">Ask me anything about your productivity</p>
            <p className="text-sm text-gray-400">
              "How productive was I today?" or "What are my top distractions?"
            </p>
          </div>
        ) : (
          conversation.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-3 ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot size={16} className="text-blue-600" />
                </div>
              )}
              <div
                className={`max-w-[70%] rounded-lg p-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                {msg.error ? (
                  <div className="flex items-start gap-2">
                    <AlertCircle size={16} className="text-red-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-900 mb-2">⚠ Unable to generate a response.</p>
                      <div className="flex gap-2">
                        <button
                          onClick={handleRetry}
                          className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        >
                          Retry
                        </button>
                        <button
                          onClick={handleDismissError}
                          className="text-xs px-3 py-1.5 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>
                  </div>
                ) : msg.role === 'assistant' ? (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code: ({ node, inline, className, children, ...props }: any) => (
                          inline ? (
                            <code className="bg-gray-200 px-1.5 py-0.5 rounded text-sm" {...props}>
                              {children}
                            </code>
                          ) : (
                            <code className="block bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto text-sm" {...props}>
                              {children}
                            </code>
                          )
                        ),
                        pre: ({ children }: any) => (
                          <pre className="bg-gray-900 rounded-lg overflow-x-auto p-3">
                            {children}
                          </pre>
                        ),
                        h1: ({ children }: any) => (
                          <h1 className="text-lg font-bold mb-2">{children}</h1>
                        ),
                        h2: ({ children }: any) => (
                          <h2 className="text-base font-bold mb-2">{children}</h2>
                        ),
                        h3: ({ children }: any) => (
                          <h3 className="text-sm font-bold mb-1">{children}</h3>
                        ),
                        ul: ({ children }: any) => (
                          <ul className="list-disc list-inside mb-2">{children}</ul>
                        ),
                        ol: ({ children }: any) => (
                          <ol className="list-decimal list-inside mb-2">{children}</ol>
                        ),
                        li: ({ children }: any) => (
                          <li className="mb-1">{children}</li>
                        ),
                        blockquote: ({ children }: any) => (
                          <blockquote className="border-l-4 border-gray-300 pl-3 italic my-2">{children}</blockquote>
                        ),
                        table: ({ children }: any) => (
                          <div className="overflow-x-auto my-2">
                            <table className="min-w-full border border-gray-300">{children}</table>
                          </div>
                        ),
                        thead: ({ children }: any) => (
                          <thead className="bg-gray-100">{children}</thead>
                        ),
                        tbody: ({ children }: any) => (
                          <tbody>{children}</tbody>
                        ),
                        tr: ({ children }: any) => (
                          <tr className="border-b border-gray-200">{children}</tr>
                        ),
                        th: ({ children }: any) => (
                          <th className="px-3 py-2 text-left font-semibold">{children}</th>
                        ),
                        td: ({ children }: any) => (
                          <td className="px-3 py-2">{children}</td>
                        ),
                        hr: () => (
                          <hr className="my-3 border-gray-300" />
                        ),
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                  <User size={16} className="text-gray-600" />
                </div>
              )}
            </div>
          ))
        )}

        {chatMutation.isPending && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Bot size={16} className="text-blue-600" />
            </div>
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <Loader2 size={16} className="text-blue-600 animate-spin" />
                <span className="text-sm text-gray-600">🧠 Looking at your analytics...</span>
              </div>
            </div>
          </div>
        )}

        {/* Suggested Questions */}
        {suggestedQuestions.length > 0 && !chatMutation.isPending && (
          <div className="pt-4 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-2">Suggested questions:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestion(question)}
                  className="text-xs px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-100">
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={chatMutation.isPending}
          />
          <button
            type="submit"
            disabled={!message.trim() || chatMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {chatMutation.isPending ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </form>

      {/* Clear Conversation Confirmation Dialog */}
      {showClearConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4 shadow-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Clear Conversation?</h3>
            <p className="text-sm text-gray-600 mb-4">
              This will permanently remove your conversation history. This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmClearConversation}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Delete Conversation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
