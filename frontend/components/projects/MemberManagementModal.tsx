'use client';

import { useState } from 'react';
import { X, UserPlus, Trash2, Shield, User, Eye } from 'lucide-react';
import { useProjects } from '@/hooks/useProjects';
import { cn, getRoleColor } from '@/lib/utils';
import type { RoleEnum } from '@/types';

interface MemberManagementModalProps {
  onClose: () => void;
}

export default function MemberManagementModal({ onClose }: MemberManagementModalProps) {
  const { currentProject, addMember, removeMember } = useProjects();
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<RoleEnum>('member');
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  if (!currentProject) return null;

  const isAdmin = currentProject.role === 'admin';

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setIsAdding(true);
    setError('');
    setSuccess('');

    try {
      // Note: The backend expects user_id, but for UX we use email
      // In a real implementation, you'd search for the user by email first
      await addMember(currentProject.id, email.trim(), role);
      setSuccess(`Invitation sent to ${email}`);
      setEmail('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add member');
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!confirm('Are you sure you want to remove this member?')) return;

    try {
      await removeMember(currentProject.id, userId);
      setSuccess('Member removed successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove member');
    }
  };

  const getRoleIcon = (r: RoleEnum) => {
    switch (r) {
      case 'admin':
        return <Shield className="h-4 w-4" />;
      case 'member':
        return <User className="h-4 w-4" />;
      case 'viewer':
        return <Eye className="h-4 w-4" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Manage Members
            </h2>
            <p className="text-sm text-gray-500">{currentProject.name}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {/* Add member form (admin only) */}
          {isAdmin && (
            <form onSubmit={handleAddMember} className="mb-6">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Add New Member
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="User ID or email"
                  className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as RoleEnum)}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                >
                  <option value="viewer">Viewer</option>
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                </select>
                <button
                  type="submit"
                  disabled={isAdding || !email.trim()}
                  className="inline-flex items-center gap-2 rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <UserPlus className="h-4 w-4" />
                  {isAdding ? 'Adding...' : 'Add'}
                </button>
              </div>
            </form>
          )}

          {/* Messages */}
          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}
          {success && (
            <div className="mb-4 rounded-md bg-green-50 p-3 text-sm text-green-700">
              {success}
            </div>
          )}

          {/* Role descriptions */}
          <div className="mb-4 rounded-md bg-gray-50 p-4">
            <h4 className="mb-2 text-sm font-medium text-gray-700">Role Permissions</h4>
            <ul className="space-y-1 text-xs text-gray-600">
              <li className="flex items-center gap-2">
                <Shield className="h-3 w-3 text-red-500" />
                <span><strong>Admin:</strong> Full control, can delete tasks and manage members</span>
              </li>
              <li className="flex items-center gap-2">
                <User className="h-3 w-3 text-blue-500" />
                <span><strong>Member:</strong> Can create and edit tasks</span>
              </li>
              <li className="flex items-center gap-2">
                <Eye className="h-3 w-3 text-gray-500" />
                <span><strong>Viewer:</strong> Read-only access</span>
              </li>
            </ul>
          </div>

          {/* Current user's role */}
          <div className="mb-4 flex items-center gap-2 rounded-md border border-gray-200 bg-white p-3">
            <span className="text-sm text-gray-600">Your role:</span>
            <span
              className={cn(
                'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium',
                getRoleColor(currentProject.role)
              )}
            >
              {getRoleIcon(currentProject.role)}
              {currentProject.role}
            </span>
          </div>

          {/* Info message for non-admins */}
          {!isAdmin && (
            <div className="rounded-md bg-yellow-50 p-3 text-sm text-yellow-700">
              Only project admins can add or remove members.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end border-t border-gray-200 px-6 py-4">
          <button
            onClick={onClose}
            className="rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
