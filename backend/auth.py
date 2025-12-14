"""Authentication middleware for validating BetterAuth sessions.

This module validates session tokens issued by BetterAuth (Next.js frontend).
The FastAPI backend verifies tokens by looking up sessions in the shared database.
"""

from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select, text

from db import get_session
from config import get_settings

settings = get_settings()

# JWT Bearer scheme for extracting token from Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
):
    """
    Get the current authenticated user from BetterAuth session token.

    This validates the session token by:
    1. Extracting the token from the Authorization header
    2. Looking up the session in the BetterAuth 'session' table
    3. Verifying the session hasn't expired
    4. Returning the associated user from the 'user' table

    Raises 401 Unauthorized if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    if not token:
        raise credentials_exception

    # Look up the session in BetterAuth's session table
    # BetterAuth uses camelCase column names
    session_query = text("""
        SELECT s.id, s."userId", s."expiresAt", u.id as user_id, u.email, u.name, u.image, u."createdAt", u."updatedAt"
        FROM session s
        JOIN "user" u ON s."userId" = u.id
        WHERE s.token = :token
    """)

    result = db.exec(session_query, params={"token": token}).first()

    if result is None:
        raise credentials_exception

    # Check if session is expired
    expires_at = result.expiresAt
    if expires_at and expires_at < datetime.utcnow():
        raise credentials_exception

    # Return user data as a dict-like object
    class UserData:
        def __init__(self, row):
            self.id = row.user_id
            self.email = row.email
            self.name = row.name
            self.image = row.image
            self.created_at = row.createdAt
            self.updated_at = row.updatedAt

    return UserData(result)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_session)
):
    """Get the current user if authenticated, otherwise return None."""
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def verify_session_token(db: Session, token: str) -> Optional[dict]:
    """
    Verify a BetterAuth session token and return session data.

    Args:
        db: Database session
        token: The session token to verify

    Returns:
        Session data dict if valid, None if invalid/expired
    """
    session_query = text("""
        SELECT s.id, s."userId", s."expiresAt", s."ipAddress", s."userAgent"
        FROM session s
        WHERE s.token = :token
    """)

    result = db.exec(session_query, params={"token": token}).first()

    if result is None:
        return None

    # Check expiration
    if result.expiresAt and result.expiresAt < datetime.utcnow():
        return None

    return {
        "session_id": result.id,
        "user_id": result.userId,
        "expires_at": result.expiresAt,
        "ip_address": result.ipAddress,
        "user_agent": result.userAgent,
    }
