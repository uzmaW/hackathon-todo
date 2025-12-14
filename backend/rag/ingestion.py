"""Document ingestion pipeline for RAG."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import uuid

from .pdf_parser import PDFParser
from .chunker import TextChunker
from .embeddings import EmbeddingService, get_embedding_service
from .qdrant_client import QdrantManager, get_qdrant_manager


@dataclass
class IngestionResult:
    """Result of document ingestion."""
    success: bool
    document_id: str
    filename: str
    chunks_created: int
    total_pages: int
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentIngestionPipeline:
    """
    Pipeline for ingesting documents into the RAG system.

    Flow: PDF → Parse → Chunk → Embed → Store in Qdrant
    """

    def __init__(
        self,
        qdrant_manager: Optional[QdrantManager] = None,
        embedding_service: Optional[EmbeddingService] = None,
        pdf_parser: Optional[PDFParser] = None,
        text_chunker: Optional[TextChunker] = None,
    ):
        """
        Initialize the ingestion pipeline.

        Args:
            qdrant_manager: Qdrant client manager
            embedding_service: OpenAI embedding service
            pdf_parser: PDF parser instance
            text_chunker: Text chunker instance
        """
        self.qdrant = qdrant_manager or get_qdrant_manager()
        self.embeddings = embedding_service or get_embedding_service()
        self.pdf_parser = pdf_parser or PDFParser()
        self.chunker = text_chunker or TextChunker()

    def ingest_pdf(
        self,
        user_id: str,
        file_content: bytes,
        filename: str,
        project_id: Optional[int] = None,
        document_id: Optional[str] = None,
    ) -> IngestionResult:
        """
        Ingest a PDF document into the RAG system.

        Args:
            user_id: User ID for isolation
            file_content: PDF file content as bytes
            filename: Original filename
            project_id: Optional project ID for filtering
            document_id: Optional document ID (auto-generated if not provided)

        Returns:
            IngestionResult with status and metadata
        """
        document_id = document_id or str(uuid.uuid4())

        try:
            # Step 1: Parse PDF
            parsed_doc = self.pdf_parser.parse(file_content, filename)

            if not parsed_doc.pages:
                return IngestionResult(
                    success=False,
                    document_id=document_id,
                    filename=filename,
                    chunks_created=0,
                    total_pages=0,
                    error="No text could be extracted from the PDF",
                )

            # Step 2: Create chunks with page metadata
            pages_data = [
                {"page_number": page.page_number, "text": page.text}
                for page in parsed_doc.pages
            ]

            chunks = self.chunker.chunk_document_pages(
                pages=pages_data,
                document_id=document_id,
                filename=filename,
            )

            if not chunks:
                return IngestionResult(
                    success=False,
                    document_id=document_id,
                    filename=filename,
                    chunks_created=0,
                    total_pages=parsed_doc.total_pages,
                    error="No chunks could be created from the document",
                )

            # Step 3: Generate embeddings
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embeddings.embed_texts(chunk_texts, show_progress=True)

            # Filter out failed embeddings
            valid_chunks = []
            valid_embeddings = []
            for chunk, embedding in zip(chunks, embeddings):
                if embedding:  # Non-empty embedding
                    valid_chunks.append(chunk)
                    valid_embeddings.append(embedding)

            if not valid_embeddings:
                return IngestionResult(
                    success=False,
                    document_id=document_id,
                    filename=filename,
                    chunks_created=0,
                    total_pages=parsed_doc.total_pages,
                    error="Failed to generate embeddings for document",
                )

            # Step 4: Store in Qdrant
            payloads = []
            for chunk in valid_chunks:
                payload = {
                    "document_id": document_id,
                    "filename": filename,
                    "text": chunk.text,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.metadata.get("page_number", 1),
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "ingested_at": datetime.utcnow().isoformat(),
                }
                if project_id:
                    payload["project_id"] = project_id
                payloads.append(payload)

            # Generate unique IDs for each chunk
            chunk_ids = [
                f"{document_id}_{chunk.chunk_index}"
                for chunk in valid_chunks
            ]

            self.qdrant.upsert_vectors(
                user_id=user_id,
                vectors=valid_embeddings,
                payloads=payloads,
                ids=chunk_ids,
            )

            return IngestionResult(
                success=True,
                document_id=document_id,
                filename=filename,
                chunks_created=len(valid_chunks),
                total_pages=parsed_doc.total_pages,
                metadata={
                    "pdf_metadata": parsed_doc.metadata,
                    "embedding_model": self.embeddings.model,
                    "chunk_size": self.chunker.chunk_size,
                    "chunk_overlap": self.chunker.chunk_overlap,
                },
            )

        except Exception as e:
            return IngestionResult(
                success=False,
                document_id=document_id,
                filename=filename,
                chunks_created=0,
                total_pages=0,
                error=str(e),
            )

    def delete_document(self, user_id: str, document_id: str) -> bool:
        """
        Delete a document and its vectors from the system.

        Args:
            user_id: User ID
            document_id: Document ID to delete

        Returns:
            True if successful
        """
        try:
            self.qdrant.delete_by_document(user_id, document_id)
            return True
        except Exception:
            return False

    def get_ingestion_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about a user's ingested documents.

        Args:
            user_id: User ID

        Returns:
            Dictionary with collection statistics
        """
        return self.qdrant.get_collection_info(user_id) or {
            "name": None,
            "vectors_count": 0,
            "points_count": 0,
            "status": "not_created",
        }

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all pipeline components.

        Returns:
            Dictionary with component health status
        """
        return {
            "qdrant": self.qdrant.health_check(),
            "embeddings": self.embeddings.health_check(),
        }
