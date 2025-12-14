"""OpenAI embeddings service for RAG pipeline."""

import asyncio
from typing import List, Optional
from openai import OpenAI
import time

from config import get_settings

settings = get_settings()


class EmbeddingService:
    """Service for generating embeddings using OpenAI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the embedding service.

        Args:
            api_key: OpenAI API key. Defaults to settings.
            model: Embedding model name. Defaults to settings.
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_embedding_model
        self.client = OpenAI(api_key=self.api_key)

        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        # Rate limiting
        self._rate_limit()

        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )

        return response.data[0].embedding

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 100,
        show_progress: bool = False,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to embed per API call
            show_progress: Whether to print progress

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts and track indices
        valid_indices = []
        valid_texts = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_indices.append(i)
                valid_texts.append(text.strip())

        if not valid_texts:
            return [[] for _ in texts]

        embeddings = [[] for _ in texts]

        # Process in batches
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            batch_indices = valid_indices[i:i + batch_size]

            if show_progress:
                print(f"Embedding batch {i // batch_size + 1}/{(len(valid_texts) + batch_size - 1) // batch_size}")

            # Rate limiting
            self._rate_limit()

            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )

                for j, embedding_data in enumerate(response.data):
                    original_index = batch_indices[j]
                    embeddings[original_index] = embedding_data.embedding

            except Exception as e:
                # On error, try one by one
                for j, text in enumerate(batch):
                    original_index = batch_indices[j]
                    try:
                        self._rate_limit()
                        single_response = self.client.embeddings.create(
                            model=self.model,
                            input=text,
                        )
                        embeddings[original_index] = single_response.data[0].embedding
                    except Exception as single_error:
                        print(f"Failed to embed text at index {original_index}: {single_error}")
                        embeddings[original_index] = []

        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        This is a convenience method that's semantically clearer
        than embed_text for search operations.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        return self.embed_text(query)

    def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)

        self._last_request_time = time.time()

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings from this model.

        Returns:
            Embedding dimension
        """
        # text-embedding-3-small produces 1536-dimensional vectors
        # text-embedding-3-large produces 3072-dimensional vectors
        # text-embedding-ada-002 produces 1536-dimensional vectors

        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

        return model_dimensions.get(self.model, 1536)

    def health_check(self) -> bool:
        """
        Check if the embedding service is working.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to embed a simple test text
            self.embed_text("test")
            return True
        except Exception:
            return False


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
