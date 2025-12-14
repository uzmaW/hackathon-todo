/**
 * TypeScript type definitions for the Hackathon Todo app.
 */

// User types
export interface User {
  id: string;
  email: string;
  name: string;
  image?: string;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
  name: string;
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SignupResponse {
  user_id: string;
  email: string;
  name: string;
}

// Project types
export type RoleEnum = 'admin' | 'member' | 'viewer';

export interface Project {
  id: number;
  name: string;
  description?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectWithRole extends Project {
  role: RoleEnum;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
}

// Task types
export type TaskStatus = 'todo' | 'in_progress' | 'completed';

export interface Task {
  id: number;
  title: string;
  description?: string;
  status: TaskStatus;
  due_date?: string;
  project_id: number;
  creator_id: string;
  assigned_to?: string;
  completed: boolean;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  project_id: number;
  due_date?: string;
  assigned_to?: string;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: TaskStatus;
  completed?: boolean;
  due_date?: string;
  assigned_to?: string;
  position?: number;
}

// Conversation types
export interface Conversation {
  id: number;
  title: string;
  user_id: string;
  project_id?: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationCreate {
  title: string;
  project_id?: number;
}

export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

export interface Message {
  id: number;
  conversation_id: number;
  user_id: string;
  role: MessageRole;
  content: string;
  message_metadata?: Record<string, any>;
  created_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

// Chat types
export interface ChatRequest {
  conversation_id?: number;
  message: string;
}

export interface ToolCall {
  name: string;
  arguments: Record<string, any>;
  result?: any;
}

export interface ChatResponse {
  conversation_id: number;
  response: string;
  tool_calls?: ToolCall[];
}

// Draft task for approval UI
export interface DraftTask {
  id: string;  // temporary id
  title: string;
  description?: string;
  project_id: number;
  status: 'pending' | 'approved' | 'rejected';
}

// Prompt types
export type PromptType = 'task_creation' | 'task_update' | 'query' | 'general';

export interface Prompt {
  id: number;
  conversation_id: number;
  user_id: string;
  prompt_text: string;
  prompt_type: PromptType;
  ai_response?: string;
  tool_calls?: Record<string, any>;
  created_at: string;
  processed_at?: string;
}

// Project Member types
export interface ProjectMember {
  user_id: string;
  user_name?: string;
  user_email?: string;
  role: RoleEnum;
  created_at: string;
}

// API Response types
export interface ApiError {
  error: string;
  details?: string;
}

export interface DeleteResponse {
  project_id?: number;
  task_id?: number;
  status: string;
}
