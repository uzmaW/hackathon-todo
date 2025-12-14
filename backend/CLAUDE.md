# Backend Guidelines

## Stack
- FastAPI
- SQLModel (ORM)
- PostgreSQL (with BetterAuth integration)
- OpenAI Agents SDK
- MCP Server/SDK exposing task tools
- Dapr for event-driven architecture

## Project Layout (recommended)
- `main.py` - FastAPI app entrypoint with Dapr integration
- `models/` - SQLModel models (`users`, `projects`, `tasks`, `conversations`, `messages`, `prompts`)
- `routes/` - `/routes/tasks.py`, `/routes/projects.py`, `/routes/auth.py`, `/routes/chat.py`
- `db.py` - DB init and session helper
- `auth.py` - BetterAuth JWT middleware and user validation
- `migrations/` - alembic or SQLAlchemy-migrate scripts
- `mcp/` - MCP tool definitions for AI agent integration
- `dapr/` - Dapr component configurations and sidecar integration

## API conventions
- All API routes under `/api/`
- Use Pydantic models for request/response validation
- JWT Authentication via Authorization header: `Bearer <token>`
- Return consistent error format:
  { "error": "message", "details": optional }
- Implement role-based access control (admin, member, viewer)

## Database Models
- **Identity Layer:** BetterAuth managed `users` and `sessions`
- **Containers Layer:** `projects` with owner and creation metadata
- **Access Control Layer:** `permissions` table for user-project-role relationships
- **Work Layer:** `tasks` with project, creator, assignee, and status tracking
- **Chat Layer:** `conversations`, `messages`, and `prompts` with persistent history

## Dapr Integration
- Use Dapr pub/sub for event-driven task/project updates
- Publish events: `task.created`, `task.updated`, `task.deleted`, `project.created`, etc.
- Use Dapr state management for caching if needed
- Implement resilient event publishing with fallbacks

## Authentication & Authorization
- Integrate BetterAuth for user management and JWT generation
- Implement permission checking middleware for project-based access
- Validate user roles (admin, member, viewer) for different operations

## Chat & AI Integration
- Implement persistent chat history in database
- Store and retrieve conversation context
- Integrate OpenAI Agents SDK for task automation
- Support MCP tools for task CRUD operations

## Running
uvicorn main:app --reload --port 8000

## Key Specifications
- Database schema: `specs/database/schema.md`
- API endpoints: `specs/api/api-spec.md`
- Task CRUD logic: `specs/features/task-crud.md`
- Project CRUD logic: `specs/features/project-crud.md`
- Dapr configuration: `specs/infra/dapr-config.md`
- Project config: `.spec-kit/config.yaml`