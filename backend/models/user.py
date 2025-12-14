"""User model - BetterAuth compatible."""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    """Base user fields."""
    email: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(max_length=255)
    image: Optional[str] = Field(default=None, max_length=500)


class User(UserBase, table=True):
    """User database model."""
    __tablename__ = "users"

    id: str = Field(primary_key=True, max_length=36)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    """User creation schema."""
    email: str
    name: str
    password: str


class UserRead(UserBase):
    """User response schema."""
    id: str
    created_at: datetime
    updated_at: datetime


class UserUpdate(SQLModel):
    """User update schema."""
    name: Optional[str] = None
    image: Optional[str] = None
