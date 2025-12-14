# Project Overview: Hackathon-Todo (v2.0)

## System Vision
A next-generation productivity ecosystem that evolves from a high-performance Project based Todo application into an AI-agentic, event-driven microservices architecture. It leverages the "Spec-Kit-Plus" methodology to ensure alignment between architectural intent and implementation.

## Development Roadmap
| Phase | Title | Focus | Core Tech |
| :--- | :--- | :--- | :--- |
| **P1** | Full-Stack Web | Foundational CRUD & Auth | Next.js 15, FastAPI, GraphQL, BetterAuth |
| **P2** | AI Integration | Agentic UX & Intelligent Drafting | OpenAI SDK, MCP Tools, JSON-RPC Streaming |
| **P3** | Event-Driven | Scale & Service Decomposition | Kafka/Redpanda, Dapr, Microservices |
| **P4** | Cloud-Native | Infrastructure Automation | Kubernetes, Helm, Kagent, kubectl-ai |

## Key Architectural Pillars
- **Agentic UX:** AI doesn't just suggest; it executes via Model Context Protocol (MCP) tools.
- **Draft Workflow:** Human-in-the-loop validation for all AI-suggested state changes.
- **Event-Driven:** Every task interaction is an immutable event in the `task-events` stream.