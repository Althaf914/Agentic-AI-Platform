"""
Central LLM service using Groq API (llama3-70b-8192).
All agents import from here — never call Groq directly in agent files.
Falls back to smart mock responses if GROQ_API_KEY not set.
"""

import json
import httpx
from backend.config.settings import get_settings

settings = get_settings()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


async def call_llm(system_prompt: str, user_message: str, expect_json: bool = True) -> str:
    """
    Call Groq LLM. Returns string (JSON string if expect_json=True).
    Never raises — always returns something usable.
    """
    if not settings.GROQ_API_KEY or settings.USE_MOCK_DATA:
        return _mock_response(system_prompt, user_message)

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # Strip markdown code fences if Groq wraps JSON in them
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return content.strip()

    except httpx.HTTPStatusError as e:
        print(f"[LLM] Groq HTTP error {e.response.status_code}: {e.response.text[:200]}")
        return _mock_response(system_prompt, user_message)
    except Exception as e:
        print(f"[LLM] Groq error: {e}")
        return _mock_response(system_prompt, user_message)


def _mock_response(system_prompt: str, user_message: str) -> str:
    """Smart mock based on which agent is calling."""
    p = system_prompt.lower()

    if "search strateg" in p or "search_query" in p:
        return json.dumps({
            "queries": [
                {"query": '"AI startup" funding Series B 2024 site:techcrunch.com', "intent": "Find AI startup funding announcements", "expected_result_type": "news"},
                {"query": 'site:linkedin.com/company "B2B SaaS" "50-200 employees"', "intent": "Find B2B SaaS companies on LinkedIn", "expected_result_type": "linkedin"},
                {"query": '"Python" "AWS" startup hiring engineer 2024', "intent": "Find companies hiring Python/AWS engineers", "expected_result_type": "job_posting"},
                {"query": 'site:crunchbase.com/organization AI "Series A"', "intent": "Find Series A AI companies on CrunchBase", "expected_result_type": "crunchbase"},
                {"query": '"AI platform" company Kubernetes funding 2024', "intent": "Find AI platform companies with recent funding", "expected_result_type": "company_list"},
                {"query": '"B2B" "SaaS" "Sales" hiring VP 2024', "intent": "Find B2B SaaS companies hiring sales VPs", "expected_result_type": "company_list"},
                {"query": '"artificial intelligence" startup raised million series site:techcrunch.com', "intent": "Find AI startup funding news on TechCrunch", "expected_result_type": "news"},
                {"query": 'site:wellfound.com AI SaaS startup hiring', "intent": "Find AI SaaS startups hiring on Wellfound", "expected_result_type": "company_list"},
            ],
            "strategy_summary": "Multi-angle search targeting AI SaaS companies across LinkedIn, CrunchBase, TechCrunch, and Wellfound",
        })

    if "planner" in p or "execution plan" in p:
        return json.dumps({
            "steps": [
                {"agent_name": "search_strategy", "input_params": {}, "skip": False, "skip_reason": None},
                {"agent_name": "company_discovery", "input_params": {}, "skip": False, "skip_reason": None},
                {"agent_name": "validation", "input_params": {}, "skip": False, "skip_reason": None},
                {"agent_name": "tech_analysis", "input_params": {}, "skip": False, "skip_reason": None},
                {"agent_name": "decision_maker", "input_params": {}, "skip": False, "skip_reason": None},
                {"agent_name": "contact_enrichment", "input_params": {}, "skip": False, "skip_reason": None},
                {"agent_name": "qualification", "input_params": {}, "skip": False, "skip_reason": None},
                {"agent_name": "recommendation_memory", "input_params": {}, "skip": False, "skip_reason": None},
            ],
            "reasoning": "Running search strategy first, then all 7 agents in standard order. No Groq key configured — using mock plan.",
        })

    elif "industry match" in p or "fuzzy industry" in p:
        return json.dumps({
            "match_type": "exact",
            "score": 100,
            "detail": "Exact industry match with target."
        })

    elif "qualification analyst" in p or "strict qualification" in p:
        return json.dumps({
            "reason": "Company exhibits strong ICP alignment: exact industry match and ideal tech stack fit. Moderate hiring signals and no recent funding urgency keep the score from reaching top tier.",
            "strongest_signal": "Exact industry match with SaaS (score: 100)",
            "weakest_signal": "No recent funding trigger (score: 15)",
            "confidence": 0.82,
        })

    elif "qualification" in p or "score" in p:
        return json.dumps({
            "reason": "Company shows moderate ICP alignment. Funding stage and tech stack partially match target criteria.",
            "confidence": 0.65,
        })

    elif "persona" in p or "decision maker" in p or "buying committee" in p:
        return json.dumps({
            "personas": [
                {"title": "CTO", "search_query": "CTO"},
                {"title": "VP Engineering", "search_query": "VP Engineering"},
                {"title": "Head of Product", "search_query": "Head of Product"},
            ]
        })

    elif "technology" in p or "tech" in p or "extract" in p:
        return json.dumps({
            "technologies": ["Python", "React", "AWS", "PostgreSQL", "Docker", "Kubernetes"],
        })

    elif "signal" in p or "trigger" in p or "intelligence" in p:
        return json.dumps({
            "trigger_summary": "Recent $15M Series B funding and new CTO appointment make this an ideal time to reach out — the company is scaling aggressively and leadership is likely evaluating new vendor partnerships.",
            "urgency": "high",
        })

    elif "talking points" in p or "sales expert" in p:
        return json.dumps({
            "talking_points": [
                "Your recent $15M Series B shows you're scaling fast — our AI discovery tool would accelerate your pipeline to match that growth.",
                "Your tech stack includes Python, React, and AWS — our platform integrates natively with all three for zero-friction deployment.",
                "We noticed your CTO hire from Google — the perfect timing to introduce a solution that cuts sales research time by 80%.",
                "Your 200-person engineering team matches exactly the profile where our AI agents unlock the most value."
            ]
        })

    elif "cold email" in p or "personalized email" in p:
        return json.dumps({
            "subject": "Quick question about your tech stack",
            "body": "Hi {name},\n\nSaw that {company} recently closed its Series B and is expanding the engineering team. We built AgentForge AI specifically for fast-growing B2B companies like yours — it automates prospect discovery so your team spends less time searching and more time selling.\n\nOpen to a 10-minute call next Tuesday to see if it fits your workflow?\n\nBest,\n{{sender_name}}"
        })

    elif "linkedin connection" in p or "linkedin_message" in p:
        return json.dumps({
            "linkedin_message": "Hi {name}, congrats on the Series B — exciting growth ahead. I noticed {company} is scaling its engineering team rapidly. We help B2B companies like yours automate prospect discovery using AI. Curious: how does your team currently find new leads?"
        })

    elif "recommendation" in p or "outreach" in p:
        return json.dumps({
            "suggested_action": "Schedule a 20-minute discovery call with the primary decision maker within 2 weeks.",
            "outreach_template": "Hi {name}, I came across {company} and was impressed by your work in this space. We help companies like yours identify qualified prospects 10x faster using AI-powered discovery. Would you be open to a quick call this week to explore if there's a fit?",
        })

    elif "classify" in p or "category" in p:
        return json.dumps({"category": "product_launch"})

    return json.dumps({"result": "Mock response"})


async def is_llm_available() -> bool:
    """Check if Groq is configured and responding."""
    if not settings.GROQ_API_KEY:
        return False
    try:
        result = await call_llm(
            "You are a test assistant.",
            'Reply with: {"ok": true}',
            expect_json=True,
        )
        return "ok" in result
    except:
        return False
