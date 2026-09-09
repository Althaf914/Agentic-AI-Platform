"""
Workflow engine package — orchestration and event emission.
"""

from backend.workflow_engine.engine import WorkflowEngine
from backend.workflow_engine.events import emit

__all__ = ["WorkflowEngine", "emit"]
