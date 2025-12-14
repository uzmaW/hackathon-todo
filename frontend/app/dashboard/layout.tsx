'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useProjects } from '@/hooks/useProjects';
import ProjectSidebar from '@/components/projects/ProjectSidebar';
import ChatSidebar from '@/components/chat/ChatSidebar';
import Header from '@/components/ui/Header';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, isLoading, fetchSession, user } = useAuth();
  const { fetchProjects } = useProjects();
  const [chatOpen, setChatOpen] = useState(false);
  const hasCheckedSession = useRef(false);

  useEffect(() => {
    // Fetch session on mount if not authenticated (only once)
    if (!hasCheckedSession.current && !user && !isLoading) {
      hasCheckedSession.current = true;
      fetchSession();
    }
  }, [fetchSession, user, isLoading]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchProjects();
    }
  }, [isAuthenticated, fetchProjects]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Project Sidebar */}
      <ProjectSidebar />

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header onChatToggle={() => setChatOpen(!chatOpen)} chatOpen={chatOpen} />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>

      {/* Chat Sidebar */}
      {chatOpen && <ChatSidebar onClose={() => setChatOpen(false)} />}
    </div>
  );
}
