/**
 * BetterAuth client configuration for Next.js.
 *
 * This creates the client-side auth hooks and methods
 * that communicate with the BetterAuth API routes.
 */

import { createAuthClient } from 'better-auth/react';
import type { Auth } from './auth.server';

/**
 * BetterAuth client instance.
 *
 * Configured to work with the Next.js API route at /api/auth/*
 * The baseURL should point to the Next.js app (not the FastAPI backend).
 */
export const authClient = createAuthClient<Auth>({
  baseURL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
});

/**
 * Export auth hooks and methods for use in components.
 */
export const {
  signIn,
  signUp,
  signOut,
  useSession,
  getSession,
} = authClient;
