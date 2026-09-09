import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from backend.models.agent_log import AgentLog

# Agent registry for extensibility
AGENT_REGISTRY = {}


def register_agent(name: str):
    def decorator(cls):
        AGENT_REGISTRY[name] = cls
        cls._agent_name = name
        return cls
    return decorator


def get_agent_class(name: str):
    if name not in AGENT_REGISTRY:
        raise ValueError(f"Agent '{name}' not registered. Available: {list(AGENT_REGISTRY.keys())}")
    return AGENT_REGISTRY[name]


class BaseAgent(ABC):
    def __init__(self, db, websocket_manager=None):
        self.db = db
        self.websocket_manager = websocket_manager

    @abstractmethod
    async def run(self, input: dict, memory, config: dict) -> dict:
        """Run the agent. Must return dict that gets merged into accumulated_results."""
        pass

    async def emit(self, workflow_id: str, agent_name: str, status: str, data: dict = {}):
        """Emit WebSocket event to frontend."""
        if self.websocket_manager:
            try:
                from backend.workflow_engine.events import emit as _emit
                await _emit(workflow_id, agent_name, status, data)
            except Exception as e:
                print(f"[WebSocket] Emit error: {e}")

    async def _emit_substep(self, workflow_id: str, substep_name: str,
                            substep_detail: str = "", progress_pct: int | None = None):
        """
        Emit a granular sub-step progress event for the current agent.

        Call this at each logical sub-operation within an agent run.
        The frontend uses these to build animated per-step progress indicators.

        Args:
            workflow_id: Current workflow ID.
            substep_name: Machine-readable sub-step identifier (snake_case).
            substep_detail: Human-readable description of what's happening now.
            progress_pct: Optional 0-100 progress indicator for the current agent.
        """
        agent_name = getattr(self, "_agent_name", "unknown")
        await self.emit(
            workflow_id,
            agent_name,
            "agent_substep",
            {
                "substep_name": substep_name,
                "substep_detail": substep_detail,
                "progress_pct": progress_pct,
            },
        )

    async def _emit_company_event(self, workflow_id: str, event_type: str,
                                  company_name: str, domain: str = "", **kwargs):
        """
        Emit a company-level event (discovered, validated, rejected, etc.).

        Args:
            workflow_id: Current workflow ID.
            event_type: One of 'company_discovered', 'company_validated',
                        'company_rejected', 'tech_detected', 'contact_found',
                        'qualification_scored', 'recommendation_created'.
            company_name: Company name string.
            domain: Company domain string.
            **kwargs: Extra fields passed to the event data payload.
        """
        agent_name = getattr(self, "_agent_name", "unknown")
        data = {"company_name": company_name, "domain": domain, **kwargs}
        await self.emit(workflow_id, agent_name, event_type, data)

    async def log_start(self, workflow_id: str, agent_name: str, input_json: dict) -> str:
        log = AgentLog(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            agent_name=agent_name,
            status="running",
            input_json=input_json,
            started_at=datetime.utcnow(),
        )
        self.db.add(log)
        self.db.commit()
        return log.id

    async def log_complete(self, log_id: str, output_json: dict):
        log = self.db.query(AgentLog).filter(AgentLog.id == log_id).first()
        if log:
            log.status = "completed"
            log.output_json = output_json
            log.completed_at = datetime.utcnow()
            self.db.commit()

    async def log_failed(self, log_id: str, error: str):
        log = self.db.query(AgentLog).filter(AgentLog.id == log_id).first()
        if log:
            log.status = "failed"
            log.error_message = error
            log.completed_at = datetime.utcnow()
            self.db.commit()
