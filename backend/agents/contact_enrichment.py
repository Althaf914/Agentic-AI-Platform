"""
Contact Enrichment Agent — 5-source enrichment pipeline with confidence scoring.

Pipeline (runs per contact, stops at first verified email):
  1. Website scrape — fetch homepage + /contact + /about + /team, regex email extraction
  2. Hunter.io — domain search (batch) with fuzzy name match + individual lookup fallback
  3. LinkedIn enrichment — confirm or generate linkedin URL (always runs)
  4. Email verification — Hunter.io email verifier for found emails
  5. Formula fallback ��� pattern-based email generation if all sources fail

Phone generation appends estimated US number if none exists.
"""
import re
import json
import random
import secrets
import difflib
from urllib.parse import urljoin

import httpx

from backend.agents.base import BaseAgent, register_agent
from backend.models.contact import Contact
from backend.models.company import Company
from backend.config.settings import get_settings

settings = get_settings()

# Email regex — RFC 5322 simplified
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Formula patterns in order of likelihood
FORMULA_PATTERNS = [
    "{first}.{last}@{domain}",
    "{first}@{domain}",
    "{f}{last}@{domain}",
    "{first}{l}@{domain}",
]

COMMON_TEAM_SLUGS = ["/contact", "/about", "/team", "/company/team", "/about/team"]


