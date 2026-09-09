"""
Qualification Agent - 8-dimension dynamic scorecard with weighted composite scoring.

Each dimension scores 0-100 independently. Composite = weighted average using
campaign config weights. Companies are tiered A/B/C/Discard.

Dimensions:
  1. Industry match (LLM fuzzy matching)
  2. Location match (city → state → country → adjacent)
  3. Hiring signals (from validation + market signals)
  4. Tech stack match (from TechAnalysisAgent)
  5. Funding stage (mapped + recent funding boost)
  6. Revenue tier (mapped)
  7. Employee range fit (% buffer calculation)
  8. Decision makers found (from contact enrichment)

Stores full breakdown in company.score_breakdown JSON.
"""
import json
import uuid

from backend.agents.base import BaseAgent, register_agent
from backend.models.company import Company
from backend.models.contact import Contact
from backend.models.recommendation import Recommendation
from backend.services.llm_service import call_llm
from backend.config.settings import get_settings

settings = get_settings()

# ── Funding stage → score mapping ─────────────────────────────────────────
STAGE_SCORES = {
    "pre-seed": 10, "pre seed": 10,
    "seed": 30,
    "series a": 60, "series-a": 60,
    "series b": 80, "series-b": 80,
    "series c": 90, "series-c": 90,
    "series d": 70, "series-d": 70,
    "series d_plus": 70,
    "series e": 70, "series-e": 70,
    "public": 50,
    "bootstrapped": 40, "self-funded": 40,
    "acquired": 60,
}

# Revenue tier → score
REVENUE_MAP = {
    "$0-1M": 10,
    "$1-10M": 40,
    "$10-50M": 65,
    "$50-100M": 80,
    "$100-500M": 90,
    "$500M+": 85,
}

# Default scoring weights (8-dimension wizard format)
DEFAULT_WEIGHTS = {
    "industry_match": 25,
    "location_match": 10,
    "hiring_signals": 15,
    "tech_stack_match": 15,
    "funding_stage": 15,
    "revenue_tier": 5,
    "employee_range": 10,
    "decision_makers_found": 5,
}

# Legacy weight format → new format mapping
LEGACY_WEIGHT_MAP = {
    "funding_weight": "funding_stage",
    "hiring_weight": "hiring_signals",
    "revenue_weight": "revenue_tier",
    "icp_match_weight": "industry_match",       # legacy ICP → industry + location
    "tech_stack_weight": "tech_stack_match",
    "growth_weight": "decision_makers_found",   # closest match
}


