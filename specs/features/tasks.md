# Implementation Tasks: Hackathon-Todo Full-Stack Application

## Overview
This document contains all implementation tasks for the hackathon-todo fullstack application, organized by feature and phase. Tasks are dependency-ordered and include acceptance criteria.

---

## Phase 1: Foundation & Infrastructure

### 1.1 Backend Setup
- [ ] **TASK-001**: Initialize FastAPI project structure
  - Create `backend/main.py` with FastAPI app initialization
  - Create `backend/requirements.txt` with dependencies (fastapi, uvicorn, sqlmodel, psycopg2-binary, python-jose, passlib)
  - Create `backend/db.py` with PostgreSQL connection and session management
  - **Acceptance:** `uvicorn main:app --reload` starts without errors

- [ ] **TASK-002**: Create SQLModel database models
  - Create `backend/models/__init__.py`
  - Create `backend/models/user.py` with User model (BetterAuth compatible)
  - Create `backend/models/session.py` with Session model
  - Create `backend/models/project.py` with Project model
  - Create `backend/models/permission.py` with Permission model (user_id, project_id, role enum)
  - Create `backend/models/task.py` with Task model (project_id, creator_id, assigned_to, title, description, completed, position, status, due_date)
  - **Acceptance:** All models import without errors; foreign key relationships are valid

- [ ] **TASK-003**: Create chat/conversation models
  - Create `backend/models/conversation.py` with Conversation model
  - Create `backend/models/message.py` with Message model (role enum: user|assistant|system|tool)
  - Create `backend/models/prompt.py` with Prompt model (prompt_type enum, tool_calls jsonb)
  - **Acceptance:** Chat models integrate with existing user/project models

- [ ] **TASK-004**: Set up database migrations
  - Install and configure Alembic
  - Create initial migration with all tables
  - Create indexes for performance (as per schema.md)
  - **Acceptance:** `alembic upgrade head` creates all tables with correct constraints

### 1.2 Authentication (BetterAuth)
- [ ] **TASK-005**: Implement BetterAuth JWT validation middleware
  - Create `backend/auth.py` with `get_current_user` dependency
  - Implement JWT decoding using BETTER_AUTH_SECRET
  - Implement session validation against sessions table
  - Return 401 Unauthorized for invalid tokens
  - **Acceptance:** Protected endpoints reject invalid/expired tokens

- [ ] **TASK-006**: Create auth routes
  - Create `backend/routes/auth.py`
  - Implement `POST /api/auth/signup` (email, password) -> user_id
  - Implement `POST /api/auth/login` (email, password) -> JWT
  - Implement password hashing with bcrypt
  - **Acceptance:** User can sign up and receive JWT on login

### 1.3 Frontend Setup
- [ ] **TASK-007**: Initialize Next.js 15 project
  - Create `frontend/` with Next.js 15 App Router
  - Configure TypeScript, Tailwind CSS, ESLint
  - Create `frontend/lib/api.ts` for API client with JWT handling
  - Create `frontend/types/` directory with TypeScript interfaces
  - **Acceptance:** `npm run dev` starts without errors

- [ ] **TASK-008**: Set up BetterAuth React integration
  - Install and configure `@better-auth/react`
  - Create `frontend/lib/auth.ts` with auth client configuration
  - Create auth context/provider for session management
  - Implement JWT storage (secure cookies or localStorage)
  - **Acceptance:** Auth state is accessible throughout the app

- [ ] **TASK-009**: Create authentication pages
  - Create `frontend/app/login/page.tsx` with login form
  - Create `frontend/app/signup/page.tsx` with signup form
  - Implement form validation and error handling
  - Redirect to dashboard on successful auth
  - **Acceptance:** User can sign up and log in via UI

---

## Phase 2: Project CRUD

### 2.1 Backend - Project API
- [ ] **TASK-010**: Create project routes
  - Create `backend/routes/projects.py`
  - Implement `GET /api/projects` - list user's projects with role filter
  - Implement `POST /api/projects` - create project (user becomes admin)
  - Implement `GET /api/projects/{id}` - get single project (permission check)
  - Implement `PUT /api/projects/{id}` - update project (admin/manager only)
  - Implement `DELETE /api/projects/{id}` - delete project (admin only, cascade delete tasks)
  - **Acceptance:** All CRUD operations work with proper authorization

- [ ] **TASK-011**: Implement project permission checking
  - Create `backend/utils/permissions.py` with `check_user_permission(user_id, project_id, required_role)` helper
  - Integrate permission checks in project routes
  - Return 403 Forbidden for unauthorized access
  - **Acceptance:** Role-based access control works correctly (admin > member > viewer)

