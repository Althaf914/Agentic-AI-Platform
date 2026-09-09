"""
MarketIntelligenceAgent — fetches business trigger signals for validated companies.

Signal types (all 5 run in parallel per company):
  1. Recent funding  (SerpAPI + LLM parse)
  2. News / press    (SerpAPI + LLM classify)
  3. Hiring surge    (SerpAPI + existing score)
  4. Geographic expansion (SerpAPI)
  5. Leadership changes (SerpAPI)

Batches: 10 companies at a time to respect rate limits.
Stores results in company.market_signals JSON.
Produces LLM-synthesized trigger summary per company.
"""

import asyncio
import json
import re

import httpx

from backend.agents.base import BaseAgent, register_agent
from backend.models.company import Company
from backend.config.settings import get_settings
from backend.services.llm_service import call_llm

settings = get_settings()

BATCH_SIZE = 10  # companies per batch

SYSTEM_TRIGGER_SUMMARY = (
    "You are a B2B sales intelligence analyst. Given these recent signals "
    "for a company, write ONE sentence explaining why NOW is a good time to reach out. "
    "Be specific. Reference the actual signal."
)

SYSTEM_NEWS_CLASSIFY = (
    "Classify this company news headline into exactly one category. "
    "Categories: expansion | product_launch | partnership | acquisition | award | other. "
    'Return JSON: {"category": "..."}.'
)


