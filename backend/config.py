"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/hackathon_todo"

    # Authentication
    better_auth_secret: str = "your-secret-key-here-min-32-chars-long"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OpenAI
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # Qdrant Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_prefix: str = "user_"
    qdrant_vector_size: int = 1536  # OpenAI embedding dimension

    # RAG Settings
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 3
    max_file_size_mb: int = 10

    # Dapr
    dapr_http_port: int = 3500
    dapr_grpc_port: int = 50001

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
