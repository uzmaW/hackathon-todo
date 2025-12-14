'use client';

import { useState } from 'react';
import type { Task, TaskStatus } from '@/types';
import { useTasks } from '@/hooks/useTasks';
import { useProjects } from '@/hooks/useProjects';
import { X, Trash2, Calendar, User } from 'lucide-react';
import { formatDateTime, getStatusColor, cn } from '@/lib/utils';

interface TaskDetailModalProps {
  task: Task;
  onClose: () => void;
}

export default function TaskDetailModal({ task, onClose }: TaskDetailModalProps) {
  const { updateTask, deleteTask, isLoading } = useTasks();
  const { currentProject } = useProjects();
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description || '');
  const [status, setStatus] = useState<TaskStatus>(task.status);
  const [dueDate, setDueDate] = useState(task.due_date?.split('T')[0] || '');
  const [error, setError] = useState('');

  const canEdit = currentProject?.role === 'admin' || currentProject?.role === 'member';
  const canDelete = currentProject?.role === 'admin';

  const handleSave = async () => {
    setError('');
    try {
      await updateTask(task.id, {
        title: title.trim(),
        description: description.trim() || undefined,
        status,
        due_date: dueDate || undefined,
      });
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this task?')) return;

    try {
      await deleteTask(task.id);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete task');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">Task Details</h2>
          <div className="flex items-center gap-2">
            {canDelete && (
              <button
                onClick={handleDelete}
                className="rounded-md p-2 text-red-500 hover:bg-red-50"
                title="Delete task"
              >
                <Trash2 className="h-5 w-5" />
              </button>
            )}
            <button
              onClick={onClose}
              className="rounded-md p-2 text-gray-400 hover:bg-gray-100"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {isEditing ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as TaskStatus)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                >
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Due Date</label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">{task.title}</h3>
                <span
                  className={cn(
                    'mt-2 inline-block rounded-full px-3 py-1 text-sm font-medium',
                    getStatusColor(task.status)
                  )}
                >
                  {task.status.replace('_', ' ')}
                </span>
              </div>

              {task.description && (
                <p className="text-gray-600">{task.description}</p>
              )}

              <div className="space-y-2 text-sm text-gray-500">
                {task.due_date && (
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    <span>Due: {formatDateTime(task.due_date)}</span>
                  </div>
                )}
                {task.assigned_to && (
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4" />
                    <span>Assigned to: {task.assigned_to}</span>
                  </div>
                )}
                <div className="text-xs text-gray-400">
                  Created: {formatDateTime(task.created_at)}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 border-t border-gray-200 px-6 py-4">
          {isEditing ? (
            <>
              <button
                onClick={() => setIsEditing(false)}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isLoading}
                className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
              >
                {isLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={onClose}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Close
              </button>
              {canEdit && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
                >
                  Edit
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
