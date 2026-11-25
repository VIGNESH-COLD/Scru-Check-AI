from pathlib import Path

from llama_index.core import Document
from llama_index.core.schema import TextNode
from starlette.concurrency import run_in_threadpool

from app.schemas.syllabus import (
    IngestionResponse,
    ParsedSyllabus,
    RetrievalResponse,
    SyllabusTopicRecord,
    TopicSearchResult,
)
from app.services.embedding_service import EmbeddingGenerator, embedding_service
from app.services.syllabus_parser import SyllabusParser, syllabus_parser
from app.services.vector_store import (
    SyllabusVectorStore,
    get_syllabus_vector_store,
)


class SyllabusIngestionService:
    """End-to-end syllabus ingestion service combining structured parsing,

    embedding generation, and persistent vector indexing.
    """

    def __init__(
        self,
        parser: SyllabusParser | None = None,
        embedder: EmbeddingGenerator | None = None,
        vector_store: SyllabusVectorStore | None = None,
    ):
        self.parser = parser or syllabus_parser
        self.embedder = embedder or embedding_service
        self.vector_store = vector_store or get_syllabus_vector_store()

    async def ingest_file(
        self,
        file_path: str | Path,
        syllabus_id: str | None = None,
        course_code: str | None = None,
        course_title: str | None = None,
    ) -> IngestionResponse:
        """Parse, generate embeddings, and persistently index all syllabus topics."""
        parsed: ParsedSyllabus = await run_in_threadpool(
            self.parser.parse_file,
            file_path=file_path,
            syllabus_id=syllabus_id,
            course_code=course_code,
            course_title=course_title,
        )

        if not parsed.topics:
            return IngestionResponse(
                syllabus_id=parsed.syllabus_id,
                course_code=parsed.course_code,
                course_title=parsed.course_title,
                indexed_records_count=0,
                units_indexed=[],
                unrecognized_units_count=0,
                status="no_topics_extracted",
            )

        # Generate embeddings in batch for all topic contents
        texts_to_embed = [topic.content for topic in parsed.topics]
        embeddings = await run_in_threadpool(self.embedder.get_text_embeddings, texts_to_embed)

        # Repeatable upsert to persistent vector store
        indexed_count = await self.vector_store.upsert_topics(
            syllabus_id=parsed.syllabus_id,
            topics=parsed.topics,
            embeddings=embeddings,
        )

        distinct_units = sorted({t.unit_number for t in parsed.topics if t.unit_number is not None})
        unrec_count = sum(1 for t in parsed.topics if t.is_unrecognized_unit)

        return IngestionResponse(
            syllabus_id=parsed.syllabus_id,
            course_code=parsed.course_code,
            course_title=parsed.course_title,
            indexed_records_count=indexed_count,
            units_indexed=distinct_units,
            unrecognized_units_count=unrec_count,
            status="success",
        )


class SyllabusRetriever:
    """Retrieval service returning top candidate topics with similarity scores and metadata."""

    def __init__(
        self,
        embedder: EmbeddingGenerator | None = None,
        vector_store: SyllabusVectorStore | None = None,
    ):
        self.embedder = embedder or embedding_service
        self.vector_store = vector_store or get_syllabus_vector_store()

    async def retrieve_top_topics(
        self,
        query: str,
        top_k: int = 5,
        syllabus_id: str | None = None,
        unit_number: int | None = None,
    ) -> RetrievalResponse:
        """Retrieve top candidate topics with similarity scores and rich metadata.

        Strictly limits candidates to the requested top_k (default 5).
        """
        if not query or not query.strip():
            return RetrievalResponse(query=query, total_candidates=0, results=[])

        # Generate query embedding
        query_embedding = await run_in_threadpool(self.embedder.get_text_embedding, query.strip())

        # Search vector store
        candidate_results: list[TopicSearchResult] = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            syllabus_id=syllabus_id,
            unit_number=unit_number,
        )

        return RetrievalResponse(
            query=query,
            total_candidates=len(candidate_results),
            results=candidate_results,
        )


class LlamaIndexSyllabusBridge:
    """LlamaIndex integration bridge creating LlamaIndex Document and Node structures

    from structured SyllabusTopicRecord entries.
    """

    @classmethod
    def to_llamaindex_documents(cls, topics: list[SyllabusTopicRecord]) -> list[Document]:
        """Convert SyllabusTopicRecords into LlamaIndex Document objects preserving all metadata."""
        documents: list[Document] = []
        for topic in topics:
            doc = Document(
                text=topic.content,
                doc_id=topic.topic_id,
                metadata={
                    "syllabus_id": topic.syllabus_id,
                    "course_code": topic.course_code,
                    "course_title": topic.course_title,
                    "unit_number": topic.unit_number,
                    "unit_title": topic.unit_title,
                    "raw_unit_heading": topic.raw_unit_heading,
                    "topic_title": topic.topic_title,
                    "subtopics": topic.subtopics,
                    "co_identifiers": topic.co_identifiers,
                    "source_page": topic.source_page,
                    "source_file": topic.source_file,
                    "is_unrecognized_unit": topic.is_unrecognized_unit,
                },
                excluded_llm_metadata_keys=["source_file", "metadata"],
                excluded_embed_metadata_keys=["source_file", "metadata"],
            )
            documents.append(doc)
        return documents

    @classmethod
    def to_llamaindex_nodes(cls, topics: list[SyllabusTopicRecord]) -> list[TextNode]:
        """Convert SyllabusTopicRecords into LlamaIndex TextNodes for fine-grained chunk indexing."""
        nodes: list[TextNode] = []
        for topic in topics:
            node = TextNode(
                text=topic.content,
                id_=topic.topic_id,
                metadata={
                    "unit_number": topic.unit_number,
                    "unit_title": topic.unit_title,
                    "topic_title": topic.topic_title,
                    "subtopics": topic.subtopics,
                    "co_identifiers": topic.co_identifiers,
                    "source_page": topic.source_page,
                    "is_unrecognized_unit": topic.is_unrecognized_unit,
                },
            )
            nodes.append(node)
        return nodes


# Global service singletons
syllabus_ingestion_service = SyllabusIngestionService()
syllabus_retriever = SyllabusRetriever()
