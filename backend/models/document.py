"""Document model for RAG document tracking."""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel


class DocumentStatus(str, Enum):
    """Status of document processing."""
    PROCESSING = "processing"
    INGESTED = "ingested"
    FAILED = "failed"


class Document(SQLModel, table=True):
    """
    Model for tracking uploaded documents for RAG.

    Documents are stored in Qdrant as vectors, but metadata
    is tracked here in PostgreSQL for management.
    """
    __tablename__ = "document"

    id: str = Field(primary_key=True)  # UUID string
    user_id: str = Field(foreign_key="user.id", index=True)
    project_id: Optional[int] = Field(default=None, foreign_key="project.id", index=True)

    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_size: int  # Size in bytes
    mime_type: str = Field(default="application/pdf", max_length=100)

    chunk_count: int = Field(default=0)
    page_count: int = Field(default=0)
    qdrant_collection: str = Field(max_length=255)

    status: DocumentStatus = Field(default=DocumentStatus.PROCESSING)
    error_message: Optional[str] = Field(default=None, max_length=1000)

    # Metadata from PDF
    pdf_metadata: Optional[dict] = Field(default=None, sa_type_kwargs={"nullable": True})

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(default=None)


# Pydantic schemas for API

class DocumentCreate(BaseModel):
    """Schema for document creation (internal use)."""
    filename: str
    original_filename: str
    file_size: int
    project_id: Optional[int] = None


class DocumentRead(BaseModel):
    """Schema for reading document data."""
    id: str
    user_id: str
    project_id: Optional[int]
    filename: str
    original_filename: str
    file_size: int
    chunk_count: int
    page_count: int
    status: str
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""
    document_id: str
    filename: str
    chunks_created: int
    page_count: int
    status: str
    message: str


class DocumentListResponse(BaseModel):
    """Response schema for listing documents."""
    documents: list[DocumentRead]
    total: int


class DocumentDeleteResponse(BaseModel):
    """Response schema for document deletion."""
    document_id: str
    status: str
    message: str
