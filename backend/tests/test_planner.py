"""
Unit tests for PlannerAgent — mock plan generation, logging, and memory awareness.
"""

import uuid
import pytest
import asyncio

from backend.config.presets import PRESET_CONFIGS
from backend.planner.planner_agent import PlannerAgent
from backend.models.workflow import Workflow
from backend.models.configuration import Configuration
from backend.models.planner_log import PlannerLog
from backend.memory.shared_memory import SharedMemory


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _create_workflow(test_db, user_id, config_json):
    """Helper to create a workflow with a configuration."""
    config = Configuration(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name="Planner Test Config",
        type="icp",
        config_json=config_json,
    )
    test_db.add(config)
    test_db.flush()

    workflow = Workflow(
        id=str(uuid.uuid4()),
        user_id=user_id,
        configuration_id=config.id,
        status="running",
    )
    test_db.add(workflow)
    test_db.commit()
    return workflow


class TestPlannerAgent:
    def test_planner_mock_returns_all_agents(self, test_db, seed_users):
        """run_mock should return a plan with all 9 agents, none skipped."""
        admin = seed_users["admin"]
        workflow = _create_workflow(test_db, admin.id, PRESET_CONFIGS["b2b_saas"]["icp"])

        planner = PlannerAgent(test_db, websocket_manager=None)
        plan = run_async(planner.run_mock(workflow.id, PRESET_CONFIGS["b2b_saas"]))

        expected = [
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
        assert len(plan.steps) == 9
        for i, name in enumerate(expected):
            assert plan.steps[i].agent_name == name, f"Step {i}: expected {name}, got {plan.steps[i].agent_name}"
        assert all(step.skip is False for step in plan.steps)

    def test_planner_logs_written(self, test_db, seed_users):
        """run_mock should write 9 PlannerLog rows to the database."""
        admin = seed_users["admin"]
        workflow = _create_workflow(test_db, admin.id, PRESET_CONFIGS["b2b_saas"]["icp"])

        planner = PlannerAgent(test_db, websocket_manager=None)
        run_async(planner.run_mock(workflow.id, PRESET_CONFIGS["b2b_saas"]))

        logs = (
            test_db.query(PlannerLog)
            .filter(PlannerLog.workflow_id == workflow.id)
            .order_by(PlannerLog.step_number)
            .all()
        )

        assert len(logs) == 9
        assert logs[0].step_number == 1
        assert logs[0].agent_selected == "search_strategy"
        assert logs[8].step_number == 9
        assert logs[8].agent_selected == "recommendation_memory"

    def test_planner_plan_has_correct_workflow_id(self, test_db, seed_users):
        """The returned plan should reference the correct workflow_id."""
        admin = seed_users["admin"]
        workflow = _create_workflow(test_db, admin.id, PRESET_CONFIGS["cybersecurity"]["icp"])

        planner = PlannerAgent(test_db, websocket_manager=None)
        plan = run_async(planner.run_mock(workflow.id, PRESET_CONFIGS["cybersecurity"]))

        assert plan.workflow_id == workflow.id
        assert "Mock plan" in plan.reasoning
