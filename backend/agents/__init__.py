"""
Agents package — imports all agents to trigger @register_agent decorators.
"""

from backend.agents.base import BaseAgent, AGENT_REGISTRY, get_agent_class, register_agent
from backend.agents.search_strategy_agent import SearchStrategyAgent
from backend.agents.company_discovery import CompanyDiscoveryAgent
from backend.agents.validation_agent import CompanyValidationAgent
from backend.agents.tech_analysis_agent import TechAnalysisAgent
from backend.agents.market_intelligence_agent import MarketIntelligenceAgent
from backend.agents.decision_maker import DecisionMakerAgent
from backend.agents.contact_enrichment import ContactEnrichmentAgent
from backend.agents.qualification import QualificationAgent
from backend.agents.recommendation_memory import RecommendationMemoryAgent

__all__ = [
    "BaseAgent",
    "AGENT_REGISTRY",
    "get_agent_class",
    "register_agent",
    "SearchStrategyAgent",
    "CompanyDiscoveryAgent",
    "CompanyValidationAgent",
    "TechAnalysisAgent",
    "MarketIntelligenceAgent",
    "DecisionMakerAgent",
    "ContactEnrichmentAgent",
    "QualificationAgent",
    "RecommendationMemoryAgent",
]
