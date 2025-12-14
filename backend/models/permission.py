"""Permission model for user-project relationships."""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlmodel import SQLModel, Field, UniqueConstraint


class RoleEnum(str, Enum):
    """User roles in a project."""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(SQLModel, table=True):
    """Permission database model - many-to-many between users and projects."""
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="unique_user_project"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    project_id: int = Field(foreign_key="projects.id", index=True)
    role: RoleEnum = Field(default=RoleEnum.MEMBER)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PermissionCreate(SQLModel):
    """Permission creation schema."""
    user_id: str
    project_id: int
    role: RoleEnum = RoleEnum.MEMBER


class PermissionRead(SQLModel):
    """Permission response schema."""
    id: int
    user_id: str
    project_id: int
    role: RoleEnum
    created_at: datetime
    updated_at: datetime


class PermissionUpdate(SQLModel):
    """Permission update schema."""
    role: RoleEnum
