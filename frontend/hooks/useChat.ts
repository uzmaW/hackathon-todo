/**
 * Chat hook with state management.
 */

import { create } from 'zustand';
import type { Conversation, Message, ChatResponse, ToolCall } from '@/types';
import { api } from '@/lib/api';

interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  lastToolCalls: ToolCall[];
  fetchConversations: () => Promise<void>;
  selectConversation: (conversationId: number | null) => Promise<void>;
  createConversation: (title: string, projectId?: number) => Promise<Conversation>;
  sendMessage: (userId: string, message: string) => Promise<ChatResponse>;
  clearMessages: () => void;
  clearError: () => void;
}

export const useChat = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  isSending: false,
  error: null,
  lastToolCalls: [],

  fetchConversations: async () => {
    set({ isLoading: true, error: null });
    try {
      const conversations = await api.conversations.list();
      set({ conversations, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch conversations',
        isLoading: false
      });
    }
  },

  selectConversation: async (conversationId: number | null) => {
    if (conversationId === null) {
      set({ currentConversation: null, messages: [] });
      return;
    }

    set({ isLoading: true, error: null });
    try {
      const conversation = await api.conversations.get(conversationId);
      set({
        currentConversation: conversation,
        messages: conversation.messages || [],
        isLoading: false
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch conversation',
        isLoading: false
      });
    }
  },

  createConversation: async (title: string, projectId?: number) => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await api.conversations.create({ title, project_id: projectId });
      set(state => ({
        conversations: [conversation, ...state.conversations],
        currentConversation: conversation,
        messages: [],
        isLoading: false
      }));
      return conversation;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to create conversation',
        isLoading: false
      });
      throw error;
    }
  },

  sendMessage: async (userId: string, message: string) => {
    const { currentConversation } = get();

    // Add user message optimistically
    const optimisticUserMessage: Message = {
      id: Date.now(),
      conversation_id: currentConversation?.id || 0,
      user_id: userId,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };

    set(state => ({
      messages: [...state.messages, optimisticUserMessage],
      isSending: true,
      error: null,
      lastToolCalls: [],
    }));

    try {
      const response = await api.chat.send(userId, {
        conversation_id: currentConversation?.id,
        message,
      });

      // Format tool calls for display
      const formattedToolCalls = (response.tool_calls || []).map((call: any) => ({
        name: call.tool || call.name || 'unknown',
        arguments: call.arguments || {},
        result: call.result,
      }));

      // Add assistant response
      const assistantMessage: Message = {
        id: Date.now() + 1,
        conversation_id: response.conversation_id,
        user_id: userId,
        role: 'assistant',
        content: response.response,
        message_metadata: formattedToolCalls.length > 0 ? { tool_calls: formattedToolCalls } : undefined,
        created_at: new Date().toISOString(),
      };

      set(state => ({
        messages: [...state.messages, assistantMessage],
        isSending: false,
        lastToolCalls: formattedToolCalls,
        // Update current conversation if it was just created
        currentConversation: state.currentConversation || {
          id: response.conversation_id,
          title: message.slice(0, 50),
          user_id: userId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      }));

      // Return response with properly formatted tool calls
      return {
        ...response,
        tool_calls: formattedToolCalls,
      };
    } catch (error) {
      // Remove optimistic message on error
      set(state => ({
        messages: state.messages.filter(m => m.id !== optimisticUserMessage.id),
        isSending: false,
        error: error instanceof Error ? error.message : 'Failed to send message',
        lastToolCalls: [],
      }));
      throw error;
    }
  },

  clearMessages: () => {
    set({ messages: [], currentConversation: null, lastToolCalls: [] });
  },

  clearError: () => {
    set({ error: null });
  },
}));
