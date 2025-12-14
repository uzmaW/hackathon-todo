/**
 * API client for the Hackathon Todo backend.
 */

import type {
  User,
  LoginRequest,
  LoginResponse,
  SignupResponse,
  Project,
  ProjectWithRole,
  ProjectCreate,
  ProjectUpdate,
  Task,
  TaskCreate,
  TaskUpdate,
  TaskStatus,
  Conversation,
  ConversationCreate,
  ConversationWithMessages,
  Message,
  ChatRequest,
  ChatResponse,
  Prompt,
  DeleteResponse,
  RoleEnum,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Get the stored session token from auth storage.
 * BetterAuth stores the session token which is used for API authentication.
 */
function getToken(): string | null {
  if (typeof window === 'undefined') return null;

  // Get token from auth-storage (Zustand persisted state)
  try {
    const authStorage = localStorage.getItem('auth-storage');
    if (authStorage) {
      const parsed = JSON.parse(authStorage);
      return parsed.state?.sessionToken || null;
    }
  } catch {
    // Ignore parse errors
  }

  return null;
}

/**
 * Set the auth token (for backward compatibility).
 * Note: With BetterAuth, tokens are managed automatically.
 */
export function setToken(token: string): void {
  // BetterAuth manages tokens via cookies and session
  // This is kept for backward compatibility
  console.warn('setToken is deprecated with BetterAuth. Tokens are managed automatically.');
}

/**
 * Clear the auth token (for backward compatibility).
 * Note: With BetterAuth, use signOut() instead.
 */
export function clearToken(): void {
  // BetterAuth manages tokens via cookies and session
  // This is kept for backward compatibility
  console.warn('clearToken is deprecated with BetterAuth. Use signOut() instead.');
}

/**
 * Make an authenticated API request.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.detail || error.error || 'Request failed');
  }

  return response.json();
}

// Auth API - Now handled by BetterAuth
// These endpoints are kept for backward compatibility but authentication
// should be done via the BetterAuth client (signIn, signUp, signOut)
export const auth = {
  // Deprecated: Use signUp from '@/lib/auth-client' instead
  signup: (data: { email: string; password: string; name: string }) => {
    console.warn('auth.signup is deprecated. Use signUp from @/lib/auth-client');
    return Promise.reject(new Error('Use BetterAuth signUp instead'));
  },

  // Deprecated: Use signIn from '@/lib/auth-client' instead
  login: (data: LoginRequest) => {
    console.warn('auth.login is deprecated. Use signIn from @/lib/auth-client');
    return Promise.reject(new Error('Use BetterAuth signIn instead'));
  },

  // Deprecated: Use signOut from '@/lib/auth-client' instead
  logout: () => {
    console.warn('auth.logout is deprecated. Use signOut from @/lib/auth-client');
    return Promise.reject(new Error('Use BetterAuth signOut instead'));
  },

  // Get current user from session - still useful for API calls
  me: () => apiRequest<User>('/api/auth/me'),

  // Token refresh is handled automatically by BetterAuth
  refresh: () => {
    console.warn('auth.refresh is deprecated. BetterAuth handles token refresh automatically');
    return Promise.reject(new Error('BetterAuth handles refresh automatically'));
  },
};

// Projects API
export const projects = {
  list: (role?: RoleEnum) =>
    apiRequest<ProjectWithRole[]>(
      `/api/projects${role ? `?role=${role}` : ''}`
    ),

  get: (id: number) => apiRequest<ProjectWithRole>(`/api/projects/${id}`),

  create: (data: ProjectCreate) =>
    apiRequest<ProjectWithRole>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: ProjectUpdate) =>
    apiRequest<Project>(`/api/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    apiRequest<DeleteResponse>(`/api/projects/${id}`, {
      method: 'DELETE',
    }),

  addMember: (projectId: number, userId: string, role: RoleEnum = 'member') =>
    apiRequest<{ message: string }>(
      `/api/projects/${projectId}/members?user_id=${userId}&role=${role}`,
      { method: 'POST' }
    ),

  removeMember: (projectId: number, userId: string) =>
    apiRequest<{ message: string }>(
      `/api/projects/${projectId}/members/${userId}`,
      { method: 'DELETE' }
    ),
};

// Tasks API
export const tasks = {
  list: (params?: { project_id?: number; status?: TaskStatus; sort?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.project_id) searchParams.set('project_id', String(params.project_id));
    if (params?.status) searchParams.set('status', params.status);
    if (params?.sort) searchParams.set('sort', params.sort);
    const query = searchParams.toString();
    return apiRequest<Task[]>(`/api/tasks${query ? `?${query}` : ''}`);
  },

  get: (id: number) => apiRequest<Task>(`/api/tasks/${id}`),

  create: (data: TaskCreate) =>
    apiRequest<Task>('/api/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: TaskUpdate) =>
    apiRequest<Task>(`/api/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    apiRequest<DeleteResponse>(`/api/tasks/${id}`, {
      method: 'DELETE',
    }),

  updatePosition: (id: number, newPosition: number, newStatus?: TaskStatus) => {
    const params = new URLSearchParams({ new_position: String(newPosition) });
    if (newStatus) params.set('new_status', newStatus);
    return apiRequest<Task>(`/api/tasks/${id}/position?${params.toString()}`, {
      method: 'PUT',
    });
  },
};

// Conversations API
export const conversations = {
  list: (params?: { project_id?: number; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.project_id) searchParams.set('project_id', String(params.project_id));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    const query = searchParams.toString();
    return apiRequest<Conversation[]>(`/api/conversations${query ? `?${query}` : ''}`);
  },

  get: (id: number) => apiRequest<ConversationWithMessages>(`/api/conversations/${id}`),

  create: (data: ConversationCreate) =>
    apiRequest<Conversation>('/api/conversations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMessages: (id: number, params?: { limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    const query = searchParams.toString();
    return apiRequest<Message[]>(
      `/api/conversations/${id}/messages${query ? `?${query}` : ''}`
    );
  },
};

// Chat API
export const chat = {
  send: (userId: string, data: ChatRequest) =>
    apiRequest<ChatResponse>(`/api/${userId}/chat`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

// Prompts API
export const prompts = {
  list: (params?: { conversation_id?: number; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.conversation_id)
      searchParams.set('conversation_id', String(params.conversation_id));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    const query = searchParams.toString();
    return apiRequest<Prompt[]>(`/api/prompts${query ? `?${query}` : ''}`);
  },

  get: (id: number) => apiRequest<Prompt>(`/api/prompts/${id}`),
};

// Export all as a single api object
export const api = {
  auth,
  projects,
  tasks,
  conversations,
  chat,
  prompts,
  setToken,
  clearToken,
};

export default api;
