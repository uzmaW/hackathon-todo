# Dapr Infrastructure Spec: Unified Backend (CRUD + Chat)

## Component Manifests

These are YAML files located in your dapr/components folder that tell the Dapr sidecar exactly which infrastructure (Redis, Postgres, Kafka, etc.) to use for things like Pub/Sub and State Management.

Because they are now in the same app, you only need one set of components that the backend-api app ID will use.

### A. Pub/Sub Component (dapr/components/pubsub.yaml)

This enables the event-driven architecture. Even if you use Redis for local development, you can swap this to Redpanda (Kafka) in Phase 4 without changing your Python code.

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
```

### B. State Store Component (dapr/components/statestore.yaml)

While you use PostgreSQL for your primary Task CRUD, Dapr can use a State Store for AI session caching or temporary task drafts.

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
  - name: redisPassword
    value: ""
```

## Unified API Specification (specs/api/fastapi-routes.md)

This updated spec tells Claude to register both CRUD and Chat routes under the same FastAPI instance.

### App Layout
- `main.py`: Entry point.
- `/api/tasks`: Task CRUD Router.
- `/api/projects`: Project CRUD Router.
- `/api/chat`: AI Agent Router.

### Logic Integration
- Both routers share the `get_current_user` dependency (BetterAuth JWT).
- The Chat Agent can call the CRUD logic directly (as local functions) or via the **MCP Tools** layer.

### Dapr Invocation
- The unified app uses the Dapr Sidecar to publish events to **itself** or other listeners (like a future Notification service).

## Simplified dapr.yaml (Local Runner)

Since the agent is now part of the backend, the runner becomes much simpler.

```yaml
version: 1
common:
  resourcesPath: ./dapr/components
apps:
  - appID: backend-api  # One App ID for both CRUD and Chat
    appPort: 8000
    command: ["uvicorn", "main:app", "--port", "8000"]
    env:
      BETTER_AUTH_SECRET: ${BETTER_AUTH_SECRET}
      DATABASE_URL: ${DATABASE_URL}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
```

## Updated Logic for Implementation

When generating code, ensure it handles the Dapr Sidecar Lifecycle:

1. **Initialization**: The FastAPI app should wait for the Dapr sidecar to be "Ready" before accepting requests.

2. **Topic Naming**: Ensure the topic names in the code (e.g., task.created, project.created) match the subscriptions in the Dapr components.

3. **Resilience**: Implement a check to see if the Dapr sidecar is reachable; if not, the CRUD should still save to the DB but log a "Pub/Sub Failure."

## Why this is better for Phase 1 & 2

- **Shared Memory**: The Chat Agent can instantly "see" the SQLModel classes for Todos and Projects.

- **Simplified Security**: You only have to implement the BETTER_AUTH_SECRET validation once.

- **Local Performance**: No network latency between the Chat logic and the Database.

## Final Implementation Step

To have Claude generate this unified version, use this prompt:

"Claude, follow the unified spec. Create a single FastAPI application (backend-api) that contains both the Task CRUD routes and the AI Chat Agent routes.

Ensure both use the same BetterAuth JWT validation.

The Chat Agent should use the OpenAI Agents SDK and have access to the CRUD functions as tools.

Use the dapr/components/pubsub.yaml for all event publishing."