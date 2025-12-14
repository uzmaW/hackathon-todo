'use client';

import type { Message, ToolCall } from '@/types';
import { Bot, User, Wrench, Info, CheckCircle, XCircle, ListTodo, Pencil, Trash2, Eye } from 'lucide-react';
import { cn, formatRelativeTime } from '@/lib/utils';

interface ChatMessageProps {
  message: Message;
}

/**
 * Get icon for specific tool name
 */
function getToolIcon(toolName: string) {
  switch (toolName) {
    case 'add_task':
      return <ListTodo className="h-3 w-3" />;
    case 'list_tasks':
      return <Eye className="h-3 w-3" />;
    case 'update_task':
      return <Pencil className="h-3 w-3" />;
    case 'complete_task':
      return <CheckCircle className="h-3 w-3" />;
    case 'delete_task':
      return <Trash2 className="h-3 w-3" />;
    default:
      return <Wrench className="h-3 w-3" />;
  }
}

/**
 * Get friendly name for tool
 */
function getToolDisplayName(toolName: string) {
  switch (toolName) {
    case 'add_task':
      return 'Created task';
    case 'list_tasks':
      return 'Listed tasks';
    case 'update_task':
      return 'Updated task';
    case 'complete_task':
      return 'Completed task';
    case 'delete_task':
      return 'Deleted task';
    case 'get_user_projects':
      return 'Fetched projects';
    default:
      return toolName;
  }
}

/**
 * Render tool call result in a friendly way
 */
function ToolCallDisplay({ call }: { call: ToolCall | any }) {
  const toolName = call.name || call.function?.name || 'Unknown';
  const args = call.arguments || call.function?.arguments || {};
  const result = call.result;

  return (
    <div className="rounded-md bg-white/50 border border-gray-200 overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border-b border-gray-200">
        <span className="text-amber-600">{getToolIcon(toolName)}</span>
        <span className="text-xs font-medium text-gray-700">
          {getToolDisplayName(toolName)}
        </span>
      </div>

      {/* Show relevant arguments */}
      {args && Object.keys(args).length > 0 && (
        <div className="px-3 py-2 text-xs text-gray-600">
          {args.title && (
            <div className="flex gap-2">
              <span className="text-gray-400">Title:</span>
              <span className="font-medium">{args.title}</span>
            </div>
          )}
          {args.description && (
            <div className="flex gap-2">
              <span className="text-gray-400">Description:</span>
              <span>{args.description}</span>
            </div>
          )}
          {args.status && (
            <div className="flex gap-2">
              <span className="text-gray-400">Status:</span>
              <span className="font-medium">{args.status}</span>
            </div>
          )}
          {args.task_id && (
            <div className="flex gap-2">
              <span className="text-gray-400">Task ID:</span>
              <span className="font-mono">{args.task_id}</span>
            </div>
          )}
        </div>
      )}

      {/* Show result if available */}
      {result && (
        <div className="px-3 py-2 bg-green-50 border-t border-green-100 text-xs text-green-700">
          <CheckCircle className="inline h-3 w-3 mr-1" />
          {typeof result === 'string' ? result : 'Action completed'}
        </div>
      )}
    </div>
  );
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const isTool = message.role === 'tool';
  const isSystem = message.role === 'system';

  const getIcon = () => {
    if (isUser) return <User className="h-4 w-4" />;
    if (isAssistant) return <Bot className="h-4 w-4" />;
    if (isTool) return <Wrench className="h-4 w-4" />;
    return <Info className="h-4 w-4" />;
  };

  const getBubbleStyles = () => {
    if (isUser) return 'bg-primary-600 text-white';
    if (isAssistant) return 'bg-gray-100 text-gray-900';
    if (isTool) return 'bg-amber-50 text-amber-900 border border-amber-200';
    return 'bg-blue-50 text-blue-900 border border-blue-200';
  };

  const toolCalls = message.message_metadata?.tool_calls as ToolCall[] | undefined;

  return (
    <div
      className={cn('flex gap-3', isUser ? 'justify-end' : 'justify-start')}
    >
      {!isUser && (
        <div
          className={cn(
            'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full',
            isAssistant && 'bg-primary-100 text-primary-600',
            isTool && 'bg-amber-100 text-amber-600',
            isSystem && 'bg-blue-100 text-blue-600'
          )}
        >
          {getIcon()}
        </div>
      )}

      <div className={cn('max-w-[80%] space-y-2', isUser && 'items-end')}>
        <div className={cn('rounded-lg px-4 py-2', getBubbleStyles())}>
          <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        </div>

        {/* Enhanced tool calls display */}
        {toolCalls && toolCalls.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-500 flex items-center gap-1">
              <Wrench className="h-3 w-3" />
              Actions performed:
            </p>
            {toolCalls.map((call, idx) => (
              <ToolCallDisplay key={idx} call={call} />
            ))}
          </div>
        )}

        <p
          className={cn(
            'text-xs text-gray-400',
            isUser ? 'text-right' : 'text-left'
          )}
        >
          {formatRelativeTime(message.created_at)}
        </p>
      </div>

      {isUser && (
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-600 text-white">
          {getIcon()}
        </div>
      )}
    </div>
  );
}
