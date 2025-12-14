"""Project model."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ProjectBase(SQLModel):
    """Base project fields."""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)


class Project(ProjectBase, table=True):
    """Project database model."""
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectCreate(ProjectBase):
    """Project creation schema."""
    pass


class ProjectRead(ProjectBase):
    """Project response schema."""
    id: int
    owner_id: str
    created_at: datetime
    updated_at: datetime


class ProjectUpdate(SQLModel):
    """Project update schema."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