@register_agent("qualification")
class QualificationAgent(BaseAgent):
    """
    8-dimension dynamic scorecard. Each dimension scores 0-100.
    Weighted composite → tier assignment → LLM reasoning.
    Stores full breakdown in company.score_breakdown JSON.
    """

    async def run(self, input: dict, memory, config: dict) -> dict:
        workflow_id = input.get("workflow_id")
        company_ids = input.get("company_ids", [])
        campaign_config = input.get("config", config) or {}

        # Resolve scoring weights (support both new + legacy formats)
        weights = self._resolve_weights(campaign_config)

        log_id = await self.log_start(workflow_id, "qualification", {
            "company_count": len(company_ids),
        })

        await self.emit(workflow_id, "qualification", "running", {
            "message": f"📊 Scoring {len(company_ids)} companies across 8 dimensions..."
        })

        scored_ids = []
        recommendation_ids = []
        tier_counts = {"A": 0, "B": 0, "C": 0, "discarded": 0}
        composite_total = 0.0

        for idx, company_id in enumerate(company_ids):
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                continue

            # Skip if already scored (idempotent)
            if company.qualification_score is not None and company.score_breakdown:
                scored_ids.append(company_id)
                old_rec = self.db.query(Recommendation).filter(
                    Recommendation.company_id == company_id
                ).first()
                if old_rec:
                    recommendation_ids.append(old_rec.id)
                if old_rec and old_rec.priority == "high":
                    tier_counts["A"] += 1
                elif old_rec and old_rec.priority == "medium":
                    tier_counts["B"] += 1
                elif old_rec and old_rec.priority == "low":
                    tier_counts["C"] += 1
                else:
                    tier_counts["discarded"] += 1
                continue

            await self.emit(workflow_id, "qualification", "running", {
                "message": f"Scoring {idx+1}/{len(company_ids)}: {company.name}",
                "progress": round(((idx + 1) / len(company_ids)) * 100),
            })

            # ── Calculate all 8 dimensions ─────────────────────────────────
            dim1 = await self._dim_industry(company, campaign_config)
            dim2 = self._dim_location(company, campaign_config)
            dim3 = self._dim_hiring(company)
            dim4 = self._dim_tech_stack(company)
            dim5 = self._dim_funding(company)
            dim6 = self._dim_revenue(company)
            dim7 = self._dim_employee_range(company, campaign_config)
            dim8 = self._dim_decision_makers(company)

            dimensions = [dim1, dim2, dim3, dim4, dim5, dim6, dim7, dim8]
            dim_names = [
                "industry_match", "location_match", "hiring_signals",
                "tech_stack_match", "funding_stage", "revenue_tier",
                "employee_range", "decision_makers_found",
            ]

            # ── Compute weighted composite ─────────────────────────────────
            breakdown = {}
            composite = 0.0
            for name, dim in zip(dim_names, dimensions):
                weight = weights.get(name, DEFAULT_WEIGHTS[name]) / 100.0
                weighted = round(dim["score"] * weight, 1)
                breakdown[name] = {
                    "score": dim["score"],
                    "weight": round(weight * 100, 1),   # store as percentage
                    "weighted": weighted,
                    "detail": dim.get("detail", ""),
                }
                composite += weighted

            composite = round(composite, 1)

            # ── Tier assignment ────────────────────────────────────────────
            tier, priority = self._assign_tier(composite)

            # ── LLM reasoning ──────────────────��───────────────────────────
            llm_result = await self._llm_reason(company, dimensions, dim_names, composite)
            reasoning = llm_result["reason"]
            confidence = llm_result["confidence"]
            strongest = llm_result["strongest_signal"]
            weakest = llm_result["weakest_signal"]

            # ── Persist score_breakdown on company ─────────────────────────
            breakdown["composite"] = composite
            breakdown["tier"] = tier
            breakdown["reason"] = reasoning
            breakdown["strongest_signal"] = strongest
            breakdown["weakest_signal"] = weakest
            company.score_breakdown = breakdown
            company.qualification_score = composite

            # ── Create recommendation row ──────────────────────────────────
            rec = Recommendation(
                id=str(uuid.uuid4()),
                company_id=company_id,
                priority=priority,
                reason=reasoning,
                suggested_action=self._suggest_action(tier, strongest),
                outreach_template="",
                confidence=round(confidence, 2),
            )
            self.db.add(rec)
            self.db.flush()

            scored_ids.append(company_id)
            recommendation_ids.append(rec.id)
            tier_counts[tier if tier != "discard" else "discarded"] += 1
            composite_total += composite

        self.db.commit()

        avg_composite = round(composite_total / max(len(scored_ids), 1), 1)

        result = {
            "scored_ids": scored_ids,
            "scored_company_ids": scored_ids,
            "recommendation_ids": recommendation_ids,
            "scored": len(scored_ids),
            "tier_a_count": tier_counts["A"],
            "tier_b_count": tier_counts["B"],
            "tier_c_count": tier_counts["C"],
            "discarded_count": tier_counts["discarded"],
            "avg_composite_score": avg_composite,
        }

        await self.emit(workflow_id, "qualification", "completed", {
            "message": (
                f"✓ Scored {len(scored_ids)} companies | "
                f"A:{tier_counts['A']} B:{tier_counts['B']} "
                f"C:{tier_counts['C']} Discard:{tier_counts['discarded']} | "
                f"Avg: {avg_composite}"
            ),
            **result,
        })

        await self.log_complete(log_id, result)
        return result

    # ══════════════════════════════════════════════════════════════════════
    # DIMENSION 1 — Industry match  (LLM fuzzy matching)
    # ══════════════════════════════════════════════════════════════════════

    async def _dim_industry(self, company: Company, config: dict) -> dict:
        """
        LLM-based fuzzy industry matching.
        Score 100 exact → 70 related → 40 adjacent → 0 no match.
        """
        target_industries = self._get_config_list(config, "company_filters", "industries")
        if not target_industries:
            target_industries = self._get_config_list(config, "industries")
        if not target_industries:
            return {"score": 50, "detail": "No target industries configured"}

        company_industry = (company.industry or "").strip()
        if not company_industry:
            return {"score": 30, "detail": "Company industry unknown"}

        # Quick exact match check (no LLM needed)
        cl = company_industry.lower()
        for t in target_industries:
            if t.lower() == cl or t.lower() in cl or cl in t.lower():
                return {"score": 100, "detail": f"Exact match: {t}"}

        # LLM fuzzy match
        system_prompt = (
            "You are a strict industry-matching analyst. Given a company's stated "
            "industry and a list of target industries, determine the match quality.\n\n"
            "Rules:\n"
            '- exact → company industry IS one of the target industries (score 100)\n'
            '- related → company industry is conceptually related to a target\n'
            '  (e.g. "AI" matches "Machine Learning") — score 70\n'
            '- adjacent → company industry is in the same broad sector\n'
            '  (e.g. "Enterprise Software" when targeting "SaaS") — score 40\n'
            '- none → completely unrelated — score 0\n\n'
            "Output ONLY valid JSON:\n"
            '{"match_type": "exact"|"related"|"adjacent"|"none", '
            '"score": int, "detail": "brief explanation"}'
        )

        user_msg = json.dumps({
            "company_industry": company_industry,
            "target_industries": target_industries,
        })

        raw = await call_llm(system_prompt, user_msg, expect_json=True)
        try:
            data = json.loads(raw)
            return {
                "score": max(0, min(100, int(data.get("score", 0)))),
                "detail": data.get("detail", f"LLM: {data.get('match_type', 'unknown')} match"),
            }
        except (json.JSONDecodeError, ValueError, TypeError):
            # Fallback: partial keyword match
            for t in target_industries:
                if any(word in cl for word in t.lower().split() if len(word) > 3):
                    return {"score": 70, "detail": f"Related: keyword overlap with '{t}'"}
            return {"score": 40, "detail": "Adjacent: no direct match found"}

    # ══════════════════════════════════════════════════════════════════════
    # DIMENSION 2 — Location match
    # ══════���═══════════════════════════════════════════════════════════════

    def _dim_location(self, company: Company, config: dict) -> dict:
        """City → country+state → country → adjacent → no match."""
        target_countries = self._get_config_list(config, "geography", "countries")
        target_states = self._get_config_list(config, "geography", "states")
        target_cities = self._get_config_list(config, "geography", "cities")

        if not target_countries and not target_states and not target_cities:
            return {"score": 50, "detail": "No location targets configured"}

        company_city = (company.city or "").lower().strip()
        company_country = (company.country or "").lower().strip()

        if not company_country and not company_city:
            return {"score": 30, "detail": "Company location unknown"}

        # City match → 100
        if company_city and any(c.lower() == company_city for c in target_cities):
            return {"score": 100, "detail": f"Exact city: {company.city}"}

        # Country + state match → 80
        if company_country and target_states and company.state:
            state_match = any(s.lower() == company.state.lower() for s in target_states)
            country_match = any(c.lower() == company_country for c in target_countries)
            if state_match and country_match:
                return {"score": 80, "detail": f"{company.state}, {company.country}"}

        # Country only → 60
        if company_country and any(c.lower() == company_country for c in target_countries):
            return {"score": 60, "detail": f"Country: {company.country}"}

        # Adjacent country → 30
        adjacent = self._adjacent_countries(target_countries)
        if company_country in adjacent:
            return {"score": 30, "detail": f"Adjacent country: {company.country}"}

        return {"score": 0, "detail": f"No geography match for {company.country}"}

    # ══════════════════════════════════════════════════════════════════════
    # DIMENSION 3 — Hiring signals
    # ═══════════════════════════════════════��══════════════════════════════

    def _dim_hiring(self, company: Company) -> dict:
        """Use hiring_signal_score + market_signals hiring surge."""
        base = company.hiring_signal_score or 0.0
        score = base * 100

        # Boost if market intelligence detected a hiring surge
        signals = company.market_signals or {}
        hiring = signals.get("hiring") or {}
        if hiring.get("hiring_surge") or hiring.get("detected"):
            score += 20

        score = min(100, score)

        detail_parts = []
        if base > 0:
            detail_parts.append(f"signal score {base:.2f}")
        if hiring.get("hiring_surge"):
            detail_parts.append("hiring surge detected")
        if hiring.get("hiring_count_estimate"):
            detail_parts.append(f"~{hiring['hiring_count_estimate']} openings")

        detail = "; ".join(detail_parts) if detail_parts else "No hiring signal"
        return {"score": round(score, 1), "detail": detail}

    # ══════════════════════════════════════════════════════════��═══════════
    # DIMENSION 4 — Tech stack match
    # ══════════════════════════════════════════════════════════════════════

    def _dim_tech_stack(self, company: Company) -> dict:
        """Use tech_stack_detected.required_match + nice_to_have bonuses."""
        detected = company.tech_stack_detected or {}

        required_match = detected.get("required_match", 0.0)
        nice_to_have_match = detected.get("nice_to_have_match", 0.0)
        excluded_found = detected.get("excluded_tech_found", False)

        # Base from required tech match
        if isinstance(required_match, (int, float)):
            score = required_match * 100
        else:
            score = 0.0

        # Nice-to-have bonus: +10 per matched, max +20
        if isinstance(nice_to_have_match, (int, float)):
            nice_bonus = min(nice_to_have_match * 100, 20.0)
        else:
            nice_bonus = 0.0
        score += nice_bonus

        # Excluded tech penalty: -30
        if excluded_found:
            score -= 30

        score = max(0, min(100, score))

        detail_parts = []
        if required_match:
            detail_parts.append(f"required {required_match:.0%} match")
        if nice_bonus > 0:
            detail_parts.append(f"+{nice_bonus:.0f} nice-to-have bonus")
        if excluded_found:
            detail_parts.append("-30 excluded tech penalty")

        return {
            "score": round(score, 1),
            "detail": "; ".join(detail_parts) if detail_parts else "No tech data",
        }

    # ══════════════════════════════════════════════════════════════════════
    # DIMENSION 5 — Funding stage
    # ══════════════════════════════════════════════════════════════════════

    def _dim_funding(self, company: Company) -> dict:
        """Map funding stage to score + boost for recent funding in market_signals."""
        stage_key = str(company.funding_stage or "").lower().strip()
        score = STAGE_SCORES.get(stage_key, 20)

        # Boost if market_signals has recent funding
        signals = company.market_signals or {}
        funding = signals.get("funding") or {}
        if funding.get("detected"):
            score += 15

        score = min(100, score)

        detail_parts = [stage_key or "unknown"]
        if funding.get("detected"):
            amount = funding.get("amount", "")
            if amount:
                detail_parts.append(f"+15 recent funding ({amount})")
            else:
                detail_parts.append("+15 recent funding")

        return {"score": score, "detail": " | ".join(detail_parts)}

    # ══════════════════════════════════════════════════════════════════════
    # DIMENSION 6 — Revenue tier
    # ══════════════════════════════════════════════════════════════════════

    def _dim_revenue(self, company: Company) -> dict:
        """Map revenue range to score."""
        revenue = company.revenue_range or ""
        score = REVENUE_MAP.get(revenue, 25)
        return {"score": score, "detail": revenue or "Unknown revenue"}

    # ══════════════════════════════════════════════════════════════════════
    # DIMENSION 7 — Employee range fit
    # ══════════════════════════════════════════════════════════════════════

    def _dim_employee_range(self, company: Company, config: dict) -> dict:
        """Score based on how well employee count fits ICP range."""
        filters = config.get("company_filters", config)
        min_emp = filters.get("min_employees", 0)
        max_emp = filters.get("max_employees", float("inf"))

        emp = company.employee_count
        if emp is None:
            return {"score": 25, "detail": "Employee count unknown"}

        if min_emp <= emp <= max_emp:
            return {"score": 100, "detail": f"{emp} within ICP range [{min_emp}-{max_emp}]"}

        # Calculate how far outside range
        if emp < min_emp:
            ratio = emp / max(min_emp, 1)
        else:
            ratio = max_emp / max(emp, 1)

        if ratio >= 0.8:
            return {"score": 70, "detail": f"{emp} within 20% of ICP range"}
        elif ratio >= 0.5:
            return {"score": 40, "detail": f"{emp} within 50% of ICP range"}
        else:
            return {"score": 0, "detail": f"{emp} outside 50% buffer of ICP range"}

    # ══════════════════════════════════════════════════════════════════════
    # DIMENSION 8 — Decision makers found
    # ══════════════════════════════════════════════════════════════════════

    def _dim_decision_makers(self, company: Company) -> dict:
        """
        Score based on contacts found and their source quality.
        100: All or most personas found with LinkedIn confirmation
        70: Primary persona found (is_primary_persona with non-generated source)
        30: Only generated contacts
        0: No contacts found at all
        """
        contacts = self.db.query(Contact).filter(
            Contact.company_id == company.id
        ).all()

        if not contacts:
            return {"score": 0, "detail": "No contacts found"}

        primary_linkedin = sum(
            1 for c in contacts
            if c.is_primary_persona and c.source == "linkedin_serpapi"
        )
        any_linkedin = sum(
            1 for c in contacts
            if c.source == "linkedin_serpapi"
        )
        any_generated = sum(
            1 for c in contacts
            if c.source == "generated"
        )
        total = len(contacts)

        # All confirmed via LinkedIn
        if any_linkedin == total:
            return {"score": 100, "detail": f"All {total} contacts LinkedIn-confirmed"}

        # Primary found via LinkedIn
        if primary_linkedin >= 1:
            return {
                "score": 70,
                "detail": f"Primary persona LinkedIn-confirmed; {any_generated} generated",
            }

        # Mixed: some LinkedIn, some generated
        if any_linkedin > 0:
            return {
                "score": max(30, int((any_linkedin / total) * 70)),
                "detail": f"{any_linkedin} LinkedIn + {any_generated} generated",
            }

        # Only generated
        if any_generated == total:
            return {"score": 30, "detail": f"All {total} contacts generated (no LinkedIn)"}

        return {"score": 30, "detail": "Mixed/unconfirmed contacts"}

    # ══════════════════════════════════════════════════════════════════════
    # LLM reasoning (post-scoring)
    # ══════════════════════════════════════════════════════════════════════

    async def _llm_reason(self, company: Company, dimensions: list[dict],
                          names: list[str], composite: float) -> dict:
        """
        Generate qualification reasoning via LLM after all dimension scores computed.
        """
        scores_dict = {n: d["score"] for n, d in zip(names, dimensions)}

        system_prompt = (
            "You are a strict B2B qualification analyst. Given these exact dimension "
            "scores, explain in 2 sentences WHY this company is or isn't a strong fit. "
            "Be specific — mention the actual scores.\n\n"
            "Output ONLY valid JSON:\n"
            '{"reason": str, "strongest_signal": str, '
            '"weakest_signal": str, "confidence": float}'
        )

        user_msg = json.dumps({
            "company": {
                "name": company.name,
                "industry": company.industry,
                "country": company.country,
            },
            "dimension_scores": scores_dict,
            "composite_score": composite,
        })

        raw = await call_llm(system_prompt, user_msg, expect_json=True)
        try:
            data = json.loads(raw)
            return {
                "reason": data.get("reason", ""),
                "strongest_signal": data.get("strongest_signal", ""),
                "weakest_signal": data.get("weakest_signal", ""),
                "confidence": float(data.get("confidence", composite / 100)),
            }
        except (json.JSONDecodeError, ValueError, TypeError):
            # Fallback
            strongest = max(scores_dict, key=scores_dict.get)
            weakest = min(scores_dict, key=scores_dict.get)
            return {
                "reason": f"{company.name} scored {composite}/100. "
                          f"Strongest dimension: {strongest} ({scores_dict[strongest]}). "
                          f"Weakest: {weakest} ({scores_dict[weakest]}).",
                "strongest_signal": f"{strongest}: {scores_dict[strongest]}",
                "weakest_signal": f"{weakest}: {scores_dict[weakest]}",
                "confidence": round(composite / 100, 2),
            }

    # ══════════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _resolve_weights(config: dict) -> dict:
        """
        Resolve scoring weights from campaign config.
        Handles both new 8-dimension wizard format and legacy 6-dimension format.
        """
        # New wizard format: config.scoring_weights.{industry_match, location_match, ...}
        weights = config.get("scoring_weights")
        if weights and all(k in DEFAULT_WEIGHTS for k in weights):
            return weights

        # Legacy format: config.scoring.{funding_weight, hiring_weight, ...}
        legacy = config.get("scoring", {})
        if legacy:
            resolved = dict(DEFAULT_WEIGHTS)
            for old_key, new_key in LEGACY_WEIGHT_MAP.items():
                if old_key in legacy:
                    resolved[new_key] = legacy[old_key]

            # ICP match in legacy maps to industry (60%) + location (40%) split
            if "icp_match_weight" in legacy:
                icp_total = legacy["icp_match_weight"]
                resolved["industry_match"] = round(icp_total * 0.6)
                resolved["location_match"] = round(icp_total * 0.4)

            return resolved

        return dict(DEFAULT_WEIGHTS)

    @staticmethod
    def _assign_tier(composite: float) -> tuple[str, str]:
        """
        Assign tier + priority label.
          A: >= 80 (hot prospect)
          B: >= 60 (warm)
          C: >= 40 (lukewarm)
          Discard: < 40
        """
        if composite >= 80:
            return "A", "high"
        elif composite >= 60:
            return "B", "medium"
        elif composite >= 40:
            return "C", "low"
        else:
            return "discard", "low"

    @staticmethod
    def _suggest_action(tier: str, strongest: str) -> str:
        """Generate suggested outreach action based on tier."""
        actions = {
            "A": f"Schedule discovery call immediately. Key strength: {strongest}",
            "B": f"Add to nurture sequence with personalized outreach. Signal: {strongest}",
            "C": f"Monitor for trigger events before outreach.",
            "discard": "Low priority — archive or revisit in 90 days.",
        }
        return actions.get(tier, "Standard outreach cadence.")

    @staticmethod
    def _adjacent_countries(targets: list[str]) -> set:
        """Map target countries to adjacent countries."""
        mapping = {
            "us": {"canada", "mexico"},
            "canada": {"us"},
            "uk": {"ireland", "france", "germany", "netherlands"},
            "germany": {"austria", "switzerland", "france", "netherlands"},
            "france": {"belgium", "switzerland", "germany", "luxembourg"},
            "australia": {"new zealand", "singapore"},
            "india": {"sri lanka", "bangladesh", "nepal", "pakistan"},
            "singapore": {"malaysia", "indonesia"},
            "uae": {"saudi arabia", "qatar", "oman", "bahrain"},
            "israel": {"cyprus"},
        }
        adjacent = set()
        for t in targets:
            t_lower = t.lower().strip()
            for key, vals in mapping.items():
                if t_lower == key or t_lower in vals:
                    adjacent.update(vals)
        adjacent.difference_update(t.lower() for t in targets)
        return adjacent

    @staticmethod
    def _get_config_list(config: dict, *keys: str) -> list:
        """Safely traverse nested config dict to get a list value."""
        current = config
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, {})
            else:
                return []
        if isinstance(current, list):
            return current
        return []
