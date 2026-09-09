"""
Recommendation Agent — generates enterprise-grade outreach packages for qualified companies.

For each tier A/B company, produces:
  - Buying committee identification with confidence scores
  - LLM-generated talking points referencing specific company signals
  - Personalized cold email (subject + body)
  - LinkedIn connection message
  - 3-touch follow-up sequence
  - Channel selection and market trigger
  - Complete score_breakdown in recommendation metadata
"""
import json
import uuid

from backend.agents.base import BaseAgent, register_agent
from backend.models.company import Company
from backend.models.contact import Contact
from backend.models.recommendation import Recommendation
from backend.models.approval import Approval
from backend.services.llm_service import call_llm


TALKING_POINTS_PROMPT = """You are a B2B sales expert. Generate 3-5 SPECIFIC talking points
for outreach to this company. Each point must reference something SPECIFIC about this company
(their tech stack, recent news, hiring signal, funding round, or score dimension).
Do NOT use generic sales language. Be precise.

Output ONLY valid JSON:
{"talking_points": ["Point 1 with specific reference...", "Point 2...", ...]}"""

EMAIL_PROMPT = """Write a SHORT (max 120 words) personalized B2B cold email.
Rules:
- Open with THEIR specific situation (not generic phrases like 'I came across your company')
- Reference the most relevant market signal (funding, hiring, news, expansion)
- Connect to campaign value proposition in ONE sentence
- End with a specific, low-friction CTA
- No buzzwords, no generic phrases
- Subject line: specific + under 50 chars

Output ONLY valid JSON:
{"subject": "Under 50 chars", "body": "Email body (max 120 words)"}"""

LINKEDIN_PROMPT = """Write a LinkedIn connection note (max 300 chars).
Be personal and specific. Reference one relevant signal about the company.
Ask one specific question related to their role/challenge.
No buzzwords. No generic 'I admire your work'.

Output ONLY valid JSON:
{"linkedin_message": "Max 300 chars connection note"}"""


