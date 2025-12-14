'use client';

import { useState } from 'react';
import type { DraftTask, TaskCreate } from '@/types';
import { Check, X, Pencil, ListTodo, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DraftTaskApprovalProps {
  drafts: DraftTask[];
  onApprove: (draft: DraftTask) => Promise<void>;
  onReject: (draftId: string) => void;
  onEdit: (draft: DraftTask) => void;
}

/**
 * Draft Task Approval component for approving AI-suggested tasks
 * before they are created in the system.
 */
export default function DraftTaskApproval({
  drafts,
  onApprove,
  onReject,
  onEdit,
}: DraftTaskApprovalProps) {
  const [processingId, setProcessingId] = useState<string | null>(null);

  if (drafts.length === 0) {
    return null;
  }

  const handleApprove = async (draft: DraftTask) => {
    setProcessingId(draft.id);
    try {
      await onApprove(draft);
    } finally {
      setProcessingId(null);
    }
  };

  const pendingDrafts = drafts.filter(d => d.status === 'pending');

  if (pendingDrafts.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-gray-200 bg-amber-50 p-4">
      <div className="mb-3 flex items-center gap-2">
        <ListTodo className="h-4 w-4 text-amber-600" />
        <h3 className="text-sm font-medium text-amber-900">
          Draft Tasks ({pendingDrafts.length})
        </h3>
      </div>

      <p className="mb-3 text-xs text-amber-700">
        Review and approve AI-suggested tasks before they're created.
      </p>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {pendingDrafts.map((draft) => (
          <DraftTaskCard
            key={draft.id}
            draft={draft}
            isProcessing={processingId === draft.id}
            onApprove={() => handleApprove(draft)}
            onReject={() => onReject(draft.id)}
            onEdit={() => onEdit(draft)}
          />
        ))}
      </div>

      {/* Bulk actions */}
      {pendingDrafts.length > 1 && (
        <div className="mt-3 flex gap-2">
          <button
            onClick={async () => {
              for (const draft of pendingDrafts) {
                await handleApprove(draft);
              }
            }}
            disabled={processingId !== null}
            className="flex-1 rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            Approve All
          </button>
          <button
            onClick={() => pendingDrafts.forEach(d => onReject(d.id))}
            disabled={processingId !== null}
            className="flex-1 rounded-md bg-red-100 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-200 disabled:opacity-50"
          >
            Reject All
          </button>
        </div>
      )}
    </div>
  );
}

interface DraftTaskCardProps {
  draft: DraftTask;
  isProcessing: boolean;
  onApprove: () => void;
  onReject: () => void;
  onEdit: () => void;
}

function DraftTaskCard({
  draft,
  isProcessing,
  onApprove,
  onReject,
  onEdit,
}: DraftTaskCardProps) {
  return (
    <div className="rounded-lg bg-white border border-amber-200 p-3 shadow-sm">
      <div className="mb-2">
        <h4 className="text-sm font-medium text-gray-900">{draft.title}</h4>
        {draft.description && (
          <p className="mt-1 text-xs text-gray-600 line-clamp-2">
            {draft.description}
          </p>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onApprove}
          disabled={isProcessing}
          className={cn(
            'flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors',
            'bg-green-100 text-green-700 hover:bg-green-200',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {isProcessing ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Check className="h-3 w-3" />
          )}
          Approve
        </button>

        <button
          onClick={onEdit}
          disabled={isProcessing}
          className={cn(
            'flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors',
            'bg-gray-100 text-gray-700 hover:bg-gray-200',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          <Pencil className="h-3 w-3" />
          Edit
        </button>

        <button
          onClick={onReject}
          disabled={isProcessing}
          className={cn(
            'flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors',
            'bg-red-100 text-red-700 hover:bg-red-200',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          <X className="h-3 w-3" />
          Reject
        </button>
      </div>
    </div>
  );
}
