"""
Workflow Engine — orchestrates agent execution with granular event emission.
Emits workflow_started, agent_started/completed/substep, and workflow_completed/failed.
"""
import time
import asyncio
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models.workflow import Workflow
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowEngine:
    """Runs agents in order per the execution plan, chaining outputs as inputs."""

    def __init__(self, db: Session, websocket_manager=None):
        self.db = db
        self.websocket_manager = websocket_manager
        self.accumulated_results = {}

    async def run(self, workflow_id: str):
        from backend.memory.shared_memory import SharedMemory
        from backend.memory.redis_state import RedisState
        from backend.agents.search_strategy_agent import SearchStrategyAgent
        from backend.agents.company_discovery import CompanyDiscoveryAgent
        from backend.agents.validation_agent import CompanyValidationAgent
        from backend.agents.tech_analysis_agent import TechAnalysisAgent
        from backend.agents.market_intelligence_agent import MarketIntelligenceAgent
        from backend.agents.decision_maker import DecisionMakerAgent
        from backend.agents.contact_enrichment import ContactEnrichmentAgent
        from backend.agents.qualification import QualificationAgent
        from backend.agents.recommendation_memory import RecommendationMemoryAgent

        redis = RedisState()
        shared_memory = SharedMemory(self.db)

        # Agent name -> class mapping
        AGENT_MAP = {
            "search_strategy": SearchStrategyAgent,
            "company_discovery": CompanyDiscoveryAgent,
            "validation": CompanyValidationAgent,
            "tech_analysis": TechAnalysisAgent,
            "market_intelligence": MarketIntelligenceAgent,
            "decision_maker": DecisionMakerAgent,
            "contact_enrichment": ContactEnrichmentAgent,
            "qualification": QualificationAgent,
            "recommendation_memory": RecommendationMemoryAgent,
        }

        workflow_start_time = time.time()

        try:
            # Load workflow
            workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            workflow.status = "running"
            workflow.started_at = datetime.now(timezone.utc)
            self.db.commit()

            # Resolve campaign config (support both Campaign and legacy Configuration)
            campaign_config = self._load_config(workflow)
            campaign_name = (
                campaign_config.get("business", {}).get("description")
                or (workflow.campaign.name if workflow.campaign else None)
                or "Untitled"
            )[:60]

            # Extract common config sections
            scoring_config = self._resolve_scoring_config(campaign_config)
            personas = self._resolve_personas(campaign_config)

            # Set up accumulated results
            self.accumulated_results = {
                "workflow_id": workflow_id,
                "icp": campaign_config,
                "personas": personas,
                "scoring_config": scoring_config,
            }

            # ── Emit workflow_started ─────────────────────────────────────
            await self.emit_event(workflow_id, "workflow", "workflow_started", {
                "campaign_name": campaign_name,
                "total_agents": len(AGENT_MAP),
                "estimated_time_minutes": max(1, len(AGENT_MAP) * 2),
            })

            # ── Run planner ───────────────────────────────────────────────
            await self.emit_event(workflow_id, "planner", "agent_started", {
                "agent_index": 0,
                "total_agents": len(AGENT_MAP) + 1,
                "start_time": datetime.now(timezone.utc).isoformat(),
            })

            from backend.planner.planner_agent import PlannerAgent
            planner = PlannerAgent(self.db, self.websocket_manager)

            try:
                plan = await planner.run(workflow_id, campaign_config)
            except Exception as e:
                logger.warning(f"Planner LLM failed ({e}), using mock plan")
                plan = await planner.run_mock(workflow_id, campaign_config)

            try:
                await redis.save_plan(workflow_id, plan.model_dump(mode="json"))
            except Exception:
                pass

            await self.emit_event(workflow_id, "planner", "agent_completed", {
                "duration_seconds": 0.5,
                "output_summary": f"Planner selected {len(plan.steps)} agents",
                "steps": [s.agent_name for s in plan.steps],
            })

            # ── Execute each agent step ───────────────────────────────────
            agent_index = 1
            total_agents = len([s for s in plan.steps if not s.skip]) + 1  # +1 for planner

            for step in plan.steps:
                if step.skip:
                    await self.emit_event(workflow_id, step.agent_name, "agent_completed", {
                        "agent_name": step.agent_name,
                        "duration_seconds": 0.0,
                        "output_summary": step.skip_reason or "Skipped by planner",
                        "company_count": 0,
                    })
                    continue

                agent_class = AGENT_MAP.get(step.agent_name)
                if not agent_class:
                    logger.warning(f"Unknown agent: {step.agent_name}")
                    continue

                agent = agent_class(self.db, self.websocket_manager)
                step_input = {**self.accumulated_results, **step.input_params}

                # ── Emit agent_started ────────────────────────────────────
                await self.emit_event(workflow_id, step.agent_name, "agent_started", {
                    "agent_name": step.agent_name,
                    "agent_index": agent_index,
                    "total_agents": total_agents,
                    "start_time": datetime.now(timezone.utc).isoformat(),
                })

                agent_start_time = time.time()
                max_retries = 2

                for attempt in range(max_retries):
                    try:
                        result = await agent.run(
                            input=step_input,
                            memory=shared_memory,
                            config=campaign_config,
                        )

                        duration = time.time() - agent_start_time
                        self.accumulated_results.update(result)

                        try:
                            await redis.save_workflow_state(workflow_id, self.accumulated_results)
                        except Exception:
                            pass

                        # ── Emit agent_completed ──────────────────────────
                        company_count = result.get("company_count", 0) or \
                                        result.get("companies_found", 0) or \
                                        result.get("analyzed_count", 0) or \
                                        result.get("contacts_found", 0) or \
                                        result.get("enriched", 0) or \
                                        result.get("scored", 0) or \
                                        result.get("companies_with_signals", 0) or \
                                        result.get("recommendations_created", 0) or \
                                        result.get("tech_analyzed", 0)

                        output_summary = self._summarize_output(step.agent_name, result)
                        await self.emit_event(workflow_id, step.agent_name, "agent_completed", {
                            "agent_name": step.agent_name,
                            "duration_seconds": round(duration, 1),
                            "output_summary": output_summary,
                            "company_count": company_count,
                        })
                        break  # success, exit retry loop

                    except Exception as e:
                        if attempt < max_retries - 1:
                            await self.emit_event(workflow_id, step.agent_name, "agent_substep", {
                                "substep_name": "retrying",
                                "substep_detail": f"Attempt {attempt+1} failed: {str(e)}, retrying...",
                                "progress_pct": None,
                            })
                            await asyncio.sleep(2)
                        else:
                            await self.emit_event(workflow_id, step.agent_name, "agent_failed", {
                                "agent_name": step.agent_name,
                                "error": str(e),
                                "retry_available": False,
                            })
                            self.accumulated_results[f"{step.agent_name}_error"] = str(e)

                agent_index += 1

            # ── Emit workflow_completed ───────────────────────────────────
            total_duration = time.time() - workflow_start_time
            workflow.status = "completed"
            workflow.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            stats = self._build_stats(self.accumulated_results)
            await self.emit_event(workflow_id, "workflow", "workflow_completed", {
                "duration_seconds": round(total_duration, 1),
                "stats": stats,
            })

        except Exception as e:
            # ── Emit workflow_failed ─────────────────────────────────────
            workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if workflow:
                workflow.status = "failed"
                self.db.commit()

            await self.emit_event(workflow_id, "workflow", "workflow_failed", {
                "failed_agent": "",
                "error": str(e),
                "recoverable": False,
            })
            raise

    # ══════════════════════════════════════════════════════════════════════
    # Event emission
    # ══════════════════════════════════════════════════════════════════════

    async def emit_event(self, workflow_id: str, agent: str, event_type: str, data: dict):
        """Emit a structured event via WebSocket."""
        from backend.workflow_engine.events import emit
        await emit(workflow_id, agent, event_type, data, self.websocket_manager)

    # ═════════════════════════════════════════════════════════���════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════

    def _load_config(self, workflow) -> dict:
        """
        Load campaign configuration from either Campaign or legacy Configuration model.
        """
        # Try campaign relationship first (new format)
        if hasattr(workflow, "campaign") and workflow.campaign:
            return workflow.campaign.config_json or {}

        # Legacy: Configuration model
        try:
            from backend.models.configuration import Configuration
            config = self.db.query(Configuration).filter(
                Configuration.id == workflow.configuration_id
            ).first()
            return config.config_json if config else {}
        except Exception:
            pass

        return {}

    @staticmethod
    def _resolve_scoring_config(config: dict) -> dict:
        """Extract scoring weights from campaign config (new or legacy format)."""
        weights = config.get("scoring_weights")
        if weights:
            return weights
        return config.get("scoring", {
            "industry_match": 25,
            "location_match": 10,
            "hiring_signals": 15,
            "tech_stack_match": 15,
            "funding_stage": 15,
            "revenue_tier": 5,
            "employee_range": 10,
            "decision_makers_found": 5,
        })

    @staticmethod
    def _resolve_personas(config: dict) -> list[dict]:
        """Extract personas from config (new campaign committee or legacy array)."""
        committee = config.get("buying_committee")
        if committee:
            personas = []
            primary = committee.get("primary_persona", {})
            if primary:
                personas.append(primary)
            for sec in committee.get("secondary_personas", []):
                personas.append(sec)
            # Add influencers as low-confidence personas
            for inf in committee.get("influencers", []):
                if isinstance(inf, str):
                    personas.append({"title": inf, "search_query": inf})
                elif isinstance(inf, dict):
                    personas.append(inf)
            return personas if personas else config.get("personas", [])
        return config.get("personas", [])

    @staticmethod
    def _summarize_output(agent_name: str, result: dict) -> str:
        """Build a one-line summary of an agent's output."""
        summaries = {
            "search_strategy": lambda r: f"Generated {r.get('query_count', r.get('query_count', 0))} search queries",
            "company_discovery": lambda r: f"Found {r.get('companies_found', 0)} companies",
            "validation": lambda r: f"Validated {r.get('validated', r.get('validated_count', 0))}, rejected {r.get('rejected', r.get('rejected_count', 0))}",
            "tech_analysis": lambda r: f"Analyzed {r.get('tech_analyzed', 0)} companies, avg match: {r.get('avg_required_match', 0)}",
            "market_intelligence": lambda r: f"{r.get('companies_with_signals', 0)} companies with signals, {r.get('high_urgency_count', 0)} high urgency",
            "decision_maker": lambda r: f"Found {r.get('contacts_found', 0)} contacts ({r.get('linkedin_confirmed', 0)} LinkedIn confirmed)",
            "contact_enrichment": lambda r: f"Enriched {r.get('enriched', 0)} contacts ({r.get('email_found', 0)} emails)",
            "qualification": lambda r: f"Scored {r.get('scored', 0)} companies: A:{r.get('tier_a_count', 0)} B:{r.get('tier_b_count', 0)} C:{r.get('tier_c_count', 0)}",
            "recommendation_memory": lambda r: f"Generated {r.get('recommendations_created', 0)} outreach packages",
        }
        builder = summaries.get(agent_name)
        if builder:
            return builder(result)
        return f"Processed {result.get('company_count', result.get('contacts_found', 0))} items"

    @staticmethod
    def _build_stats(results: dict) -> dict:
        """Aggregate workflow-level statistics from accumulated results."""
        return {
            "companies_found": results.get("companies_found", 0),
            "contacts_found": results.get("contacts_found", 0),
            "emails_found": results.get("email_found", 0),
            "high_urgency": results.get("high_urgency_count", 0),
            "tier_a": results.get("tier_a_count", 0),
            "tier_b": results.get("tier_b_count", 0),
            "tier_c": results.get("tier_c_count", 0),
            "recommendations": results.get("recommendations_created", 0),
            "scored": results.get("scored", 0),
        }
