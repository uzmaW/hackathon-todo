'use client';

import { useState } from 'react';
import { useProjects } from '@/hooks/useProjects';
import { Plus, Folder, ChevronRight, Users, Settings } from 'lucide-react';
import { cn, getRoleColor } from '@/lib/utils';
import CreateProjectModal from './CreateProjectModal';
import MemberManagementModal from './MemberManagementModal';

export default function ProjectSidebar() {
  const { projects, currentProject, selectProject, isLoading } = useProjects();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMemberModal, setShowMemberModal] = useState(false);

  return (
    <>
      <aside className="flex w-64 flex-col border-r border-gray-200 bg-white">
        <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4">
          <h2 className="text-lg font-semibold text-gray-900">Projects</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
            title="Create project"
          >
            <Plus className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-auto p-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
            </div>
          ) : projects.length === 0 ? (
            <div className="py-8 text-center text-sm text-gray-500">
              No projects yet. Create one to get started!
            </div>
          ) : (
            <ul className="space-y-1">
              {projects.map((project) => (
                <li key={project.id}>
                  <button
                    onClick={() => selectProject(project.id)}
                    className={cn(
                      'flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors',
                      currentProject?.id === project.id
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    )}
                  >
                    <Folder
                      className={cn(
                        'h-5 w-5',
                        currentProject?.id === project.id
                          ? 'text-primary-500'
                          : 'text-gray-400'
                      )}
                    />
                    <div className="flex-1 overflow-hidden">
                      <div className="truncate font-medium">{project.name}</div>
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            'inline-flex rounded-full px-2 py-0.5 text-xs font-medium',
                            getRoleColor(project.role)
                          )}
                        >
                          {project.role}
                        </span>
                      </div>
                    </div>
                    {currentProject?.id === project.id && (
                      <ChevronRight className="h-4 w-4 text-primary-500" />
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Current project actions */}
        {currentProject && (
          <div className="border-t border-gray-200 p-2">
            <button
              onClick={() => setShowMemberModal(true)}
              className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-gray-600 hover:bg-gray-100"
            >
              <Users className="h-4 w-4" />
              Manage Members
            </button>
          </div>
        )}
      </aside>

      {showCreateModal && (
        <CreateProjectModal onClose={() => setShowCreateModal(false)} />
      )}

      {showMemberModal && (
        <MemberManagementModal onClose={() => setShowMemberModal(false)} />
      )}
    </>
  );
}
