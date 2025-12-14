"""Conversation model for chat functionality."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ConversationBase(SQLModel):
    """Base conversation fields."""
    title: str = Field(max_length=255)


class Conversation(ConversationBase, table=True):
    """Conversation database model."""
    __tablename__ = "conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    project_id: Optional[int] = Field(
        default=None, foreign_key="projects.id", index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationCreate(SQLModel):
    """Conversation creation schema."""
    title: str = Field(max_length=255)
    project_id: Optional[int] = None


class ConversationRead(ConversationBase):
    """Conversation response schema."""
    id: int
    user_id: str
    project_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class ConversationUpdate(SQLModel):
    """Conversation update schema."""
    title: Optional[str] = Field(default=None, max_length=255)
