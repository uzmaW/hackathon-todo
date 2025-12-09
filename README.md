# hackathon-todo

Spec-driven monorepo scaffold for a Todo app using Spec-Kit and Claude Code.

Phases:
- phase1-console: minimal console task CRUD
- phase2-web: full-stack web app with authentication
- phase3-chatbot: AI chatbot using MCP tools and OpenAI Agents

Structure highlights:
- .spec-kit/config.yaml — Spec-Kit configuration and phases
- /specs — human- and machine-readable specs (features, API, DB, UI)
- /frontend — Next.js app (CLAUDE.md for frontend conventions)
- /backend — FastAPI app (CLAUDE.md for backend conventions)
- CLAUDE.md — root context for Claude Code and how to use the specs
- docker-compose.yml — local dev services (frontend, backend, db)

How to use:
1. Read the relevant spec under /specs before implementing.
2. Request Claude Code with: "Implement @specs/features/<feature>.md"
3. Follow phase branches (we recommend one branch per phase).

See .spec-kit/config.yaml for phase definitions and how features map to phases.