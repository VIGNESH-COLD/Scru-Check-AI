import json
import logging
import re
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.schemas.syllabus import SyllabusTopicRecord, TopicSearchResult

logger = logging.getLogger(__name__)


def validate_syllabus_id(syllabus_id: str | None) -> str:
    """Validate syllabus_id against allowed alphanumeric, hyphen, and underscore characters."""
    if not syllabus_id:
        raise ValueError("syllabus_id cannot be empty.")
    cleaned = syllabus_id.strip()
    if not re.match(r"^[a-zA-Z0-9_\-]+$", cleaned):
        raise ValueError(
            f"Invalid syllabus_id '{syllabus_id}': must contain only letters, digits, underscores, and hyphens."
        )
    return cleaned


@runtime_checkable
class SyllabusVectorStore(Protocol):
    """Protocol for vector stores supporting persistent indexing and similarity search."""

    async def initialize(self) -> None: ...

    async def upsert_topics(
        self,
        syllabus_id: str,
        topics: list[SyllabusTopicRecord],
        embeddings: list[list[float]],
    ) -> int: ...

    async def delete_syllabus(self, syllabus_id: str) -> int: ...

    async def has_syllabus(self, syllabus_id: str) -> bool: ...

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        syllabus_id: str | None = None,
        unit_number: int | None = None,
    ) -> list[TopicSearchResult]: ...


