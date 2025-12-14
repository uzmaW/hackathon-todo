/**
 * Projects hook with state management.
 */

import { create } from 'zustand';
import type { ProjectWithRole, ProjectCreate, ProjectUpdate, RoleEnum } from '@/types';
import { api } from '@/lib/api';

interface ProjectsState {
  projects: ProjectWithRole[];
  currentProject: ProjectWithRole | null;
  isLoading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  selectProject: (projectId: number | null) => void;
  createProject: (data: ProjectCreate) => Promise<ProjectWithRole>;
  updateProject: (id: number, data: ProjectUpdate) => Promise<void>;
  deleteProject: (id: number) => Promise<void>;
  addMember: (projectId: number, userId: string, role: RoleEnum) => Promise<void>;
  removeMember: (projectId: number, userId: string) => Promise<void>;
}

export const useProjects = create<ProjectsState>((set, get) => ({
  projects: [],
  currentProject: null,
  isLoading: false,
  error: null,

  fetchProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const projects = await api.projects.list();
      set({ projects, isLoading: false });

      // Auto-select first project if none selected
      if (!get().currentProject && projects.length > 0) {
        set({ currentProject: projects[0] });
      }
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch projects',
        isLoading: false
      });
    }
  },

  selectProject: (projectId: number | null) => {
    if (projectId === null) {
      set({ currentProject: null });
      return;
    }
    const project = get().projects.find(p => p.id === projectId) || null;
    set({ currentProject: project });
  },

  createProject: async (data: ProjectCreate) => {
    set({ isLoading: true, error: null });
    try {
      const project = await api.projects.create(data);
      set(state => ({
        projects: [project, ...state.projects],
        currentProject: project,
        isLoading: false
      }));
      return project;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to create project',
        isLoading: false
      });
      throw error;
    }
  },

  updateProject: async (id: number, data: ProjectUpdate) => {
    set({ isLoading: true, error: null });
    try {
      const updated = await api.projects.update(id, data);
      set(state => ({
        projects: state.projects.map(p =>
          p.id === id ? { ...p, ...updated } : p
        ),
        currentProject: state.currentProject?.id === id
          ? { ...state.currentProject, ...updated }
          : state.currentProject,
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to update project',
        isLoading: false
      });
      throw error;
    }
  },

  deleteProject: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      await api.projects.delete(id);
      set(state => {
        const projects = state.projects.filter(p => p.id !== id);
        return {
          projects,
          currentProject: state.currentProject?.id === id
            ? projects[0] || null
            : state.currentProject,
          isLoading: false,
        };
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to delete project',
        isLoading: false
      });
      throw error;
    }
  },

  addMember: async (projectId: number, userId: string, role: RoleEnum) => {
    set({ error: null });
    try {
      await api.projects.addMember(projectId, userId, role);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to add member',
      });
      throw error;
    }
  },

  removeMember: async (projectId: number, userId: string) => {
    set({ error: null });
    try {
      await api.projects.removeMember(projectId, userId);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to remove member',
      });
      throw error;
    }
  },
}));
