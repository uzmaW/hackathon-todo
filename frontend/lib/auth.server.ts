/**
 * BetterAuth server configuration for Next.js.
 *
 * This configures BetterAuth with PostgreSQL database adapter.
 * The auth tables (user, session, account, verification) are managed by BetterAuth.
 */

import { betterAuth } from 'better-auth';
import { Pool } from 'pg';

/**
 * PostgreSQL connection pool for BetterAuth.
 * Uses the same database as the FastAPI backend.
 */
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/hackathon_todo',
});

/**
 * BetterAuth server instance.
 *
 * Configuration:
 * - Uses PostgreSQL for session/user storage
 * - Email/password authentication enabled
 * - JWT tokens are used for API authentication
 */
export const auth = betterAuth({
  database: pool,
  emailAndPassword: {
    enabled: true,
    // Minimum password length
    minPasswordLength: 8,
  },
  session: {
    // Session expires in 7 days
    expiresIn: 60 * 60 * 24 * 7,
    // Update session expiry on each request
    updateAge: 60 * 60 * 24,
    // Cookie settings
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5, // 5 minutes cache
    },
  },
  // Secret for signing tokens - must match BETTER_AUTH_SECRET env var
  secret: process.env.BETTER_AUTH_SECRET,
  // Base URL for auth endpoints
  baseURL: process.env.BETTER_AUTH_URL || 'http://localhost:3000',
  // Trust the host header (for reverse proxies)
  trustedOrigins: [
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  ],
});

/**
 * Export auth type for client-side type inference.
 */
export type Auth = typeof auth;
