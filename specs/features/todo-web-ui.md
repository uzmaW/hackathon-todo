# Feature: Todo Web UI (Kanban + Chat + Projects)

## Purpose
Provide a responsive Next.js 15 web UI mirroring the [Lovable Template](https://id-preview--a61eaf9f-8d62-48d6-8b73-445f78660142.lovable.app/).

## Components
### 1. Project Navigation
- **Sidebar:** Project list with create/new project button
- **Project Switching:** Dropdown to switch between projects
- **Project Creation:** Modal form for creating new projects

### 2. Kanban Board
- **Columns:** To Do, In Progress, Completed.
- **Cards:** Draggable items showing Title, Due Date, Project, and "AI Provenance" badge.
- **Logic:** Dragging a card triggers `updateTodo(status)` mutation.

### 3. Chat Sidebar (ChatView)
- **Location:** Collapsible right-hand panel.
- **Tech:** OpenAI ChatKit + RAG Citations.
- **Features:**
  - "Draft Queue" overlay for approving AI tasks.
  - "Knowledge Dropzone" for uploading PDFs to RAG.
  - Project context awareness for AI suggestions.

### 4. Project Management Panel
- **Location:** Collapsible left-hand panel or dedicated project page
- **Features:**
  - List of user's projects
  - Project details and member management
  - Project creation and editing forms

## Behavior
- **Optimistic UI:** Board updates immediately on drag; reverts if server fails.
- **Real-time:** Listens to `todoCreated`, `todoUpdated`, `projectCreated`, and `projectUpdated` subscriptions.
- **Project Context:** UI filters tasks by selected project by default.

## Acceptance Criteria
- [ ] User can create and manage projects.
- [ ] User can switch between projects in the UI.
- [ ] User can drag a task from "To Do" to "Done".
- [ ] User can see AI "Thinking..." chips in the Chat Sidebar.
- [ ] User can upload PDFs to the Knowledge Dropzone.
- [ ] User can approve/reject AI-generated tasks in the Draft Queue.
- [ ] UI updates immediately on drag operations (optimistic updates).
- [ ] Real-time updates work for task changes made by other users.
- [ ] Project filtering works correctly for task display.
- [ ] Project members can see tasks within their projects.

## UI/UX Requirements (Lovable UI)
- **Responsive Design:** Works on mobile, tablet, and desktop
- **Visual Feedback:** Smooth transitions and loading states
- **Accessibility:** Full keyboard navigation and screen reader support
- **Performance:** Fast loading and smooth interactions
- **Consistency:** Follows the Lovable Template design system
- **Project Context:** Clear visual indication of current project