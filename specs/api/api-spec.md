# API Spec: Unified Backend (CRUD + Chat)

## App Layout
- `main.py`: Entry point.
- `/api/tasks`: Task CRUD Router.
- `/api/projects`: Project CRUD Router.
- `/api/chat`: AI Agent Router.

## Base URL
- Development: http://localhost:8000

## Authentication
All protected endpoints require:
- Authorization: Bearer <token>
- Both routers share the `get_current_user` dependency (BetterAuth JWT).

## Tasks API

### GET /api/tasks
- Query: status (all|pending|completed), sort
- Response: array of Task
- Requires authentication

### POST /api/tasks
- Body: { title: string, description?: string, project_id: number }
- Response: created Task
- Requires authentication
- User must be member of the project

### GET /api/tasks/{id}
- Response: Task
- Requires authentication
- User must have access to the task's project

### PUT /api/tasks/{id}
- Body: { title?, description?, completed?, project_id? }
- Response: updated Task
- Requires authentication
- Only project members can update tasks

### DELETE /api/tasks/{id}
- Response: { task_id, status: "deleted" }
- Requires authentication
- Only project admins can delete tasks

## Projects API

### GET /api/projects
- Query: role (admin|member|viewer)
- Response: array of Project
- Requires authentication
- Returns projects user belongs to

### POST /api/projects
- Body: { name: string, description?: string }
- Response: created Project
- Requires authentication
- Creates user as project admin

### GET /api/projects/{id}
- Response: Project
- Requires authentication
- User must be member of the project

### PUT /api/projects/{id}
- Body: { name?, description? }
- Response: updated Project
- Requires authentication
- Only project admins or managers can update

### DELETE /api/projects/{id}
- Response: { project_id, status: "deleted" }
- Requires authentication
- Only project admins can delete projects

## Chat API (Phase 2+)

### POST /api/{user_id}/chat
- Body: { conversation_id?: int, message: string }
- Response:
  {
    conversation_id: int,
    response: string,
    tool_calls: [ ... ]
  }
- Requires authentication
- The Chat Agent can call the CRUD logic directly (as local functions) or via the **MCP Tools** layer.

### GET /api/conversations
- Query: project_id (optional), limit (default 20), offset (default 0)
- Response: array of Conversation
- Requires authentication
- Returns conversations for the authenticated user

### GET /api/conversations/{conversation_id}
- Response: Conversation with messages
- Requires authentication
- User must have access to the conversation's project

### POST /api/conversations
- Body: { project_id?: int, title: string }
- Response: created Conversation
- Requires authentication
- User must have access to the project if specified

### GET /api/conversations/{conversation_id}/messages
- Response: array of Message
- Requires authentication
- Returns messages for the specified conversation

### GET /api/prompts
- Query: conversation_id (optional), limit (default 20), offset (default 0)
- Response: array of Prompt
- Requires authentication
- Returns prompts for the authenticated user or specified conversation

### GET /api/prompts/{prompt_id}
- Response: Prompt
- Requires authentication
- User must have access to the prompt's conversation

## Dapr Invocation
- The unified app uses the Dapr Sidecar to publish events to **itself** or other listeners (like a future Notification service).
- Events published: task.created, task.updated, task.deleted, project.created, project.updated, project.deleted