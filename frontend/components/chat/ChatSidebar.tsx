'use client';

import { useEffect, useState, useRef } from 'react';
import { useChat } from '@/hooks/useChat';
import { useAuth } from '@/lib/auth';
import { useTasks } from '@/hooks/useTasks';
import { useProjects } from '@/hooks/useProjects';
import type { DraftTask, ToolCall } from '@/types';
import { X, Plus, MessageSquare, Send, Loader2, Sparkles, AlertCircle } from 'lucide-react';
import { cn, formatRelativeTime } from '@/lib/utils';
import ChatMessage from './ChatMessage';
import DraftTaskApproval from './DraftTaskApproval';

interface ChatSidebarProps {
  onClose: () => void;
}

export default function ChatSidebar({ onClose }: ChatSidebarProps) {
  const { user } = useAuth();
  const { currentProject } = useProjects();
  const { createTask, fetchTasks } = useTasks();
  const {
    conversations,
    currentConversation,
    messages,
    isLoading,
    isSending,
    error,
    fetchConversations,
    selectConversation,
    sendMessage,
    clearMessages,
  } = useChat();

  const [input, setInput] = useState('');
  const [showConversations, setShowConversations] = useState(true);
  const [draftTasks, setDraftTasks] = useState<DraftTask[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Extract draft tasks from tool calls in messages
  useEffect(() => {
    const newDrafts: DraftTask[] = [];
    messages.forEach((msg) => {
      const toolCalls = msg.message_metadata?.tool_calls as ToolCall[] | undefined;
      if (toolCalls) {
        toolCalls.forEach((call) => {
          // Check if this is an add_task call that should be shown as draft
          if (call.name === 'add_task' && call.arguments) {
            const existingDraft = draftTasks.find(
              (d) => d.title === call.arguments.title
            );
            if (!existingDraft) {
              // Task was already created by agent, no need to add to drafts
            }
          }
        });
      }
    });
  }, [messages, draftTasks]);

  const handleSend = async () => {
    if (!input.trim() || !user) return;

    const message = input.trim();
    setInput('');

    try {
      const response = await sendMessage(user.id, message);
      setShowConversations(false);

      // Refresh tasks if any task-related operations were performed
      if (response.tool_calls && currentProject) {
        const hasTaskOps = response.tool_calls.some((call) =>
          ['add_task', 'update_task', 'complete_task', 'delete_task'].includes(
            call.name || ''
          )
        );
        if (hasTaskOps) {
          fetchTasks(currentProject.id);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    clearMessages();
    setDraftTasks([]);
    setShowConversations(true);
  };

  const handleApproveDraft = async (draft: DraftTask) => {
    if (!currentProject) return;

    await createTask({
      title: draft.title,
      description: draft.description,
      project_id: draft.project_id || currentProject.id,
    });

    setDraftTasks((prev) =>
      prev.map((d) => (d.id === draft.id ? { ...d, status: 'approved' as const } : d))
    );

    // Refresh tasks
    fetchTasks(currentProject.id);
  };

  const handleRejectDraft = (draftId: string) => {
    setDraftTasks((prev) =>
      prev.map((d) => (d.id === draftId ? { ...d, status: 'rejected' as const } : d))
    );
  };

  const handleEditDraft = (draft: DraftTask) => {
    // Pre-fill input with edit instructions
    setInput(`Edit task "${draft.title}": `);
  };

  // Quick action suggestions
  const suggestions = [
    'List my tasks',
    'Add a new task',
    'What tasks are pending?',
    'Help me prioritize',
  ];

  return (
    <aside className="flex w-96 flex-col border-l border-gray-200 bg-white shadow-lg">
      {/* Header */}
      <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4 bg-gradient-to-r from-primary-50 to-white">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-primary-100">
            <Sparkles className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">AI Assistant</h2>
            <p className="text-xs text-gray-500">Manage tasks with AI</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleNewChat}
            className="rounded-md p-2 text-gray-500 hover:bg-gray-100 transition-colors"
            title="New conversation"
          >
            <Plus className="h-5 w-5" />
          </button>
          <button
            onClick={onClose}
            className="rounded-md p-2 text-gray-500 hover:bg-gray-100 transition-colors"
            title="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="mx-4 mt-4 p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2">
          <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-red-700">{error}</p>
            <button
              onClick={() => fetchConversations()}
              className="text-xs text-red-600 hover:underline mt-1"
            >
              Try again
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {showConversations && !currentConversation ? (
          /* Conversation List */
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-12 gap-2">
                <Loader2 className="h-8 w-8 animate-spin text-primary-400" />
                <p className="text-sm text-gray-500">Loading conversations...</p>
              </div>
            ) : conversations.length === 0 ? (
              <div className="p-6 text-center">
                <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-primary-50 flex items-center justify-center">
                  <MessageSquare className="h-8 w-8 text-primary-400" />
                </div>
                <h3 className="font-medium text-gray-900 mb-1">No conversations yet</h3>
                <p className="text-sm text-gray-500 mb-4">
                  Start chatting to manage your tasks with AI
                </p>

                {/* Quick action suggestions */}
                <div className="space-y-2">
                  <p className="text-xs text-gray-400 uppercase tracking-wide">Try asking:</p>
                  {suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInput(suggestion)}
                      className="block w-full text-left px-3 py-2 rounded-lg bg-gray-50 hover:bg-gray-100 text-sm text-gray-700 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {conversations.map((conv) => (
                  <li key={conv.id}>
                    <button
                      onClick={() => {
                        selectConversation(conv.id);
                        setShowConversations(false);
                      }}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors"
                    >
                      <div className="font-medium text-gray-900 truncate">
                        {conv.title}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatRelativeTime(conv.updated_at)}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : (
          /* Chat Messages */
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col h-full items-center justify-center text-center px-4">
                <div className="mb-4 w-12 h-12 rounded-full bg-primary-50 flex items-center justify-center">
                  <Sparkles className="h-6 w-6 text-primary-400" />
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  I can help you manage tasks. Try:
                </p>
                <div className="space-y-2 w-full max-w-xs">
                  {suggestions.slice(0, 3).map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInput(suggestion)}
                      className="block w-full text-left px-3 py-2 rounded-lg bg-gray-50 hover:bg-gray-100 text-sm text-gray-700 transition-colors"
                    >
                      "{suggestion}"
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                {isSending && (
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100">
                      <Loader2 className="h-4 w-4 animate-spin text-primary-600" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-gray-700">Thinking...</p>
                      <p className="text-xs text-gray-400">Processing your request</p>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        )}

        {/* Draft Task Approval */}
        <DraftTaskApproval
          drafts={draftTasks}
          onApprove={handleApproveDraft}
          onReject={handleRejectDraft}
          onEdit={handleEditDraft}
        />

        {/* Back to conversations button */}
        {currentConversation && (
          <button
            onClick={() => {
              clearMessages();
              setDraftTasks([]);
              setShowConversations(true);
            }}
            className="border-t border-gray-100 px-4 py-2 text-sm text-primary-600 hover:bg-gray-50 transition-colors"
          >
            ← Back to conversations
          </button>
        )}

        {/* Input */}
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me to create, list, or manage tasks..."
              rows={2}
              className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 transition-all"
              disabled={isSending}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isSending}
              className={cn(
                'rounded-lg p-3 transition-all',
                input.trim() && !isSending
                  ? 'bg-primary-600 text-white hover:bg-primary-700 shadow-sm'
                  : 'bg-gray-200 text-gray-400'
              )}
            >
              {isSending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-400 text-center">
            Press Enter to send • Shift+Enter for new line
          </p>
        </div>
      </div>
    </aside>
  );
}
