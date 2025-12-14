"""RAG retrieval service for querying documents."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from .qdrant_client import QdrantManager, get_qdrant_manager
from .embeddings import EmbeddingService, get_embedding_service
from config import get_settings

settings = get_settings()


@dataclass
class RetrievedChunk:
    """Represents a retrieved chunk from the vector store."""
    text: str
    score: float
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class Citation:
    """Citation for RAG response."""
    index: int
    text: str
    source: str
    page: int
    score: float


@dataclass
class RetrievalResult:
    """Result of a RAG retrieval operation."""
    success: bool
    chunks: List[RetrievedChunk]
    citations: List[Citation]
    context_text: str
    latency_ms: float
    error: Optional[str] = None


class RAGRetriever:
    """
    Retriever for RAG (Retrieval-Augmented Generation).

    Handles embedding queries and retrieving relevant document chunks.
    """

    def __init__(
        self,
        qdrant_manager: Optional[QdrantManager] = None,
        embedding_service: Optional[EmbeddingService] = None,
        top_k: Optional[int] = None,
        score_threshold: float = 0.5,
    ):
        """
        Initialize the RAG retriever.

        Args:
            qdrant_manager: Qdrant client manager
            embedding_service: OpenAI embedding service
            top_k: Number of chunks to retrieve
            score_threshold: Minimum similarity score
        """
        self.qdrant = qdrant_manager or get_qdrant_manager()
        self.embeddings = embedding_service or get_embedding_service()
        self.top_k = top_k or settings.rag_top_k
        self.score_threshold = score_threshold

    def retrieve(
        self,
        user_id: str,
        query: str,
        project_id: Optional[int] = None,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> RetrievalResult:
        """
        Retrieve relevant document chunks for a query.

        Args:
            user_id: User ID for isolation
            query: Search query
            project_id: Optional project filter
            document_id: Optional document filter
            top_k: Override default top_k

        Returns:
            RetrievalResult with chunks and citations
        """
        start_time = time.time()
        top_k = top_k or self.top_k

        try:
            # Step 1: Embed the query
            query_embedding = self.embeddings.embed_query(query)

            # Step 2: Build filter conditions
            filter_conditions = {}
            if project_id:
                filter_conditions["project_id"] = project_id
            if document_id:
                filter_conditions["document_id"] = document_id

            # Step 3: Search Qdrant
            results = self.qdrant.search(
                user_id=user_id,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=self.score_threshold,
                filter_conditions=filter_conditions if filter_conditions else None,
            )

            # Step 4: Process results
            chunks = []
            citations = []

            for i, result in enumerate(results):
                payload = result.get("payload", {})

                chunk = RetrievedChunk(
                    text=payload.get("text", ""),
                    score=result.get("score", 0),
                    document_id=payload.get("document_id", ""),
                    filename=payload.get("filename", ""),
                    page_number=payload.get("page_number", 1),
                    chunk_index=payload.get("chunk_index", 0),
                    metadata=payload,
                )
                chunks.append(chunk)

                citation = Citation(
                    index=i + 1,
                    text=self._truncate_text(chunk.text, 200),
                    source=chunk.filename,
                    page=chunk.page_number,
                    score=chunk.score,
                )
                citations.append(citation)

            # Build context text for injection into prompts
            context_text = self._build_context_text(chunks)

            latency_ms = (time.time() - start_time) * 1000

            return RetrievalResult(
                success=True,
                chunks=chunks,
                citations=citations,
                context_text=context_text,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return RetrievalResult(
                success=False,
                chunks=[],
                citations=[],
                context_text="",
                latency_ms=latency_ms,
                error=str(e),
            )

    def retrieve_with_fallback(
        self,
        user_id: str,
        query: str,
        **kwargs,
    ) -> RetrievalResult:
        """
        Retrieve with fallback to empty result if RAG is unavailable.

        This ensures chat can continue even if RAG fails.

        Args:
            user_id: User ID
            query: Search query
            **kwargs: Additional arguments for retrieve()

        Returns:
            RetrievalResult (empty if RAG unavailable)
        """
        try:
            # Check if Qdrant is available
            if not self.qdrant.health_check():
                return RetrievalResult(
                    success=False,
                    chunks=[],
                    citations=[],
                    context_text="",
                    latency_ms=0,
                    error="RAG service unavailable",
                )

            return self.retrieve(user_id, query, **kwargs)

        except Exception as e:
            return RetrievalResult(
                success=False,
                chunks=[],
                citations=[],
                context_text="",
                latency_ms=0,
                error=f"RAG retrieval failed: {str(e)}",
            )

    def _build_context_text(self, chunks: List[RetrievedChunk]) -> str:
        """
        Build context text from retrieved chunks for prompt injection.

        Args:
            chunks: List of retrieved chunks

        Returns:
            Formatted context string
        """
        if not chunks:
            return ""

        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(
                f"[Source {i + 1}: {chunk.filename}, Page {chunk.page_number}]\n{chunk.text}"
            )

        return "\n\n---\n\n".join(context_parts)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text with ellipsis if too long."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def format_citations_for_response(self, citations: List[Citation]) -> List[Dict[str, Any]]:
        """
        Format citations for API response.

        Args:
            citations: List of Citation objects

        Returns:
            List of citation dictionaries
        """
        return [
            {
                "index": c.index,
                "text": c.text,
                "source": c.source,
                "page": c.page,
            }
            for c in citations
        ]

    def get_system_prompt_with_context(
        self,
        base_prompt: str,
        context_text: str,
    ) -> str:
        """
        Augment a system prompt with retrieved context.

        Args:
            base_prompt: Original system prompt
            context_text: Retrieved context to inject

        Returns:
            Augmented system prompt
        """
        if not context_text:
            return base_prompt

        rag_instruction = """
You have access to the following relevant information from the user's documents.
Use this context to answer questions and create tasks when appropriate.
When you use information from the context, cite the source using [Source N] notation.

CONTEXT FROM USER'S DOCUMENTS:
{context}

END OF CONTEXT
""".format(context=context_text)

        return base_prompt + "\n\n" + rag_instruction
