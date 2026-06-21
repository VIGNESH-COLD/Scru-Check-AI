"""
RAG Retriever
Retrieves relevant syllabus content for question analysis
"""

from typing import Dict, Any, List, Optional
import os

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class RAGRetriever:
    """
    RAG-based retrieval for syllabus content.
    Uses ChromaDB for vector storage and sentence-transformers for embeddings.
    """
    
    COLLECTION_NAME = "syllabus_content"
    PERSIST_DIR = "./chroma_db"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedder = None
        self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB and embedding model."""
        if CHROMA_AVAILABLE:
            try:
                self.client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.PERSIST_DIR,
                    anonymized_telemetry=False
                ))
            except:
                # Fallback for newer chromadb versions
                self.client = chromadb.PersistentClient(path=self.PERSIST_DIR)
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedder = SentenceTransformer(self.EMBEDDING_MODEL)
            except:
                self.embedder = None
    
    async def index_syllabus(self, syllabus: Dict[str, Any]) -> bool:
        """
        Index syllabus content into vector store.
        """
        if not self.client:
            return False
        
        text = syllabus.get("raw_text", "")
        filename = syllabus.get("filename", "syllabus")
        
        # Chunk the text
        chunks = self._chunk_text(text)
        
        if not chunks:
            return False
        
        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Syllabus content for question paper scrutiny"}
            )
        except Exception as e:
            print(f"Collection error: {e}")
            return False
        
        # Generate embeddings and store
        for i, chunk in enumerate(chunks):
            try:
                # Generate ID
                chunk_id = f"{filename}_{i}"
                
                # Add to collection (ChromaDB handles embedding if using default)
                self.collection.add(
                    documents=[chunk["text"]],
                    metadatas=[{"unit": chunk.get("unit", "unknown"), "index": i}],
                    ids=[chunk_id]
                )
            except Exception as e:
                print(f"Indexing error: {e}")
                continue
        
        return True
    
    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant syllabus content for a query.
        """
        if not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            retrieved = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    retrieved.append({
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0
                    })
            
            return retrieved
            
        except Exception as e:
            print(f"Retrieval error: {e}")
            return []
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[Dict[str, Any]]:
        """Split text into chunks."""
        import re
        
        chunks = []
        
        # First, try to split by units
        unit_pattern = r'(UNIT\s*[-:]?\s*[IVX1-5]+\s*[-:]?\s*.+?)(?=UNIT|$)'
        unit_matches = re.findall(unit_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if unit_matches:
            for i, unit_text in enumerate(unit_matches):
                # Further split large units
                if len(unit_text) > chunk_size:
                    sub_chunks = self._split_by_sentences(unit_text, chunk_size)
                    for sc in sub_chunks:
                        chunks.append({"text": sc, "unit": f"Unit {i+1}"})
                else:
                    chunks.append({"text": unit_text.strip(), "unit": f"Unit {i+1}"})
        else:
            # Fall back to simple chunking
            chunks = [{"text": text[i:i+chunk_size], "unit": "unknown"} 
                      for i in range(0, len(text), chunk_size)]
        
        return chunks
    
    def _split_by_sentences(self, text: str, max_length: int) -> List[str]:
        """Split text by sentences, respecting max length."""
        import re
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
