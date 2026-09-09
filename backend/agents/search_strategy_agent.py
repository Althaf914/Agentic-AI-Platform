"""
SearchStrategyAgent — generates intelligent SerpAPI search queries from a campaign config.

Stage 0 agent: runs BEFORE any discovery agents to produce a targeted set of
search queries that cover multiple angles (industry, location, tech, job, funding).

Output is stored in accumulated_results["search_queries"] so that
CompanyDiscoveryAgent can iterate over queries in parallel.
"""

import json
from pathlib import Path

from backend.agents.base import BaseAgent, register_agent
from backend.services.llm_service import call_llm

# Load system prompt once at module level
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "search_strategy.txt"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

# Example queries baked into the agent for zero-shot / fallback scenarios
EXAMPLE_QUERIES = [
    {
        "query": '"AI startup" "Series B" San Francisco 2024',
        "intent": "Find Series B AI startups in San Francisco",
        "expected_result_type": "company_list",
    },
    {
        "query": 'site:linkedin.com/company "artificial intelligence" "50-200 employees" "San Francisco"',
        "intent": "Find AI companies on LinkedIn with 50-200 employees in SF",
        "expected_result_type": "linkedin",
    },
    {
        "query": 'site:wellfound.com AI SaaS startup hiring "machine learning engineer"',
        "intent": "Find AI SaaS startups hiring ML engineers on Wellfound",
        "expected_result_type": "company_list",
    },
    {
        "query": '"AI platform" company AWS Kubernetes San Francisco funding 2024',
        "intent": "Find AI platform companies using AWS/K8s with recent funding",
        "expected_result_type": "company_list",
    },
    {
        "query": 'site:crunchbase.com/organization AI "Series B" "San Francisco" 2023 2024',
        "intent": "Find Series B AI companies on CrunchBase",
        "expected_result_type": "crunchbase",
    },
    {
        "query": '"AI" "SaaS" "Python" hiring engineer Austin Seattle 2024',
        "intent": "Find AI SaaS companies hiring Python engineers in Austin/Seattle",
        "expected_result_type": "job_posting",
    },
    {
        "query": '"artificial intelligence" startup "raised" million series 2024 site:techcrunch.com',
        "intent": "Find AI startup funding announcements on TechCrunch",
        "expected_result_type": "news",
    },
    {
        "query": 'AI SaaS B2B company "uses AWS" "500 employees" OR "200 employees"',
        "intent": "Find B2B AI SaaS companies using AWS with specific employee counts",
        "expected_result_type": "company_list",
    },
]


