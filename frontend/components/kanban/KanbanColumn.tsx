'use client';

import { useState } from 'react';
import type { Task, TaskStatus } from '@/types';
import TaskCard from './TaskCard';
import { cn } from '@/lib/utils';

interface KanbanColumnProps {
  id: TaskStatus;
  title: string;
  color: string;
  tasks: Task[];
  onDrop: (taskId: number, newStatus: TaskStatus, newPosition: number) => void;
}

export default function KanbanColumn({
  id,
  title,
  color,
  tasks,
  onDrop,
}: KanbanColumnProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const taskId = parseInt(e.dataTransfer.getData('taskId'), 10);
    if (isNaN(taskId)) return;

    // Calculate new position (end of column)
    const newPosition = tasks.length;
    onDrop(taskId, id, newPosition);
  };

  return (
    <div className="flex w-80 flex-shrink-0 flex-col rounded-lg bg-gray-50">
      <div className={cn('rounded-t-lg px-4 py-3', color)}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <span className="rounded-full bg-white/50 px-2 py-0.5 text-sm font-medium text-gray-700">
            {tasks.length}
          </span>
        </div>
      </div>

      <div
        className={cn(
          'flex-1 space-y-3 overflow-y-auto p-3 transition-colors',
          isDragOver && 'bg-primary-50 ring-2 ring-primary-300 ring-inset'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {tasks.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-400">
            No tasks in this column
          </div>
        ) : (
          tasks.map((task) => <TaskCard key={task.id} task={task} />)
        )}
      </div>
    </div>
  );
}
