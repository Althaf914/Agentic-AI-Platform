"""
LangGraph StateGraph for tracking workflow execution state.

Defines the graph topology: start → agent_node(s) → approval_wait → memory → end
"""

from typing import TypedDict, Any

from langgraph.graph import StateGraph, END

from backend.planner.execution_plan import ExecutionPlan
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# ─── State Schema ────────────────────────────────────────────────────────────

class WorkflowState(TypedDict):
    """Shared state passed through the LangGraph workflow."""
    workflow_id: str
    current_agent: str
    completed_agents: list[str]
    failed_agents: list[str]
    plan: dict  # Serialized ExecutionPlan
    results: dict  # agent_name -> output dict


# ─── Node Functions ──────────────────────────────────────────────────────────

def start_node(state: WorkflowState) -> WorkflowState:
    """
    Entry node — initializes state, logs workflow start.
    """
    logger.info(f"Workflow {state['workflow_id']} starting with plan: {len(state['plan'].get('steps', []))} steps")
    state["completed_agents"] = []
    state["failed_agents"] = []
    state["results"] = {}
    return state


def agent_node(state: WorkflowState) -> WorkflowState:
    """
    Generic agent execution node — runs the current agent.
    The actual agent is determined by state['current_agent'].
    Agent execution is handled externally by the workflow engine;
    this node updates state tracking.
    """
    agent_name = state["current_agent"]
    logger.info(f"Executing agent: {agent_name} for workflow {state['workflow_id']}")

    # Mark agent as completed (actual execution happens in workflow_engine.engine)
    # If execution fails, the engine will update failed_agents instead
    if agent_name not in state["completed_agents"]:
        state["completed_agents"].append(agent_name)

    return state


def approval_wait_node(state: WorkflowState) -> WorkflowState:
    """
    Pause node — waits for human approval of recommendations.
    In practice, this creates approval records and the workflow
    resumes when approvals are submitted via the API.
    """
    logger.info(f"Workflow {state['workflow_id']} waiting for approvals")
    return state


def memory_node(state: WorkflowState) -> WorkflowState:
    """
    Memory write node — persists results to long-term memory (ChromaDB).
    Triggered after approvals are processed.
    """
    logger.info(f"Writing results to memory for workflow {state['workflow_id']}")
    return state


def end_node(state: WorkflowState) -> WorkflowState:
    """
    Terminal node — marks workflow as completed.
    """
    logger.info(
        f"Workflow {state['workflow_id']} completed. "
        f"Agents completed: {state['completed_agents']}, "
        f"Failed: {state['failed_agents']}"
    )
    return state


# ─── Edge Routing ────────────────────────────────────────────────────────────

def route_after_start(state: WorkflowState) -> str:
    """Determine which agent to run first based on the plan."""
    plan_steps = state["plan"].get("steps", [])
    active_steps = [s for s in plan_steps if not s.get("skip", False)]

    if not active_steps:
        return "end_node"

    # Set current agent to the first active step
    state["current_agent"] = active_steps[0]["agent_name"]
    return "agent_node"


def route_after_agent(state: WorkflowState) -> str:
    """Determine next step after an agent completes."""
    plan_steps = state["plan"].get("steps", [])
    active_steps = [s for s in plan_steps if not s.get("skip", False)]
    completed = state["completed_agents"]

    # Find the next unfinished agent
    for step in active_steps:
        if step["agent_name"] not in completed:
            state["current_agent"] = step["agent_name"]
            return "agent_node"

    # All agents done — move to approval wait
    return "approval_wait_node"


def route_after_approval(state: WorkflowState) -> str:
    """After approval, write to memory."""
    return "memory_node"


def route_after_memory(state: WorkflowState) -> str:
    """After memory write, end the workflow."""
    return "end_node"


# ─── Graph Builder ───────────────────────────────────────────────────────────

def build_workflow_graph():
    """
    Builds and compiles the LangGraph StateGraph for workflow execution.

    Topology:
        start_node → agent_node (repeated per plan step) → approval_wait_node → memory_node → end_node

    Returns:
        CompiledGraph ready for invocation.
    """
    graph = StateGraph(WorkflowState)

    # Add nodes
    graph.add_node("start_node", start_node)
    graph.add_node("agent_node", agent_node)
    graph.add_node("approval_wait_node", approval_wait_node)
    graph.add_node("memory_node", memory_node)
    graph.add_node("end_node", end_node)

    # Set entry point
    graph.set_entry_point("start_node")

    # Add conditional edges
    graph.add_conditional_edges("start_node", route_after_start, {
        "agent_node": "agent_node",
        "end_node": "end_node",
    })

    graph.add_conditional_edges("agent_node", route_after_agent, {
        "agent_node": "agent_node",
        "approval_wait_node": "approval_wait_node",
    })

    graph.add_conditional_edges("approval_wait_node", route_after_approval, {
        "memory_node": "memory_node",
    })

    graph.add_conditional_edges("memory_node", route_after_memory, {
        "end_node": "end_node",
    })

    # End node terminates the graph
    graph.add_edge("end_node", END)

    # Compile
    compiled = graph.compile()
    logger.info("Workflow graph compiled successfully")
    return compiled
