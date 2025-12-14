'use client';

import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { MessageSquare, LogOut, User } from 'lucide-react';

interface HeaderProps {
  onChatToggle: () => void;
  chatOpen: boolean;
}

export default function Header({ onChatToggle, chatOpen }: HeaderProps) {
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold text-gray-900">Hackathon Todo</h1>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={onChatToggle}
          className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
            chatOpen
              ? 'bg-primary-100 text-primary-700'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <MessageSquare className="h-5 w-5" />
          <span>AI Chat</span>
        </button>

        <div className="flex items-center gap-3 border-l border-gray-200 pl-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-700">
              <User className="h-4 w-4" />
            </div>
            <span className="text-sm font-medium text-gray-700">{user?.name}</span>
          </div>

          <button
            onClick={handleLogout}
            className="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
            title="Sign out"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}
