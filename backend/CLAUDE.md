# Backend Guidelines

## Stack
- FastAPI
- SQLModel (ORM)
- Neon/Postgres (or any Postgres-compatible DB)
- OpenAI Agents SDK (for phase3)
- MCP Server/SDK exposing task tools (phase3)

## Project Layout (recommended)
- `main.py` - FastAPI app entrypoint
- `models.py` - SQLModel models for `tasks`, `conversations`, `messages`
- `routes/` - `/routes/tasks.py`, `/routes/auth.py`, `/routes/chat.py`
- `db.py` - DB init and session helper
- `migrations/` - alembic or SQLAlchemy-migrate scripts
- `mcp/` - MCP tool definitions for phase3

## API conventions
- All API routes under `/api/`
- Use Pydantic models for request/response validation
- JWT Authentication via Authorization header: `Bearer <token>`
- Return consistent error format:
  { "error": "message", "details": optional }

## Running
uvicorn main:app --reload --port 8000