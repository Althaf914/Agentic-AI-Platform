"""
Decision Maker Agent — uses LLM to dynamically determine the best personas
to search for at each company based on the campaign's buying committee config,
company industry, and company size.

Flow per company:
  1. LLM determines 2-3 search personas from campaign buying_committee + company profile
  2. LinkedIn SerpAPI search per persona (2 queries each)
  3. Fallback generated name if no LinkedIn results
  4. Contact stored with source tracking + confidence
"""
import uuid
import random
import json

from backend.agents.base import BaseAgent, register_agent
from backend.models.company import Company
from backend.models.contact import Contact
from backend.services.llm_service import call_llm
from backend.tools.web_search import search_raw
from backend.config.settings import get_settings

settings = get_settings()

FIRST_NAMES = [
    "Sarah", "Michael", "Priya", "James", "Aisha", "David",
    "Emma", "Carlos", "Lisa", "Raj", "Jennifer", "Omar",
    "Wei", "Alexandra", "Marcus", "Fatima", "Ryan", "Ananya",
]
LAST_NAMES = [
    "Chen", "Johnson", "Patel", "Williams", "Kim", "Rodriguez",
    "Thompson", "Singh", "Martinez", "Lee", "Anderson", "Hassan",
    "Park", "Mueller", "Sharma", "Cohen", "Taylor", "Nakamura",
]

# Diverse fallback name pools for culture-aware generation
CULTURE_PREFIXES = {
    "tech": ["Alex", "Jordan", "Morgan", "Casey", "Riley", "Taylor", "Avery"],
    "enterprise": ["James", "Robert", "Michael", "David", "Jennifer", "Catherine"],
    "startup": ["Eli", "Noa", "Maya", "Kai", "Luna", "Zion", "Nova"],
}


