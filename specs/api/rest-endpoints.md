# REST API Endpoints

## Base URL
- Development: http://localhost:8000

## Authentication
All protected endpoints require:
Authorization: Bearer <token>

## Tasks
GET /api/tasks
- Query: status (all|pending|completed), sort
- Response: array of Task

POST /api/tasks
- Body: { title: string, description?: string }
- Response: created Task

GET /api/tasks/{id}
- Response: Task

PUT /api/tasks/{id}
- Body: { title?, description?, completed? }
- Response: updated Task

DELETE /api/tasks/{id}
- Response: { task_id, status: "deleted" }

## Chat (phase3)
POST /api/{user_id}/chat
- Body: { conversation_id?: int, message: string }
- Response:
  {
    conversation_id: int,
    response: string,
    tool_calls: [ ... ]
  }