- [ ] **TASK-012**: Add project event publishing (Dapr prep)
  - Create `backend/events/publisher.py` with event publishing interface
  - Publish `project.created`, `project.updated`, `project.deleted` events
  - Implement fallback logging when Dapr is unavailable
  - **Acceptance:** Events are published/logged on project mutations

### 2.2 Frontend - Project UI
- [ ] **TASK-013**: Create project list component
  - Create `frontend/components/projects/ProjectList.tsx`
  - Display user's projects in sidebar
  - Show project name, member count, role badge
  - Implement project selection (context switching)
  - **Acceptance:** User can see and select their projects

- [ ] **TASK-014**: Create project creation modal
  - Create `frontend/components/projects/CreateProjectModal.tsx`
  - Form fields: name (required, 1-100 chars), description (optional, max 500)
  - Integrate with `POST /api/projects`
  - Show loading state and error handling
  - **Acceptance:** User can create new projects via modal

- [ ] **TASK-015**: Create project settings page
  - Create `frontend/app/projects/[id]/settings/page.tsx`
  - Display project details and member list
  - Allow editing name/description (admin/manager only)
  - Allow deleting project (admin only)
  - **Acceptance:** Admins can manage project settings

---

## Phase 3: Task CRUD

### 3.1 Backend - Task API
- [ ] **TASK-016**: Create task routes
  - Create `backend/routes/tasks.py`
  - Implement `GET /api/tasks` - list tasks with filters (project_id, status, sort)
  - Implement `POST /api/tasks` - create task in project (member+ required)
  - Implement `GET /api/tasks/{id}` - get single task (viewer+ required)
  - Implement `PUT /api/tasks/{id}` - update task (member+ required)
  - Implement `DELETE /api/tasks/{id}` - delete task (admin only)
  - **Acceptance:** All CRUD operations with permission checks work

- [ ] **TASK-017**: Implement task position management
  - Add position calculation on task creation (count of existing tasks)
  - Implement `PUT /api/tasks/{id}/position` for drag-and-drop reordering
  - Batch update positions when tasks are moved between statuses
  - **Acceptance:** Tasks maintain correct order after drag operations

- [ ] **TASK-018**: Add task event publishing
  - Publish `task.created`, `task.updated`, `task.deleted` events
  - Include relevant payload (task_id, project_id, creator_id, changes)
  - **Acceptance:** Events are published on task mutations

### 3.2 Frontend - Kanban Board
- [ ] **TASK-019**: Create Kanban board layout
  - Create `frontend/components/kanban/KanbanBoard.tsx`
  - Three columns: "To Do", "In Progress", "Completed"
  - Responsive design (mobile: stacked, desktop: side-by-side)
  - **Acceptance:** Board renders with three columns

- [ ] **TASK-020**: Create task card component
  - Create `frontend/components/kanban/TaskCard.tsx`
  - Display: title, due date, assignee avatar, project badge
  - Show "AI Provenance" badge for AI-created tasks
  - Truncate long titles with tooltip
  - **Acceptance:** Task cards display all required information

- [ ] **TASK-021**: Implement drag-and-drop functionality
  - Integrate react-beautiful-dnd or @dnd-kit
  - Handle drag between columns (status change)
  - Handle drag within column (position change)
  - Optimistic UI: update immediately, revert on error
  - **Acceptance:** Smooth drag-and-drop with optimistic updates

