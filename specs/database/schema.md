# Database Schema: Project-Based Task Management with Chat

## I. User & Identity (BetterAuth Managed)
These tables are managed by BetterAuth and generated using `npx @better-auth/cli migrate`.
The schema follows BetterAuth's core requirements.

### user (BetterAuth Core Table)
- `id`: string (PK) - Unique identifier for each user
- `name`: string - User's display name
- `email`: string (UNIQUE) - Email address for login and communication
- `emailVerified`: boolean - Whether email has been verified
- `image`: string (nullable) - URL to user's profile image
- `createdAt`: timestamp - Account creation timestamp
- `updatedAt`: timestamp - Last modification timestamp

### session (BetterAuth Core Table)
- `id`: string (PK) - Session identifier
- `userId`: string (FK -> user.id) - Links to user account
- `token`: string (UNIQUE) - The unique session token (JWT)
- `expiresAt`: timestamp - Session expiration time
- `ipAddress`: string (nullable) - Client IP address
- `userAgent`: string (nullable) - Browser/device information
- `createdAt`: timestamp - Session start timestamp
- `updatedAt`: timestamp - Last activity timestamp

### account (BetterAuth Core Table)
- `id`: string (PK) - Account identifier
- `userId`: string (FK -> user.id) - Associated user
- `accountId`: string - Provider-specific account ID
- `providerId`: string - Authentication provider name (e.g., 'credential', 'google')
- `accessToken`: string (nullable) - OAuth access token
- `refreshToken`: string (nullable) - Token renewal credential
- `accessTokenExpiresAt`: timestamp (nullable) - Token expiration
- `refreshTokenExpiresAt`: timestamp (nullable) - Refresh token expiration
- `scope`: string (nullable) - OAuth permissions granted
- `idToken`: string (nullable) - Provider's ID token
- `password`: string (nullable) - Hashed password for email/password auth
- `createdAt`: timestamp - Creation timestamp
- `updatedAt`: timestamp - Modification timestamp

### verification (BetterAuth Core Table)
- `id`: string (PK) - Verification record ID
- `identifier`: string - The identifier for the verification request (e.g., email)
- `value`: string - Data to be verified (e.g., verification token)
- `expiresAt`: timestamp - Request expiration time
- `createdAt`: timestamp - Creation timestamp
- `updatedAt`: timestamp (nullable) - Update timestamp

**Note:** To generate/migrate these tables, run:
```bash
cd frontend && npx @better-auth/cli generate  # Generate migration
cd frontend && npx @better-auth/cli migrate   # Apply migration
```

## II. Structural Tables (Projects & Access)
This layer defines who can see what.

### projects
- `id`: integer (SERIAL PK) - Primary key for project identification
- `name`: string (VARCHAR 100) - Project name (1-100 characters)
- `description`: text - Project description (optional)
- `ownerId`: string (FK -> user.id) - The creator/admin of the project
- `createdAt`: timestamp - When the project was created
- `updatedAt`: timestamp - When the project was last updated

### permissions (The Join Table)
Handles the Many-to-Many relationship between Users and Projects.

- `id`: integer (SERIAL PK) - Primary key for permission record
- `userId`: string (FK -> user.id) - Reference to the user
- `projectId`: integer (FK -> projects.id) - Reference to the project
- `role`: string (ENUM) - User's role in the project: 'admin', 'member', 'viewer'
- `createdAt`: timestamp - When the permission was granted
- `updatedAt`: timestamp - When the permission was last updated
- **Constraint:** Unique pair of (userId, projectId)

## III. Functional Tables (Work)

### tasks
- `id`: integer (SERIAL PK) - Primary key for task identification
- `project_id`: integer (FK -> projects.id) - Reference to the project this task belongs to
- `creator_id`: string (FK -> users.id) - Reference to the user who created the task
- `assigned_to`: string (FK -> users.id) - Reference to the user assigned to the task (nullable)
- `title`: string (VARCHAR 200) - Task title (required, 1-200 characters)
- `description`: text - Task description (optional)
- `completed`: boolean (default false) - Whether the task is completed
- `position`: integer - For drag-and-drop Kanban ordering
- `due_date`: timestamp (nullable) - When the task is due (optional)
- `created_at`: timestamp - When the task was created
- `updated_at`: timestamp - When the task was last updated
- `status`: string - Task status: 'todo', 'in_progress', 'completed'

## IV. Chat & Conversation Tables (Phase 3)

### conversations
- `id`: integer (SERIAL PK) - Conversation identifier
- `user_id`: string (FK -> users.id) - User who started the conversation
- `project_id`: integer (FK -> projects.id) - Project context for the conversation (nullable)
- `title`: string - Conversation title
- `created_at`: timestamp
- `updated_at`: timestamp

### messages
- `id`: integer (SERIAL PK) - Message identifier
- `conversation_id`: integer (FK -> conversations.id) - Conversation this message belongs to
- `user_id`: string (FK -> users.id) - User who sent the message
- `role`: string (user|assistant|system|tool) - Role of the message sender
- `content`: text - Message content
- `message_metadata`: jsonb - Additional metadata about the message (tool calls, citations, etc.)
- `created_at`: timestamp

### prompts
- `id`: integer (SERIAL PK) - Prompt identifier
- `conversation_id`: integer (FK -> conversations.id) - Conversation this prompt belongs to
- `user_id`: string (FK -> users.id) - User who triggered the prompt
- `prompt_text`: text - The original prompt sent to the AI
- `prompt_type`: string - Type of prompt: 'task_creation', 'task_update', 'query', 'general'
- `ai_response`: text - The AI's response to the prompt
- `tool_calls`: jsonb - Tool calls made as result of the prompt
- `created_at`: timestamp
- `processed_at`: timestamp (nullable) - When the prompt was processed

## V. Additional Supporting Tables

### project_invites (Optional)
- `id`: integer (SERIAL PK) - Primary key for invite record
- `project_id`: integer (FK -> projects.id) - Reference to the project
- `inviter_id`: string (FK -> users.id) - User who sent the invite
- `email`: string - Email of invited user
- `role`: string (ENUM) - Role to be granted: 'admin', 'member', 'viewer'
- `token`: string (UNIQUE) - Unique invite token
- `expires_at`: timestamp - When the invite expires
- `created_at`: timestamp - When the invite was created

## VI. Database Relationships

### Foreign Key Constraints
- `projects.owner_id` references `users.id`
- `permissions.user_id` references `users.id`
- `permissions.project_id` references `projects.id`
- `tasks.project_id` references `projects.id`
- `tasks.creator_id` references `users.id`
- `tasks.assigned_to` references `users.id`
- `conversations.user_id` references `users.id`
- `conversations.project_id` references `projects.id`
- `messages.user_id` references `users.id`
- `messages.conversation_id` references `conversations.id`
- `prompts.conversation_id` references `conversations.id`
- `prompts.user_id` references `users.id`

## VII. Indexes for Performance
- Index on `tasks.project_id` for project-based queries
- Index on `permissions.user_id` for user-based permission checks
- Index on `permissions.project_id` for project-based permission checks
- Index on `tasks.creator_id` for creator-based queries
- Index on `tasks.assigned_to` for assignment-based queries
- Composite index on `(permissions.user_id, permissions.project_id)` for fast permission lookups
- Index on `conversations.project_id` for project-based conversations
- Index on `messages.conversation_id` for conversation message queries
- Index on `prompts.conversation_id` for conversation-based prompt queries
- Index on `prompts.user_id` for user-based prompt queries
- Index on `prompts.created_at` for chronological prompt retrieval