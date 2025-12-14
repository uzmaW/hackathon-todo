'use client';

import { useEffect, ReactNode, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';

interface AuthProviderProps {
  children: ReactNode;
}

// Routes that don't require authentication
const publicRoutes = ['/', '/login', '/signup'];

/**
 * AuthProvider component that handles authentication state
 * and protects routes that require authentication.
 *
 * Uses BetterAuth for session management.
 */
export default function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, fetchSession } = useAuth();
  const hasCheckedSession = useRef(false);

  useEffect(() => {
    // Try to fetch session on mount (only once)
    if (!hasCheckedSession.current && !isAuthenticated && !isLoading) {
      hasCheckedSession.current = true;
      fetchSession();
    }
  }, [isAuthenticated, isLoading, fetchSession]);

  useEffect(() => {
    // Redirect logic
    if (!isLoading) {
      const isPublicRoute = publicRoutes.includes(pathname);

      if (!isAuthenticated && !isPublicRoute) {
        // Redirect to login if trying to access protected route
        router.push('/login');
      } else if (isAuthenticated && (pathname === '/login' || pathname === '/signup')) {
        // Redirect to dashboard if already authenticated
        router.push('/dashboard');
      }
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  // Show loading state while checking auth
  if (isLoading && !publicRoutes.includes(pathname)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}
