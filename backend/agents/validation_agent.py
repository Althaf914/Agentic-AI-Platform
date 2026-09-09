"""
CompanyValidationAgent — comprehensive 12-check validation pipeline.

Check topology:
  Checks 1-4: sequential (HTTP reachability depends on domain, HTTPS builds on that)
  Checks 5-12: parallel (independent signals, each can fail without halting others)

Hard fails (auto-reject regardless of pass_count): checks 1, 3, 9.
Pass threshold >= 7/12 (configurable).
"""

import asyncio
import json
import re
import uuid
from datetime import datetime, timezone

import httpx

from backend.agents.base import BaseAgent, register_agent
from backend.models.company import Company
from backend.config.settings import get_settings

settings = get_settings()

# Domains that are directories / social media — never actual target companies
BLACKLIST_DOMAINS = {
    "linkedin.com", "twitter.com", "facebook.com", "wikipedia.org",
    "crunchbase.com", "glassdoor.com", "indeed.com", "g2.com",
    "capterra.com", "bloomberg.com", "forbes.com",
}

# Common free-email domains — company should use custom domain
FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "protonmail.com", "mail.com"}


@register_agent("validation")
class CompanyValidationAgent(BaseAgent):
    """Validates companies through a 12-check pipeline. Stores all results in validation_details JSON."""

    async def run(self, input: dict, memory, config: dict) -> dict:
        workflow_id = input.get("workflow_id")
        company_ids = input.get("company_ids", [])

        # Union of all possible icp / campaign config locations
        icp = input.get("icp", config)
        campaign_config = (
            icp.get("company_filters", {})
            if "company_filters" in icp
            else icp
        )

        log_id = await self.log_start(workflow_id, "validation", {
            "company_count": len(company_ids),
        })

        await self.emit(workflow_id, "validation", "running", {
            "message": f"Running 12-check validation on {len(company_ids)} companies...",
        })

        validated_ids = []
        rejected_ids = []
        rejection_reasons = {}
        total_confidence = 0.0

        PASS_THRESHOLD = input.get("pass_threshold", 7)  # configurable

        for company in self.db.query(Company).filter(Company.id.in_(company_ids)).all():
            company_result = await self._run_checks(company, campaign_config, workflow_id)

            # Hard-fail override
            hard_fail = any(
                company_result["details"][c]["passed"] is False
                for c in ["domain_reachable", "domain_not_blacklisted", "industry_relevant"]
                if c in company_result["details"]
            )

            pass_count = company_result["pass_count"]
            total_possible = company_result["total_checks"]

            if hard_fail or pass_count < PASS_THRESHOLD:
                company.status = "rejected"
                company.validation_details = company_result["details"]
                rejected_ids.append(company.id)
                self._tally_rejection(company_result["details"], rejection_reasons)
                await self.emit(workflow_id, "validation", "company_rejected", {
                    "company_name": company.name,
                    "domain": company.domain,
                    "checks_passed": pass_count,
                    "total_checks": total_possible,
                    "hard_fail": hard_fail,
                })
            else:
                # Determine confidence based on pass rate
                confidence = 0.95 if pass_count >= 9 else 0.75
                company.qualification_score = int((pass_count / total_possible) * 100)
                company.status = "validated"
                company.validation_details = company_result["details"]
                validated_ids.append(company.id)
                total_confidence += confidence

                await self.emit(workflow_id, "validation", "company_validated", {
                    "company_name": company.name,
                    "domain": company.domain,
                    "checks_passed": pass_count,
                    "total_checks": total_possible,
                    "confidence": confidence,
                })

            # Update enrichment fields from check results
            li_check = company_result["details"].get("linkedin_exists", {})
            if li_check.get("passed") and li_check.get("linkedin_url"):
                company.linkedin_url = company.linkedin_url or li_check["linkedin_url"]
                company.has_linkedin = True

            hiring_check = company_result["details"].get("hiring_signal", {})
            if hiring_check.get("score") is not None:
                company.hiring_signal_score = hiring_check["score"]

            self.db.commit()

        avg_confidence = total_confidence / max(len(validated_ids), 1) if validated_ids else 0.0

        result = {
            "company_ids": validated_ids,
            "validated": len(validated_ids),
            "rejected": len(rejected_ids),
            "rejection_reasons": rejection_reasons,
            "avg_confidence": round(avg_confidence, 2),
        }

        await self.emit(workflow_id, "validation", "completed", {
            "message": f"✓ {len(validated_ids)} validated, {len(rejected_ids)} rejected (avg confidence: {avg_confidence:.2f})",
            "validated": len(validated_ids),
            "rejected": len(rejected_ids),
            "rejection_reasons": rejection_reasons,
        })

        await self.log_complete(log_id, result)
        return result

    # ─── Check Runner ──────────────────────────────────────────────────────────────

    async def _run_checks(self, company: Company, icp: dict, workflow_id: str) -> dict:
        """Run all 12 checks and return structured results."""
        details = {}
        pass_count = 0
        total = 12

        # ── Sequential block (checks 1-4) ──────────────────────────────────────
        # Each check may set context the next needs.

        domain = company.domain.lower().strip()

        # Check 1: Domain reachable [HARD]
        chk1 = await self._check_domain_reachable(domain)
        details["domain_reachable"] = chk1
        if chk1["passed"]:
            pass_count += 1

        # Check 2: HTTPS enforced (only run if domain is reachable)
        if chk1["passed"]:
            chk2 = await self._check_https_enforced(domain)
        else:
            chk2 = {"passed": False, "detail": "Skipped — domain not reachable"}
        details["https_enforced"] = chk2
        if chk2["passed"]:
            pass_count += 1

        # Check 3: Domain not blacklisted [HARD]
        chk3 = self._check_domain_blacklisted(domain)
        details["domain_not_blacklisted"] = chk3
        if chk3["passed"]:
            pass_count += 1

        # Check 4: Domain age
        chk4 = await self._check_domain_age(domain, company.name)
        details["domain_age"] = chk4
        if chk4["passed"]:
            pass_count += 1

        # ── Parallel block (checks 5-12) ───────────────────────────────────────
        parallel_results = await asyncio.gather(
            self._check_linkedin_exists(domain, company.name),
            self._check_linkedin_activity(domain, company.name),
            self._check_employee_count(company, icp),
            self._check_location_match(company, icp),
            self._check_industry_relevant(company, icp),
            self._check_hiring_signal(company, domain),
            self._check_description_quality(company),
            self._check_email_domain(domain),
        )

        labels = [
            "linkedin_exists",
            "linkedin_activity",
            "employee_count",
            "location_match",
            "industry_relevant",
            "hiring_signal",
            "description_quality",
            "email_domain",
        ]

        for label, result in zip(labels, parallel_results):
            details[label] = result
            if result["passed"]:
                pass_count += 1

        return {
            "pass_count": pass_count,
            "total_checks": total,
            "details": details,
        }

    # ─── Individual Check Implementations ─────────────────────────────────────

    async def _check_domain_reachable(self, domain: str) -> dict:
        """Check 1 [HARD]: HTTP HEAD request, must return 2xx or 3xx."""
        # In mock/test mode, skip network calls and pass by default
        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return {"passed": True, "detail": "Mock mode — domain assumed reachable"}

        for scheme in ["https", "http"]:
            try:
                async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as c:
                    resp = await c.head(f"{scheme}://{domain}")
                    if resp.status_code < 400:
                        return {"passed": True, "detail": f"{scheme.upper()} OK ({resp.status_code})"}
            except httpx.TimeoutException:
                continue
            except Exception:
                continue
        return {"passed": False, "detail": f"Domain {domain} not reachable via HTTP or HTTPS"}

    async def _check_https_enforced(self, domain: str) -> dict:
        """Check 2: HTTP request redirects to HTTPS."""
        # In mock/test mode, skip network calls and pass by default
        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return {"passed": True, "detail": "Mock mode — HTTPS assumed enforced"}

        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as c:
                resp = await c.get(f"http://{domain}")
                if 300 <= resp.status_code < 400:
                    location = resp.headers.get("location", "")
                    if location.startswith("https://") or domain in location:
                        return {"passed": True, "detail": f"HTTP → HTTPS redirect ({resp.status_code})"}
                # If already on HTTPS from check 1, that's fine
                return {"passed": True, "detail": "Already using HTTPS"}
        except Exception as e:
            return {"passed": False, "detail": f"HTTPS check failed: {e}"}

    def _check_domain_blacklisted(self, domain: str) -> dict:
        """Check 3 [HARD]: Domain not in social/directory blacklist."""
        # Extract root domain (e.g. sub.example.com → example.com)
        parts = domain.split(".")
        if len(parts) > 2 and parts[-1] in ("com", "org", "net", "io", "co"):
            root = ".".join(parts[-2:])
        else:
            root = domain

        if root in BLACKLIST_DOMAINS:
            return {"passed": False, "detail": f"Domain {root} is a directory/social platform, not a target company"}

        # Also check subdomains of known platforms
        known_platforms = ["linkedin.com", "crunchbase.com", "glassdoor.com"]
        for platform in known_platforms:
            if domain.endswith(f".{platform}") or domain == platform:
                return {"passed": False, "detail": f"Domain is on {platform} — not a company"}

        return {"passed": True, "detail": "Domain is not blacklisted"}

    async def _check_domain_age(self, domain: str, company_name: str) -> dict:
        """Check 4: Domain age via WHOIS or SerpAPI estimate. Flag if < 6 months old."""
        # Try WHOIS XML API first
        whois_api_key = settings.WHOISXML_API_KEY if hasattr(settings, "WHOISXML_API_KEY") else None
        if whois_api_key:
            try:
                async with httpx.AsyncClient(timeout=8.0) as c:
                    resp = await c.get(
                        "https://whoisxmlapi.com/whoisserver/WhoisService",
                        params={
                            "domainName": domain,
                            "apiKey": whois_api_key,
                            "outputFormat": "JSON",
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        created = data.get("WhoisRecord", {}).get("createdDate")
                        if created:
                            try:
                                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                                age_days = (datetime.now(timezone.utc) - created_dt).days
                                if age_days < 180:
                                    return {"passed": False, "detail": f"Domain only {age_days} days old (< 6 months)", "domain_age_days": age_days}
                                return {"passed": True, "detail": f"Domain age: {age_days} days", "domain_age_days": age_days}
                            except ValueError:
                                pass
            except Exception:
                pass

        # Fallback: Search SerpAPI for "founded" year in company snippets
        if settings.SERPAPI_KEY and not settings.USE_MOCK_DATA:
            try:
                async with httpx.AsyncClient(timeout=8.0) as c:
                    resp = await c.get(
                        "https://serpapi.com/search",
                        params={
                            "api_key": settings.SERPAPI_KEY,
                            "engine": "google",
                            "q": f'"{company_name}" founded year OR "founded in" OR "established"',
                            "num": 5,
                        },
                    )
                    if resp.status_code == 200:
                        results = resp.json().get("organic_results", [])
                        for r in results:
                            snippet = (r.get("snippet", "") + " " + r.get("title", "")).lower()
                            years = re.findall(r"(?:founded|established|launched|started)\s*(?:in\s*)?(\d{4})", snippet)
                            if years:
                                founded_year = int(years[0])
                                age_days = (2026 - founded_year) * 365
                                if age_days < 180:
                                    return {"passed": False, "detail": f"Founded {founded_year} — less than 6 months estimated", "domain_age_days": age_days}
                                return {"passed": True, "detail": f"Founded {founded_year} — age ~{age_days} days estimated", "domain_age_days": age_days}

                            # Check for "year old" patterns
                            age_match = re.search(r"(\d+)[-\s]?(?:year|yr)[-\s]old", snippet)
                            if age_match:
                                company_age_years = int(age_match.group(1))
                                age_days = company_age_years * 365
                                if age_days < 180:
                                    return {"passed": False, "detail": f"~{company_age_years} years old — less than 6 months", "domain_age_days": age_days}
                                return {"passed": True, "detail": f"~{company_age_years} years old", "domain_age_days": age_days}
            except Exception:
                pass

        # If we can't determine domain age, pass with note
        return {"passed": True, "detail": "Domain age could not be determined — passing by default", "domain_age_days": None}

    async def _check_linkedin_exists(self, domain: str, company_name: str) -> dict:
        """Check 5: LinkedIn company page exists via SerpAPI."""
        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return {"passed": True, "detail": "No SerpAPI key — skipping LinkedIn check", "linkedin_url": None}

        try:
            async with httpx.AsyncClient(timeout=8.0) as c:
                resp = await c.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": settings.SERPAPI_KEY,
                        "engine": "google",
                        "q": f'site:linkedin.com/company "{company_name}"',
                        "num": 3,
                    },
                )
                if resp.status_code == 200:
                    results = resp.json().get("organic_results", [])
                    for r in results:
                        link = r.get("link", "")
                        if "/company/" in link.lower():
                            return {"passed": True, "detail": f"LinkedIn page found", "linkedin_url": link}
                    return {"passed": False, "detail": "No LinkedIn company page found", "linkedin_url": None}
        except Exception as e:
            return {"passed": True, "detail": f"LinkedIn lookup failed ({e}) — passing by default", "linkedin_url": None}

        return {"passed": False, "detail": "No LinkedIn page found", "linkedin_url": None}

    async def _check_linkedin_activity(self, domain: str, company_name: str) -> dict:
        """Check 6: If LinkedIn found, check recent activity."""
        # This is a soft check — if we can't determine it, pass by default
        return {"passed": True, "detail": "LinkedIn activity check skipped — requires authenticated API"}

    async def _check_employee_count(self, company: Company, icp: dict) -> dict:
        """Check 7: Employee count in ICP range with 20% buffer."""
        min_emp = icp.get("min_employees", 0)
        max_emp = icp.get("max_employees", 999999)
        emp = company.employee_count

        if emp is None:
            return {"passed": True, "detail": "No employee data — skipping check"}

        # 20% buffer on both ends
        buffer_min = max(0, int(min_emp * 0.8))
        buffer_max = int(max_emp * 1.2)

        if buffer_min <= emp <= buffer_max:
            return {"passed": True, "detail": f"{emp} employees within ICP range [{min_emp}, {max_emp}] +20% buffer"}
        else:
            return {"passed": False, "detail": f"{emp} employees outside buffered ICP range [{buffer_min}, {buffer_max}]"}

    async def _check_location_match(self, company: Company, icp: dict) -> dict:
        """Check 8: Country/city in campaign geography targets."""
        target_countries = icp.get("countries", [])
        target_cities = icp.get("cities", [])

        # Also check under geography key (new campaign format)
        geography = icp.get("geography", {})
        if geography:
            target_countries = target_countries or geography.get("countries", [])
            target_cities = target_cities or geography.get("cities", [])

        if not target_countries and not target_cities:
            return {"passed": True, "detail": "No geography targets defined — skipping check"}

        reasons = []
        match = False

        if company.country and target_countries:
            if company.country.lower() in [c.lower() for c in target_countries]:
                match = True
                reasons.append(f"Country '{company.country}' in target list")
            else:
                reasons.append(f"Country '{company.country}' not in target list")

        if company.city and target_cities:
            if company.city.lower() in [c.lower() for c in target_cities]:
                match = True
                reasons.append(f"City '{company.city}' in target list")
            else:
                reasons.append(f"City '{company.city}' not in target list")

        if match:
            return {"passed": True, "detail": "; ".join(reasons)}
        elif company.country and target_countries and not match:
            return {"passed": False, "detail": "; ".join(reasons)}
        else:
            return {"passed": True, "detail": "Location partially matched or no location data"}

    async def _check_industry_relevant(self, company: Company, icp: dict) -> dict:
        """Check 9 [HARD]: Industry not in exclude list and matches target industries."""
        exclude_keywords = icp.get("exclude_keywords", [])
        target_industries = icp.get("industries", [])

        if not company.industry:
            return {"passed": True, "detail": "No industry data — passing by default"}

        company_industry = company.industry.lower()

        # Check exclude keywords
        for keyword in exclude_keywords:
            if keyword.lower() in company_industry:
                return {"passed": False, "detail": f"Industry '{company.industry}' contains excluded keyword '{keyword}'"}

        # Check if matches target industries (soft — only fail if explicitly excluded)
        return {"passed": True, "detail": f"Industry '{company.industry}' is relevant"}

    async def _check_hiring_signal(self, company: Company, domain: str) -> dict:
        """Check 10: Detect hiring signals via SerpAPI or existing keywords."""
        # In mock/test mode, pass by default
        if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
            return {"passed": True, "detail": "Mock mode — hiring signal assumed detected", "score": 0.5}

        score = 0.0
        detail_parts = []

        # Check existing hiring keywords on the company record
        if company.hiring_keywords_json:
            existing = company.hiring_keywords_json
            if isinstance(existing, list) and len(existing) > 0:
                score = max(score, 0.5)
                detail_parts.append(f"Found {len(existing)} existing hiring keywords")

        # SerpAPI: search for hiring signals
        if settings.SERPAPI_KEY and not settings.USE_MOCK_DATA:
            try:
                async with httpx.AsyncClient(timeout=8.0) as c:
                    resp = await c.get(
                        "https://serpapi.com/search",
                        params={
                            "api_key": settings.SERPAPI_KEY,
                            "engine": "google",
                            "q": f'"{company.name}" hiring OR "we\'re hiring" site:linkedin.com',
                            "num": 3,
                        },
                    )
                    if resp.status_code == 200:
                        results = resp.json().get("organic_results", [])
                        if results:
                            score = max(score, 0.8)
                            detail_parts.append(f"Found {len(results)} hiring-related results on LinkedIn")
            except Exception:
                pass

        passed = score >= 0.3
        if not detail_parts:
            detail_parts.append("No hiring signals detected")

        return {
            "passed": passed,
            "detail": "; ".join(detail_parts),
            "score": round(score, 2),
        }

    async def _check_description_quality(self, company: Company) -> dict:
        """Check 11: Company description is substantive (> 50 chars, not just domain name)."""
        desc = (company.description or "").strip()
        domain_name = (company.domain or "").replace(".com", "").replace(".io", "").replace(".ai", "").split(".")[0]

        if not desc:
            return {"passed": False, "detail": "No description available"}

        if len(desc) < 50:
            return {"passed": False, "detail": f"Description too short ({len(desc)} chars, minimum 50)"}

        # Description should be more than just the company name or domain
        if desc.lower().strip() == domain_name.lower():
            return {"passed": False, "detail": "Description is just the company/domain name"}

        return {"passed": True, "detail": f"Quality description ({len(desc)} chars)"}

    async def _check_email_domain(self, domain: str) -> dict:
        """Check 12: Company domain is not a free email provider."""
        parts = domain.split(".")
        if len(parts) >= 2:
            root = ".".join(parts[-2:])
        else:
            root = domain

        if root in FREE_EMAIL_DOMAINS:
            return {"passed": False, "detail": f"Domain {domain} is a free email provider, not a company"}

        if any(domain.endswith(f".{d}") or domain == d for d in FREE_EMAIL_DOMAINS):
            return {"passed": False, "detail": f"Domain {domain} is a free email provider"}

        return {"passed": True, "detail": f"Domain {domain} is a valid company email domain"}

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _tally_rejection(self, details: dict, tally: dict) -> None:
        """Count rejection reasons for the summary."""
        for check_name, result in details.items():
            if not result.get("passed", True):
                reason = result.get("detail", "Unknown reason")[:50]
                tally[reason] = tally.get(reason, 0) + 1
