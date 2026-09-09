"""
ChromaDB client — connection, collection management, and embedding generation.
"""

import chromadb

from backend.config.settings import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level cache for the embedding model
_embedding_model = None


def get_chroma_client() -> chromadb.HttpClient:
    """Returns a ChromaDB HttpClient connected to the configured host/port."""
    return chromadb.HttpClient(
        host=settings.CHROMADB_HOST,
        port=settings.CHROMADB_PORT,
    )


def get_or_create_collection(name: str = "agentforge_memory"):
    """Get or create a ChromaDB collection by name."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"ChromaDB collection '{name}' ready (count={collection.count()})")
    return collection


def embed_text(text: str) -> list[float]:
    """
    Generate an embedding vector for the given text.
    Uses sentence-transformers 'all-MiniLM-L6-v2' model.
    The model is cached on first call for performance.
    """
    global _embedding_model

    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Falling back to hash-based mock embeddings."
            )
            return _mock_embedding(text)

    embedding = _embedding_model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def _mock_embedding(text: str) -> list[float]:
    """
    Fallback: generate a deterministic 384-dim mock embedding from text hash.
    Only used when sentence-transformers is not installed.
    """
    import hashlib
    import struct

    hash_bytes = hashlib.sha512(text.encode()).digest()
    # Extend to 384 floats by repeating hash
    extended = hash_bytes * 3  # 192 bytes -> will use first 384*4 bytes
    values = []
    for i in range(384):
        byte_val = extended[i % len(extended)]
        values.append((byte_val / 255.0) * 2 - 1)  # Normalize to [-1, 1]

    # L2 normalize
    norm = sum(v * v for v in values) ** 0.5
    if norm > 0:
        values = [v / norm for v in values]

    return values