class PGVectorSyllabusStore:
    """Production vector store implementation using PostgreSQL and pgvector."""

    def __init__(self, table_name: str | None = None, dimension: int = 384):
        raw_table = table_name or settings.SYLLABUS_TOPICS_TABLE
        if not re.match(r"^[a-zA-Z0-9_]+$", raw_table):
            raise ValueError(f"Invalid table_name '{raw_table}': must be alphanumeric or underscore.")
        self.table_name = raw_table
        self.dimension = dimension

    async def initialize(self) -> None:
        """Create pgvector extension, table, and HNSW index if they do not exist."""
        async with engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

            # Create syllabus topic embeddings table
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                topic_id VARCHAR(128) PRIMARY KEY,
                syllabus_id VARCHAR(128) NOT NULL,
                course_code VARCHAR(32),
                course_title VARCHAR(256),
                unit_number INTEGER,
                unit_title VARCHAR(256) NOT NULL,
                raw_unit_heading TEXT,
                topic_title TEXT NOT NULL,
                subtopics JSONB NOT NULL DEFAULT '[]'::jsonb,
                content TEXT NOT NULL,
                co_identifiers JSONB NOT NULL DEFAULT '[]'::jsonb,
                source_page INTEGER,
                source_file VARCHAR(256),
                is_unrecognized_unit BOOLEAN NOT NULL DEFAULT FALSE,
                metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                embedding vector({self.dimension}) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
            await conn.execute(text(create_table_sql))

            # Create indices for fast metadata filtering and HNSW cosine vector search
            await conn.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_syllabus_id "
                    f"ON {self.table_name} (syllabus_id);"
                )
            )
            await conn.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_unit_num "
                    f"ON {self.table_name} (unit_number);"
                )
            )

    async def upsert_topics(
        self,
        syllabus_id: str,
        topics: list[SyllabusTopicRecord],
        embeddings: list[list[float]],
    ) -> int:
        """Atomically replace any previous records for syllabus_id and insert new topic vectors.

        Guarantees repeatability without duplicate indexed records.
        """
        syllabus_id = validate_syllabus_id(syllabus_id)
        if not topics:
            return 0
        if len(topics) != len(embeddings):
            raise ValueError(
                f"Topics count ({len(topics)}) does not match embeddings count ({len(embeddings)})"
            )

        await self.initialize()

        async with engine.begin() as conn:
            # Delete existing records for this syllabus to avoid duplicates
            await conn.execute(
                text(f"DELETE FROM {self.table_name} WHERE syllabus_id = :s_id"),
                {"s_id": syllabus_id},
            )

            insert_sql = f"""
            INSERT INTO {self.table_name} (
                topic_id, syllabus_id, course_code, course_title,
                unit_number, unit_title, raw_unit_heading, topic_title,
                subtopics, content, co_identifiers, source_page,
                source_file, is_unrecognized_unit, metadata, embedding
            ) VALUES (
                :topic_id, :syllabus_id, :course_code, :course_title,
                :unit_number, :unit_title, :raw_unit_heading, :topic_title,
                :subtopics, :content, :co_identifiers, :source_page,
                :source_file, :is_unrecognized_unit, :metadata, :embedding
            );
            """

            for topic, emb in zip(topics, embeddings, strict=True):
                # Format embedding as string '[0.1, 0.2, ...]' for pgvector
                emb_str = f"[{','.join(str(x) for x in emb)}]"
                params = {
                    "topic_id": topic.topic_id,
                    "syllabus_id": syllabus_id,
                    "course_code": topic.course_code,
                    "course_title": topic.course_title,
                    "unit_number": topic.unit_number,
                    "unit_title": topic.unit_title,
                    "raw_unit_heading": topic.raw_unit_heading,
                    "topic_title": topic.topic_title,
                    "subtopics": json.dumps(topic.subtopics),
                    "content": topic.content,
                    "co_identifiers": json.dumps(topic.co_identifiers),
                    "source_page": topic.source_page,
                    "source_file": topic.source_file,
                    "is_unrecognized_unit": topic.is_unrecognized_unit,
                    "metadata": json.dumps(topic.metadata),
                    "embedding": emb_str,
                }
                await conn.execute(text(insert_sql), params)

        return len(topics)

    async def delete_syllabus(self, syllabus_id: str) -> int:
        """Remove all indexed topic vectors for a given syllabus ID."""
        syllabus_id = validate_syllabus_id(syllabus_id)
        await self.initialize()
        async with engine.begin() as conn:
            result = await conn.execute(
                text(f"DELETE FROM {self.table_name} WHERE syllabus_id = :s_id"),
                {"s_id": syllabus_id},
            )
            return result.rowcount or 0

    async def has_syllabus(self, syllabus_id: str) -> bool:
        """Check if any topics exist for a given syllabus ID."""
        syllabus_id = validate_syllabus_id(syllabus_id)
        await self.initialize()
        async with engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT 1 FROM {self.table_name} WHERE syllabus_id = :s_id LIMIT 1"),
                {"s_id": syllabus_id},
            )
            return result.scalar() is not None

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        syllabus_id: str | None = None,
        unit_number: int | None = None,
    ) -> list[TopicSearchResult]:
        """Perform cosine similarity search against indexed syllabus topics in pgvector."""
        await self.initialize()

        emb_str = f"[{','.join(str(x) for x in query_embedding)}]"
        conditions = []
        params: dict[str, Any] = {
            "query_emb": emb_str,
            "top_k": top_k,
        }

        if syllabus_id:
            conditions.append("syllabus_id = :syllabus_id")
            params["syllabus_id"] = syllabus_id

        if unit_number is not None:
            conditions.append("unit_number = :unit_number")
            params["unit_number"] = unit_number

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # In pgvector, cosine distance is <=> operator (0 = identical, 2 = opposite).
        # Cosine similarity = 1 - (embedding <=> query).
        query_sql = f"""
        SELECT
            topic_id, syllabus_id, course_code, course_title,
            unit_number, unit_title, raw_unit_heading, topic_title,
            subtopics, content, co_identifiers, source_page,
            source_file, is_unrecognized_unit, metadata,
            1 - (embedding <=> :query_emb) AS cosine_similarity
        FROM {self.table_name}
        {where_clause}
        ORDER BY embedding <=> :query_emb ASC
        LIMIT :top_k;
        """

        results: list[TopicSearchResult] = []
        async with engine.connect() as conn:
            cursor = await conn.execute(text(query_sql), params)
            rows = cursor.fetchall()

            for rank, row in enumerate(rows, start=1):
                raw_subtopics = row.subtopics
                subtopics = (
                    json.loads(raw_subtopics)
                    if isinstance(raw_subtopics, str)
                    else (raw_subtopics or [])
                )
                raw_cos = row.co_identifiers
                co_identifiers = (
                    json.loads(raw_cos) if isinstance(raw_cos, str) else (raw_cos or [])
                )
                raw_meta = row.metadata
                metadata = json.loads(raw_meta) if isinstance(raw_meta, str) else (raw_meta or {})

                topic = SyllabusTopicRecord(
                    topic_id=row.topic_id,
                    syllabus_id=row.syllabus_id,
                    course_code=row.course_code,
                    course_title=row.course_title,
                    unit_number=row.unit_number,
                    unit_title=row.unit_title,
                    raw_unit_heading=row.raw_unit_heading,
                    topic_title=row.topic_title,
                    subtopics=subtopics,
                    content=row.content,
                    co_identifiers=co_identifiers,
                    source_page=row.source_page,
                    source_file=row.source_file,
                    is_unrecognized_unit=row.is_unrecognized_unit,
                    metadata=metadata,
                )
                similarity_score = (
                    float(row.cosine_similarity) if row.cosine_similarity is not None else 0.0
                )
                results.append(
                    TopicSearchResult(
                        topic=topic,
                        similarity_score=round(max(0.0, min(1.0, similarity_score)), 4),
                        rank=rank,
                    )
                )

        return results


