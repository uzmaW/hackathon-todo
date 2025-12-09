# Feature: Chatbot (Phase 3)

## Goal
Allow users to manage todos via natural language using an AI agent and MCP tools.

## High-level behavior
- Agents must call well-defined MCP tools: add_task, list_tasks, complete_task, update_task, delete_task.
- Agent confirms actions and handles errors gracefully.
- Server remains stateless: all conversation state is stored in DB.

## MCP Tools (summary)
- add_task(user_id, title, description?) → { task_id, status, title }
- list_tasks(user_id, status?) → [ task objects ]
- complete_task(user_id, task_id) → { task_id, status, title }
- delete_task(user_id, task_id) → { task_id, status, title }
- update_task(user_id, task_id, title?, description?) → { task_id, status, title }

## Agent policies
- Call list_tasks when user references a task by name or when context is ambiguous
- Confirm destructive actions (delete) before executing, if user intent is ambiguous
- Use filters if user asks "show pending" or "show completed"

## Conversation flow (stateless)
1. Client POST /api/{user_id}/chat with message & optional conversation_id
2. Server retrieves conversation messages (if conversation_id)
3. Server stores user message
4. Server composes messages & runs agent with MCP tools
5. Agent may call tools; server executes tool calls and returns results to agent
6. Store assistant response and tool call metadata
7. Return assistant text + any tool calls to client