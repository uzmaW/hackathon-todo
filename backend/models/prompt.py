"""Prompt model for tracking AI interactions."""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class PromptType(str, Enum):
    """Type of prompt interaction."""
    TASK_CREATION = "task_creation"
    TASK_UPDATE = "task_update"
    QUERY = "query"
    GENERAL = "general"


class PromptBase(SQLModel):
    """Base prompt fields."""
    prompt_text: str
    prompt_type: PromptType = PromptType.GENERAL


class Prompt(PromptBase, table=True):
    """Prompt database model for tracking AI interactions."""
    __tablename__ = "prompts"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    ai_response: Optional[str] = None
    tool_calls: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    processed_at: Optional[datetime] = None


class PromptCreate(SQLModel):
    """Prompt creation schema."""
    conversation_id: int
    prompt_text: str
    prompt_type: PromptType = PromptType.GENERAL


class PromptRead(PromptBase):
    """Prompt response schema."""
    id: int
    conversation_id: int
    user_id: str
    ai_response: Optional[str]
    tool_calls: Optional[dict]
    created_at: datetime
    processed_at: Optional[datetime]
