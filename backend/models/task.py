"""Task model."""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlmodel import SQLModel, Field


class TaskStatus(str, Enum):
    """Task status enum."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskBase(SQLModel):
    """Base task fields."""
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    due_date: Optional[datetime] = None


class Task(TaskBase, table=True):
    """Task database model."""
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    creator_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    assigned_to: Optional[str] = Field(
        default=None, foreign_key="users.id", index=True, max_length=36
    )
    completed: bool = Field(default=False)
    position: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskCreate(SQLModel):
    """Task creation schema."""
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    project_id: int
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None


class TaskRead(TaskBase):
    """Task response schema."""
    id: int
    project_id: int
    creator_id: str
    assigned_to: Optional[str]
    completed: bool
    position: int
    created_at: datetime
    updated_at: datetime


class TaskUpdate(SQLModel):
    """Task update schema."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[TaskStatus] = None
    completed: Optional[bool] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    position: Optional[int] = None
