from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from app.core.config import settings

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@runtime_checkable
class EmbeddingGenerator(Protocol):
    """Protocol isolating embedding logic from any storage or database layer."""

    def get_text_embedding(self, text: str) -> list[float]: ...

    def get_text_embeddings(self, texts: list[str]) -> list[list[float]]: ...

    @property
    def dimension(self) -> int: ...


class SentenceTransformerEmbeddingService:
    """Sentence Transformers embedding service using all-MiniLM-L6-v2 (384-dimensional).

    Strictly isolated from any database access or vector store.
    """

    _instance = None
    _model: Any = None

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._dim = settings.EMBEDDING_DIMENSION

    @classmethod
    def get_model(cls, model_name: str | None = None) -> SentenceTransformer:
        """Lazy-load and cache the SentenceTransformer model in memory.
        
        Checks for a local pre-downloaded model in backend/local_model/all-MiniLM-L6-v2
        first to ensure instantaneous 0.6s loading, zero network latency, and 100% offline support.
        Falls back to Hugging Face Hub if local files are not present.
        """
        if cls._model is None:
            from sentence_transformers import SentenceTransformer

            local_path = Path(__file__).resolve().parent.parent.parent / "local_model" / "all-MiniLM-L6-v2"
            if local_path.exists() and (local_path / "model.safetensors").exists():
                cls._model = SentenceTransformer(str(local_path), local_files_only=True)
            else:
                target_model = model_name or settings.EMBEDDING_MODEL_NAME
                cls._model = SentenceTransformer(target_model)
        return cls._model

    def get_text_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for a single text string."""
        if not text or not text.strip():
            return [0.0] * self.dimension
        model = self.get_model(self.model_name)
        embedding = model.encode(text.strip(), convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    def get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Batch generate embeddings for multiple texts."""
        if not texts:
            return []
        cleaned = [t.strip() if t and t.strip() else " " for t in texts]
        model = self.get_model(self.model_name)
        embeddings = model.encode(
            cleaned,
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self._dim


embedding_service = SentenceTransformerEmbeddingService()
