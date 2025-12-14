'use client';

import { useState } from 'react';
import type { Task } from '@/types';
import { Calendar, User, Sparkles } from 'lucide-react';
import { cn, formatDate, truncate } from '@/lib/utils';
import TaskDetailModal from '../tasks/TaskDetailModal';

interface TaskCardProps {
  task: Task;
}

export default function TaskCard({ task }: TaskCardProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [showDetail, setShowDetail] = useState(false);

  const handleDragStart = (e: React.DragEvent) => {
    setIsDragging(true);
    e.dataTransfer.setData('taskId', task.id.toString());
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragEnd = () => {
    setIsDragging(false);
  };

  // Check if task was created by AI (placeholder logic)
  const isAIGenerated = task.creator_id?.startsWith('ai-');

  return (
    <>
      <div
        draggable
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onClick={() => setShowDetail(true)}
        className={cn(
          'cursor-pointer rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all hover:shadow-md',
          isDragging && 'opacity-50 rotate-2 scale-105'
        )}
      >
        <div className="mb-2 flex items-start justify-between gap-2">
          <h4 className="font-medium text-gray-900" title={task.title}>
            {truncate(task.title, 50)}
          </h4>
          {isAIGenerated && (
            <span
              className="flex items-center gap-1 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700"
              title="AI Generated"
            >
              <Sparkles className="h-3 w-3" />
              AI
            </span>
          )}
        </div>

        {task.description && (
          <p className="mb-3 text-sm text-gray-600">
            {truncate(task.description, 80)}
          </p>
        )}

        <div className="flex items-center gap-3 text-xs text-gray-500">
          {task.due_date && (
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDate(task.due_date)}
            </span>
          )}
          {task.assigned_to && (
            <span className="flex items-center gap-1">
              <User className="h-3 w-3" />
              Assigned
            </span>
          )}
        </div>
      </div>

      {showDetail && (
        <TaskDetailModal task={task} onClose={() => setShowDetail(false)} />
      )}
    </>
  );
}
