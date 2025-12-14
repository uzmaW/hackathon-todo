# Frontend Guidelines

## Stack
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- BetterAuth React integration

## Project Structure
- `/app` - Next.js App Router pages
- `/components` - Reusable UI components
- `/ui` - Low-level UI primitives
- `/lib` - Utilities and API clients
- `/hooks` - Custom React hooks
- `/types` - TypeScript type definitions

## Patterns
- Prefer server components for data fetching; mark UI interactivity with client components.
- Keep components small & reusable: `/components`, `/ui`, `/app`.
- Centralize API calls in `/lib/api.ts` and call backend endpoints (JWT-protected).
- Use the Lovable UI design system for consistent styling.

## API Client
Use a lightweight client that reads JWT from cookies/local storage; example usage:
```typescript
import { api } from '@/lib/api'
const tasks = await api.getTasks()
const projects = await api.getProjects()
```

## Authentication
- Integrate with BetterAuth using `@better-auth/react`
- Secure all routes that require authentication
- Handle JWT tokens for API calls

## UI Components
- **Kanban Board:** Drag-and-drop task management with columns (To Do, In Progress, Completed)
- **Project Navigation:** Sidebar with project list and create functionality
- **Chat Sidebar:** Collapsible right-hand panel with AI assistant
- **Draft Queue:** Overlay for approving AI-generated tasks
- **Knowledge Dropzone:** PDF upload for RAG integration

## Styling
- Tailwind CSS
- No inline styles; prefer utility classes and reusable component tokens.
- Follow Lovable Template design system for consistency

## Chat & AI Integration
- Use OpenAI ChatKit for chat interface
- Implement persistent chat history with conversation switching
- Include RAG citations and knowledge base integration
- Support AI "Thinking..." indicators and tool call visualization

## State Management
- Use React Query/SWR for server state management
- Implement optimistic UI updates for task operations
- Real-time updates via WebSocket subscriptions

## Key Specifications
- UI specification: `specs/features/todo-web-ui.md`
- API endpoints: `specs/api/api-spec.md`
- Database schema: `specs/database/schema.md`
- Project config: `.spec-kit/config.yaml`