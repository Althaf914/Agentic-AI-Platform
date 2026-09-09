"""
Celery task runner — not used when Redis is unavailable.
Workflow execution is handled via asyncio tasks in workflow_service.py
"""

# Placeholder — Celery tasks are only used in production with Redis
def run_workflow_task(workflow_id: str):
    """Stub — real execution happens via asyncio.create_task in workflow_service."""
    raise NotImplementedError("Use workflow_service._run_workflow_async instead")
