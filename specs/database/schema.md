# Database Schema

## Tables

### users
- id: string (PK)
- email: string (unique)
- name: string
- created_at: timestamp

### tasks
- id: integer (PK)
- user_id: string (FK -> users.id)
- title: string (not null)
- description: text (nullable)
- completed: boolean (default false)
- created_at: timestamp
- updated_at: timestamp
- deleted_at: timestamp (nullable) — optional soft delete

### conversations (phase3)
- id: integer (PK)
- user_id: string (FK)
- created_at: timestamp
- updated_at: timestamp

### messages (phase3)
- id: integer (PK)
- conversation_id: integer (FK -> conversations.id)
- user_id: string (FK)
- role: string (user|assistant|system|tool)
- content: text
- created_at: timestamp

## Indexes
- tasks(user_id)
- tasks(completed)
- messages(conversation_id)