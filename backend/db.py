"""Database connection and session management."""

from sqlmodel import SQLModel, Session, create_engine
from typing import Generator
from config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)


def init_db() -> None:
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session as a dependency."""
    with Session(engine) as session:
        yield session
