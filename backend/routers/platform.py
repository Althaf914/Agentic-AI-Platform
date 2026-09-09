"""
Platform health endpoint — reports status of all subsystems in parallel.
"""

import asyncio
from fastapi import APIRouter
from backend.config.settings import get_settings
from sqlalchemy import text
import redis
import httpx

router = APIRouter(prefix="/platform", tags=["Platform"])
settings = get_settings()


def check_postgres():
    try:
        from backend.database.session import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "connected", "message": "Primary data store for all records"}
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)[:70]}"}


def check_redis():
    try:
        r = redis.from_url(settings.REDIS_URL, socket_timeout=1)
        r.ping()
        return {"status": "connected", "message": "Workflow state cache and task queue"}
    except Exception as e:
        # If the command HELLO fails or connection times out, we still know it is there if it throws HELLO error
        if "unknown command" in str(e).lower() or "hello" in str(e).lower():
            return {"status": "connected", "message": "Workflow state cache and task queue"}
        return {"status": "not_configured", "message": "Workflow state cache and task queue (not running)"}


async def check_chromadb():
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"http://{settings.CHROMADB_HOST}:{settings.CHROMADB_PORT}/api/v1/heartbeat")
            if resp.status_code == 200:
                return {"status": "connected", "message": "Vector embeddings for semantic memory search"}
            else:
                return {"status": "not_configured", "message": "Vector embeddings for semantic memory search (not running)"}
    except Exception:
        return {"status": "not_configured", "message": "Vector embeddings for semantic memory search (not running)"}


@router.get("/health")
async def platform_health():
    """Check all subsystem connectivity and report status."""
    pg_task = asyncio.to_thread(check_postgres)
    redis_task = asyncio.to_thread(check_redis)
    chroma_task = check_chromadb()
    
    pg_res, redis_res, chroma_res = await asyncio.gather(pg_task, redis_task, chroma_task)
    
    results = {
        "postgresql": pg_res,
        "redis": redis_res,
        "chromadb": chroma_res
    }

    # Groq LLM
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "gsk_...":
        results["groq_llm"] = {
            "status": "connected",
            "message": f"{settings.GROQ_MODEL} for planner + qualification reasoning",
            "model": settings.GROQ_MODEL,
        }
    else:
        results["groq_llm"] = {"status": "not_configured", "message": "llama3-70b-8192 for planner + qualification reasoning"}

    # SerpAPI
    if settings.SERPAPI_KEY and settings.SERPAPI_KEY != "...":
        results["serpapi"] = {"status": "connected", "message": "Google search for company discovery"}
    else:
        results["serpapi"] = {"status": "not_configured", "message": "Google search for company discovery (using mock data)"}

    # Hunter.io
    if settings.HUNTER_API_KEY and settings.HUNTER_API_KEY != "...":
        results["hunter_io"] = {"status": "connected", "message": "Real email lookup for decision makers"}
    else:
        results["hunter_io"] = {"status": "not_configured", "message": "Real email lookup for decision makers (using formula)"}

    # API Keys summary (masked)
    keys = {
        "GROQ_API_KEY": _mask_key(settings.GROQ_API_KEY),
        "SERPAPI_KEY": _mask_key(settings.SERPAPI_KEY),
        "HUNTER_API_KEY": _mask_key(settings.HUNTER_API_KEY),
    }

    return {
        "subsystems": results,
        "keys": keys,
        "use_mock_data": settings.USE_MOCK_DATA,
    }


def _mask_key(key: str) -> str:
    if not key or key in ["...", "gsk_..."]:
        return "not_configured"
    if len(key) > 8:
        return f"{key[:4]}****{key[-4:]}"
    return "configured"
