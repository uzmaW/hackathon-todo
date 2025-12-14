---
title: Task management API Backend
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
app_file: backend/app/main.py
pinned: false
---


# Hackathon Todo

A project-based task management system with AI chat integration, built using Spec-Driven Development (SDD).

## Features

- **Project Management**: Create and manage multiple projects with role-based access control (admin, member, viewer)
- **Task Management**: Kanban board with drag-and-drop functionality for task organization
- **AI Chat Integration**: Integrated AI assistant for natural language task management
- **Authentication**: JWT-based authentication with BetterAuth
- **Event-Driven Architecture**: Dapr integration for scalable microservices (Phase 3+)

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLModel** - SQL databases in Python with type hints
- **PostgreSQL** - Primary database
- **Alembic** - Database migrations
- **OpenAI Agents SDK** - AI chat integration
- **Dapr** - Event-driven architecture (optional)

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS
- **Zustand** - Lightweight state management
- **Lucide React** - Beautiful icons

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL (or use Docker)

### Quick Start with Docker

```bash
# Clone the repository
git clone <repo-url>
cd hackathon-todo

# Create environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit backend/.env with your settings (especially OPENAI_API_KEY)

# Start all services
docker-compose up --build
```

### Manual Setup

#### 1. Start Database Services

```bash
# Using Docker
docker-compose up -d postgres redis
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start server
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Project Structure

```
hackathon-todo/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── db.py                # Database connection
│   ├── auth.py              # JWT authentication
│   ├── models/              # SQLModel database models
│   │   ├── user.py          # User model
│   │   ├── project.py       # Project model
│   │   ├── permission.py    # Permission model (roles)
│   │   ├── task.py          # Task model
│   │   ├── conversation.py  # Chat conversation model
│   │   └── message.py       # Chat message model
│   ├── routes/              # API route handlers
│   │   ├── auth.py          # Authentication routes
│   │   ├── projects.py      # Project CRUD routes
│   │   ├── tasks.py         # Task CRUD routes
│   │   └── chat.py          # Chat/AI routes
│   ├── utils/               # Utility functions
│   └── migrations/          # Alembic migrations
├── frontend/
│   ├── app/                 # Next.js App Router
│   │   ├── login/           # Login page
│   │   ├── signup/          # Signup page
│   │   └── dashboard/       # Main dashboard
│   ├── components/          # React components
│   │   ├── ui/              # UI primitives
│   │   ├── kanban/          # Kanban board components
│   │   ├── projects/        # Project components
│   │   ├── tasks/           # Task components
│   │   └── chat/            # Chat sidebar components
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utilities and API client
│   └── types/               # TypeScript definitions
├── specs/                   # Feature specifications
│   ├── features/            # Feature specs
│   ├── api/                 # API specifications
│   └── database/            # Database schema
├── dapr/                    # Dapr configuration
└── docker-compose.yml       # Docker services
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register new user |
| POST | `/api/auth/login` | Login and get JWT |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Get current user |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List user's projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/{id}` | Get project |
| PUT | `/api/projects/{id}` | Update project |
| DELETE | `/api/projects/{id}` | Delete project |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create task |
| GET | `/api/tasks/{id}` | Get task |
| PUT | `/api/tasks/{id}` | Update task |
| DELETE | `/api/tasks/{id}` | Delete task |
| PUT | `/api/tasks/{id}/position` | Update task position |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/{user_id}/chat` | Send message to AI |
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/{id}` | Get conversation |

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hackathon_todo
BETTER_AUTH_SECRET=your-secret-key-here-min-32-chars-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OPENAI_API_KEY=your-openai-api-key
```

### Frontend (.env)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development Phases

This project follows a phased development approach:

1. **Phase 1 (Web)**: Full-stack web app with authentication, project/task CRUD
2. **Phase 2 (AI)**: AI chatbot integration with MCP tools
3. **Phase 3 (Events)**: Event-driven architecture with Kafka/Dapr
4. **Phase 4 (Cloud)**: Cloud-native deployment with Kubernetes

See `.spec-kit/config.yaml` for detailed phase definitions.

## Specifications

All features are documented in the `/specs` directory:

- `specs/features/authentication.md` - Auth requirements
- `specs/features/project-crud.md` - Project management
- `specs/features/task-crud.md` - Task management
- `specs/features/todo-web-ui.md` - Web UI requirements
- `specs/features/chatbot.md` - AI chatbot requirements
- `specs/api/api-spec.md` - API specification
- `specs/database/schema.md` - Database schema

## License

MIT
