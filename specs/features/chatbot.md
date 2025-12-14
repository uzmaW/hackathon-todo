# Feature: RAG-Integrated AI Chatbot

## Purpose
Enable users to manage tasks using natural language, augmented by their personal documents/history.

## Technology Stack

### Frontend - OpenAI ChatKit-Plus
- **Package:** `@openai/chatkit-plus` (Next.js components)
- **Features:**
  - Streaming message display
  - Tool call visualization
  - Citation rendering for RAG
  - Thinking/loading indicators
  - File upload integration
  - Markdown rendering

### Backend - RAG Pipeline
- **Vector Database:** Qdrant (self-hosted or cloud)
- **Embeddings:** OpenAI `text-embedding-3-small` (1536 dimensions)
- **PDF Parsing:** PyPDF2 or pdfplumber
- **Text Chunking:** LangChain RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)
- **LLM:** OpenAI GPT-4o-mini with function calling

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  OpenAI ChatKit-Plus Components                            │  │
│  │  ├── <ChatWindow />      - Main chat interface             │  │
│  │  ├── <MessageList />     - Streaming messages              │  │
│  │  ├── <ToolCallCard />    - Tool execution display          │  │
│  │  ├── <CitationBlock />   - RAG source citations            │  │
│  │  ├── <DraftQueue />      - Task approval overlay           │  │
│  │  └── <KnowledgeDropzone /> - PDF upload area               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  /api/documents/upload  - PDF ingestion endpoint         │   │
│  │  /api/{user_id}/chat    - RAG-enhanced chat endpoint     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  RAG Pipeline                                            │   │
│  │  1. Parse PDF → Extract text                             │   │
│  │  2. Chunk text → 1000 chars with 200 overlap             │   │
│  │  3. Embed chunks → OpenAI text-embedding-3-small         │   │
│  │  4. Store in Qdrant → user_id isolated collections       │   │
│  │  5. Query → Vector search top 3 chunks                   │   │
│  │  6. Augment → Inject context into LLM prompt             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  AI Agent (OpenAI GPT-4o-mini + Function Calling)        │   │
│  │  - Receives: User Query + RAG Context + Conversation     │   │
│  │  - Executes: MCP Tools (add_task, list_tasks, etc.)      │   │
│  │  - Returns: Response + Citations + Tool Calls            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Qdrant (Vector DB)                          │
│  - Collection per user: user_{user_id}_documents                 │
│  - Vector dimension: 1536                                        │
│  - Metadata: filename, page_number, chunk_index, upload_date     │
│  - < 200ms retrieval latency                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Logic Flow (RAG + MCP)
1. **Ingest:** User uploads file -> PDF Parsed -> Chunked -> Embedded -> Stored in Qdrant
2. **Retrieve:** User asks question -> Embed query -> Vector Search -> Top 3 Chunks retrieved
3. **Reason:** Agent receives `(User Query + Retrieved Context + Conversation History)`
4. **Act:** Agent calls MCP Tool (`add_task`) or answers question with citations
5. **Respond:** Return response with tool calls and RAG citations

## User Stories
- "Based on the marketing PDF I uploaded, create a task list for launch."
- "What did I finish last week regarding the backend?" (Requires RAG on Audit Logs)
- "Summarize the requirements from the uploaded document."
- "Create tasks from the action items in my meeting notes."

## Technical Constraints
- **Latency:** Vector retrieval must happen in < 200ms
- **Fallback:** If Qdrant is down, proceed with standard Chat logic (no RAG)
- **File Size:** Max 10MB per PDF upload
- **Chunk Size:** 1000 characters with 200 character overlap
- **Context Window:** Top 3 chunks injected (≈3000 tokens max)

## UI/UX Requirements (OpenAI ChatKit-Plus)

### Chat Interface
- Clean, responsive chat interface using ChatKit-Plus components
- Streaming message display with typing indicators
- Markdown rendering for formatted responses
- Code block syntax highlighting

### Visual Feedback
- "Thinking..." indicator during AI processing
- Tool call cards showing what actions the AI is taking
- Progress bar for file uploads
- Smooth transitions and animations

### RAG Citations
- Inline citation markers [1], [2], [3] in responses
- Expandable citation blocks showing source text
- Link to original document/page number
- Visual distinction between RAG-augmented and standard responses

### Draft Preview (Draft Queue)
- Overlay panel for AI-suggested tasks
- Preview card showing: title, description, project
- Approve / Edit / Reject buttons per draft
- Bulk approve/reject actions
- Rationale summary from AI explaining suggestion

