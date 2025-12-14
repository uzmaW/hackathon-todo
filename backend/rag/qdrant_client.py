"""Qdrant vector database client for RAG."""

from typing import Optional, List, Dict, Any
from functools import lru_cache
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from config import get_settings

settings = get_settings()


class QdrantManager:
    """Manager for Qdrant vector database operations."""

    def __init__(self, url: Optional[str] = None):
        """
        Initialize Qdrant client.

        Args:
            url: Qdrant server URL. Defaults to settings.
        """
        self.url = url or settings.qdrant_url
        self.client = QdrantClient(url=self.url)
        self.vector_size = settings.qdrant_vector_size
        self.collection_prefix = settings.qdrant_collection_prefix

    def get_collection_name(self, user_id: str) -> str:
        """Get collection name for a user."""
        return f"{self.collection_prefix}{user_id}_documents"

    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        try:
            collections = self.client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception:
            return False

    def create_collection(self, user_id: str) -> str:
        """
        Create a collection for a user if it doesn't exist.

        Args:
            user_id: User ID for the collection

        Returns:
            Collection name
        """
        collection_name = self.get_collection_name(user_id)

        if not self.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

        return collection_name

    def delete_collection(self, user_id: str) -> bool:
        """
        Delete a user's collection.

        Args:
            user_id: User ID

        Returns:
            True if deleted, False if didn't exist
        """
        collection_name = self.get_collection_name(user_id)

        if self.collection_exists(collection_name):
            self.client.delete_collection(collection_name=collection_name)
            return True
        return False

    def upsert_vectors(
        self,
        user_id: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> int:
        """
        Insert or update vectors in a user's collection.

        Args:
            user_id: User ID
            vectors: List of embedding vectors
            payloads: List of metadata payloads
            ids: Optional list of point IDs (auto-generated if not provided)

        Returns:
            Number of vectors upserted
        """
        collection_name = self.create_collection(user_id)

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in vectors]

        points = [
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]

        self.client.upsert(
            collection_name=collection_name,
            points=points,
        )

        return len(points)

    def search(
        self,
        user_id: str,
        query_vector: List[float],
        limit: int = 3,
        score_threshold: float = 0.5,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in a user's collection.

        Args:
            user_id: User ID
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_conditions: Optional filter conditions

        Returns:
            List of search results with payload and score
        """
        collection_name = self.get_collection_name(user_id)

        if not self.collection_exists(collection_name):
            return []

        # Build filter if provided
        query_filter = None
        if filter_conditions:
            must_conditions = []
            for key, value in filter_conditions.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )
            query_filter = models.Filter(must=must_conditions)

        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    def delete_by_document(self, user_id: str, document_id: str) -> int:
        """
        Delete all vectors for a specific document.

        Args:
            user_id: User ID
            document_id: Document ID to delete

        Returns:
            Number of points deleted (estimate)
        """
        collection_name = self.get_collection_name(user_id)

        if not self.collection_exists(collection_name):
            return 0

        # Delete points matching document_id
        self.client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )

        return 1  # Qdrant doesn't return count, return 1 as success indicator

    def get_collection_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a user's collection.

        Args:
            user_id: User ID

        Returns:
            Collection info or None if doesn't exist
        """
        collection_name = self.get_collection_name(user_id)

        if not self.collection_exists(collection_name):
            return None

        info = self.client.get_collection(collection_name=collection_name)

        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status.value,
        }

    def health_check(self) -> bool:
        """
        Check if Qdrant is healthy and accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False


@lru_cache
def get_qdrant_manager() -> QdrantManager:
    """Get cached Qdrant manager instance."""
    return QdrantManager()
