"""
Shared Memory — unified read/write interface backed by PostgreSQL + ChromaDB.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models.memory import Memory
from backend.memory.chroma_client import embed_text, get_or_create_collection
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SharedMemory:
    """
    Unified memory interface.
    - PostgreSQL: structured storage (entity_type, summary, metadata)
    - ChromaDB: vector embeddings for semantic search
    """

    def __init__(self, db: Session):
        self.db = db

    async def write(
        self,
        entity_type: str,
        entity_id: str,
        summary: str,
        metadata: dict = None,
    ) -> str:
        """
        Write a memory entry.

        Step 1: Create memory row in PostgreSQL
        Step 2: Generate embedding via embed_text()
        Step 3: Upsert into ChromaDB collection
        Step 4: Update memory_row.embedding_id

        Returns: memory_row.id
        """
        # Step 1: Create PostgreSQL row
        memory_row = Memory(
            id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            embedding_id=None,
            last_seen=datetime.now(timezone.utc),
            metadata_json=metadata or {},
        )
        self.db.add(memory_row)
        self.db.commit()
        self.db.refresh(memory_row)

        # Step 2: Generate embedding
        try:
            embedding = embed_text(summary)
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return memory_row.id

        # Step 3: Upsert into ChromaDB
        try:
            collection = get_or_create_collection()
            collection.upsert(
                ids=[memory_row.id],
                embeddings=[embedding],
                metadatas=[{
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "summary": summary[:500],  # ChromaDB metadata limit
                }],
                documents=[summary],
            )
        except Exception as e:
            logger.warning(f"ChromaDB upsert failed: {e}")
            return memory_row.id

        # Step 4: Update embedding_id
        memory_row.embedding_id = memory_row.id
        self.db.commit()

        logger.info(f"Memory written: {entity_type}/{entity_id} (id={memory_row.id})")
        return memory_row.id

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Semantic search over memory.

        Step 1: Embed query
        Step 2: Query ChromaDB collection
        Step 3: Load matching memory rows from PostgreSQL

        Returns: list of {entity_type, entity_id, summary, last_seen, metadata, distance}
        """
        # Step 1: Embed query
        try:
            query_embedding = embed_text(query)
        except Exception as e:
            logger.warning(f"Query embedding failed: {e}")
            return []

        # Step 2: Query ChromaDB
        try:
            collection = get_or_create_collection()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
        except Exception as e:
            logger.warning(f"ChromaDB query failed: {e}, falling back to DB search")
            return self._fallback_search(query, top_k)

        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        # Step 3: Load from PostgreSQL
        ids = results["ids"][0]
        distances = results.get("distances", [[]])[0]

        entries = []
        for i, memory_id in enumerate(ids):
            row = self.db.query(Memory).filter(Memory.id == memory_id).first()
            if row:
                entries.append({
                    "entity_type": row.entity_type,
                    "entity_id": row.entity_id,
                    "summary": row.summary,
                    "last_seen": row.last_seen,
                    "metadata": row.metadata_json,
                    "distance": distances[i] if i < len(distances) else None,
                })

        return entries

    def check_duplicate(self, domain: str) -> bool:
        """
        Check if a company domain was already processed in any previous workflow.

        Queries PostgreSQL: memory WHERE entity_type='company' AND
        metadata_json contains domain.
        """
        from sqlalchemy import cast, String

        result = (
            self.db.query(Memory)
            .filter(
                Memory.entity_type == "company",
                cast(Memory.metadata_json["domain"], String) == f'"{domain}"',
            )
            .first()
        )

        if result:
            return True

        # Fallback: search summary text for domain
        result = (
            self.db.query(Memory)
            .filter(
                Memory.entity_type == "company",
                Memory.summary.ilike(f"%{domain}%"),
            )
            .first()
        )
        return result is not None

    async def get_timeline(self, entity_id: str) -> list[dict]:
        """
        Get all memory entries for an entity, ordered chronologically.

        Returns ordered list of all memory entries for that entity.
        """
        rows = (
            self.db.query(Memory)
            .filter(Memory.entity_id == entity_id)
            .order_by(Memory.created_at.asc())
            .all()
        )

        return [
            {
                "id": row.id,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "summary": row.summary,
                "last_seen": row.last_seen,
                "metadata": row.metadata_json,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def _fallback_search(self, query: str, top_k: int) -> list[dict]:
        """Fallback text search when ChromaDB is unavailable."""
        rows = (
            self.db.query(Memory)
            .filter(Memory.summary.ilike(f"%{query}%"))
            .limit(top_k)
            .all()
        )
        return [
            {
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "summary": row.summary,
                "last_seen": row.last_seen,
                "metadata": row.metadata_json,
                "distance": None,
            }
            for row in rows
        ]


# Module-level convenience functions for use without instantiation
def search_memory(query: str, top_k: int = 5, db: Session = None) -> list:
    """Convenience function for searching memory (used by routers/planner)."""
    if db is None:
        from backend.database.session import SessionLocal
        db = SessionLocal()
    mem = SharedMemory(db)
    import asyncio
    return asyncio.run(mem.search(query, top_k))


def write_memory(
    entity_type: str,
    entity_id: str,
    summary: str,
    metadata_json: dict = None,
    db: Session = None,
) -> str:
    """Convenience function for writing memory (used by approval_service)."""
    if db is None:
        from backend.database.session import SessionLocal
        db = SessionLocal()
    mem = SharedMemory(db)
    import asyncio
    return asyncio.run(mem.write(entity_type, entity_id, summary, metadata_json))