@register_agent("recommendation_memory")
class RecommendationMemoryAgent(BaseAgent):
    """
    Generates complete enterprise-grade outreach packages for qualified companies.
    Only generates for tier A (hot) and tier B (warm). Skips tier C and discarded.
    """

    async def run(self, input: dict, memory, config: dict) -> dict:
        workflow_id = input.get("workflow_id")
        campaign_config = input.get("config", config) or {}
        include_c = campaign_config.get("include_c", False)

        # Get company IDs from qualification output
        company_ids = input.get("company_ids", []) or input.get("scored_ids", []) or input.get("scored_company_ids", [])
        min_score_threshold = input.get("min_score_threshold", 60.0)

        log_id = await self.log_start(workflow_id, "recommendation_memory", {
            "company_count": len(company_ids),
            "min_score_threshold": min_score_threshold,
        })

        await self.emit(workflow_id, "recommendation_memory", "running", {
            "message": f"📦 Generating outreach packages for qualified companies..."
        })

        recommendations_created = 0
        high_priority = 0
        medium_priority = 0
        total_email_score = 0.0

        for company_id in company_ids:
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                continue

            # Check qualification: only process tier A and B (and optionally C)
            breakdown = company.score_breakdown or {}
            tier = breakdown.get("tier", "C")
            composite = breakdown.get("composite", 0)

            if tier == "discard" or composite < min_score_threshold:
                continue
            if tier == "C" and not include_c:
                continue

            # Load all data needed
            contacts = self.db.query(Contact).filter(
                Contact.company_id == company.id
            ).all()
            market_signals = company.market_signals or {}
            tech_stack = company.tech_stack_detected or {}

            # Find existing recommendation (created by qualification step)
            rec = self.db.query(Recommendation).filter(
                Recommendation.company_id == company.id
            ).first()

            if not rec:
                # Create new recommendation for tier C that wasn't scored
                rec = Recommendation(
                    id=str(uuid.uuid4()),
                    company_id=company.id,
                    priority="low",
                    reason=f"{company.name} scored {composite}/100",
                    suggested_action="",
                    outreach_template="",
                    confidence=composite / 100 if composite > 0 else 0.5,
                )
                self.db.add(rec)
                self.db.flush()

            # ── STEP 1: Identify buying committee ──────────────────────────
            primary_contact, secondary_contacts = self._identify_committee(contacts)
            buying_committee = self._build_committee(primary_contact, secondary_contacts)
            rec.buying_committee = buying_committee

            # ── STEP 2: Generate talking points ────────────────────────────
            talking_points = await self._generate_talking_points(
                company, market_signals, tech_stack, breakdown, campaign_config
            )
            rec.talking_points = talking_points

            # ── STEP 3: Generate personalized email ────────────────────────
            email_content = await self._generate_email(
                company, primary_contact, market_signals, campaign_config, breakdown
            )
            rec.outreach_subject = email_content.get("subject", "")
            rec.outreach_template = email_content.get("body", "")

            # ── STEP 4: Generate LinkedIn message ────���─────────────────────
            linkedin_msg = await self._generate_linkedin(
                company, primary_contact, market_signals
            )
            rec.linkedin_message = linkedin_msg.get("linkedin_message", "")

            # ── STEP 5: Build follow-up sequence ───────────────────────────
            rec.follow_up_sequence = self._build_follow_up(
                rec.outreach_subject,
                rec.outreach_template,
                rec.linkedin_message,
            )

            # ── STEP 6: Determine outreach channel ─────────────────────────
            channel = self._determine_channel(primary_contact)
            rec.outreach_channel = channel

            # ── STEP 7: Set market trigger ─────────────────────────────────
            market_trigger = self._get_market_trigger(market_signals, breakdown, company)
            rec.market_trigger = market_trigger

            # ── STEP 8: Suggested action ───────────────────────────────────
            rec.suggested_action = self._build_suggested_action(
                company, primary_contact, channel, market_trigger
            )

            # Create approval row
            approval = Approval(
                id=str(uuid.uuid4()),
                recommendation_id=rec.id,
                status="pending",
            )
            self.db.add(approval)
            self.db.flush()

            # Track counts
            recommendations_created += 1
            if rec.priority == "high":
                high_priority += 1
            else:
                medium_priority += 1

            # Self-rate personalization score
            total_email_score += self._rate_email_score(rec)

            # Write to SharedMemory
            if memory:
                try:
                    await memory.write(
                        entity_type="company",
                        entity_id=company.id,
                        summary=(
                            f"{company.name} ({company.domain}) - "
                            f"Score: {composite}/100 - Tier: {tier} - "
                            f"Workflow: {workflow_id}"
                        ),
                        metadata={
                            "domain": company.domain,
                            "name": company.name,
                            "score": composite,
                            "tier": tier,
                            "priority": rec.priority,
                            "workflow_id": workflow_id,
                        },
                    )
                except Exception as e:
                    print(f"[Memory] Write failed for {company.name}: {e}")

        self.db.commit()

        avg_score = round(total_email_score / max(recommendations_created, 1), 2)

        result = {
            "recommendations_created": recommendations_created,
            "recommendations_ready": recommendations_created,
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "avg_email_personalization_score": avg_score,
        }

        await self.emit(workflow_id, "recommendation_memory", "completed", {
            "message": (
                f"✓ {recommendations_created} outreach packages generated "
                f"({high_priority} high, {medium_priority} medium) "
                f"Avg personalization: {avg_score}"
            ),
            **result,
        })

        await self.log_complete(log_id, result)
        return result

    # ══════════════════════════════════════════════════════════════════════
    # STEP 1 — Buying committee identification
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _identify_committee(contacts: list[Contact]) -> tuple[Contact | None, list[Contact]]:
        """
        Identify primary contact (highest confidence primary persona)
        and secondary contacts.
        """
        if not contacts:
            return None, []

        # Primary: highest-confidence contact with is_primary_persona=True
        primary_candidates = [
            c for c in contacts
            if c.is_primary_persona
        ]
        if primary_candidates:
            primary = max(primary_candidates, key=lambda c: c.confidence_score or 0)
        else:
            # Fallback: highest confidence overall
            primary = max(contacts, key=lambda c: c.confidence_score or 0)

        secondary = [c for c in contacts if c.id != primary.id]
        return primary, secondary

    @staticmethod
    def _build_committee(primary: Contact | None, secondary: list[Contact]) -> dict:
        """Build buying committee JSON structure."""
        committee = {
            "primary_persona": None,
            "secondary_personas": [],
            "influencers": [],
        }

        if primary:
            committee["primary_persona"] = {
                "id": primary.id,
                "full_name": primary.full_name,
                "role": primary.role or "",
                "linkedin_url": primary.linkedin_url or "",
                "confidence_score": primary.confidence_score,
                "source": primary.source or "",
            }

        for sec in secondary[:5]:  # cap at 5
            entry = {
                "id": sec.id,
                "full_name": sec.full_name,
                "role": sec.role or "",
                "linkedin_url": sec.linkedin_url or "",
                "confidence_score": sec.confidence_score,
                "source": sec.source or "",
            }
            # Non-primary persona contacts or generated contacts → influencers
            if sec.source == "generated":
                committee["influencers"].append(entry)
            else:
                committee["secondary_personas"].append(entry)

        return committee

    # ══════════════════════════════════════════════════════════════════════
    # STEP 2 — Talking points generation
    # ══════════════════════════════════════════════════════════════════════

    async def _generate_talking_points(
        self, company: Company, signals: dict, tech_stack: dict,
        breakdown: dict, config: dict,
    ) -> list[str]:
        """LLM generates 3-5 specific talking points."""
        value_prop = self._get_value_prop(config)

        user_msg = json.dumps({
            "company": {
                "name": company.name,
                "industry": company.industry,
                "employee_count": company.employee_count,
                "description": company.description or "",
            },
            "market_signals": signals,
            "tech_stack": tech_stack,
            "score_breakdown": {
                k: v for k, v in breakdown.items()
                if k in ("composite", "tier", "industry_match", "tech_stack_match",
                         "funding_stage", "hiring_signals")
            },
            "campaign_value_proposition": value_prop,
        })

        raw = await call_llm(TALKING_POINTS_PROMPT, user_msg, expect_json=True)
        try:
            data = json.loads(raw)
            points = data.get("talking_points", [])
            return points[:5] if isinstance(points, list) else self._fallback_talking_points(company, signals, tech_stack)
        except (json.JSONDecodeError, TypeError):
            return self._fallback_talking_points(company, signals, tech_stack)

    @staticmethod
    def _fallback_talking_points(company: Company, signals: dict, tech_stack: dict) -> list[str]:
        """Rule-based fallback talking points."""
        points = []
        funding = signals.get("funding")
        if funding and funding.get("detected"):
            amount = funding.get("amount", "recent round")
            points.append(f"{company.name}'s {amount} shows strong growth momentum — ideal timing for a new efficiency tool.")

        tech = tech_stack.get("confirmed", [])
        if tech:
            stack_str = ", ".join(tech[:3])
            points.append(f"Your stack ({stack_str}) integrates well with our AI discovery platform — minimal onboarding friction.")

        hiring = signals.get("hiring")
        if hiring and hiring.get("hiring_surge"):
            count = hiring.get("hiring_count_estimate", "significant")
            points.append(f"Your {count} new hires signal expansion — our platform helps teams ramp up pipeline faster.")

        if company.description:
            desc_short = company.description[:100]
            points.append(f"We understand {company.industry} challenges like '{desc_short}' — our solution is built for exactly this use case.")

        if not points:
            points = [
                f"{company.name}'s industry profile aligns strongly with our ICP.",
                f"Your {company.employee_count or 'growing'} team is the right size for our platform.",
            ]

        return points[:5]

    # ═══════════════════════════════════════════════���══════════════════════
    # STEP 3 — Personalized email generation
    # ══════════════════════════════════════════════════════════════════════

    async def _generate_email(
        self, company: Company, primary: Contact | None,
        signals: dict, config: dict, breakdown: dict,
    ) -> dict:
        """LLM generates personalized cold email subject + body."""
        value_prop = self._get_value_prop(config)
        strongest = breakdown.get("strongest_signal", "")
        trigger = self._get_market_trigger(signals, breakdown, company)

        user_msg = json.dumps({
            "company_name": company.name,
            "company_industry": company.industry,
            "primary_contact": {
                "name": primary.full_name if primary else "Decision Maker",
                "role": primary.role if primary else "",
                "linkedin_url": primary.linkedin_url if primary else "",
            },
            "market_signals": {
                "key_trigger": trigger,
                "funding": signals.get("funding"),
                "hiring": signals.get("hiring"),
                "news": signals.get("news"),
                "expanding": signals.get("expansion"),
            },
            "campaign_value_proposition": value_prop,
            "strongest_qualification_signal": strongest,
            "composite_score": breakdown.get("composite", 0),
        })

        raw = await call_llm(EMAIL_PROMPT, user_msg, expect_json=True)
        try:
            data = json.loads(raw)
            return {
                "subject": (data.get("subject", "") or "")[:50],
                "body": data.get("body", ""),
            }
        except (json.JSONDecodeError, TypeError):
            return self._fallback_email(company, primary, trigger)

    @staticmethod
    def _fallback_email(company: Company, primary: Contact | None, trigger: str) -> dict:
        """Rule-based fallback email."""
        contact_name = primary.full_name if primary else "there"
        subject = f"Quick thought for {company.name}"
        if trigger:
            subject = f"Re: {trigger[:40]}"

        body = (
            f"Hi {contact_name},\n\n"
            f"Saw that {company.name} is {trigger} — impressive trajectory. "
            f"We built AgentForge AI specifically for companies at this stage: "
            f"it automates prospect discovery so your team sells smarter, not harder.\n\n"
            f"Open to a 10-minute call next week to see if it's relevant?\n\n"
            f"Best,\n{{sender_name}}"
        )
        return {"subject": subject[:50], "body": body}

    # ══════════════════════════════════════════════════════════════════════
    # STEP 4 — LinkedIn message generation
    # ══════════════════════════════════════════════════════════════════════

    async def _generate_linkedin(
        self, company: Company, primary: Contact | None, signals: dict,
    ) -> dict:
        """LLM generates personalized LinkedIn connection note."""
        contact_name = primary.full_name if primary else "you"
        trigger = self._get_market_trigger(signals, {}, company)

        user_msg = json.dumps({
            "contact_name": contact_name,
            "contact_role": primary.role if primary else "",
            "company_name": company.name,
            "company_industry": company.industry,
            "market_trigger": trigger,
        })

        raw = await call_llm(LINKEDIN_PROMPT, user_msg, expect_json=True)
        try:
            data = json.loads(raw)
            msg = data.get("linkedin_message", "")
            return {"linkedin_message": msg[:300]}
        except (json.JSONDecodeError, TypeError):
            msg = (
                f"Hi {contact_name}, I noticed {company.name} is {trigger}. "
                f"Curious: how does your team currently find new leads?"
            )
            return {"linkedin_message": msg[:300]}

    # ══════════════════════════════════════════════════════════════════════
    # STEP 5 — Follow-up sequence
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _build_follow_up(subject: str, email_body: str, linkedin_msg: str) -> list[dict]:
        """Build 3-touch follow-up sequence."""
        sequence = [
            {
                "touch": 1,
                "channel": "email",
                "day": 0,
                "subject": subject,
                "message": email_body,
            },
            {
                "touch": 2,
                "channel": "linkedin",
                "day": 3,
                "subject": "Connection request",
                "message": linkedin_msg,
            },
            {
                "touch": 3,
                "channel": "email",
                "day": 7,
                "subject": f"Following up: {subject}",
                "message": (
                    f"Hi {{{{contact_name}}}},\n\n"
                    f"Just wanted to circle back on my note from last week. "
                    f"Would our AI discovery platform fit a 10-minute slot on your calendar? "
                    f"Happy to share how similar {{{{company_industry}}}} teams are using it.\n\n"
                    f"Best,\n{{{{sender_name}}}}"
                ),
            },
        ]
        return sequence

    # ══════════════════════════════════════════════════════════════════════
    # STEP 6 — Channel selection
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _determine_channel(primary: Contact | None) -> str:
        """
        Determine best outreach channel.
        - email_confidence > 0.8 → email
        - linkedin confirmed + low email → linkedin
        - else → email with linkedin backup
        """
        if not primary:
            return "email"

        email_conf = primary.email_confidence or 0.0
        linkedin_ok = primary.linkedin_confirmed if hasattr(primary, "linkedin_confirmed") else bool(primary.linkedin_url)

        if email_conf > 0.8:
            return "email"
        elif linkedin_ok and email_conf < 0.6:
            return "linkedin"
        else:
            return "email"

    # ══════════════════════════════════════════════════════════════════════
    # STEP 7 — Market trigger
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _get_market_trigger(signals: dict, breakdown: dict, company: Company) -> str:
        """
        Determine the single most compelling reason to reach out NOW.
        Uses urgency from market_signals, or falls back to qualification data.
        """
        # Priority 1: Market intelligence urgency
        urgency = signals.get("urgency", "")
        trigger_summary = signals.get("trigger_summary", "")

        if urgency == "high" and trigger_summary:
            return trigger_summary[:200]

        # Priority 2: Specific signal detected
        funding = signals.get("funding")
        if funding and funding.get("detected"):
            amount = funding.get("amount", "recent round")
            return f"Recently raised {amount} — scaling and likely evaluating new vendors"

        hiring = signals.get("hiring")
        if hiring and hiring.get("hiring_surge"):
            count = hiring.get("hiring_count_estimate", "many")
            return f"Actively hiring ~{count} roles — team expansion creates new needs"

        expansion = signals.get("expansion")
        if expansion and expansion.get("detected"):
            loc = expansion.get("new_location", "new markets")
            return f"Expanding into {loc} — growing companies need scalable solutions"

        leadership = signals.get("leadership")
        if leadership and leadership.get("detected"):
            role = leadership.get("new_role", "new leadership")
            return f"New {role} appointment — new leaders often reassess vendor relationships"

        # Priority 3: Qualification-based
        strongest = breakdown.get("strongest_signal", "") if breakdown else ""
        if strongest:
            return strongest[:200]

        # Fallback
        return f"{company.industry or 'B2B'} company at {company.employee_count or 'growing'} employee count"

    # ══════════════════════════════���═══════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _build_suggested_action(company: Company, primary: Contact | None,
                                channel: str, trigger: str) -> str:
        """Generate one-sentence suggested next action."""
        contact_name = primary.full_name if primary else "the decision maker"
        if channel == "linkedin":
            return (
                f"Send LinkedIn connection request to {contact_name} at {company.name} "
                f"with a personalized note referencing: {trigger[:80]}"
            )
        return (
            f"Schedule 10-minute discovery call with {contact_name} at {company.name}. "
            f"Key hook: {trigger[:100]}"
        )

    @staticmethod
    def _rate_email_score(rec: Recommendation) -> float:
        """Self-rate the personalization quality of the recommendation package."""
        score = 0.5  # baseline

        if rec.talking_points:
            score += 0.1
        if rec.buying_committee and rec.buying_committee.get("primary_persona"):
            score += 0.1
        if rec.market_trigger and len(rec.market_trigger) > 20:
            score += 0.1
        if rec.linkedin_message and len(rec.linkedin_message) > 50:
            score += 0.05
        if rec.outreach_subject and len(rec.outreach_subject) > 10:
            score += 0.05
        if rec.follow_up_sequence and len(rec.follow_up_sequence) >= 2:
            score += 0.05
        if rec.outreach_template and "{company}" not in rec.outreach_template:
            score += 0.05  # already personalized (no template placeholders)

        return round(min(score, 1.0), 2)

    @staticmethod
    def _get_value_prop(config: dict) -> str:
        """Extract value proposition from campaign config."""
        business = config.get("business", config)
        return business.get("value_proposition", business.get("description", ""))