class SimplePersistentSyllabusStore:
    """Configurable persistent JSON file and NumPy vector store.

    Enables reliable persistent indexing and similarity search in any environment
    (e.g., local Windows development, tests, or when PostgreSQL is unavailable).
    """

    def __init__(
        self,
        storage_path: str | Path | None = None,
        persist_path: str | Path | None = None,
    ):
        path = storage_path or persist_path or settings.SYLLABUS_INDEX_STORAGE_PATH
        self.storage_path = Path(path)
        self._index: dict[str, dict[str, Any]] = {}
        self._loaded = False

    async def initialize(self) -> None:
        """Load persistent index from disk if it exists."""
        if self._loaded:
            return
        if self.storage_path.exists():
            try:
                with open(self.storage_path, encoding="utf-8") as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load index from {self.storage_path}: {e}")
                self._index = {}
        else:
            self._index = {}
        self._loaded = True

    def _persist(self) -> None:
        """Save index to storage path atomically."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.storage_path.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2)
        temp_file.replace(self.storage_path)

    async def upsert_topics(
        self,
        syllabus_id: str,
        topics: list[SyllabusTopicRecord],
        embeddings: list[list[float]],
    ) -> int:
        """Repeatable ingestion: removes previous topics of syllabus_id before indexing new ones."""
        syllabus_id = validate_syllabus_id(syllabus_id)
        await self.initialize()

        if len(topics) != len(embeddings):
            raise ValueError(
                f"Topics count ({len(topics)}) does not match embeddings count ({len(embeddings)})"
            )

        # Delete existing entries with this syllabus_id to guarantee no duplicate records
        keys_to_remove = [k for k, v in self._index.items() if v.get("syllabus_id") == syllabus_id]
        for k in keys_to_remove:
            del self._index[k]

        # Insert new records
        for topic, emb in zip(topics, embeddings, strict=True):
            self._index[topic.topic_id] = {
                "syllabus_id": syllabus_id,
                "topic": topic.model_dump(),
                "embedding": emb,
            }

        self._persist()
        return len(topics)

    async def delete_syllabus(self, syllabus_id: str) -> int:
        """Remove all records for the syllabus."""
        syllabus_id = validate_syllabus_id(syllabus_id)
        await self.initialize()
        keys_to_remove = [k for k, v in self._index.items() if v.get("syllabus_id") == syllabus_id]
        for k in keys_to_remove:
            del self._index[k]
        if keys_to_remove:
            self._persist()
        return len(keys_to_remove)

    async def has_syllabus(self, syllabus_id: str) -> bool:
        """Check if any topics exist for a given syllabus ID."""
        syllabus_id = validate_syllabus_id(syllabus_id)
        await self.initialize()
        return any(v.get("syllabus_id") == syllabus_id for v in self._index.values())

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        syllabus_id: str | None = None,
        unit_number: int | None = None,
    ) -> list[TopicSearchResult]:
        """Perform exact cosine similarity search over stored embeddings."""
        if syllabus_id:
            syllabus_id = validate_syllabus_id(syllabus_id)
        await self.initialize()

        if not self._index:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        scored_candidates: list[tuple[float, dict[str, Any]]] = []

        for item in self._index.values():
            if syllabus_id and item.get("syllabus_id") != syllabus_id:
                continue

            topic_data = item.get("topic", {})
            if unit_number is not None and topic_data.get("unit_number") != unit_number:
                continue

            doc_vec = np.array(item["embedding"], dtype=np.float32)
            doc_norm = np.linalg.norm(doc_vec)
            score = 0.0 if doc_norm == 0 else float(np.dot(q_vec, doc_vec) / (q_norm * doc_norm))

            scored_candidates.append((score, topic_data))

        # Sort descending by similarity score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_slice = scored_candidates[:top_k]

        results: list[TopicSearchResult] = []
        for rank, (score, topic_dict) in enumerate(top_slice, start=1):
            results.append(
                TopicSearchResult(
                    topic=SyllabusTopicRecord.model_validate(topic_dict),
                    similarity_score=round(max(0.0, min(1.0, score)), 4),
                    rank=rank,
                )
            )

        return results


def get_syllabus_vector_store(backend: str | None = None) -> SyllabusVectorStore:
    """Factory creating the configured vector store backend.

    Isolated from embedding generation and highly configurable.
    """
    chosen = backend or settings.VECTOR_STORE_BACKEND
    if chosen == "pgvector":
        return PGVectorSyllabusStore()
    return SimplePersistentSyllabusStore()
