"""
Contact email enrichment using Hunter.io API (100 free lookups/month).
Falls back to formatted email guess if Hunter not configured.
"""

import re
import random
import httpx
from backend.config.settings import get_settings

settings = get_settings()


async def find_email(first_name: str, last_name: str, domain: str) -> dict:
    """
    Find verified email via Hunter.io. Falls back to formula.
    Returns: {email, source, confidence, verified}
    """
    if settings.HUNTER_API_KEY:
        result = await _hunter_find(first_name, last_name, domain)
        if result:
            return result

    # Fallback: formula-based email
    first = _clean_name(first_name)
    last = _clean_name(last_name)
    email = f"{first}.{last}@{domain}"

    return {
        "email": email,
        "source": "formula_generated",
        "confidence": 0.55,
        "verified": False,
    }


async def find_emails_by_domain(domain: str) -> list[dict]:
    """
    Get ALL emails Hunter.io has for a domain (domain search endpoint).
    Returns list of {email, first_name, last_name, position, confidence}
    Great for finding real contacts at a company.
    """
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
                result = []
                for e in emails:
                    result.append({
                        "email": e.get("value", ""),
                        "first_name": e.get("first_name", ""),
                        "last_name": e.get("last_name", ""),
                        "position": e.get("position", ""),
                        "confidence": e.get("confidence", 50) / 100,
                        "source": "hunter.io_domain_search",
                        "verified": e.get("verification", {}).get("status") == "valid",
                        "linkedin_url": e.get("linkedin", ""),
                    })
                print(f"[Hunter] Found {len(result)} emails for {domain}")
                return result
            elif resp.status_code == 429:
                print("[Hunter] Rate limit hit")
                return []
    except Exception as e:
        print(f"[Hunter] Domain search error for {domain}: {e}")

    return []


async def _hunter_find(first: str, last: str, domain: str) -> dict | None:
    """Hunter.io email finder endpoint."""
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
                        "source": "hunter.io",
                        "confidence": data.get("score", 50) / 100,
                        "verified": data.get("verification", {}).get("status") == "valid",
                    }
    except Exception as e:
        print(f"[Hunter] Finder error: {e}")
    return None


def _clean_name(name: str) -> str:
    """firstname → lowercase, remove special chars."""
    return re.sub(r'[^a-z]', '', name.lower())


def generate_linkedin_url(first: str, last: str) -> str:
    """Generate LinkedIn profile URL pattern."""
    f = _clean_name(first)
    l = _clean_name(last)
    return f"https://www.linkedin.com/in/{f}-{l}"


def generate_phone() -> str:
    """Generate realistic mock US phone number."""
    area = random.choice([415, 212, 646, 512, 650, 408, 617, 206, 303, 404])
    return f"+1-{area}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
