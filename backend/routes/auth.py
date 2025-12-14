"""Authentication routes for BetterAuth integration.

Authentication is handled by BetterAuth in the Next.js frontend.
This module provides utility endpoints for the FastAPI backend to
verify sessions and get user information.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlmodel import Session

from auth import get_current_user
from db import get_session

router = APIRouter()


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    name: str
    image: str | None = None


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """
    Get current authenticated user.

    This endpoint validates the BetterAuth session token and returns
    the authenticated user's information.

    Requires: Authorization header with Bearer token (BetterAuth session token)
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        image=current_user.image
    )


class SessionResponse(BaseModel):
    """Session response schema with session validity info."""
    authenticated: bool = True
    user_id: str
    email: str
    name: str
    expires_at: str


@router.get("/session", response_model=SessionResponse)
async def get_session_info(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_session)
):
    """
    Get current session information from token.

    This endpoint validates the session token and returns session info
    including user details and expiration time.

    Note: IP address and user agent are intentionally not exposed
    for security/privacy reasons (PII data, fingerprinting concerns).

    Requires: Authorization header with Bearer token (BetterAuth session token)
    """
    from auth import verify_session_token

    token = credentials.credentials
    session_data = verify_session_token(db, token)

    if session_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user details
    from sqlmodel import text
    user_query = text('SELECT email, name FROM "user" WHERE id = :user_id')
    user_result = db.exec(user_query, params={"user_id": session_data["user_id"]}).first()

    return SessionResponse(
        authenticated=True,
        user_id=session_data["user_id"],
        email=user_result.email if user_result else "",
        name=user_result.name if user_result else "",
        expires_at=session_data["expires_at"].isoformat() if session_data["expires_at"] else "",
    )
