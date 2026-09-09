"""
Company enrichment using Clearbit Autocomplete (free, no key needed)
+ additional enrichment via SerpAPI knowledge graph if available.
"""

import re
import httpx
import json
from backend.config.settings import get_settings

settings = get_settings()


async def enrich_company(domain: str, company_name: str = "") -> dict:
    """
    Enrich company details. Returns dict with name, logo, industry, employees, location.
    Uses Clearbit free API — no key needed.
    """
    result = {
        "name": company_name or domain.split(".")[0].title(),
        "domain": domain,
        "logo_url": f"https://logo.clearbit.com/{domain}",
        "industry": None,
        "employee_count": None,
        "city": None,
        "country": None,
        "linkedin_url": None,
        "description": None,
        "enriched": False,
    }

    # Try Clearbit Autocomplete (free)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"https://autocomplete.clearbit.com/v1/companies/suggest",
                params={"query": domain},
            )
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    r = results[0]
                    result["name"] = r.get("name") or result["name"]
                    result["domain"] = r.get("domain") or domain
                    result["logo_url"] = r.get("logo") or result["logo_url"]
                    result["enriched"] = True
                    print(f"[Clearbit] Enriched {domain}: {result['name']}")
    except Exception as e:
        print(f"[Clearbit] Failed for {domain}: {e}")

    # Try SerpAPI knowledge graph for more details
    if settings.SERPAPI_KEY and not result.get("employee_count"):
        try:
            from backend.tools.web_search import search_raw
            kg_results = await search_raw(
                f"{result['name']} company employees location", num=3
            )
            for r in kg_results:
                snippet = r.get("snippet", "").lower()
                # Try to extract employee count from snippet
                emp_match = re.search(r'(\d[\d,]+)\s*(employees|staff|people)', snippet)
                if emp_match:
                    count_str = emp_match.group(1).replace(",", "")
                    result["employee_count"] = int(count_str)
                    break
        except:
            pass

    return result
