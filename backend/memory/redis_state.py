"""
Redis State — workflow state caching with 24h TTL.
"""

import json

import redis.asyncio as aioredis

from backend.config.settings import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

TTL_SECONDS = 86400  # 24 hours


class RedisState:
    """
    Manages workflow state and execution plans in Redis.
    Keys:
        agentforge:workflow:{workflow_id} → serialized state dict
        agentforge:plan:{workflow_id} → serialized plan dict
    """

    def __init__(self):
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def save_workflow_state(self, workflow_id: str, state: dict):
        """Save workflow state with 24h TTL."""
        key = f"agentforge:workflow:{workflow_id}"
        await self.redis.set(key, json.dumps(state), ex=TTL_SECONDS)
        logger.info(f"Saved workflow state: {key}")

    async def get_workflow_state(self, workflow_id: str) -> dict | None:
        """Retrieve workflow state from Redis."""
        key = f"agentforge:workflow:{workflow_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def save_plan(self, workflow_id: str, plan: dict):
        """Save execution plan with 24h TTL."""
        key = f"agentforge:plan:{workflow_id}"
        await self.redis.set(key, json.dumps(plan), ex=TTL_SECONDS)
        logger.info(f"Saved execution plan: {key}")

    async def get_plan(self, workflow_id: str) -> dict | None:
        """Retrieve execution plan from Redis."""
        key = f"agentforge:plan:{workflow_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def delete_workflow(self, workflow_id: str):
        """Delete both workflow state and plan keys."""
        wf_key = f"agentforge:workflow:{workflow_id}"
        plan_key = f"agentforge:plan:{workflow_id}"
        await self.redis.delete(wf_key, plan_key)
        logger.info(f"Deleted Redis state for workflow {workflow_id}")