- [ ] **TASK-022**: Create task creation form
  - Create `frontend/components/tasks/CreateTaskForm.tsx`
  - Form fields: title (required), description, due_date, assignee
  - Project selector (from user's accessible projects)
  - Integrate with `POST /api/tasks`
  - **Acceptance:** User can create tasks via form

- [ ] **TASK-023**: Create task detail modal
  - Create `frontend/components/tasks/TaskDetailModal.tsx`
  - Display full task details (title, description, status, dates, creator, assignee)
  - Allow editing (if member+)
  - Allow deleting (if admin)
  - **Acceptance:** User can view and edit task details

---

## Phase 4: Chat & AI Integration

### 4.1 Backend - Chat API
- [ ] **TASK-024**: Create conversation routes
  - Create `backend/routes/chat.py`
  - Implement `GET /api/conversations` - list user's conversations
  - Implement `POST /api/conversations` - create new conversation
  - Implement `GET /api/conversations/{id}` - get conversation with messages
  - Implement `GET /api/conversations/{id}/messages` - paginated messages
  - **Acceptance:** Conversation CRUD works with proper auth

- [ ] **TASK-025**: Implement chat endpoint
  - Implement `POST /api/{user_id}/chat` with message and optional conversation_id
  - Store user message in messages table
  - Retrieve conversation history for context
  - Return response with conversation_id and tool_calls
  - **Acceptance:** Chat endpoint stores messages and returns structured response

- [ ] **TASK-026**: Create prompt tracking
  - Implement `GET /api/prompts` - list prompts with filters
  - Implement `GET /api/prompts/{id}` - get prompt details
  - Store prompt_text, ai_response, tool_calls in prompts table
  - **Acceptance:** All prompts are tracked and queryable

### 4.2 Backend - MCP Tools Integration
- [ ] **TASK-027**: Create MCP tool definitions
  - Create `backend/mcp/__init__.py`
  - Create `backend/mcp/tools.py` with tool schemas
  - Define: `add_task`, `list_tasks`, `complete_task`, `update_task`, `delete_task`
  - Each tool includes: name, description, parameters schema
  - **Acceptance:** Tool definitions match chatbot.md spec

- [ ] **TASK-028**: Implement MCP tool handlers
  - Create `backend/mcp/handlers.py`
  - Implement `add_task(user_id, title, description?, project_id)` -> task object
  - Implement `list_tasks(user_id, status?, project_id?)` -> task array
  - Implement `complete_task(user_id, task_id)` -> updated task
  - Implement `update_task(user_id, task_id, ...)` -> updated task
  - Implement `delete_task(user_id, task_id)` -> confirmation
  - **Acceptance:** Tools execute CRUD operations with permission checks

- [ ] **TASK-029**: Integrate OpenAI Agents SDK
  - Install openai-agents-sdk
  - Create `backend/agent/agent.py` with agent configuration
  - Register MCP tools with agent
  - Implement agent execution with conversation context
  - Generate rationale_summary for each tool call (per constitution)
  - **Acceptance:** Agent can process messages and call tools

### 4.3 Frontend - OpenAI ChatKit-Plus Integration
- [ ] **TASK-030**: Install and configure OpenAI ChatKit-Plus
  - Install `@openai/chatkit-plus` package (or Vercel AI SDK if unavailable)
  - Create `frontend/components/chat/ChatWindow.tsx` using ChatKit-Plus
  - Configure streaming message display
  - Set up markdown rendering for responses
  - **Acceptance:** ChatKit-Plus components render correctly

- [ ] **TASK-031**: Create chat message components with ChatKit-Plus
  - Create `frontend/components/chat/ChatMessage.tsx` using ChatKit-Plus MessageList
  - Support roles: user, assistant, system, tool
  - Display tool calls with expandable ToolCallCard component
  - Show "Thinking..." indicator during processing
  - Implement streaming message updates
  - **Acceptance:** Messages render correctly with streaming support

- [ ] **TASK-032**: Create RAG citation components
  - Create `frontend/components/chat/CitationBlock.tsx`
  - Display inline citation markers [1], [2], [3] in responses
  - Create expandable citation cards showing source text
  - Show document name and page number
  - Visual distinction for RAG-augmented responses
  - **Acceptance:** Citations display and expand correctly

- [ ] **TASK-033**: Implement chat state management with streaming
  - Create `frontend/hooks/useChat.ts` with streaming support
  - Manage conversation list, active conversation, messages
  - Handle streaming responses from ChatKit-Plus
  - Store and display RAG citations
  - Integrate with chat API endpoints
  - **Acceptance:** Chat state syncs with backend including citations

- [ ] **TASK-034**: Create draft queue overlay
  - Create `frontend/components/chat/DraftQueue.tsx`
  - Display AI-suggested tasks pending approval
  - Approve/Edit/Reject buttons for each draft
  - Show rationale_summary for each suggestion
  - Bulk approve/reject actions
  - **Acceptance:** User can review and approve AI suggestions

- [ ] **TASK-035**: Create knowledge dropzone
  - Create `frontend/components/chat/KnowledgeDropzone.tsx`
  - Drag-and-drop file upload area with react-dropzone
  - Support PDF files (max 10MB)
  - Show upload progress indicator
  - Display list of uploaded documents
  - Delete document functionality
  - **Acceptance:** User can upload and manage PDF files

### 4.4 Backend - RAG Pipeline
- [ ] **TASK-051**: Set up Qdrant vector database
  - Add Qdrant to `docker-compose.yml` (qdrant/qdrant:latest)
  - Create `backend/rag/__init__.py` module
  - Create `backend/rag/qdrant_client.py` with connection management
  - Implement collection creation per user: `user_{user_id}_documents`
  - Configure vector dimension: 1536 (OpenAI embedding size)
  - **Acceptance:** Qdrant container runs; collections can be created

- [ ] **TASK-052**: Implement PDF parsing and text extraction
  - Install pdfplumber and PyPDF2
  - Create `backend/rag/pdf_parser.py`
  - Extract text from PDF pages
  - Handle multi-page documents
  - Extract metadata (page numbers, filename)
  - **Acceptance:** PDF text is extracted with page metadata

- [ ] **TASK-053**: Implement text chunking
  - Create `backend/rag/chunker.py`
  - Use RecursiveCharacterTextSplitter pattern
  - chunk_size=1000, chunk_overlap=200
  - Preserve metadata (page_number, chunk_index)
  - **Acceptance:** Text is chunked with proper overlap and metadata

- [ ] **TASK-054**: Implement OpenAI embeddings integration
  - Create `backend/rag/embeddings.py`
  - Use OpenAI `text-embedding-3-small` model
  - Batch embedding for efficiency
  - Handle rate limiting with retries
  - **Acceptance:** Text chunks are embedded into 1536-dim vectors

- [ ] **TASK-055**: Create document ingestion pipeline
  - Create `backend/rag/ingestion.py`
  - Pipeline: PDF → Parse → Chunk → Embed → Store in Qdrant
  - Store document metadata in PostgreSQL (Document model)
  - Background processing with status updates
  - **Acceptance:** Full pipeline ingests PDF into Qdrant

- [ ] **TASK-056**: Implement vector search/retrieval
  - Create `backend/rag/retrieval.py`
  - Embed user query
  - Search Qdrant for top 3 similar chunks
  - Return chunks with metadata and similarity scores
  - < 200ms latency requirement
  - **Acceptance:** Relevant chunks retrieved within latency budget

- [ ] **TASK-057**: Create document management routes
  - Create `backend/routes/documents.py`
  - `POST /api/documents/upload` - Upload and ingest PDF
  - `GET /api/documents` - List user's documents
  - `DELETE /api/documents/{id}` - Delete document and vectors
  - **Acceptance:** Document CRUD works with proper auth

- [ ] **TASK-058**: Integrate RAG with chat endpoint
  - Update `backend/routes/chat.py` to include RAG
  - Query Qdrant before calling AI agent
  - Inject retrieved context into system prompt
  - Include citations in response
  - Fallback to non-RAG if Qdrant unavailable
  - **Acceptance:** Chat responses include RAG context and citations

- [ ] **TASK-059**: Create Document database model
  - Create `backend/models/document.py`
  - Fields: id, user_id, project_id, filename, file_size, chunk_count, qdrant_collection, uploaded_at, status
  - Create Alembic migration
  - **Acceptance:** Document model persists to database

- [ ] **TASK-060**: Update agent to handle RAG context
  - Update `backend/agent/task_agent.py`
  - Accept RAG context in system prompt
  - Generate citations when using document context
  - Include rationale_summary for tool calls
  - **Acceptance:** Agent uses RAG context and generates citations

---

## Phase 5: Dapr & Event-Driven Architecture

### 5.1 Dapr Setup
- [ ] **TASK-036**: Create Dapr component configurations
  - Create `dapr/components/pubsub.yaml` (Redis for local dev)
  - Create `dapr/components/statestore.yaml` (Redis)
  - **Acceptance:** Dapr components are valid YAML

- [ ] **TASK-037**: Create Dapr runner configuration
  - Create `dapr.yaml` with backend-api app configuration
  - Configure app port (8000), environment variables
  - **Acceptance:** `dapr run -f dapr.yaml` starts the application

- [ ] **TASK-038**: Implement Dapr sidecar integration
  - Add Dapr SDK to backend dependencies
  - Implement sidecar health check on startup
  - Graceful degradation when sidecar unavailable
  - **Acceptance:** App works with and without Dapr sidecar

- [ ] **TASK-039**: Implement event subscriptions
  - Create subscription handlers for task/project events
  - Log events for debugging/audit
  - Prepare hooks for future notification service
  - **Acceptance:** Events are received and processed

---

## Phase 6: Polish & Production Readiness

### 6.1 UI/UX Enhancements
- [ ] **TASK-040**: Implement responsive design
  - Mobile-first Kanban (collapsible columns)
  - Mobile chat (full-screen overlay)
  - Tablet layout optimization
  - **Acceptance:** UI works on mobile, tablet, desktop

- [ ] **TASK-041**: Add accessibility features
  - Keyboard navigation for Kanban
  - ARIA labels for interactive elements
  - Screen reader announcements for state changes
  - Focus management in modals
  - **Acceptance:** WCAG 2.1 AA compliance

- [ ] **TASK-042**: Implement loading states
  - Skeleton loaders for project/task lists
  - Button loading states
  - Page transition indicators
  - **Acceptance:** All async operations have visual feedback

- [ ] **TASK-043**: Add error handling UI
  - Toast notifications for errors
  - Inline form validation errors
  - Connection error recovery UI
  - **Acceptance:** Users see friendly error messages

### 6.2 Performance & Reliability
- [ ] **TASK-044**: Implement optimistic updates
  - Task status changes
  - Task position changes
  - Project updates
  - Rollback on failure
  - **Acceptance:** UI feels instant; reverts correctly on errors

- [ ] **TASK-045**: Add real-time updates (WebSocket/SSE)
  - Subscribe to task/project changes
  - Update UI when other users make changes
  - Handle reconnection gracefully
  - **Acceptance:** Multi-user updates work in real-time

- [ ] **TASK-046**: Implement caching strategy
  - SWR/React Query for API data
  - Cache invalidation on mutations
  - Stale-while-revalidate pattern
  - **Acceptance:** Reduced API calls; fresh data on mutations

### 6.3 Testing
- [ ] **TASK-047**: Write backend unit tests
  - Test models and database operations
  - Test permission checking logic
  - Test authentication middleware
  - **Acceptance:** 80%+ code coverage on critical paths

- [ ] **TASK-048**: Write backend integration tests
  - Test API endpoints with test database
  - Test authentication flow
  - Test permission-gated operations
  - **Acceptance:** All API endpoints tested

- [ ] **TASK-049**: Write frontend component tests
  - Test Kanban board interactions
  - Test form validations
  - Test chat components
  - **Acceptance:** Key components have test coverage

- [ ] **TASK-050**: Write E2E tests
  - Test full user flow: signup -> create project -> create task -> chat
  - Test permission boundaries
  - Test error recovery
  - **Acceptance:** Critical user journeys automated

---

## Task Dependencies

```
TASK-001 -> TASK-002 -> TASK-003 -> TASK-004
TASK-001 -> TASK-005 -> TASK-006
TASK-007 -> TASK-008 -> TASK-009
TASK-005 -> TASK-010 -> TASK-011 -> TASK-012
TASK-008 -> TASK-013 -> TASK-014 -> TASK-015
TASK-011 -> TASK-016 -> TASK-017 -> TASK-018
TASK-013 -> TASK-019 -> TASK-020 -> TASK-021 -> TASK-022 -> TASK-023
TASK-003 -> TASK-024 -> TASK-025 -> TASK-026
TASK-016 -> TASK-027 -> TASK-028 -> TASK-029
TASK-029 -> TASK-030 -> TASK-031 -> TASK-032 -> TASK-033 -> TASK-034 -> TASK-035
TASK-012 -> TASK-036 -> TASK-037 -> TASK-038 -> TASK-039
TASK-023 -> TASK-040 -> TASK-041 -> TASK-042 -> TASK-043
TASK-021 -> TASK-044 -> TASK-045 -> TASK-046
TASK-018 -> TASK-047 -> TASK-048
TASK-023 -> TASK-049
TASK-048 -> TASK-050

# RAG Pipeline Dependencies
TASK-051 -> TASK-052 -> TASK-053 -> TASK-054 -> TASK-055 -> TASK-056
TASK-003 -> TASK-059  # Document model depends on base models
TASK-056 -> TASK-057 -> TASK-058
TASK-029 -> TASK-060  # Agent RAG depends on base agent
TASK-058 -> TASK-060  # Agent RAG depends on RAG integration
TASK-035 -> TASK-057  # Dropzone UI needs document routes
```

---

## Priority Matrix

| Priority | Tasks | Rationale |
|----------|-------|-----------|
| P0 (Critical) | 001-009 | Foundation: Backend setup, auth, frontend setup |
| P1 (High) | 010-023 | Core features: Project & Task CRUD |
| P2 (Medium) | 024-035 | AI features: Chat & MCP tools with ChatKit-Plus |
| P2 (Medium) | 051-060 | RAG Pipeline: Qdrant, embeddings, document ingestion |
| P3 (Low) | 036-039 | Infrastructure: Dapr integration |
| P4 (Polish) | 040-050 | UX, performance, testing |

---

## Estimation Notes
Tasks are designed to be atomic and testable. Each task should be completable in a single focused session. Dependencies are explicit to enable parallel work where possible.
