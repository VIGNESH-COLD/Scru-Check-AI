from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "OmniRAG Document Intelligence"
    INSTITUTION_NAME: str = "Rajalakshmi Institute of Technology"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Security & Upload Resource Ceilings
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    MAX_QP_PDF_PAGES: int = 50
    MAX_SYLLABUS_PDF_PAGES: int = 100
    MAX_DOCX_UNCOMPRESSED_BYTES: int = 50 * 1024 * 1024  # 50 MB

    # PostgreSQL & pgvector Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ragdb"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
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

    model_config = SettingsConfigDict(
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
