'use client';

import { useTasks } from '@/hooks/useTasks';
import KanbanColumn from './KanbanColumn';
import type { TaskStatus } from '@/types';

const columns: { id: TaskStatus; title: string; color: string }[] = [
  { id: 'todo', title: 'To Do', color: 'bg-gray-100' },
  { id: 'in_progress', title: 'In Progress', color: 'bg-blue-100' },
  { id: 'completed', title: 'Completed', color: 'bg-green-100' },
];

export default function KanbanBoard() {
  const { getTasksByStatus, moveTask } = useTasks();

  const handleDrop = async (
    taskId: number,
    newStatus: TaskStatus,
    newPosition: number
  ) => {
    await moveTask(taskId, newStatus, newPosition);
  };

  return (
    <div className="flex h-full gap-6 overflow-x-auto pb-4">
      {columns.map((column) => (
        <KanbanColumn
          key={column.id}
          id={column.id}
          title={column.title}
          color={column.color}
          tasks={getTasksByStatus(column.id)}
          onDrop={handleDrop}
        />
      ))}
    </div>
  );
}
