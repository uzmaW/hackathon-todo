# Feature: Task CRUD Operations

## User Stories
- As a user, I can create a new task
- As a user, I can view all my tasks
- As a user, I can update a task
- As a user, I can delete a task
- As a user, I can mark a task complete

## Acceptance Criteria

### Create Task
- Title is required (1-200 chars)
- Description is optional (max 1000 chars)
- Task is associated with the logged-in user
- Response returns created task with id and timestamps

### View Tasks
- Only return tasks for the current user
- Support query parameters:
  - status: "all" | "pending" | "completed"
  - sort: "created" | "title" | "due_date"
- Response fields: id, title, description, completed, created_at, updated_at

### Update Task
- Allow updating title and/or description and completed flag
- Validate title length
- Return updated task

### Delete Task
- Soft delete is acceptable for phase1; can be hard delete later
- Return a success object with task_id and status

### Security
- All endpoints require JWT auth (except for phase1 console demo)