@register_agent("search_strategy")
class SearchStrategyAgent(BaseAgent):
    """Generates 8-12 targeted SerpAPI search queries from a campaign config."""

    async def run(self, input: dict, memory, config: dict) -> dict:
        workflow_id = input.get("workflow_id")
        icp = input.get("icp", config)  # fallback to full config

        agent_name = "search_strategy"

        log_id = await self.log_start(workflow_id, agent_name, {
            "industries": icp.get("industries", icp.get("company_filters", {}).get("industries", [])),
            "countries": icp.get("countries", icp.get("geography", {}).get("countries", [])),
        })

        await self.emit(workflow_id, agent_name, "running", {
            "message": "Analyzing campaign configuration to build targeted search queries..."
        })

        # ── Step 1: Build context dict from campaign config ──────────────────
        context = self._build_context(icp)

        # ── Step 2: Build user message ───────────────────────────────────────
        user_message = json.dumps(context, indent=2, default=str)

        # ── Step 3: Call LLM ─────────────────────────────────────────────────
        raw_response = await call_llm(SYSTEM_PROMPT, user_message, expect_json=True)

        # ── Step 4: Parse response ───────────────────────────────────────────
        queries, strategy_summary = self._parse_response(raw_response)

        # ── Step 5: Validate query count (6-15) ──────────────────────────────
        if len(queries) < 6:
            # Pad with fallback examples if LLM returned too few
            needed = 8 - len(queries)
            fallback_queries = self._get_fallback_queries(context, needed)
            queries.extend(fallback_queries)

        if len(queries) > 15:
            queries = queries[:15]

        # ── Step 6: Store in memory ─────────────────────────────────────────
        if memory:
            try:
                await memory.write(
                    entity_type="workflow",
                    entity_id=workflow_id,
                    summary=f"Search strategy generated {len(queries)} queries: {strategy_summary}",
                    metadata={
                        "agent": agent_name,
                        "query_count": len(queries),
                        "strategy_summary": strategy_summary,
                        "queries": [q["query"] for q in queries],
                    },
                )
            except Exception as e:
                print(f"[SearchStrategyAgent] Memory write error: {e}")

        # ── Step 7: Return ──────────────────────────────────────────────────
        result = {
            "search_queries": queries,
            "strategy_summary": strategy_summary,
            "query_count": len(queries),
        }

        await self.emit(workflow_id, agent_name, "completed", {
            "message": f"✓ {len(queries)} search queries generated — {strategy_summary}",
            "query_count": len(queries),
        })

        await self.log_complete(log_id, result)
        return result

    # ── Private helpers ──────────────────────────────────────────────────────

    def _build_context(self, icp: dict) -> dict:
        """Build a structured context dict from whatever shape the config arrives in.

        Supports both the legacy flat ICP format and the new nested Campaign
        config_json format.
        """
        # Support both legacy flat ICP and new nested Campaign format
        business = icp.get("business", {})
        geography = icp.get("geography", {})
        company_filters = icp.get("company_filters", {})
        technology_filters = icp.get("technology_filters", {})
        hiring_signals = icp.get("hiring_signals", {})

        return {
            "product_category": business.get(
                "product_category",
                icp.get("product_category", "unknown"),
            ),
            "value_proposition": business.get(
                "value_proposition",
                icp.get("value_proposition", ""),
            ),
            "industries": company_filters.get(
                "industries",
                icp.get("industries", []),
            ),
            "countries": geography.get(
                "countries",
                icp.get("countries", []),
            ),
            "cities": geography.get(
                "cities",
                icp.get("cities", icp.get("locations", [])),
            ),
            "funding_stages": company_filters.get(
                "funding_stages",
                icp.get("funding_stages", []),
            ),
            "tech_stack_required": technology_filters.get(
                "required_tech",
                icp.get("tech_stack", []),
            ),
            "tech_stack_nice_to_have": technology_filters.get(
                "nice_to_have_tech",
                [],
            ),
            "hiring_keywords": hiring_signals.get(
                "keywords",
                icp.get("hiring_keywords", []),
            ),
            "employee_range": {
                "min": company_filters.get(
                    "min_employees",
                    icp.get("min_employees", 1),
                ),
                "max": company_filters.get(
                    "max_employees",
                    icp.get("max_employees", 10000),
                ),
            },
            "min_revenue": company_filters.get(
                "min_revenue",
                icp.get("min_revenue", ""),
            ),
            "max_revenue": company_filters.get(
                "max_revenue",
                icp.get("max_revenue", ""),
            ),
            "company_age_min_years": company_filters.get(
                "company_age_min_years",
                icp.get("company_age_min_years", 0),
            ),
        }

    def _parse_response(self, raw_response: str) -> tuple[list[dict], str]:
        """Parse LLM JSON response into queries list and strategy summary."""
        cleaned = raw_response.strip()

        # Strip markdown code fences if present
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: try to find JSON array in the response
            data = self._extract_json_fallback(cleaned)

        queries = data.get("queries", []) if isinstance(data, dict) else data
        strategy_summary = (
            data.get("strategy_summary", "")
            if isinstance(data, dict)
            else "Multi-angle search strategy targeting ICP companies"
        )

        # Ensure each query has the required fields
        validated = []
        for q in queries:
            if isinstance(q, str):
                validated.append({
                    "query": q,
                    "intent": "Targeted company discovery based on ICP criteria",
                    "expected_result_type": "company_list",
                })
            elif isinstance(q, dict) and q.get("query"):
                validated.append({
                    "query": q["query"],
                    "intent": q.get("intent", "Targeted company discovery"),
                    "expected_result_type": q.get(
                        "expected_result_type", "company_list"
                    ),
                })

        return validated, strategy_summary

    def _extract_json_fallback(self, text: str) -> dict:
        """Attempt to extract JSON from free-form LLM output."""
        import re

        # Try to find a JSON object
        obj_match = re.search(r"\{[^{}]*\"queries\"[^{}]*\}", text, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group())
            except json.JSONDecodeError:
                pass

        # Try to find a JSON array
        arr_match = re.search(r"\[.*\]", text, re.DOTALL)
        if arr_match:
            try:
                items = json.loads(arr_match.group())
                return {"queries": items, "strategy_summary": "Extracted from LLM output"}
            except json.JSONDecodeError:
                pass

        return {"queries": [], "strategy_summary": "Fallback: no valid queries parsed"}

    def _get_fallback_queries(self, context: dict, count: int) -> list[dict]:
        """Generate fallback queries based on context when LLM fails or returns too few."""
        industries = context.get("industries", ["B2B", "SaaS"])
        countries = context.get("countries", ["US"])
        cities = context.get("cities", [])
        funding = context.get("funding_stages", [])
        tech = context.get("tech_stack_required", [])

        industry_str = " ".join(industries[:2])
        location = " ".join(cities[:1]) if cities else " ".join(countries[:1])
        funding_str = " ".join(funding[:1]) if funding else "funded"
        tech_str = " ".join(tech[:2]) if tech else "technology"

        fallback_pool = [
            {
                "query": f'"{industry_str}" startup "{funding_str}" {location} 2024',
                "intent": f"Find {industry_str} companies with {funding_str} funding in {location}",
                "expected_result_type": "company_list",
            },
            {
                "query": f'site:linkedin.com/company "{industry_str}" {location}',
                "intent": f"Find {industry_str} companies on LinkedIn in {location}",
                "expected_result_type": "linkedin",
            },
            {
                "query": f'site:crunchbase.com/organization {industry_str} "{funding_str}" {location}',
                "intent": f"Find {industry_str} companies on CrunchBase",
                "expected_result_type": "crunchbase",
            },
            {
                "query": f'"{industry_str}" company {tech_str} hiring {location} 2024',
                "intent": f"Find {industry_str} companies using {tech_str} that are hiring in {location}",
                "expected_result_type": "job_posting",
            },
            {
                "query": f'"{industry_str}" "{funding_str}" raised million site:techcrunch.com',
                "intent": f"Find {industry_str} company funding announcements",
                "expected_result_type": "news",
            },
            {
                "query": f'{industry_str} B2B company "uses {tech_str}" {location}',
                "intent": f"Find B2B {industry_str} companies using {tech_str} in {location}",
                "expected_result_type": "company_list",
            },
            {
                "query": f'site:wellfound.com {industry_str} startup hiring',
                "intent": f"Find {industry_str} startups hiring on Wellfound",
                "expected_result_type": "company_list",
            },
            {
                "query": f'"{industry_str}" AI platform {tech_str} {location} funding',
                "intent": f"Find {industry_str} AI platform companies with {tech_str} stack",
                "expected_result_type": "company_list",
            },
        ]

        return fallback_pool[:count]
