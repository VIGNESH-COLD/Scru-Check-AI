"""
Embeddings Module
Generates and manages sentence embeddings for semantic matching
"""

import os
from typing import List, Dict, Any, Optional
import json
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    np = None


class EmbeddingsManager:
    """
    Manages sentence embeddings for semantic similarity.
    Uses all-MiniLM-L6-v2 model for efficient embeddings.
    """
    
    MODEL_NAME = "all-MiniLM-L6-v2"
    CACHE_DIR = "./embedding_cache"
    
    def __init__(self):
        self.model = None
        self.cache = {}
        self._initialize()
    
    def _initialize(self):
        """Initialize embedding model."""
        if not EMBEDDINGS_AVAILABLE:
            print("⚠️ sentence-transformers not available, using fallback")
            return
        
        try:
            self.model = SentenceTransformer(self.MODEL_NAME)
            print(f"✅ Embedding model loaded: {self.MODEL_NAME}")
            
            # Load cache
            os.makedirs(self.CACHE_DIR, exist_ok=True)
            self._load_cache()
        except Exception as e:
            print(f"⚠️ Embedding model failed: {e}")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding vector for text.
        Uses cache for efficiency.
        """
        if not self.model:
            return self._fallback_embedding(text)
        
        # Check cache
        cache_key = self._get_cache_key(text)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            embedding = self.model.encode(text).tolist()
            self.cache[cache_key] = embedding
            return embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return self._fallback_embedding(text)
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts efficiently."""
        if not self.model:
            return [self._fallback_embedding(t) for t in texts]
        
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            print(f"Batch embedding error: {e}")
            return [self._fallback_embedding(t) for t in texts]
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        Returns score from 0.0 to 1.0.
        """
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        
        if emb1 is None or emb2 is None:
            return self._fallback_similarity(text1, text2)
        
        return self._cosine_similarity(emb1, emb2)
    
    def find_most_similar(self, query: str, candidates: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find most similar texts from candidates.
        Returns list of {text, similarity} sorted by similarity.
        """
        query_emb = self.get_embedding(query)
        if query_emb is None:
            return []
        
        results = []
        for candidate in candidates:
            cand_emb = self.get_embedding(candidate)
            if cand_emb:
                sim = self._cosine_similarity(query_emb, cand_emb)
                results.append({"text": candidate, "similarity": sim})
        
        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if EMBEDDINGS_AVAILABLE and np:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        else:
            # Pure Python fallback
            dot = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            return dot / (norm1 * norm2) if norm1 and norm2 else 0.0
    
    def _fallback_embedding(self, text: str) -> List[float]:
        """Simple fallback embedding using character-based hashing."""
        # Create a simple 64-dim embedding based on text hash
        text = text.lower()
        embedding = []
        for i in range(64):
            # Hash different parts of text
            h = hashlib.md5(f"{text}_{i}".encode()).hexdigest()
            val = int(h[:8], 16) / 0xFFFFFFFF  # Normalize to 0-1
            embedding.append(val * 2 - 1)  # Scale to -1 to 1
        return embedding
    
    def _fallback_similarity(self, text1: str, text2: str) -> float:
        """Fallback similarity using Jaccard on words."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _load_cache(self):
        """Load embedding cache from disk."""
        cache_file = os.path.join(self.CACHE_DIR, "embeddings.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    self.cache = json.load(f)
                print(f"Loaded {len(self.cache)} cached embeddings")
            except:
                self.cache = {}
    
    def save_cache(self):
        """Save embedding cache to disk."""
        cache_file = os.path.join(self.CACHE_DIR, "embeddings.json")
        try:
            with open(cache_file, "w") as f:
                json.dump(self.cache, f)
        except Exception as e:
            print(f"Cache save error: {e}")


# Singleton instance
embeddings_manager = EmbeddingsManager()
