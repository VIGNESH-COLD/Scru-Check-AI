import json
from pathlib import Path
from typing import Annotated, Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "OmniRAG Document Intelligence"
    INSTITUTION_NAME: str = "Rajalakshmi Institute of Technology"
    ENVIRONMENT: str = "development"  # "development" or "production"
    ENABLE_API_DOCS: bool | None = None
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @property
    def DOCS_ENABLED(self) -> bool:
        if self.ENABLE_API_DOCS is not None:
            return self.ENABLE_API_DOCS
        return self.ENVIRONMENT.strip().lower() != "production"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        """Accept either a JSON array string, list of origins, or comma-separated URLs."""
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item).strip().rstrip("/") for item in parsed if str(item).strip()]
            return [origin.strip().rstrip("/") for origin in stripped.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(item).strip().rstrip("/") for item in value if str(item).strip()]
        return value

    # Security & Upload Resource Ceilings
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    MAX_QP_PDF_PAGES: int = 50
    MAX_SYLLABUS_PDF_PAGES: int = 100
    MAX_DOCX_UNCOMPRESSED_BYTES: int = 50 * 1024 * 1024  # 50 MB

    # PostgreSQL & pgvector Database Settings
    POSTGRES_URL: str = Field(
        default="",
        validation_alias=AliasChoices("POSTGRES_URL", "DATABASE_URL"),
    )  # Reads DATABASE_URL from .env.local (Neon) or POSTGRES_URL from .env
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ragdb"
    POSTGRES_SSL: bool = False

    @property
    def USE_POSTGRES_SSL(self) -> bool:
        if self.POSTGRES_SSL:
            return True
        url_lower = self.POSTGRES_URL.lower()
        return "sslmode=require" in url_lower or "ssl=require" in url_lower or "neon.tech" in url_lower or "supabase.co" in url_lower

    @property
    def DATABASE_URL(self) -> str:
        if self.POSTGRES_URL.strip():
            raw = self.POSTGRES_URL.strip()
            if raw.startswith("postgres://"):
                raw = "postgresql+asyncpg://" + raw[len("postgres://"):]
            elif raw.startswith("postgresql://"):
                raw = "postgresql+asyncpg://" + raw[len("postgresql://"):]
            elif raw.startswith("postgresql+psycopg://"):
                raw = "postgresql+asyncpg://" + raw[len("postgresql+psycopg://"):]
            # asyncpg handles SSL via connect_args rather than libpq sslmode query params
            if "?" in raw:
                base, query = raw.split("?", 1)
                kept = [
                    part for part in query.split("&")
                    if part and not part.lower().startswith(("sslmode=", "channel_binding="))
                ]
                raw = f"{base}?{'&'.join(kept)}" if kept else base
            return raw
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        if self.POSTGRES_URL.strip():
            raw = self.POSTGRES_URL.strip()
            if raw.startswith("postgres://"):
                return "postgresql+psycopg://" + raw[len("postgres://"):]
            if raw.startswith("postgresql://"):
                return "postgresql+psycopg://" + raw[len("postgresql://"):]
            if raw.startswith("postgresql+asyncpg://"):
                return "postgresql+psycopg://" + raw[len("postgresql+asyncpg://"):]
            return raw
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # JWT Authentication & Argon2 Settings (preserved configuration)
    SECRET_KEY: str = "super-secret-enterprise-rag-jwt-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Vector Embedding & Syllabus Index Settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    VECTOR_STORE_BACKEND: str = "simple"  # "pgvector" or "simple"
    SYLLABUS_INDEX_STORAGE_PATH: str = "storage/syllabus_index.json"
    SYLLABUS_TOPICS_TABLE: str = "syllabus_topic_embeddings"

    # LLM Integrations: APInex API & Ollama
    APINEX_API_KEY: str = "apinex-mock-key-for-dev"
    APINEX_BASE_URL: str = "https://api.apinex.ai/v1"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # Configurable Primary LLM Service (Default: Mistral AI / Groq)
    LLM_PROVIDER: str = "mistral"  # "mistral", "gemini", "ollama", "openai", "apinex", "groq", "mock"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.mistral.ai/v1"
    LLM_MODEL: str = "ministral-8b-latest"
    LLM_TIMEOUT_SECONDS: float = 15.0
    LLM_RETRY_LIMIT: int = 2

    # Fallback LLM Provider (Default: Google Gemini API)
    FALLBACK_LLM_PROVIDER: str = "gemini"  # "gemini", "mistral", or ""
    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_MODEL: str = "gemini-flash-lite-latest"

    # Dedicated Mistral Settings
    MISTRAL_API_KEY: str = ""
    MISTRAL_BASE_URL: str = "https://api.mistral.ai/v1"
    MISTRAL_MODEL: str = "ministral-8b-latest"

    # OCR Settings
    TESSERACT_CMD: str = "tesseract"

    # Storage Paths
    UPLOAD_DIR: str = "uploads"
    REPORT_DIR: str = "generated_reports"

    @field_validator("SYLLABUS_INDEX_STORAGE_PATH", "UPLOAD_DIR", "REPORT_DIR", mode="after")
    @classmethod
    def resolve_backend_relative_paths(cls, value: str) -> str:
        """Anchor relative storage paths to backend/ regardless of process working directory."""
        p = Path(value)
        if not p.is_absolute():
            return str((BACKEND_DIR / p).resolve())
        return value

    model_config = SettingsConfigDict(
        env_file=[
            str(BACKEND_DIR.parent / ".env"),
            str(BACKEND_DIR.parent / ".env.local"),
            str(BACKEND_DIR / ".env"),
            str(BACKEND_DIR / ".env.local"),
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
