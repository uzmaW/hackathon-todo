# Feature: Project CRUD (Project-Based)

## Pre-Conditions
- `current_user.id` is available in the request state.
- Database connection to PostgreSQL is active.
- User must be a member of the project to perform operations on tasks in that project.

## User Stories
- As any authenticated user, I can create a new project
- As any user in the project, I can view all projects I belong to
- As any user in the project, I can update a project I belong to
- As a project admin, I can delete any project I admin
- As any user, I can invite other users to a project I admin

## Execution Logic (Pseudocode)

### CREATE [POST /api/projects]
- **Input**: `name` (required), `description` (optional).
- **Process**:
    1. SET `created_by` = `current_user.id`.
    2. SET `admin_user_id` = `current_user.id`.
    3. INSERT INTO `projects`.
    4. INSERT INTO `user_projects` (user_id, project_id, role='admin').
    5. **Dapr Publish**: Topic `project.created` with payload `{project_id, created_by, name}`.
- **Return**: The created Project object.

### READ [GET /api/projects]
- **Process**:
    - SELECT * FROM `projects`
    - WHERE `project_id` IN (SELECT project_id FROM user_projects WHERE user_id = `current_user.id`)
    - ORDER BY `created_at` DESC.

### UPDATE [PUT /api/projects/{id}]
- **Input**: `id` (path), `data` (body).
- **Security**:
    - IF `current_user.id` NOT IN (SELECT user_id FROM user_projects WHERE project_id = `{id}` AND role IN ('admin', 'manager')) -> RAISE 403 Forbidden.
- **Process**:
    1. UPDATE `projects` SET fields WHERE `id` = `{id}`.
    2. **Dapr Publish**: Topic `project.updated` with delta change.

### DELETE [DELETE /api/projects/{id}]
- **Security**:
    - IF `current_user.id` NOT IN (SELECT user_id FROM user_projects WHERE project_id = `{id}` AND role = 'admin') -> RAISE 403 Forbidden.
- **Process**:
    1. DELETE FROM `projects` WHERE `id` = `{id}`.
    2. DELETE FROM `user_projects` WHERE `project_id` = `{id}`.
    3. DELETE FROM `todos` WHERE `project_id` = `{id}`.
    2. **Dapr Publish**: Topic `project.deleted`.

## Acceptance Criteria

### Create Project
- Name is required (1-100 chars)
- Description is optional (max 500 chars)
- Created by current user who becomes admin
- Response returns created project with id, timestamps, and admin association
- Event published to `project.created` topic via Dapr

### View Projects
- All users can see projects they belong to
- Project admins can see all projects they admin
- Projects ordered by creation date in descending order
- Support query parameters:
  - role: filter by user role in project ('admin', 'member', 'viewer')
- Response fields: id, name, description, created_by, created_at, updated_at

### Update Project
- Allow updating name and/or description
- Validate name length
- Return updated project
- Only project admins or managers can update the project
- Event published to `project.updated` topic via Dapr

### Delete Project
- Only project admins can delete projects
- Deleting a project also removes all associated tasks and user-project relationships
- Return a success object with project_id and status
- Event published to `project.deleted` topic via Dapr

### Security
- All endpoints require JWT auth
- CREATE: Any authenticated user can create projects (becomes admin)
- READ: Users can see projects they belong to
- UPDATE: Only project admins or managers can update projects
- DELETE: Only project admins can delete projects
- Admin users have elevated permissions to manage projects