/**
 * Authentication store using Zustand with BetterAuth integration.
 *
 * This module provides authentication state management that works with
 * BetterAuth for session management and the FastAPI backend for data.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { signIn, signUp, signOut, getSession } from './auth-client';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  sessionToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchSession: () => Promise<void>;
  setUser: (user: User | null) => void;
  getToken: () => string | null;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      sessionToken: null,

      /**
       * Login with email and password using BetterAuth.
       */
      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const result = await signIn.email({
            email,
            password,
          });

          if (result.error) {
            throw new Error(result.error.message || 'Login failed');
          }

          // Fetch the session to get user data
          await get().fetchSession();
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      /**
       * Sign up a new user using BetterAuth.
       */
      signup: async (email: string, password: string, name: string) => {
        set({ isLoading: true });
        try {
          const result = await signUp.email({
            email,
            password,
            name,
          });

          if (result.error) {
            throw new Error(result.error.message || 'Signup failed');
          }

          // Auto-login after signup
          await get().login(email, password);
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      /**
       * Logout the current user using BetterAuth.
       */
      logout: async () => {
        set({ isLoading: true });
        try {
          await signOut();
        } catch (error) {
          // Ignore errors on logout - clear local state anyway
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            sessionToken: null,
          });
        }
      },

      /**
       * Fetch the current session from BetterAuth.
       */
      fetchSession: async () => {
        set({ isLoading: true });
        try {
          const session = await getSession();

          if (session.data?.user) {
            const user: User = {
              id: session.data.user.id,
              email: session.data.user.email,
              name: session.data.user.name || '',
              image: session.data.user.image || undefined,
              created_at: session.data.user.createdAt?.toString() || '',
              updated_at: session.data.user.updatedAt?.toString() || '',
            };

            set({
              user,
              isAuthenticated: true,
              isLoading: false,
              sessionToken: session.data.session?.token || null,
            });
          } else {
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false,
              sessionToken: null,
            });
          }
        } catch (error) {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            sessionToken: null,
          });
        }
      },

      /**
       * Set user directly.
       */
      setUser: (user: User | null) => {
        set({
          user,
          isAuthenticated: !!user,
        });
      },

      /**
       * Get the current session token for API calls.
       */
      getToken: () => {
        return get().sessionToken;
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        sessionToken: state.sessionToken,
      }),
    }
  )
);

/**
 * Hook to check if user is authenticated.
 */
export function useRequireAuth() {
  const { isAuthenticated, isLoading, fetchSession } = useAuth();

  // Try to fetch session on mount if not authenticated
  if (!isAuthenticated && !isLoading) {
    fetchSession();
  }

  return { isAuthenticated, isLoading };
}