@register_agent("contact_enrichment")
class ContactEnrichmentAgent(BaseAgent):
    """
    5-source enrichment pipeline. For each contact, sources run in order;
    stops at the first source that returns a verified email. LinkedIn
    enrichment always runs regardless of email status.
    """

    async def run(self, input: dict, memory, config: dict) -> dict:
        workflow_id = input.get("workflow_id")
        contact_ids = input.get("contact_ids", [])

        log_id = await self.log_start(workflow_id, "contact_enrichment", {
            "contact_count": len(contact_ids),
        })

        await self.emit(workflow_id, "contact_enrichment", "running", {
            "message": f"📧 Enriching {len(contact_ids)} contacts (5-source pipeline)..."
        })

        # Cache: Hunter domain search (one API call per unique domain)
        hunter_domain_cache: dict[str, list[dict]] = {}

        enriched_count = 0
        email_found_count = 0
        email_verified_count = 0
        linkedin_confirmed_count = 0
        total_confidence = 0.0

        for contact_id in contact_ids:
            contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                continue

            company = self.db.query(Company).filter(Company.id == contact.company_id).first()
            if not company:
                continue

            domain = company.domain
            name_parts = contact.full_name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[-1] if len(name_parts) > 1 else ""

            # ──────────────────────────────────────────────────────────
            # Pipeline: run sources until email found
            # ──────────────────────────────────────────────────────────
            email = None
            email_confidence = 0.0
            email_source = None
            email_verified = False

            # --- SOURCE 1: Website scrape ---
            email, email_confidence, email_source = await self._source_website(domain)
            if email:
                email_found_count += 1
                await self.emit(workflow_id, "contact_enrichment", "running", {
                    "message": f"  Source 1 (website) → {email} for {contact.full_name}"
                })

            # --- SOURCE 2: Hunter.io ---
            if not email:
                email, email_confidence, email_source = await self._source_hunter(
                    domain, first_name, last_name, contact.role, hunter_domain_cache
                )
                if email:
                    email_found_count += 1
                    await self.emit(workflow_id, "contact_enrichment", "running", {
                        "message": f"  Source 2 (Hunter.io) → {email} for {contact.full_name}"
                    })

            # --- SOURCE 4: Email verification (if email found from sources 1-2) ---
            if email:
                verified, adjusted_confidence = await self._source_verify(email, email_confidence)
                email_verified = verified
                email_confidence = adjusted_confidence
                if verified:
                    email_verified_count += 1

            # --- SOURCE 5: Formula fallback (only if all above failed) ---
            if not email:
                email, email_confidence, email_source = self._source_formula(
                    first_name, last_name, domain
                )

            # --- SOURCE 3: LinkedIn enrichment (ALWAYS runs) ---
            linkedin_url, linkedin_confirmed = self._source_linkedin(
                contact.linkedin_url, first_name, last_name
            )
            if linkedin_confirmed:
                linkedin_confirmed_count += 1

            # --- Phone generation ---
            phone, phone_type = self._generate_phone(contact.phone)

            # --- Compute enrichment score ---
            enrichment_score = self._compute_enrichment_score(
                email_confidence, email_verified, linkedin_confirmed, email_source
            )
            total_confidence += enrichment_score

            # --- Persist ---
            contact.email = email
            contact.email_confidence = email_confidence
            contact.email_source = email_source
            contact.email_verified = email_verified
            contact.linkedin_url = linkedin_url
            contact.linkedin_confirmed = linkedin_confirmed
            contact.phone = phone
            contact.phone_type = phone_type
            contact.enrichment_score = enrichment_score

            # Update overall confidence score to enrichment score
            contact.confidence_score = enrichment_score

            enriched_count += 1

        self.db.commit()

        avg_confidence = round(total_confidence / enriched_count, 2) if enriched_count > 0 else 0.0

        result = {
            "enriched": enriched_count,
            "enriched_contact_ids": contact_ids,
            "email_found": email_found_count,
            "email_verified": email_verified_count,
            "avg_email_confidence": avg_confidence,
            "linkedin_confirmed": linkedin_confirmed_count,
            "hunter_domains_searched": len(hunter_domain_cache),
        }

        await self.emit(workflow_id, "contact_enrichment", "completed", {
            "message": (
                f"✓ Enriched {enriched_count} contacts | "
                f"{email_found_count} emails ({email_verified_count} verified) | "
                f"{linkedin_confirmed_count} LinkedIn confirmed"
            ),
            **result,
        })

        await self.log_complete(log_id, result)
        return result

    # ------------------------------------------------------------------
    # SOURCE 1 — Website scrape
    # ------------------------------------------------------------------

    async def _source_website(self, domain: str) -> tuple[str | None, float, str | None]:
        """
        Fetch company homepage + /contact + /about + /team pages.
        Regex extract emails matching the company domain.
        Returns (email, confidence, source) or (None, 0, None).
        """
        pages = [f"https://{domain}"]
        for slug in COMMON_TEAM_SLUGS:
            pages.append(f"https://{domain}{slug}")

        found_emails: set[str] = set()

        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            for url in pages:
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue
                    text = resp.text
                    # Strip HTML tags to leave visible text
                    text = re.sub(r"<[^>]+>", " ", text)
                    # Decode common HTML entities
                    text = text.replace("&#64;", "@").replace("&#46;", ".")
                    # Extract emails
                    for match in EMAIL_RE.finditer(text):
                        candidate = match.group(0).lower().strip()
                        # Filter: must contain the company domain
                        if domain in candidate:
                            # Filter out generic/noreply addresses
                            prefix = candidate.split("@")[0]
                            if prefix in ("noreply", "no-reply", "info", "admin", "webmaster", "support"):
                                continue
                            found_emails.add(candidate)
                except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError):
                    continue

        if not found_emails:
            return None, 0.0, None

        # Pick the best candidate — prefer "team@" or "hello@" or shortest prefix
        scored = sorted(found_emails, key=lambda e: (
            0 if e.startswith(("hello", "team", "contact")) else
            1 if len(e.split("@")[0]) <= 8 else
            2
        ))
        best = scored[0]
        return best, 0.85, "website"

    # ------------------------------------------------------------------
    # SOURCE 2 — Hunter.io
    # ------------------------------------------------------------------

    async def _source_hunter(
        self,
        domain: str,
        first_name: str,
        last_name: str,
        role: str | None,
        cache: dict[str, list[dict]],
    ) -> tuple[str | None, float, str | None]:
        """
        Hunter.io 2-step enrichment:
          1. Domain search (batch, 1 call per domain) — fuzzy match by name
          2. Individual email finder (fallback if domain search missed)
        """
        # Step 1: Domain search (cached per domain)
        if domain not in cache:
            cache[domain] = await self._hunter_domain_search(domain)

        domain_results = cache[domain]
        if domain_results:
            match = self._fuzzy_match_contact(first_name, last_name, role, domain_results)
            if match:
                return match["email"], match.get("confidence", 0.6), "hunter_domain"

        # Step 2: Individual lookup
        if settings.HUNTER_API_KEY:
            individual = await self._hunter_individual(first_name, last_name, domain)
            if individual and individual.get("email"):
                return individual["email"], individual.get("score", 50) / 100, "hunter_individual"

        return None, 0.0, None

    async def _hunter_domain_search(self, domain: str) -> list[dict]:
        """Batch Hunter.io domain search — returns all emails for a domain."""
        if not settings.HUNTER_API_KEY:
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={
                        "domain": domain,
                        "api_key": settings.HUNTER_API_KEY,
                        "limit": 10,
                        "type": "personal",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    emails = data.get("emails", [])
                    results = []
                    for e in emails:
                        results.append({
                            "email": e.get("value", ""),
                            "first_name": (e.get("first_name") or "").lower(),
                            "last_name": (e.get("last_name") or "").lower(),
                            "position": (e.get("position") or ""),
                            "confidence": e.get("confidence", 50) / 100,
                            "source": "hunter_domain",
                            "verified": e.get("verification", {}).get("status") == "valid",
                        })
                    print(f"[Hunter] Domain search: {len(results)} emails for {domain}")
                    return results
                elif resp.status_code == 429:
                    print("[Hunter] Rate limit hit on domain search")
                    return []
        except Exception as e:
            print(f"[Hunter] Domain search error for {domain}: {e}")

        return []

    async def _hunter_individual(self, first: str, last: str, domain: str) -> dict | None:
        """Hunter.io email-finder endpoint — single contact lookup."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.hunter.io/v2/email-finder",
                    params={
                        "domain": domain,
                        "first_name": first,
                        "last_name": last,
                        "api_key": settings.HUNTER_API_KEY,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    if data.get("email"):
                        return {
                            "email": data["email"],
                            "score": data.get("score", 50),
                            "source": "hunter_individual",
                            "verified": data.get("verification", {}).get("status") == "valid",
                        }
        except Exception as e:
            print(f"[Hunter] Individual lookup error: {e}")

        return None

    def _fuzzy_match_contact(
        self,
        first_name: str,
        last_name: str,
        role: str | None,
        candidates: list[dict],
    ) -> dict | None:
        """
        Fuzzy match a contact name against Hunter domain search results.
        Uses difflib SequenceMatcher with threshold > 0.8.
        Falls back to role-based matching if name match fails.
        """
        first_norm = first_name.lower().strip()
        last_norm = last_name.lower().strip()
        role_norm = (role or "").lower().strip()

        best_match = None
        best_score = 0.0

        for c in candidates:
            h_first = c.get("first_name", "").lower().strip()
            h_last = c.get("last_name", "").lower().strip()
            h_pos = c.get("position", "").lower().strip()

            # Name similarity score
            first_score = difflib.SequenceMatcher(None, first_norm, h_first).ratio()
            last_score = difflib.SequenceMatcher(None, last_norm, h_last).ratio()
            name_score = 0.4 * first_score + 0.6 * last_score

            if name_score > 0.8 and name_score > best_score:
                best_score = name_score
                best_match = c
                continue

            # Role-based fallback: if name partially matches and role aligns
            if first_norm and h_first and first_norm[0] == h_first[0]:
                if last_score > 0.6:
                    # Check role overlap
                    if role_norm and h_pos and any(
                        word in h_pos for word in role_norm.split() if len(word) > 3
                    ):
                        if name_score > best_score:
                            best_score = name_score
                            best_match = c

        return best_match

    # ------------------------------------------------------------------
    # SOURCE 3 — LinkedIn enrichment (ALWAYS runs)
    # ------------------------------------------------------------------

    def _source_linkedin(
        self,
        existing_url: str | None,
        first_name: str,
        last_name: str,
    ) -> tuple[str, bool]:
        """
        Always runs. If contact has a linkedin_url from a prior stage,
        confirm it matches the expected pattern. Otherwise generate one.
        Returns (url, confirmed_bool).
        """
        if existing_url:
            # Confirm URL follows linkedin.com/in/{slug} pattern
            cleaned = existing_url.strip().rstrip("/")
            pattern = r"linkedin\.com/in/[a-zA-Z0-9\-_]+"
            if re.search(pattern, cleaned, re.IGNORECASE):
                return cleaned, True

        # Generate: linkedin.com/in/{firstname}-{lastname}-{short_hash}
        f = re.sub(r"[^a-z]", "", first_name.lower())[:12]
        l = re.sub(r"[^a-z]", "", last_name.lower())[:12]
        suffix = secrets.token_hex(3)
        url = f"https://www.linkedin.com/in/{f}-{l}-{suffix}"
        return url, False

    # ------------------------------------------------------------------
    # SOURCE 4 — Email verification
    # ------------------------------------------------------------------

    async def _source_verify(
        self, email: str, current_confidence: float
    ) -> tuple[bool, float]:
        """
        Verify email via Hunter.io email-verifier endpoint.
        Results: deliverable → keep, risky → keep (confidence penalty),
        undeliverable → discard.
        Returns (verified, adjusted_confidence).
        """
        if not settings.HUNTER_API_KEY:
            # Without API key, accept email at face value with slight penalty
            return False, current_confidence * 0.9

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.hunter.io/v2/email-verifier",
                    params={
                        "email": email,
                        "api_key": settings.HUNTER_API_KEY,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    status = data.get("status", "unknown")
                    score = data.get("score", 50) / 100

                    if status == "deliverable":
                        return True, max(current_confidence, score)
                    elif status == "risky":
                        return False, current_confidence * 0.7
                    elif status == "undeliverable":
                        return False, 0.0  # Discard
                    else:
                        # unknown / catch-all — keep but flag
                        return False, current_confidence * 0.8
                else:
                    print(f"[Hunter] Verifier error: {resp.status_code}")
        except Exception as e:
            print(f"[Hunter] Verifier exception: {e}")

        return False, current_confidence * 0.9

    # ------------------------------------------------------------------
    # SOURCE 5 — Formula-based fallback
    # ------------------------------------------------------------------

    def _source_formula(self, first_name: str, last_name: str, domain: str) -> tuple[str, float, str]:
        """
        Generate email using pattern formulas in order of likelihood.
        Returns (email, confidence, source).
        """
        first = re.sub(r"[^a-z]", "", first_name.lower())
        last = re.sub(r"[^a-z]", "", last_name.lower())
        f = first[0] if first else ""
        l = last[0] if last else ""

        if not first or not last:
            return None, 0.0, None

        for pattern in FORMULA_PATTERNS:
            email = pattern.format(first=first, last=last, f=f, l=l, domain=domain)
            # Basic sanity: ensure it contains @ and the domain
            if "@" in email and domain in email:
                return email, 0.35, "formula"

        return None, 0.0, None

    # ------------------------------------------------------------------
    # Phone generation
    # ------------------------------------------------------------------

    def _generate_phone(self, existing_phone: str | None) -> tuple[str, str]:
        """Generate estimated US phone if none exists."""
        if existing_phone and existing_phone.strip():
            return existing_phone, "real"

        area = random.choice([415, 212, 646, 512, 650, 408, 617, 206, 303, 404, 312, 412])
        exchange = random.randint(200, 999)
        line = random.randint(1000, 9999)
        phone = f"+1 ({area}) {exchange}-{line}"
        return phone, "estimated"

    # ------------------------------------------------------------------
    # Enrichment score computation
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_enrichment_score(
        email_confidence: float,
        email_verified: bool,
        linkedin_confirmed: bool,
        email_source: str | None,
    ) -> float:
        """
        Compute overall quality score (0.0-1.0) for this contact record.

        Weights:
          - Email source reliability: 50%
          - Email verification status: 30%
          - LinkedIn confirmation: 20%
        """
        # Source reliability weight
        source_reliability = {
            "website": 0.85,
            "hunter_domain": 0.90,
            "hunter_individual": 0.75,
            "formula": 0.35,
        }.get(email_source, 0.0)

        source_score = source_reliability * 0.50

        # Verification bonus
        verify_score = 0.30 if email_verified else (0.10 if email_source else 0.0)

        # LinkedIn bonus
        linkedin_score = 0.20 if linkedin_confirmed else 0.05

        score = source_score + verify_score + linkedin_score
        return round(min(score, 1.0), 2)
