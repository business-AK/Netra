import hashlib
import numpy as np
from typing import List
from app.config import settings

class TextEmbedder:
    _instance = None

    def __init__(self):
        self.dimension = 384
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer
            print(f"Loading Sentence-Transformers model '{settings.TEXT_EMBEDDING_MODEL}'...")
            self.model = SentenceTransformer(settings.TEXT_EMBEDDING_MODEL)
            print("Sentence-Transformers model loaded successfully.")
        except Exception as e:
            print(f"Warning: Could not load SentenceTransformer ('{e}'). Using fallback text embedder.")
            self.model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TextEmbedder()
        return cls._instance

    def _fallback_embed(self, text: str) -> np.ndarray:
        """Deterministic pseudo-semantic embedding for offline/fallback use."""
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            vec[0] = 1.0
            return vec

        for word in words:
            # Deterministic hash projection
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            val = ((h >> 8) % 1000) / 1000.0 - 0.5
            vec[idx] += float(val)

        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embeds a list of text strings into L2-normalized 384-dim vectors.
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        if self.model is not None:
            try:
                embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
                return np.array(embeddings, dtype=np.float32)
            except Exception as e:
                print(f"Warning: SentenceTransformer encode failed ({e}), using fallback.")

        return np.vstack([self._fallback_embed(t) for t in texts])

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embeds a single query string into L2-normalized 384-dim vector.
        """
        if self.model is not None:
            try:
                embedding = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)
                return np.array(embedding, dtype=np.float32)
            except Exception as e:
                print(f"Warning: SentenceTransformer query encode failed ({e}), using fallback.")

        return np.array([self._fallback_embed(query)], dtype=np.float32)