@register_agent("decision_maker")
class DecisionMakerAgent(BaseAgent):
    """
    Finds decision makers using dynamic LLM-driven persona detection per company.

    Reads buying_committee from campaign config, lets the LLM determine the
    2-3 most relevant titles to search for at each specific company based on
    its industry and employee count, then searches LinkedIn via SerpAPI.
    Falls back to generated names with low confidence.
    """

    async def run(self, input: dict, memory, config: dict) -> dict:
        workflow_id = input.get("workflow_id")
        company_ids = input.get("company_ids", [])
        # config is the full campaign config_json — may contain buying_committee
        campaign_config = input.get("config", config) or {}

        # Extract buying committee from campaign config
        buying_committee = self._get_buying_committee(campaign_config)

        log_id = await self.log_start(workflow_id, "decision_maker", {
            "company_count": len(company_ids),
            "buying_committee_configured": bool(buying_committee.get("primary_persona")),
        })

        await self.emit(workflow_id, "decision_maker", "running", {
            "message": f"🎯 Finding decision makers at {len(company_ids)} companies..."
        })

        all_contact_ids = []
        linkedin_confirmed = 0
        generated_fallback = 0
        total_persona_slots = 0
        filled_persona_slots = 0

        for company_id in company_ids:
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                continue

            # STEP 1: LLM determines 2-3 search personas for THIS company
            personas = await self._determine_personas(company, buying_committee)
            if not personas:
                personas = self._fallback_personas(buying_committee)

            total_persona_slots += len(personas)

            for idx, persona in enumerate(personas):
                persona_title = persona.get("title", "").strip()
                search_query = persona.get("search_query", persona_title)
                if not persona_title:
                    continue

                # Derive department from buying committee config if possible
                department = self._match_department(persona_title, buying_committee)

                # STEP 2: LinkedIn search per persona
                contact_data = None
                if settings.SERPAPI_KEY:
                    contact_data = await self._search_linkedin(company.name, search_query)

                if contact_data:
                    source = "linkedin_serpapi"
                    confidence = 0.85 if contact_data.get("direct_match") else 0.65
                    linkedin_confirmed += 1
                    filled_persona_slots += 1
                else:
                    # STEP 3: Fallback generated name
                    contact_data = self._generate_fallback(persona_title)
                    source = "generated"
                    confidence = 0.4
                    generated_fallback += 1

                contact = Contact(
                    id=str(uuid.uuid4()),
                    company_id=company_id,
                    full_name=contact_data["name"],
                    role=persona_title,
                    department=department,
                    linkedin_url=contact_data.get("linkedin_url"),
                    confidence_score=confidence,
                    source=source,
                    is_primary_persona=(idx == 0),
                )
                self.db.add(contact)
                all_contact_ids.append(contact.id)

        self.db.commit()

        coverage = (filled_persona_slots / total_persona_slots * 100) if total_persona_slots > 0 else 0.0

        result = {
            "contact_ids": all_contact_ids,
            "contacts_found": len(all_contact_ids),
            "linkedin_confirmed": linkedin_confirmed,
            "generated_fallback": generated_fallback,
            "buying_committee_coverage": round(coverage, 1),
        }

        await self.emit(workflow_id, "decision_maker", "completed", {
            "message": (
                f"✓ Found {len(all_contact_ids)} decision makers "
                f"({linkedin_confirmed} LinkedIn, {generated_fallback} generated)"
            ),
            **result,
        })

        await self.log_complete(log_id, result)
        return result

    # ------------------------------------------------------------------
    # STEP 1: Dynamic persona detection via LLM
    # ------------------------------------------------------------------

    async def _determine_personas(self, company: Company, buying_committee: dict) -> list[dict]:
        """
        LLM call that takes the campaign's buying committee config + company profile
        (industry, employee count) and returns 2-3 most relevant personas to search for.
        """
        company_industry = getattr(company, "industry", "Unknown")
        company_employees = getattr(company, "employee_count", None)
        company_size_label = self._size_label(company_employees)

        primary = buying_committee.get("primary_persona", {})
        secondary = buying_committee.get("secondary_personas", [])
        influencers = buying_committee.get("influencers", [])

        committee_summary = {
            "primary_persona": primary,
            "secondary_personas": secondary[:3],
            "influencers": influencers[:3],
        }

        system_prompt = (
            "You are a B2B sales researcher. Given a company profile and a campaign's "
            "target buying committee, list the 2-3 most likely decision-maker titles "
            "to search for at THIS specific company. Consider company size and industry "
            "carefully — a startup has different decision-makers than an enterprise.\n\n"
            "Examples:\n"
            "- AI Platform + 50-person startup → CTO, Head of Engineering (not VP — too small)\n"
            "- AI Platform + 500-person company → VP Engineering, Head of AI, CTO\n"
            "- HR Software + 200 people → HR Director, Head of People, VP Talent\n"
            "- Security Tool + 1000 people → CISO, VP Security, Director InfoSec\n\n"
            "Output ONLY valid JSON with format:\n"
            '{"personas": [{"title": "CTO", "search_query": "CTO"}, ...]}\n'
            "No markdown fences, no extra text."
        )

        user_message = json.dumps({
            "company": {
                "name": company.name,
                "industry": company_industry,
                "employee_count": company_employees,
                "size_label": company_size_label,
            },
            "campaign_buying_committee": committee_summary,
        })

        raw = await call_llm(system_prompt, user_message, expect_json=True)
        parsed = self._parse_persona_response(raw)
        return parsed

    def _parse_persona_response(self, raw: str) -> list[dict]:
        """Parse LLM response into persona list."""
        try:
            # Strip markdown fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                parts = cleaned.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:]
                    if part.startswith("{"):
                        cleaned = part
                        break
                else:
                    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

            data = json.loads(cleaned)
            personas = data.get("personas", [])
            if isinstance(personas, list) and len(personas) >= 1:
                return personas[:3]
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            print(f"[DecisionMaker] Failed to parse LLM persona response: {e}")

        return []

    def _fallback_personas(self, buying_committee: dict) -> list[dict]:
        """Fallback personas from buying committee config when LLM unavailable."""
        personas = []
        primary = buying_committee.get("primary_persona", {})
        if primary.get("title"):
            personas.append({"title": primary["title"], "search_query": primary["title"]})

        for sec in buying_committee.get("secondary_personas", [])[:2]:
            if sec.get("title"):
                personas.append({"title": sec["title"], "search_query": sec["title"]})

        if not personas:
            personas = [{"title": "CTO", "search_query": "CTO"}]

        return personas

    def _match_department(self, title: str, buying_committee: dict) -> str | None:
        """Find department for a persona title from the buying committee config."""
        primary = buying_committee.get("primary_persona", {})
        if primary.get("title", "").lower() == title.lower():
            return primary.get("department")

        for sec in buying_committee.get("secondary_personas", []):
            if sec.get("title", "").lower() == title.lower():
                return sec.get("department")

        # Guess department from title keywords
        title_lower = title.lower()
        dept_map = {
            "cto": "Engineering",
            "engineering": "Engineering",
            "product": "Product",
            "security": "Security",
            "ciso": "Security",
            "hr": "HR",
            "talent": "HR",
            "people": "HR",
            "marketing": "Marketing",
            "sales": "Sales",
            "finance": "Finance",
            "ceo": "Executive",
            "coo": "Operations",
            "data": "Data",
            "it": "IT",
            "compliance": "Compliance",
        }
        for keyword, dept in dept_map.items():
            if keyword in title_lower:
                return dept

        return None

    # ------------------------------------------------------------------
    # STEP 2: LinkedIn search via SerpAPI
    # ------------------------------------------------------------------

    async def _search_linkedin(self, company_name: str, role: str) -> dict | None:
        """
        Try 2 SerpAPI queries to find a LinkedIn profile for the given persona at the company.
        Returns contact dict with name, linkedin_url, and direct_match flag, or None.
        """
        queries = [
            f'site:linkedin.com/in "{company_name}" "{role}"',
            f'"{role}" at "{company_name}" LinkedIn',
        ]

        for query in queries:
            results = await search_raw(query, num=5)
            for r in results:
                title = r.get("title", "")
                link = r.get("link", "")

                if "linkedin.com/in/" not in link:
                    continue

                # LinkedIn title format: "John Smith - CTO at Stripe | LinkedIn"
                name_part = None
                if " - " in title:
                    name_part = title.split(" - ")[0].strip()
                elif " | " in title:
                    name_part = title.split(" | ")[0].strip()

                if name_part and len(name_part.split()) >= 2 and len(name_part) < 40:
                    # Check if this is a direct profile link vs a search result page
                    path = link.split("linkedin.com/in/")[1].rstrip("/")
                    is_direct = "/" not in path and "?" not in path

                    return {
                        "name": name_part,
                        "linkedin_url": link.split("?")[0],  # clean URL params
                        "direct_match": is_direct,
                    }

        return None

    # ------------------------------------------------------------------
    # STEP 3: Fallback name generation
    # ------------------------------------------------------------------

    def _generate_fallback(self, role: str) -> dict:
        """Generate a realistic name based on role and company culture."""
        role_lower = role.lower()

        # Pick name pool based on role seniority
        if any(t in role_lower for t in ["ceo", "cto", "cfo", "ciso", "chief", "vp", "director"]):
            pool = CULTURE_PREFIXES["enterprise"]
        elif any(t in role_lower for t in ["engineer", "developer", "architect", "head of"]):
            pool = CULTURE_PREFIXES["tech"]
        else:
            pool = CULTURE_PREFIXES["startup"]

        first = random.choice(pool)
        last = random.choice(LAST_NAMES)
        return {
            "name": f"{first} {last}",
            "linkedin_url": None,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_buying_committee(self, config: dict) -> dict:
        """
        Extract buying committee from campaign config.
        Handles both nested campaign format and legacy flat format.
        """
        # Try nested campaign format
        buying_committee = config.get("buying_committee")
        if buying_committee:
            return buying_committee

        # Try legacy persona format
        personas = config.get("personas", [])
        if personas:
            # Convert legacy personas array → buying committee object
            primary = personas[0] if personas else {}
            secondary = personas[1:] if len(personas) > 1 else []
            return {
                "primary_persona": {
                    "title": (primary.get("role_keywords") or ["Executive"])[0],
                    "seniority": "C-Suite",
                    "department": (primary.get("departments") or [""])[0],
                },
                "secondary_personas": [
                    {
                        "title": (p.get("role_keywords") or ["Manager"])[0],
                        "seniority": "VP",
                        "department": (p.get("departments") or [""])[0],
                    }
                    for p in secondary
                ],
                "influencers": [],
            }

        return {}

    @staticmethod
    def _size_label(employee_count: int | None) -> str:
        """Classify company size into a label the LLM can reason about."""
        if employee_count is None:
            return "unknown size"
        if employee_count < 20:
            return "startup (<20 employees)"
        if employee_count < 100:
            return "small (20-100 employees)"
        if employee_count < 500:
            return "mid-size (100-500 employees)"
        if employee_count < 2000:
            return "large (500-2000 employees)"
        return "enterprise (2000+ employees)"
