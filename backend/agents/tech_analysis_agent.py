"""
TechAnalysisAgent — detects company technology stacks from 3 sources.

Source 1: BuiltWith API (verified, categorized tech)
Source 2: SerpAPI web scrape (tech mentions in snippets)
Source 3: Job posting analysis (LLM-extracted tech from job descriptions)

Stores results in company.tech_stack_detected JSON and scores campaign
tech-filter match rates.
"""

import json
import re
import httpx

from backend.agents.base import BaseAgent, register_agent
from backend.models.company import Company
from backend.config.settings import get_settings
from backend.services.llm_service import call_llm

settings = get_settings()

# Cloud provider keywords for detection
CLOUD_KEYWORDS = {
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda", "cloudfront"],
    "Azure": ["azure", "microsoft azure", "azure devops", "azure functions"],
    "GCP": ["gcp", "google cloud", "google cloud platform", "gke", "cloud run"],
}

# Common technology keywords detected from snippets and job posts
TECH_KEYWORDS = [
    "Python", "React", "Angular", "Vue.js", "Node.js", "TypeScript", "Go", "Rust",
    "Java", "Kotlin", "Swift", "Ruby", "PHP", "C#", ".NET", "Django", "Flask",
    "FastAPI", "Express", "Next.js", "Nuxt.js", "Tailwind", "Bootstrap",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
    "DynamoDB", "Firebase", "Supabase", "Snowflake", "BigQuery", "Redshift",
    "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitHub Actions",
    "GitLab CI", "CircleCI", "ArgoCD", "Helm",
    "OpenAI", "Anthropic", "LangChain", "PyTorch", "TensorFlow", "Hugging Face",
    "Kafka", "RabbitMQ", "NATS", "SQS",
    "GraphQL", "REST", "gRPC", "WebSocket",
    "Salesforce", "HubSpot", "Marketo", "Segment", "Stripe", "Plaid",
    "Datadog", "New Relic", "Sentry", "Grafana", "Prometheus",
    "Databricks", "Airflow", "dbt", "Fivetran",
]

SYSTEM_MSG_EXTRACT_TECH = (
    "Extract ONLY technology names from these job posting snippets. "
    "Return JSON: {\"technologies\": [...]} — no explanation."
)


