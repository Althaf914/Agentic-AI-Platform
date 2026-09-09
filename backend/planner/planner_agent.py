"""
Planner Agent — uses an LLM to dynamically create an execution plan for a workflow.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.models.configuration import Configuration
from backend.models.planner_log import PlannerLog
from backend.models.workflow import Workflow
from backend.planner.execution_plan import AgentStep, ExecutionPlan
from backend.utils.exceptions import NotFoundError
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Load planner system prompt from file
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "planner.txt"
PLANNER_SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

VALID_AGENTS = [
    "search_strategy",
    "company_discovery",
    "validation",
    "tech_analysis",
    "market_intelligence",
    "decision_maker",
    "contact_enrichment",
    "qualification",
    "recommendation_memory",
]

# Workflow stages define the ordered execution topology.
# Sequential stages run one after another; parallel execution within a stage
# is handled by the engine when an agent list contains multiple entries.
WORKFLOW_STAGES = [
    {"stage": 0, "agents": ["search_strategy"], "mode": "sequential"},
    {"stage": 1, "agents": ["company_discovery"], "mode": "parallel"},
    {"stage": 2, "agents": ["validation"], "mode": "sequential"},
    {"stage": 3, "agents": ["tech_analysis", "market_intelligence"], "mode": "parallel"},
    {"stage": 4, "agents": ["decision_maker"], "mode": "parallel"},
    {"stage": 5, "agents": ["contact_enrichment"], "mode": "sequential"},
    {"stage": 6, "agents": ["qualification"], "mode": "sequential"},
    {"stage": 7, "agents": ["recommendation_memory"], "mode": "sequential"},
]


class PlannerAgent:
    """
    LLM-powered planner that creates dynamic execution plans for discovery workflows.
    """

    def __init__(self, db: Session, websocket_manager=None):
        self.db = db
        self.ws_manager = websocket_manager

    async def run(self, workflow_id: str, config: dict) -> ExecutionPlan:
        """
        Generate an execution plan using LLM reasoning.

        Steps:
        1. Load workflow config from DB
        2. Get memory context for processed companies
        3. Build LLM messages (system + user)
        4. Call LLM (OpenAI or Anthropic)
        5. Parse response into ExecutionPlan
        6. Write planner_logs rows
        7. Emit WebSocket event
        8. Return ExecutionPlan
        """
        # Step 1: Load workflow and configuration from DB
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise NotFoundError(detail=f"Workflow {workflow_id} not found")

        configuration = self.db.query(Configuration).filter(Configuration.id == workflow.configuration_id).first()
        if not configuration:
            raise NotFoundError(detail=f"Configuration for workflow {workflow_id} not found")

        workflow_config = configuration.config_json

        # Step 2: Get memory context
        memory_context = await self._get_memory_context()

        # Step 3: Build messages array
        user_message = json.dumps({
            "workflow_config": workflow_config,
            "memory_context": memory_context,
            "workflow_id": workflow_id,
        }, indent=2)

        messages = [
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        # Step 4: Call LLM
        raw_response = await self._call_llm(messages)

        # Step 5: Parse response into ExecutionPlan
        steps = self._parse_response(raw_response)
        plan = ExecutionPlan(
            workflow_id=workflow_id,
            steps=steps,
            reasoning=f"LLM-generated plan with {len(steps)} steps ({len([s for s in steps if not s.skip])} active)",
            created_at=datetime.now(timezone.utc),
        )

        # Step 6: Write planner_logs
        self._write_planner_logs(workflow_id, plan)

        # Step 7: Emit WebSocket event
        await self._emit_event(workflow_id, plan)

        # Step 8: Return plan
        logger.info(f"Planner completed for workflow {workflow_id}: {len(plan.active_steps)} active steps")
        return plan

    async def run_mock(self, workflow_id: str, config: dict) -> ExecutionPlan:
        """
        Returns a deterministic ExecutionPlan with all 8 agents for testing without LLM.
        """
        steps = [
            AgentStep(
                agent_name="search_strategy",
                input_params={},
                skip=False,
                skip_reason=None,
            ),
            AgentStep(
                agent_name="company_discovery",
                input_params={"icp_config": config},
                skip=False,
                skip_reason=None,
            ),
            AgentStep(
                agent_name="validation",
                input_params={},
                skip=False,
                skip_reason=None,
            ),
            AgentStep(
                agent_name="tech_analysis",
                input_params={},
                skip=False,
                skip_reason=None,
            ),
            AgentStep(
                agent_name="market_intelligence",
                input_params={},
                skip=False,
                skip_reason=None,
            ),
            AgentStep(
                agent_name="decision_maker",
                input_params={"persona_config": {}},
                skip=False,
                skip_reason=None,
            ),
            AgentStep(
                agent_name="contact_enrichment",
                input_params={},
                skip=False,
                skip_reason=None,
            ),
            AgentStep(
                agent_name="qualification",
                input_params={"scoring_config": {}},
                skip=False,
                skip_reason=None,
            ),
            AgentStep(
                agent_name="recommendation_memory",
                input_params={"min_score_threshold": 60.0},
                skip=False,
                skip_reason=None,
            ),
        ]

        plan = ExecutionPlan(
            workflow_id=workflow_id,
            steps=steps,
            reasoning="Mock plan: search_strategy first, then all 8 agents in standard order, no skips (testing mode)",
            created_at=datetime.now(timezone.utc),
        )

        # Write logs even in mock mode
        self._write_planner_logs(workflow_id, plan)
        await self._emit_event(workflow_id, plan)

        logger.info(f"Mock planner completed for workflow {workflow_id}")
        return plan

    async def _get_memory_context(self) -> list[dict]:
        """Load memory context for previously processed companies."""
        try:
            from backend.memory.shared_memory import SharedMemory
            mem = SharedMemory(self.db)
            results = await mem.search(query="processed companies", top_k=10)
            if results:
                return [
                    {
                        "entity_type": r.entity_type if hasattr(r, "entity_type") else r.get("entity_type"),
                        "entity_id": r.entity_id if hasattr(r, "entity_id") else r.get("entity_id"),
                        "summary": r.summary if hasattr(r, "summary") else r.get("summary"),
                    }
                    for r in results
                ]
            return []
        except Exception as e:
            logger.warning(f"Failed to load memory context: {e}")
            return []

    async def _call_llm(self, messages: list[dict]) -> str:
        """Call OpenAI or Anthropic based on settings.DEFAULT_MODEL."""
        model = settings.DEFAULT_MODEL

        if model.startswith("claude") and settings.ANTHROPIC_API_KEY:
            return await self._call_anthropic(messages, model)
        else:
            return await self._call_openai(messages, model)

    async def _call_openai(self, messages: list[dict], model: str) -> str:
        """Call OpenAI Chat Completions API."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except ImportError:
            logger.error("openai package not installed, falling back to mock")
            return self._mock_llm_response()
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return self._mock_llm_response()

    async def _call_anthropic(self, messages: list[dict], model: str) -> str:
        """Call Anthropic Messages API."""
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

            # Anthropic uses system as a top-level param
            system_msg = messages[0]["content"] if messages[0]["role"] == "system" else ""
            user_messages = [m for m in messages if m["role"] != "system"]

            response = await client.messages.create(
                model=model,
                system=system_msg,
                messages=user_messages,
                max_tokens=2000,
                temperature=0.2,
            )
            return response.content[0].text
        except ImportError:
            logger.error("anthropic package not installed, falling back to mock")
            return self._mock_llm_response()
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            return self._mock_llm_response()

    def _mock_llm_response(self) -> str:
        """Fallback mock response when LLM is unavailable."""
        return json.dumps([
            {"agent_name": "search_strategy", "input_params": {}, "skip": False, "skip_reason": None},
            {"agent_name": "company_discovery", "input_params": {}, "skip": False, "skip_reason": None},
            {"agent_name": "validation", "input_params": {}, "skip": False, "skip_reason": None},
            {"agent_name": "tech_analysis", "input_params": {}, "skip": False, "skip_reason": None},
            {"agent_name": "market_intelligence", "input_params": {}, "skip": False, "skip_reason": None},
            {"agent_name": "decision_maker", "input_params": {}, "skip": False, "skip_reason": None},
            {"agent_name": "contact_enrichment", "input_params": {}, "skip": False, "skip_reason": None},
            {"agent_name": "qualification", "input_params": {}, "skip": False, "skip_reason": None},
            {"agent_name": "recommendation_memory", "input_params": {}, "skip": False, "skip_reason": None},
        ])

    def _parse_response(self, raw_response: str) -> list[AgentStep]:
        """Parse LLM response JSON into list of AgentStep objects."""
        # Strip markdown fences if LLM ignores instructions
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines (fences)
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse planner response as JSON: {e}")
            logger.error(f"Raw response: {raw_response[:500]}")
            # Return default plan on parse failure
            return [AgentStep(agent_name=name, input_params={}, skip=False) for name in VALID_AGENTS]

        steps = []
        for item in data:
            agent_name = item.get("agent_name", "")
            if agent_name not in VALID_AGENTS:
                logger.warning(f"Planner returned invalid agent name: {agent_name}, skipping")
                continue

            steps.append(AgentStep(
                agent_name=agent_name,
                input_params=item.get("input_params", {}),
                skip=item.get("skip", False),
                skip_reason=item.get("skip_reason"),
            ))

        return steps

    def _write_planner_logs(self, workflow_id: str, plan: ExecutionPlan):
        """Write a PlannerLog row for each step in the plan."""
        for i, step in enumerate(plan.steps):
            log = PlannerLog(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                step_number=i + 1,
                agent_selected=step.agent_name,
                decision_reasoning=(
                    f"Skip: {step.skip_reason}" if step.skip
                    else f"Run with params: {json.dumps(step.input_params)[:200]}"
                ),
            )
            self.db.add(log)

        self.db.commit()
        logger.info(f"Wrote {len(plan.steps)} planner log entries for workflow {workflow_id}")

    async def _emit_event(self, workflow_id: str, plan: ExecutionPlan):
        """Emit WebSocket event for planner completion."""
        if not self.ws_manager:
            return

        try:
            from backend.workflow_engine.events import emit
            await emit(
                workflow_id=workflow_id,
                agent_name="planner",
                event_type="completed",
                data={
                    "total_steps": len(plan.steps),
                    "active_steps": len(plan.active_steps),
                    "skipped_steps": len(plan.skipped_steps),
                    "agents": [s.agent_name for s in plan.active_steps],
                    "reasoning": plan.reasoning,
                },
                manager=self.ws_manager,
            )
        except Exception as e:
            logger.warning(f"Failed to emit planner WebSocket event: {e}")
