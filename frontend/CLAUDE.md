# Frontend Guidelines

## Stack
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS

## Patterns
- Prefer server components for data fetching; mark UI interactivity with client components.
- Keep components small & reusable: `/components`, `/ui`, `/app`.
- Centralize API calls in `/lib/api.ts` and call backend endpoints (JWT-protected).

## API Client
Use a lightweight client that reads JWT from cookies/local storage; example usage:
import { api } from '@/lib/api'
const tasks = await api.getTasks()

## Styling
- Tailwind CSS
- No inline styles; prefer utility classes and reusable component tokens.

## Chat UI (phase3)
- Use OpenAI ChatKit (hosted) or a local Chat UI wrapper.
- Ensure domain allowlist and NEXT_PUBLIC_OPENAI_DOMAIN_KEY are configured for production.