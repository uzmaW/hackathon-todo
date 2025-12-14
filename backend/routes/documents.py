"""Document management routes for RAG."""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlmodel import Session, select
import uuid

from db import get_session
from auth import get_current_user
from config import get_settings
from models.document import (
    Document,
    DocumentStatus,
    DocumentRead,
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
)
from rag import DocumentIngestionPipeline, get_qdrant_manager

settings = get_settings()
router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    project_id: Optional[int] = Query(None, description="Optional project to associate with"),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Upload and ingest a PDF document for RAG.

    The document will be:
    1. Parsed to extract text
    2. Split into chunks
    3. Embedded using OpenAI
    4. Stored in Qdrant for retrieval

    Max file size: 10MB
    Supported formats: PDF
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {settings.max_file_size_mb}MB",
        )

    # Generate document ID
    document_id = str(uuid.uuid4())

    # Create document record
    qdrant = get_qdrant_manager()
    collection_name = qdrant.get_collection_name(current_user.id)

    document = Document(
        id=document_id,
        user_id=current_user.id,
        project_id=project_id,
        filename=f"{document_id}.pdf",
        original_filename=file.filename,
        file_size=file_size,
        mime_type="application/pdf",
        qdrant_collection=collection_name,
        status=DocumentStatus.PROCESSING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(document)
    session.commit()

    try:
        # Run ingestion pipeline
        pipeline = DocumentIngestionPipeline()
        result = pipeline.ingest_pdf(
            user_id=current_user.id,
            file_content=content,
            filename=file.filename,
            project_id=project_id,
            document_id=document_id,
        )

        if result.success:
            # Update document record
            document.status = DocumentStatus.INGESTED
            document.chunk_count = result.chunks_created
            document.page_count = result.total_pages
            document.pdf_metadata = result.metadata
            document.processed_at = datetime.utcnow()
            document.updated_at = datetime.utcnow()
            session.add(document)
            session.commit()

            return DocumentUploadResponse(
                document_id=document_id,
                filename=file.filename,
                chunks_created=result.chunks_created,
                page_count=result.total_pages,
                status="ingested",
                message=f"Successfully ingested {result.chunks_created} chunks from {result.total_pages} pages",
            )
        else:
            # Update document with error
            document.status = DocumentStatus.FAILED
            document.error_message = result.error
            document.updated_at = datetime.utcnow()
            session.add(document)
            session.commit()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to ingest document: {result.error}",
            )

    except HTTPException:
        raise
    except Exception as e:
        # Update document with error
        document.status = DocumentStatus.FAILED
        document.error_message = str(e)
        document.updated_at = datetime.utcnow()
        session.add(document)
        session.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during ingestion: {str(e)}",
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    project_id: Optional[int] = Query(None, description="Filter by project"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    List user's uploaded documents.

    Returns documents with their processing status and metadata.
    """
    query = select(Document).where(Document.user_id == current_user.id)

    if project_id:
        query = query.where(Document.project_id == project_id)

    if status_filter:
        try:
            doc_status = DocumentStatus(status_filter)
            query = query.where(Document.status == doc_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    # Get total count
    count_query = select(Document).where(Document.user_id == current_user.id)
    if project_id:
        count_query = count_query.where(Document.project_id == project_id)
    total = len(session.exec(count_query).all())

    # Get paginated results
    query = query.order_by(Document.created_at.desc()).offset(offset).limit(limit)
    documents = session.exec(query).all()

    return DocumentListResponse(
        documents=[
            DocumentRead(
                id=doc.id,
                user_id=doc.user_id,
                project_id=doc.project_id,
                filename=doc.original_filename,
                original_filename=doc.original_filename,
                file_size=doc.file_size,
                chunk_count=doc.chunk_count,
                page_count=doc.page_count,
                status=doc.status.value,
                error_message=doc.error_message,
                created_at=doc.created_at,
                processed_at=doc.processed_at,
            )
            for doc in documents
        ],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: str,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Get a specific document by ID.
    """
    document = session.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document",
        )

    return DocumentRead(
        id=document.id,
        user_id=document.user_id,
        project_id=document.project_id,
        filename=document.original_filename,
        original_filename=document.original_filename,
        file_size=document.file_size,
        chunk_count=document.chunk_count,
        page_count=document.page_count,
        status=document.status.value,
        error_message=document.error_message,
        created_at=document.created_at,
        processed_at=document.processed_at,
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Delete a document and its vectors from the system.

    This will:
    1. Delete all vectors from Qdrant
    2. Delete the document record from PostgreSQL
    """
    document = session.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document",
        )

    try:
        # Delete vectors from Qdrant
        pipeline = DocumentIngestionPipeline()
        pipeline.delete_document(current_user.id, document_id)

        # Delete document record
        session.delete(document)
        session.commit()

        return DocumentDeleteResponse(
            document_id=document_id,
            status="deleted",
            message="Document and all associated vectors have been deleted",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


@router.get("/stats/overview")
async def get_document_stats(
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Get statistics about user's documents and RAG system.
    """
    # Get document counts by status
    query = select(Document).where(Document.user_id == current_user.id)
    documents = session.exec(query).all()

    total_docs = len(documents)
    ingested_docs = len([d for d in documents if d.status == DocumentStatus.INGESTED])
    processing_docs = len([d for d in documents if d.status == DocumentStatus.PROCESSING])
    failed_docs = len([d for d in documents if d.status == DocumentStatus.FAILED])

    total_chunks = sum(d.chunk_count for d in documents)
    total_pages = sum(d.page_count for d in documents)
    total_size = sum(d.file_size for d in documents)

    # Get Qdrant collection info
    qdrant = get_qdrant_manager()
    collection_info = qdrant.get_collection_info(current_user.id)

    return {
        "documents": {
            "total": total_docs,
            "ingested": ingested_docs,
            "processing": processing_docs,
            "failed": failed_docs,
        },
        "content": {
            "total_chunks": total_chunks,
            "total_pages": total_pages,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        },
        "vector_store": collection_info or {
            "status": "not_initialized",
        },
    }
