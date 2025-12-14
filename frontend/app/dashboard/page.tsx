'use client';

import { useEffect } from 'react';
import { useProjects } from '@/hooks/useProjects';
import { useTasks } from '@/hooks/useTasks';
import KanbanBoard from '@/components/kanban/KanbanBoard';
import CreateTaskForm from '@/components/tasks/CreateTaskForm';

export default function DashboardPage() {
  const { currentProject } = useProjects();
  const { fetchTasks, isLoading } = useTasks();

  useEffect(() => {
    if (currentProject) {
      fetchTasks(currentProject.id);
    }
  }, [currentProject, fetchTasks]);

  if (!currentProject) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900">No project selected</h2>
          <p className="mt-2 text-gray-600">
            Create a new project or select one from the sidebar to get started.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{currentProject.name}</h1>
          {currentProject.description && (
            <p className="mt-1 text-gray-600">{currentProject.description}</p>
          )}
        </div>
        <CreateTaskForm projectId={currentProject.id} />
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
        </div>
      ) : (
        <KanbanBoard />
      )}
    </div>
  );
}