@register_agent("market_intelligence")
class MarketIntelligenceAgent(BaseAgent):
    """Fetches 5 types of business signals per company and stores market_signals JSON."""

    async def run(self, input: dict, memory, config: dict) -> dict:
        workflow_id = input.get("workflow_id")
        company_ids = input.get("company_ids", [])

        log_id = await self.log_start(workflow_id, "market_intelligence", {
            "company_count": len(company_ids),
        })

        await self.emit(workflow_id, "market_intelligence", "running", {
            "message": f"Fetching market signals for {len(company_ids)} companies "
                       f"(batch size {BATCH_SIZE})...",
        })

        signal_counts = {"funding": 0, "news": 0, "hiring": 0, "expansion": 0, "leadership": 0}
        high_urgency_count = 0
        processed = 0

        # Fetch all company objects
        all_companies = list(
            self.db.query(Company).filter(Company.id.in_(company_ids)).all()
        )

        # Process in batches
        for batch_start in range(0, len(all_companies), BATCH_SIZE):
            batch = all_companies[batch_start:batch_start + BATCH_SIZE]

            coros = [
                self._process_company(company, workflow_id)
                for company in batch
            ]

            results = await asyncio.gather(*coros)

            for company, (signals, urgency) in zip(batch, results):
                if signals is not None:
                    company.market_signals = signals
                    self.db.commit()

                    for signal_type in signal_counts:
                        if signal_type in signals and signals.get(signal_type):
                            signal_counts[signal_type] += 1

                    if urgency == "high":
                        high_urgency_count += 1

                processed += 1

            # Emit progress after each batch
            await self.emit(workflow_id, "market_intelligence", "running", {
                "message": f"Processed {processed}/{len(all_companies)} companies...",
                "progress": round((processed / max(len(all_companies), 1)) * 100),
            })

        # Commit all at the end
        self.db.commit()

        result = {
            "companies_with_signals": processed,
            "high_urgency_count": high_urgency_count,
            "signals_breakdown": signal_counts,
        }

        await self.emit(workflow_id, "market_intelligence", "completed", {
            "message": (
                f"✓ {processed} companies analyzed, "
                f"{high_urgency_count} high urgency, "
                f"signals: {signal_counts}"
            ),
            **result,
        })

        await self.log_complete(log_id, result)
        return result

    # ─── Per-company processing ──────────────────────────────────────────────

    async def _process_company(self, company: Company, workflow_id: str) -> tuple[dict | None, str]:
        """Run all 5 signal checks for one company in parallel."""
        name = company.name
        domain = company.domain

        try:
            results = await asyncio.gather(
                self._signal_funding(name, company),
                self._signal_news(name, company),
                self._signal_hiring(name, company),
                self._signal_expansion(name, company),
                self._signal_leadership(name, company),
                return_exceptions=True,
            )

            funding_data, news_data, hiring_data, expansion_data, leadership_data = [
                r if not isinstance(r, Exception) else {}
                for r in results
            ]

            # Build LLM trigger summary
            trigger_summary, urgency = await self._synthesize_trigger(
                name, {
                    "funding": funding_data,
                    "news": news_data,
                    "hiring": hiring_data,
                    "expansion": expansion_data,
                    "leadership": leadership_data,
                }
            )

            signals = {
                "funding": funding_data or None,
                "news": news_data or None,
                "hiring": hiring_data or None,
                "expansion": expansion_data or None,
                "leadership": leadership_data or None,
                "trigger_summary": trigger_summary,
                "urgency": urgency,
                "last_updated": "2026-06",
            }

            return signals, urgency

        except Exception as e:
            print(f"[MarketIntelligence] Error processing {name}: {e}")
            return None, "low"

    # ─── Signal 1: Recent funding ────────────────────────────────────────────

    async def _signal_funding(self, company_name: str, company: Company | None = None) -> dict:
        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return self._mock_signal("funding", company_name, company)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": settings.SERPAPI_KEY,
                        "engine": "google",
                        "q": f'"{company_name}" funding OR raised million 2024 OR 2025',
                        "num": 5,
                    },
                )
                if resp.status_code != 200:
                    return {}

                items = resp.json().get("organic_results", [])
                if not items:
                    return {}

                for r in items:
                    snippet = (r.get("snippet", "") + " " + r.get("title", "")).lower()
                    link = r.get("link", "")

                    # Try to extract amount and round from snippet
                    amount_match = re.search(r'\$(\d+[\.\d]*)\s*(m|million|b|billion)', snippet, re.IGNORECASE)
                    round_match = re.search(r'(seed|series\s*[a-f]|pre-seed|ipo)', snippet, re.IGNORECASE)
                    date_match = re.search(r'(202[0-9]|202[0-9]-[01]\d)', snippet)

                    if amount_match or round_match:
                        amount = f"${amount_match.group(1)}{amount_match.group(2).upper()}" if amount_match else None
                        rnd = round_match.group(1).strip().title() if round_match else None
                        date = date_match.group(1) if date_match else None

                        return {
                            "detected": True,
                            "amount": amount,
                            "round": rnd,
                            "date": date,
                            "source_url": link,
                            "headline": r.get("title", ""),
                        }

                return {"detected": False, "detail": "No recent funding signals found"}

        except Exception:
            return {"detected": False, "detail": "Funding check failed"}

    # ─── Signal 2: News / press ──────────────────────────────────────────────

    async def _signal_news(self, company_name: str, company: Company | None = None) -> dict:
        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return self._mock_signal("news", company_name, company)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": settings.SERPAPI_KEY,
                        "engine": "google",
                        "q": f'"{company_name}" 2024 OR 2025 '
                             f'site:techcrunch.com OR site:businesswire.com '
                             f'OR site:prnewswire.com',
                        "num": 3,
                    },
                )
                if resp.status_code != 200:
                    return {}

                items = resp.json().get("organic_results", [])
                if not items:
                    return {}

                headlines = [
                    {"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
                    for r in items[:3]
                ]

                # LLM classify
                category = await self._classify_news(headlines[0]["title"])

                return {
                    "detected": True,
                    "headlines": headlines,
                    "category": category,
                    "article_count": len(headlines),
                }

        except Exception:
            return {"detected": False}

    async def _classify_news(self, headline: str) -> str:
        try:
            response = await call_llm(SYSTEM_NEWS_CLASSIFY, f"Headline: {headline}", expect_json=True)
            parsed = json.loads(response)
            return parsed.get("category", "other")
        except (json.JSONDecodeError, Exception):
            return "other"

    # ─── Signal 3: Hiring surge ──────────────────────────────────────────────

    async def _signal_hiring(self, company_name: str, company: Company) -> dict:
        hiring_surge = False
        count_estimate = 0

        # Check existing hiring score from validation step
        if company.hiring_signal_score and company.hiring_signal_score > 0.7:
            hiring_surge = True
            count_estimate = 5  # moderate estimate

        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return {
                "detected": hiring_surge,
                "hiring_surge": hiring_surge,
                "hiring_count_estimate": count_estimate,
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": settings.SERPAPI_KEY,
                        "engine": "google",
                        "q": f'"{company_name}" hiring 2024 "multiple positions" OR "we are growing"',
                        "num": 5,
                    },
                )
                if resp.status_code == 200:
                    items = resp.json().get("organic_results", [])
                    if items:
                        snippet = " ".join(r.get("snippet", "") for r in items).lower()

                        # Estimate count from snippets
                        count_matches = re.findall(r'(\d+)\s*(?:positions|roles|openings|hires)', snippet)
                        if count_matches:
                            count_estimate = max(int(c) for c in count_matches)

                        hiring_surge = True

        except Exception:
            pass

        return {
            "detected": hiring_surge,
            "hiring_surge": hiring_surge,
            "hiring_count_estimate": max(count_estimate, 1 if hiring_surge else 0),
        }

    # ─── Signal 4: Geographic expansion ──────────────────────────────────────

    async def _signal_expansion(self, company_name: str, company: Company | None = None) -> dict:
        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return self._mock_signal("expansion", company_name, company)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": settings.SERPAPI_KEY,
                        "engine": "google",
                        "q": f'"{company_name}" expanding OR "new office" OR opening 2024',
                        "num": 3,
                    },
                )
                if resp.status_code != 200:
                    return {}

                items = resp.json().get("organic_results", [])
                if not items:
                    return {}

                snippet = " ".join(r.get("snippet", "") for r in items).lower()

                # Try to extract new location from snippet
                location_match = re.search(
                    r'(?:new\s+office|expanding\s+(?:to|into))\s+(?:in\s+)?'
                    r'([A-Z][A-Za-z\s]+?)(?:\.|,|\s+\-|\s+to\s+|$)',
                    snippet,
                )
                new_location = location_match.group(1).strip() if location_match else None

                return {
                    "detected": bool(new_location or items),
                    "new_location": new_location,
                    "detail": f"Expansion signal: {items[0].get('title', '')}" if items else "No expansion found",
                }

        except Exception:
            return {"detected": False}

    # ─── Signal 5: Leadership changes ────────────────────────────────────────

    async def _signal_leadership(self, company_name: str, company: Company | None = None) -> dict:
        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return self._mock_signal("leadership", company_name, company)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": settings.SERPAPI_KEY,
                        "engine": "google",
                        "q": f'"{company_name}" "new CTO" OR "new CEO" OR appointed OR "joins as" 2024',
                        "num": 3,
                    },
                )
                if resp.status_code != 200:
                    return {}

                items = resp.json().get("organic_results", [])
                if not items:
                    return {}

                snippet = " ".join(r.get("snippet", "") for r in items).lower()

                # Extract new role
                role_match = re.search(
                    r'(?:new\s+)?(cto|ceo|cfo|coo|cio|cmo|vp\s+\w+|chief\s+\w+)',
                    snippet,
                )
                new_role = role_match.group(1).strip().upper() if role_match else None

                return {
                    "detected": True,
                    "leadership_change": True,
                    "new_role": new_role,
                    "detail": items[0].get("title", ""),
                }

        except Exception:
            return {"detected": False}

    # ─── LLM Synthesis ──────────────────────────────────────────────────────

    async def _synthesize_trigger(self, company_name: str, signals: dict) -> tuple[str, str]:
        """Use LLM to generate a trigger summary and urgency rating."""
        try:
            signal_text = json.dumps(signals, indent=2, default=str)
            response = await call_llm(
                SYSTEM_TRIGGER_SUMMARY,
                f"Signals for {company_name}:\n{signal_text}",
                expect_json=True,
            )
            parsed = json.loads(response)
            summary = parsed.get("trigger_summary", "")
            urgency = parsed.get("urgency", "low")

            if urgency not in ("high", "medium", "low"):
                urgency = "low"

            return summary, urgency

        except (json.JSONDecodeError, Exception):
            # Fallback: rule-based urgency
            urgency = "low"
            reasons = []

            if signals.get("funding", {}).get("detected"):
                urgency = "high"
                reasons.append("recent funding")
            if signals.get("leadership", {}).get("detected"):
                urgency = "medium" if urgency == "low" else urgency
                reasons.append("leadership change")
            if signals.get("hiring", {}).get("detected"):
                urgency = "medium" if urgency == "low" else urgency
                reasons.append("hiring activity")

            summary = (
                f"{company_name} shows recent signals: {', '.join(reasons)}. "
                "This is a good time to reach out as they are actively evolving."
            ) if reasons else (
                f"{company_name} is currently in a steady state with no major trigger signals detected."
            )

            return summary, urgency

    # ─── Mock helpers ────────────────────────────────────────────────────────

    def _mock_signal(self, signal_type: str, company_name: str | None = None,
                     company: Company | None = None) -> dict:
        """Return varied plausible mock data when SerpAPI is unavailable."""
        # Try dynamic generator for company-specific variety
        if company_name:
            try:
                from backend.tools.mock_data import generate_mock_signals_for_company
                industry = company.industry if company else "SaaS"
                city = getattr(company, 'city', None) or "San Francisco"
                country = getattr(company, 'country', None) or "United States"
                all_signals = generate_mock_signals_for_company(
                    company_name, industry, city, country
                )
                if signal_type in all_signals:
                    return all_signals[signal_type]
            except ImportError:
                pass

        # Static fallback
        mocks = {
            "funding": {
                "detected": True,
                "amount": "$15M",
                "round": "Series B",
                "date": "2025-01",
                "source_url": "https://techcrunch.com",
                "headline": "Raised $15M Series B to accelerate growth",
            },
            "news": {
                "detected": True,
                "headlines": [
                    {"title": "Company launches new AI platform", "url": "https://techcrunch.com", "snippet": "New product launch signals growth"},
                ],
                "category": "product_launch",
                "article_count": 1,
            },
            "expansion": {
                "detected": True,
                "new_location": "Austin, TX",
                "detail": "Opening new office in Austin",
            },
            "leadership": {
                "detected": True,
                "leadership_change": True,
                "new_role": "CTO",
                "detail": "New CTO appointed",
            },
        }
        return mocks.get(signal_type, {"detected": False})
