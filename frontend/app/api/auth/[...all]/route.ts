/**
 * BetterAuth API route handler for Next.js App Router.
 *
 * This catch-all route handles all authentication endpoints:
 * - POST /api/auth/sign-up - User registration
 * - POST /api/auth/sign-in - User login
 * - POST /api/auth/sign-out - User logout
 * - GET /api/auth/session - Get current session
 * - And other BetterAuth endpoints
 */

import { auth } from '@/lib/auth.server';
import { toNextJsHandler } from 'better-auth/next-js';

/**
 * Export GET and POST handlers for BetterAuth.
 * All auth requests are handled by BetterAuth.
 */
export const { GET, POST } = toNextJsHandler(auth);
