"""Application configuration loaded from environment variables / .env file."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """P&ID RAG API configuration.

    Values are read from environment variables or a ``.env`` file located
    in the working directory.
    """

    ANTHROPIC_API_KEY: str = ""
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    CORS_ORIGINS: str = "http://localhost:3000"
    MAX_UPLOAD_SIZE_MB: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origin_list(self) -> list[str]:
        """Return CORS origins as a list (comma-separated in the env var)."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
