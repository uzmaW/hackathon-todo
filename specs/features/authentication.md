# Feature: Authentication (BetterAuth Integration)

## Purpose
Secure all API endpoints using BetterAuth for session management in the Next.js frontend,
with FastAPI backend validating session tokens via shared PostgreSQL database.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Frontend (Next.js)                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  BetterAuth Client (better-auth/react)                           │  │
│  │  - signIn.email(), signUp.email(), signOut()                     │  │
│  │  - useSession(), getSession()                                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│                              ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  BetterAuth Server (lib/auth.server.ts)                          │  │
│  │  - Handles /api/auth/* routes                                    │  │
│  │  - Manages sessions in PostgreSQL                                │  │
│  │  - Issues session tokens                                         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PostgreSQL (Shared)                             │
│  BetterAuth Tables (camelCase columns):                                 │
│  - "user" (id, email, name, image, emailVerified, createdAt, updatedAt) │
│  - "session" (id, token, userId, expiresAt, ipAddress, userAgent, ...)  │
│  - "account" (id, userId, providerId, accountId, ...)                   │
│  - "verification" (id, identifier, value, expiresAt, ...)               │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Backend (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Session Token Validation (auth.py)                              │  │
│  │  - Extracts token from Authorization: Bearer <token>             │  │
│  │  - Validates token by querying "session" table directly          │  │
│  │  - Checks expiration, retrieves user from "user" table           │  │
│  │  - Returns user data for authenticated requests                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Requirements

### Framework
- **BetterAuth v1.2+** with PostgreSQL adapter
- **Next.js 15** App Router for auth routes
- **FastAPI** for protected API endpoints

### Dependencies

**Frontend (Next.js):**
```json
{
  "better-auth": "^1.2.0",
  "pg": "^8.11.0"
}
```

**Backend (FastAPI):**
```
fastapi
sqlmodel
psycopg2-binary
```

### Database Schema (BetterAuth Tables)

BetterAuth requires specific tables with camelCase column names. Generate using:
```bash
npx @better-auth/cli generate  # Generate migration
npx @better-auth/cli migrate   # Apply migration
```

Tables created:
- `user` - User accounts
- `session` - Active sessions with tokens
- `account` - OAuth/social login accounts
- `verification` - Email verification tokens

## User Stories
- As a user, I can sign up with email & password
- As a user, I can log in and receive a session token
- As a user, I can log out and invalidate my session
- As a user, I can view my profile information
- As a user, I can check my session validity and expiration

## Implementation

### 1. BetterAuth Server Configuration (Next.js)

**File: `frontend/lib/auth.server.ts`**
```typescript
import { betterAuth } from 'better-auth';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export const auth = betterAuth({
  database: pool,
  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
  },
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24,     // 1 day
  },
  secret: process.env.BETTER_AUTH_SECRET,
  baseURL: process.env.BETTER_AUTH_URL,
});
```

### 2. BetterAuth API Route (Next.js)

**File: `frontend/app/api/auth/[...all]/route.ts`**
```typescript
import { auth } from '@/lib/auth.server';
import { toNextJsHandler } from 'better-auth/next-js';

export const { GET, POST } = toNextJsHandler(auth);
```

### 3. BetterAuth Client (Next.js)

**File: `frontend/lib/auth-client.ts`**
```typescript
import { createAuthClient } from 'better-auth/react';
import type { Auth } from './auth.server';

export const authClient = createAuthClient<Auth>({
  baseURL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
});

export const { signIn, signUp, signOut, useSession, getSession } = authClient;
```

### 4. FastAPI Session Validation

**File: `backend/auth.py`**

BetterAuth uses session tokens (not JWTs). FastAPI validates by querying the shared database:

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
):
    token = credentials.credentials

    # Query BetterAuth's session table directly
    session_query = text("""
        SELECT s.id, s."userId", s."expiresAt",
               u.id as user_id, u.email, u.name, u.image
        FROM session s
        JOIN "user" u ON s."userId" = u.id
        WHERE s.token = :token
    """)

    result = db.exec(session_query, params={"token": token}).first()

    if result is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check expiration
    if result.expiresAt and result.expiresAt < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Session expired")

    return UserData(result)
```

### 5. FastAPI Auth Endpoints

**File: `backend/routes/auth.py`**

```python
@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        image=current_user.image
    )

@router.get("/session", response_model=SessionResponse)
async def get_session_info(credentials, db):
    """
    Get current session information from token.

    Returns: user_id, email, name, expires_at

    Note: IP address and user agent are NOT exposed
    for security/privacy reasons (PII data protection).
    """
    session_data = verify_session_token(db, token)
    return SessionResponse(
        authenticated=True,
        user_id=session_data["user_id"],
        email=user_result.email,
        name=user_result.name,
        expires_at=session_data["expires_at"].isoformat(),
    )
```

## Security Considerations

### Session Token Handling
- Tokens are stored in `localStorage` via Zustand persist middleware
- Tokens passed in `Authorization: Bearer <token>` header
- BetterAuth handles secure token generation and storage in database

### Privacy Protection
- `/session` endpoint does NOT expose `ip_address` or `user_agent`
- These fields are PII and should only be used server-side for audit logs
- Session ID is not exposed to prevent session fixation attacks

### Password Security
- BetterAuth handles password hashing (bcrypt)
- Minimum password length: 8 characters
- Passwords never returned in API responses

## Environment Variables

**Frontend (.env):**
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/hackathon_todo
BETTER_AUTH_SECRET=your-secret-key-min-32-chars
BETTER_AUTH_URL=http://localhost:3000
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend (.env):**
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/hackathon_todo
```

## API Endpoints

### BetterAuth Routes (Next.js /api/auth/*)
- `POST /api/auth/sign-up/email` - Register new user
- `POST /api/auth/sign-in/email` - Login with email/password
- `POST /api/auth/sign-out` - Logout and invalidate session
- `GET /api/auth/session` - Get current BetterAuth session

### FastAPI Auth Routes (/api/auth/*)
- `GET /api/auth/me` - Get current user profile (requires auth)
- `GET /api/auth/session` - Validate session and get expiration info (requires auth)

## Acceptance Criteria

- [ ] BetterAuth tables created via CLI migration
- [ ] Sign up creates user in `user` table with hashed password
- [ ] Sign in creates session in `session` table with token
- [ ] Sign out removes/invalidates session
- [ ] FastAPI validates session tokens against database
- [ ] `/api/auth/me` returns user profile for valid sessions
- [ ] `/api/auth/session` returns session info with expiration
- [ ] Invalid/expired tokens return 401 Unauthorized
- [ ] Passwords are hashed using bcrypt
- [ ] PII (IP, user agent) not exposed in API responses
- [ ] Session tokens stored securely in frontend (Zustand persist)
