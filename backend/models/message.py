"""Message model for chat functionality."""

from datetime import datetime
from typing import Optional, Any
from enum import Enum
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class MessageRole(str, Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageBase(SQLModel):
    """Base message fields."""
    role: MessageRole
    content: str


class Message(MessageBase, table=True):
    """Message database model."""
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    message_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessageCreate(SQLModel):
    """Message creation schema."""
    conversation_id: int
    role: MessageRole
    content: str
    message_metadata: Optional[dict] = None


class MessageRead(MessageBase):
    """Message response schema."""
    id: int
    conversation_id: int
    user_id: str
    message_metadata: Optional[dict]
    created_at: datetime
