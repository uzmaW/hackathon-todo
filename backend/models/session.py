"""Session model - BetterAuth compatible."""

from datetime import datetime
from sqlmodel import SQLModel, Field


class Session(SQLModel, table=True):
    """Session database model for BetterAuth."""
    __tablename__ = "sessions"

    id: str = Field(primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    token: str = Field(unique=True, index=True, max_length=500)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
