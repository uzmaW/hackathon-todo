/**
 * Tasks hook with state management.
 */

import { create } from 'zustand';
import type { Task, TaskCreate, TaskUpdate, TaskStatus } from '@/types';
import { api } from '@/lib/api';

interface TasksState {
  tasks: Task[];
  isLoading: boolean;
  error: string | null;
  fetchTasks: (projectId?: number) => Promise<void>;
  createTask: (data: TaskCreate) => Promise<Task>;
  updateTask: (id: number, data: TaskUpdate) => Promise<void>;
  deleteTask: (id: number) => Promise<void>;
  moveTask: (id: number, newStatus: TaskStatus, newPosition: number) => Promise<void>;
  getTasksByStatus: (status: TaskStatus) => Task[];
}

export const useTasks = create<TasksState>((set, get) => ({
  tasks: [],
  isLoading: false,
  error: null,

  fetchTasks: async (projectId?: number) => {
    set({ isLoading: true, error: null });
    try {
      const tasks = await api.tasks.list({ project_id: projectId });
      set({ tasks, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch tasks',
        isLoading: false
      });
    }
  },

  createTask: async (data: TaskCreate) => {
    set({ isLoading: true, error: null });
    try {
      const task = await api.tasks.create(data);
      set(state => ({
        tasks: [...state.tasks, task],
        isLoading: false
      }));
      return task;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to create task',
        isLoading: false
      });
      throw error;
    }
  },

  updateTask: async (id: number, data: TaskUpdate) => {
    // Optimistic update
    const previousTasks = get().tasks;
    set(state => ({
      tasks: state.tasks.map(t =>
        t.id === id ? { ...t, ...data, updated_at: new Date().toISOString() } : t
      ),
    }));

    try {
      const updated = await api.tasks.update(id, data);
      set(state => ({
        tasks: state.tasks.map(t => t.id === id ? updated : t),
      }));
    } catch (error) {
      // Rollback on error
      set({ tasks: previousTasks });
      set({ error: error instanceof Error ? error.message : 'Failed to update task' });
      throw error;
    }
  },

  deleteTask: async (id: number) => {
    // Optimistic update
    const previousTasks = get().tasks;
    set(state => ({
      tasks: state.tasks.filter(t => t.id !== id),
    }));

    try {
      await api.tasks.delete(id);
    } catch (error) {
      // Rollback on error
      set({ tasks: previousTasks });
      set({ error: error instanceof Error ? error.message : 'Failed to delete task' });
      throw error;
    }
  },

  moveTask: async (id: number, newStatus: TaskStatus, newPosition: number) => {
    // Optimistic update
    const previousTasks = get().tasks;
    set(state => ({
      tasks: state.tasks.map(t =>
        t.id === id
          ? { ...t, status: newStatus, position: newPosition, completed: newStatus === 'completed' }
          : t
      ),
    }));

    try {
      await api.tasks.updatePosition(id, newPosition, newStatus);
    } catch (error) {
      // Rollback on error
      set({ tasks: previousTasks });
      set({ error: error instanceof Error ? error.message : 'Failed to move task' });
      throw error;
    }
  },

  getTasksByStatus: (status: TaskStatus) => {
    return get().tasks
      .filter(t => t.status === status)
      .sort((a, b) => a.position - b.position);
  },
}));
