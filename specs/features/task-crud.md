# Feature: Task CRUD (Project-Based with Permission-Gated Access)

## Pre-Conditions
- `current_user.id` is available in the request state via BetterAuth JWT.
- Database connection to PostgreSQL is active.
- User must have appropriate permissions in the project to perform operations on tasks.

## User Stories
- As any authenticated user, I can create a new task in projects I have access to
- As any user in the project, I can view all tasks in the project based on my role
- As any user with member or admin role, I can update tasks in the project
- As a project admin, I can delete any task in the project
- As any user, I can mark tasks as complete if I have access

## Execution Logic (Pseudocode)

### Permission Check Helper
FUNCTION check_user_permission(user_id, project_id, required_role):
    1. SELECT role FROM permissions WHERE user_id = `user_id` AND project_id = `project_id`.
    2. IF no record found -> RETURN false.
    3. IF required_role = 'admin' AND role != 'admin' -> RETURN false.
    4. IF required_role = 'member' AND role NOT IN ('admin', 'member') -> RETURN false.
    5. IF required_role = 'viewer' AND role NOT IN ('admin', 'member', 'viewer') -> RETURN true.
    6. RETURN true.

### CREATE [POST /api/tasks]
- **Input**: `title` (required), `description` (optional), `project_id` (required).
- **Security**:
    - IF NOT check_user_permission(`current_user.id`, `project_id`, 'member') -> RAISE 403 Forbidden.
- **Process**:
    1. SET `creator_id` = `current_user.id`.
    2. SET `project_id` = `input.project_id`.
    3. SET `position` = (SELECT COUNT(*) FROM tasks WHERE project_id = `input.project_id`).
    4. INSERT INTO `tasks`.
    5. **Dapr Publish**: Topic `task.created` with payload `{task_id, project_id, creator_id, title}`.
- **Return**: The created Task object.

### READ [GET /api/tasks]
- **Security**:
    - IF `project_id` query parameter provided:
        - IF NOT check_user_permission(`current_user.id`, `project_id`, 'viewer') -> RAISE 403 Forbidden.
    - ELSE:
        - Only return tasks from projects where user has viewer+ access.
- **Process**:
    - SELECT * FROM `tasks`
    - WHERE `project_id` IN (SELECT project_id FROM permissions WHERE user_id = `current_user.id`)
    - ORDER BY `position` ASC.

### UPDATE [PUT /api/tasks/{id}]
- **Input**: `id` (path), `data` (body).
- **Security**:
    - SET `task_project_id` = (SELECT project_id FROM tasks WHERE id = `{id}`).
    - IF NOT check_user_permission(`current_user.id`, `task_project_id`, 'member') -> RAISE 403 Forbidden.
- **Process**:
    1. UPDATE `tasks` SET fields WHERE `id` = `{id}`.
    2. **Dapr Publish**: Topic `task.updated` with delta change.

### DELETE [DELETE /api/tasks/{id}]
- **Security**:
    - SET `task_project_id` = (SELECT project_id FROM tasks WHERE id = `{id}`).
    - IF NOT check_user_permission(`current_user.id`, `task_project_id`, 'admin') -> RAISE 403 Forbidden.
- **Process**:
    1. DELETE FROM `tasks` WHERE `id` = `{id}`.
    2. **Dapr Publish**: Topic `task.deleted`.

## Acceptance Criteria

### Create Task
- Title is required (1-200 chars)
- Project ID is required and user must have member+ access to project
- Description is optional (max 1000 chars)
- Any authenticated user with project access can create tasks
- Response returns created task with id, timestamps, and project association
- Task position is set based on project's current task count
- Event published to `task.created` topic via Dapr

### View Tasks
- Users can see all tasks in projects they have viewer+ access to
- Project admins can see all tasks in projects they admin
- Tasks ordered by position in ascending order
- Support query parameters:
  - project_id: filter by project (if authorized)
  - status: "all" | "pending" | "completed"
  - sort: "created" | "title" | "due_date"
- Response fields: id, title, description, completed, creator_id, project_id, created_at, updated_at

### Update Task
- Allow updating title and/or description and completed flag
- Validate title length
- Return updated task
- Any user with member+ role in the project can update tasks
- Event published to `task.updated` topic via Dapr

### Delete Task
- Only project admins can delete tasks
- Soft delete is acceptable for phase1; can be hard delete later
- Return a success object with task_id and status
- Event published to `task.deleted` topic via Dapr

### Security
- All endpoints require JWT auth from BetterAuth
- CREATE: User must have member+ role in the target project
- READ: User must have viewer+ role in the project(s)
- UPDATE: User must have member+ role in the project containing the task
- DELETE: User must have admin role in the project containing the task
- Admin users have elevated permissions to manage all projects and tasks