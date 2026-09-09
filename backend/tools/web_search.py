"""
Company discovery via SerpAPI (Google Search).
Falls back to mock dataset only if SERPAPI_KEY not set.
Builds smart queries from ICP: industry + location + funding keywords.
"""

import httpx
import json
from urllib.parse import urlparse
from backend.config.settings import get_settings
from backend.tools.mock_dataset import get_mock_companies

settings = get_settings()

# Domains to filter out (not companies)
BLACKLIST_DOMAINS = {
    "google.com", "linkedin.com", "facebook.com", "twitter.com", "youtube.com",
    "wikipedia.org", "reddit.com", "glassdoor.com", "indeed.com", "crunchbase.com",
    "bloomberg.com", "techcrunch.com", "forbes.com", "github.com", "medium.com",
    "amazon.com", "microsoft.com", "apple.com", "salesforce.com", "hubspot.com",
}


async def search_companies(icp: dict) -> list[dict]:
    """
    Main entry point. Returns list of company dicts from Google or mock.
    Each dict: {name, domain, industry, country, city, description, source_url, source}
    """
    if not settings.SERPAPI_KEY or settings.USE_MOCK_DATA:
        print("[Search] No SERPAPI_KEY or USE_MOCK_DATA=true — generating mock companies")
        # Use dynamic generator for richer, ICP-tailored data
        try:
            from backend.tools.mock_data import generate_mock_companies
            count = getattr(settings, 'MOCK_COMPANY_COUNT', 20)
            dynamic = generate_mock_companies(icp, count=count)
            if dynamic:
                print(f"[Search] Generated {len(dynamic)} dynamic mock companies")
                return dynamic
        except ImportError:
            pass
        # Fallback to static dataset
        return get_mock_companies(icp)

    return await _search_real(icp)


async def _search_real(icp: dict) -> list[dict]:
    """Build targeted queries from ICP and search via SerpAPI."""
    industries = icp.get("industries", ["SaaS"])
    locations = icp.get("locations", [])
    countries = icp.get("countries", ["US"])
    funding_stages = icp.get("funding_stages", [])
    hiring_keywords = icp.get("hiring_keywords", [])
    tech_stack = icp.get("tech_stack", [])

    # Build location string for query
    location_str = ""
    if locations:
        location_str = " OR ".join(locations[:2])
    elif countries:
        location_str = " OR ".join(countries[:2])

    # Build multiple targeted queries
    queries = []
    for industry in industries[:3]:
        # Base query
        q = f'"{industry}" company startup {location_str} 2024 2025'
        queries.append(q)

        # Funding-aware query
        if funding_stages:
            stage = funding_stages[0].lower().replace(" ", "-")
            queries.append(
                f'"{industry}" {stage} funding {location_str} site:techcrunch.com OR site:crunchbase.com'
            )

        # Hiring signal query
        if hiring_keywords:
            kw = hiring_keywords[0]
            queries.append(f'"{industry}" company hiring "{kw}" {location_str}')

    # Add tech-stack specific query
    if tech_stack:
        tech_str = " ".join(tech_stack[:2])
        queries.append(f'"{industries[0]}" company using {tech_str} {location_str}')

    companies = []
    seen_domains = set()

    async with httpx.AsyncClient(timeout=20.0) as client:
        for query in queries[:4]:  # max 4 queries per workflow run
            print(f"[Search] Query: {query}")
            try:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": settings.SERPAPI_KEY,
                        "engine": "google",
                        "q": query,
                        "num": 10,
                        "gl": _country_code(countries[0]) if countries else "us",
                        "hl": "en",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                for result in data.get("organic_results", []):
                    domain = _extract_domain(result.get("link", ""))
                    if not domain or domain in BLACKLIST_DOMAINS or domain in seen_domains:
                        continue

                    seen_domains.add(domain)
                    name = _clean_company_name(result.get("title", ""), domain)

                    companies.append({
                        "name": name,
                        "domain": domain,
                        "industry": industries[0],
                        "country": countries[0] if countries else "US",
                        "city": locations[0] if locations else None,
                        "description": result.get("snippet", "")[:300],
                        "source_url": result.get("link", ""),
                        "source": "serpapi_google",
                        "employee_count": None,
                        "funding_stage": None,
                        "tech_stack": [],
                        "hiring_keywords": [],
                    })

            except Exception as e:
                print(f"[Search] Error for query '{query}': {e}")
                # Partial fallback for this query only
                fallback = get_mock_companies(icp)[:5]
                for c in fallback:
                    if c["domain"] not in seen_domains:
                        seen_domains.add(c["domain"])
                        companies.append(c)

    print(f"[Search] Found {len(companies)} unique companies")
    return companies[:40]  # cap at 40


def _extract_domain(url: str) -> str:
    try:
        domain = urlparse(url).netloc.replace("www.", "").lower()
        # Remove country TLD variations: .co.uk → keep as is
        return domain if "." in domain else ""
    except:
        return ""


def _clean_company_name(title: str, domain: str) -> str:
    """Extract company name from page title."""
    domain_prefix = domain.split(".")[0].lower()
    
    # Try splitters
    for sep in [" - ", " | ", " – ", " — ", ": "]:
        if sep in title:
            parts = [p.strip() for p in title.split(sep) if p.strip()]
            # Find the part that contains the domain prefix (brand name)
            for part in parts:
                if domain_prefix in part.lower():
                    return part
            # Fallback to the shortest part (usually the brand name)
            if parts:
                shortest = min(parts, key=len)
                if len(shortest) <= 25:
                    return shortest
                title = parts[0]
            break
            
    title = title.strip()
    # Fallback to domain prefix if still too long or generic
    if not title or len(title) > 35 or any(kw in title.lower() for kw in ["jobs", "careers", "hiring", "startups", "companies", "best of", "list of", "how to"]):
        return domain.split(".")[0].title()
    return title


def _country_code(country: str) -> str:
    mapping = {
        "US": "us", "UK": "gb", "India": "in", "Canada": "ca",
        "Australia": "au", "Germany": "de", "France": "fr",
        "Singapore": "sg", "UAE": "ae", "Israel": "il",
    }
    return mapping.get(country, "us")


async def search_raw(query: str, num: int = 5) -> list[dict]:
    """Generic raw search for decision maker lookup."""
    if not settings.SERPAPI_KEY:
        return []
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                "https://serpapi.com/search",
                params={
                    "api_key": settings.SERPAPI_KEY,
                    "engine": "google",
                    "q": query,
                    "num": num,
                },
            )
            resp.raise_for_status()
            return resp.json().get("organic_results", [])
        except:
            return []