### Knowledge Dropzone
- Drag-and-drop file upload area
- Supported formats: PDF (future: DOCX, TXT, MD)
- Upload progress indicator
- List of uploaded documents with delete option
- Visual feedback on successful ingestion

### Error Handling
- Friendly error messages with recovery options
- Retry button for failed operations
- Fallback UI when RAG is unavailable
- Connection status indicator

### Accessibility
- Full keyboard navigation
- Screen reader announcements for state changes
- Focus management in overlays
- ARIA labels on interactive elements

## High-level Behavior
- Agents must call well-defined MCP tools: add_task, list_tasks, complete_task, update_task, delete_task
- Agent confirms actions and handles errors gracefully
- Server remains stateless: all conversation state is stored in DB
- All chat functionality must utilize OpenAI ChatKit-Plus (as per constitution)
- RAG context is injected transparently; user doesn't need to specify "search my documents"

## MCP Tools (summary)
- `add_task(user_id, project_id, title, description?)` → { task_id, status, title }
- `list_tasks(user_id, project_id?, status?)` → [ task objects ]
- `complete_task(user_id, task_id)` → { task_id, status, title }
- `delete_task(user_id, task_id)` → { task_id, status, title }
- `update_task(user_id, task_id, title?, description?, status?)` → { task_id, status, title }
- `get_user_projects(user_id)` → [ project objects ]

## Agent Policies
- Call list_tasks when user references a task by name or when context is ambiguous
- Confirm destructive actions (delete) before executing, if user intent is ambiguous
- Use filters if user asks "show pending" or "show completed"
- Always include rationale_summary explaining why a tool was called
- Cite RAG sources when answering document-based questions

## Conversation Flow (Stateless)
1. Client POST /api/{user_id}/chat with message & optional conversation_id
2. Server retrieves conversation messages (if conversation_id)
3. Server stores user message
4. **Server queries Qdrant for relevant context (RAG)**
5. Server composes messages with RAG context & runs agent with MCP tools
6. Agent may call tools; server executes tool calls and returns results to agent
7. Store assistant response, tool call metadata, and RAG citations
8. Return assistant text + tool calls + citations to client

## API Endpoints

### Document Ingestion
```
POST /api/documents/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

Request:
  - file: PDF file (max 10MB)
  - project_id: optional project context

Response:
{
  "document_id": "uuid",
  "filename": "meeting-notes.pdf",
  "chunks_created": 15,
  "status": "ingested"
}
```

### RAG-Enhanced Chat
```
POST /api/{user_id}/chat
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "conversation_id": 123,  // optional
  "message": "Create tasks from my uploaded document",
  "include_rag": true      // optional, default true
}

Response:
{
  "conversation_id": 123,
  "response": "Based on your document, I've identified 3 action items...",
  "tool_calls": [
    {"name": "add_task", "arguments": {...}, "result": {...}}
  ],
  "citations": [
    {"index": 1, "text": "Action item: Review budget...", "source": "meeting-notes.pdf", "page": 2}
  ]
}
```

### List Documents
```
GET /api/documents
Authorization: Bearer <token>

Response:
{
  "documents": [
    {"id": "uuid", "filename": "meeting-notes.pdf", "uploaded_at": "...", "chunks": 15}
  ]
}
```

### Delete Document
```
DELETE /api/documents/{document_id}
Authorization: Bearer <token>

Response:
{"status": "deleted", "document_id": "uuid"}
```

## Database Models

### Document Model
```python
class Document(SQLModel, table=True):
    id: str = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    project_id: Optional[int] = Field(foreign_key="project.id")
    filename: str
    file_size: int
    chunk_count: int
    qdrant_collection: str
    uploaded_at: datetime
    status: str  # 'processing', 'ingested', 'failed'
```

## Acceptance Criteria
- [ ] User can upload PDF files via Knowledge Dropzone
- [ ] PDFs are parsed, chunked, and embedded into Qdrant
- [ ] Chat queries automatically retrieve relevant document context
- [ ] AI responses include citation markers for RAG sources
- [ ] Citations are expandable to show source text
- [ ] Draft Queue shows AI-suggested tasks for approval
- [ ] Tool calls are visualized in the chat interface
- [ ] Fallback to standard chat when Qdrant is unavailable
- [ ] Vector retrieval completes in < 200ms
- [ ] Documents are isolated by user_id