@register_agent("tech_analysis")
class TechAnalysisAgent(BaseAgent):
    """Detects company technology stacks using BuiltWith, SerpAPI, and job posting analysis."""

    async def run(self, input: dict, memory, config: dict) -> dict:
        workflow_id = input.get("workflow_id")
        company_ids = input.get("company_ids", [])
        campaign_config = input.get("icp", config)

        # Tech filters from campaign config (support both nested and flat)
        tech_filters = campaign_config.get("technology_filters", campaign_config)

        required_tech = tech_filters.get("required_tech", [])
        nice_to_have_tech = tech_filters.get("nice_to_have_tech", [])
        exclude_tech = tech_filters.get("exclude_tech", [])
        target_cloud = tech_filters.get("cloud_providers", [])

        log_id = await self.log_start(workflow_id, "tech_analysis", {
            "company_count": len(company_ids),
        })

        await self.emit(workflow_id, "tech_analysis", "running", {
            "message": f"Analyzing tech stacks for {len(company_ids)} companies across 3 sources...",
        })

        total_required_match = 0.0
        companies_with_excluded = 0
        analyzed_count = 0

        for company in self.db.query(Company).filter(Company.id.in_(company_ids)).all():
            await self.emit(workflow_id, "tech_analysis", "sub_step", {
                "company": company.name,
                "message": f"Scanning {company.name} ({company.domain})...",
            })

            # ─── Source 1: BuiltWith API ──────────────────────────────────
            builtwith_tech = await self._source_builtwith(company.domain)

            # ─── Source 2: SerpAPI tech snippet scan ──────────────────────
            serpapi_tech = await self._source_serpapi(company.domain)

            # ─── Source 3: Job posting LLM analysis ───────────────────────
            job_tech = await self._source_jobs(company.name, company.domain)

            # ─── Combine sources ──────────────────────────────────────────
            combined = self._combine_sources(
                builtwith_tech, serpapi_tech, job_tech,
            )

            # ─── Match against campaign tech filters ──────────────────────
            required_match = self._calc_match_percentage(
                required_tech, combined["confirmed"] + combined["probable"],
            )
            nice_to_have_match = self._calc_match_percentage(
                nice_to_have_tech, combined["confirmed"] + combined["probable"],
            )

            excluded_found = any(
                t in combined["confirmed"] + combined["probable"]
                for t in exclude_tech
            )

            if excluded_found:
                companies_with_excluded += 1

            # ─── Store on company row ─────────────────────────────────────
            company.tech_stack_detected = {
                "confirmed": combined["confirmed"],
                "probable": combined["probable"],
                "cloud": combined["cloud"],
                "inferred_stack_score": combined["stack_score"],
            }

            self.db.commit()

            total_required_match += required_match
            analyzed_count += 1

            await self.emit(workflow_id, "tech_analysis", "sub_step", {
                "company": company.name,
                "result": "complete",
                "confirmed_count": len(combined["confirmed"]),
                "probable_count": len(combined["probable"]),
                "required_match": required_match,
                "nice_to_have_match": nice_to_have_match,
            })

        avg_required_match = total_required_match / max(analyzed_count, 1)

        result = {
            "tech_analyzed": analyzed_count,
            "avg_required_match": round(avg_required_match, 2),
            "companies_with_excluded_tech": companies_with_excluded,
        }

        await self.emit(workflow_id, "tech_analysis", "completed", {
            "message": (
                f"✓ {analyzed_count} companies analyzed, "
                f"avg required tech match: {avg_required_match:.0f}%, "
                f"{companies_with_excluded} with excluded tech"
            ),
            "tech_analyzed": analyzed_count,
            "avg_required_match": round(avg_required_match, 2),
            "companies_with_excluded_tech": companies_with_excluded,
        })

        await self.log_complete(log_id, result)
        return result

    # ─── Source 1: BuiltWith ──────────────────────────────────────────────

    async def _source_builtwith(self, domain: str) -> list[dict]:
        """
        Query BuiltWith API for verified technology detection.
        Returns list of {name, category} dicts.
        """
        builtwith_key = (
            settings.BUILTWITH_API_KEY
            if hasattr(settings, "BUILTWITH_API_KEY")
            else None
        )
        if not builtwith_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.builtwith.com/v21/api.json",
                    params={"KEY": builtwith_key, "LOOKUP": domain},
                )
                if resp.status_code != 200:
                    return []

                data = resp.json()
                results = data.get("Results", [])
                if not results:
                    return []

                tech_list = []
                for group in results[0].get("Result", {}).get("Paths", []):
                    category = group.get("SubDomain", "unknown")
                    for tech in group.get("Technologies", []):
                        tech_list.append({
                            "name": tech.get("Name", ""),
                            "category": category,
                            "tag": tech.get("Tag", ""),
                        })
                return tech_list

        except Exception:
            return []

    # ─── Source 2: SerpAPI tech snippet scan ─────────────────────────────

    async def _source_serpapi(self, domain: str) -> list[str]:
        """
        Search for technology mentions in web snippets about the company.
        """
        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": settings.SERPAPI_KEY,
                        "engine": "google",
                        "q": f'"{domain}" technology stack AWS OR Azure OR "React" OR "Python" OR "Kubernetes"',
                        "num": 5,
                    },
                )
                if resp.status_code != 200:
                    return []

                results = resp.json().get("organic_results", [])
                all_text = " ".join(
                    r.get("snippet", "") + " " + r.get("title", "")
                    for r in results
                ).lower()

                return self._match_tech_keywords(all_text)

        except Exception:
            return []

    # ─── Source 3: Job posting LLM analysis ──────────────────────────────

    async def _source_jobs(self, company_name: str, domain: str) -> list[str]:
        """
        Search for job postings and use LLM to extract technology names.
        This is the most reliable signal for current tech stack.
        """
        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": settings.SERPAPI_KEY,
                        "engine": "google",
                        "q": f'"{company_name}" jobs "senior engineer" site:linkedin.com OR site:indeed.com',
                        "num": 5,
                    },
                )
                if resp.status_code != 200:
                    return []

                results = resp.json().get("organic_results", [])
                if not results:
                    # Fallback: keyword match on any snippet
                    all_text = " ".join(
                        r.get("snippet", "") + " " + r.get("title", "")
                        for r in results
                    ).lower()
                    return self._match_tech_keywords(all_text)

                # Build snippets for LLM analysis
                snippets = []
                for r in results[:5]:
                    snip = r.get("snippet", "") or r.get("title", "")
                    if snip:
                        snippets.append(snip)

                if not snippets:
                    return []

                combined_snippets = "\n".join(snippets)
                llm_response = await call_llm(
                    SYSTEM_MSG_EXTRACT_TECH,
                    f"Job postings for {company_name}:\n{combined_snippets}",
                    expect_json=True,
                )

                try:
                    parsed = json.loads(llm_response)
                    raw = parsed.get("technologies", [])
                    return [t.strip() for t in raw if isinstance(t, str) and t.strip()]
                except (json.JSONDecodeError, TypeError):
                    # Fallback: keyword match
                    return self._match_tech_keywords(combined_snippets.lower())

        except Exception:
            return []

    # ─── Combine ─────────────────────────────────────────────────────────

    def _combine_sources(
        self,
        builtwith: list[dict],
        serpapi: list[str],
        jobs: list[str],
    ) -> dict:
        """
        Merge tech from all 3 sources with confidence levels.

        - confirmed: appeared in BuiltWith AND job postings (strongest signal)
        - probable: appeared in only one source
        - cloud: cloud provider determination
        - stack_score: overall confidence 0-1
        """
        builtwith_names = {t["name"].lower() for t in builtwith} | {
            t["tag"].lower() for t in builtwith if t.get("tag")
        }
        serpapi_names = {t.lower() for t in serpapi}
        jobs_names = {t.lower() for t in jobs}

        source_count = {}

        # Count appearances across sources
        all_techs = builtwith_names | serpapi_names | jobs_names
        for t in all_techs:
            count = 0
            if t in builtwith_names:
                count += 1
            if t in serpapi_names:
                count += 1
            if t in jobs_names:
                count += 1
            source_count[t] = count

        confirmed = sorted(
            t for t, c in source_count.items()
            if c >= 2
        )
        probable = sorted(
            t for t, c in source_count.items()
            if c == 1 and t not in confirmed
        )

        # Determine cloud providers
        cloud = self._detect_cloud(all_techs)

        # Stack score: confidence based on number of sources contributing
        if len(confirmed) + len(probable) == 0:
            stack_score = 0.0
        elif len(confirmed) >= 3 and len(builtwith_names) > 0:
            stack_score = 0.95  # BuiltWith verified + cross-referenced
        elif len(confirmed) >= 1:
            stack_score = 0.75  # Multi-source but no BuiltWith
        else:
            stack_score = 0.4  # Single source only

        return {
            "confirmed": confirmed,
            "probable": probable,
            "cloud": cloud,
            "stack_score": stack_score,
        }

    # ─── Helpers ─────────────────────────────────────────────────────────

    def _match_tech_keywords(self, text: str) -> list[str]:
        """Match known tech keywords in a block of text."""
        found = set()
        text_lower = text.lower()
        for tech in TECH_KEYWORDS:
            if tech.lower() in text_lower:
                found.add(tech)
        return sorted(found)

    def _detect_cloud(self, techs: set[str]) -> list[str]:
        """Detect cloud providers from detected technologies."""
        detected = []
        for provider, keywords in CLOUD_KEYWORDS.items():
            for kw in keywords:
                if kw in techs or any(kw in t for t in techs):
                    detected.append(provider)
                    break

        if len(detected) > 1:
            return ["Multi-cloud"] + detected
        return detected

    def _calc_match_percentage(self, campaign_techs: list[str], detected_techs: list[str]) -> float:
        """What percentage of campaign tech requirements are met."""
        if not campaign_techs:
            return 1.0  # No requirements = 100% match

        detected_lower = {t.lower() for t in detected_techs}
        matches = sum(1 for t in campaign_techs if t.lower() in detected_lower)
        return round(matches / len(campaign_techs), 2)
