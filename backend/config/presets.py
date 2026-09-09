"""
Preset configurations for AgentForge AI — B2B SaaS, Staffing, Cybersecurity.
"""

PRESET_CONFIGS = {
    "b2b_saas": {
        "icp": {
            "industries": ["SaaS", "Cloud", "Developer Tools"],
            "countries": ["US", "UK", "Canada"],
            "min_employees": 50,
            "max_employees": 5000,
            "funding_stages": ["Series A", "Series B", "Series C"],
            "tech_stack": ["Python", "React", "AWS", "Kubernetes"],
            "hiring_keywords": ["engineer", "product", "growth"],
        },
        "personas": [
            {
                "name": "CTO",
                "role_keywords": ["CTO", "Chief Technology Officer"],
                "departments": ["Engineering"],
                "priority": 1,
            },
            {
                "name": "VP Engineering",
                "role_keywords": ["VP Engineering", "Head of Engineering"],
                "departments": ["Engineering"],
                "priority": 2,
            },
        ],
        "scoring": {
            "funding_weight": 20,
            "hiring_weight": 20,
            "revenue_weight": 15,
            "icp_match_weight": 25,
            "tech_stack_weight": 10,
            "growth_weight": 10,
        },
    },
    "staffing": {
        "icp": {
            "industries": ["HR", "Recruiting", "Staffing", "Talent"],
            "countries": ["US", "UK", "Australia"],
            "min_employees": 10,
            "max_employees": 500,
            "funding_stages": ["Seed", "Series A"],
            "tech_stack": ["ATS", "Salesforce", "LinkedIn"],
            "hiring_keywords": ["recruiter", "talent", "HR"],
        },
        "personas": [
            {
                "name": "Head of Talent",
                "role_keywords": ["Head of Talent", "Talent Director"],
                "departments": ["HR"],
                "priority": 1,
            },
            {
                "name": "CEO",
                "role_keywords": ["CEO", "Founder", "Managing Director"],
                "departments": ["Executive"],
                "priority": 2,
            },
        ],
        "scoring": {
            "funding_weight": 10,
            "hiring_weight": 30,
            "revenue_weight": 20,
            "icp_match_weight": 25,
            "tech_stack_weight": 5,
            "growth_weight": 10,
        },
    },
    "cybersecurity": {
        "icp": {
            "industries": ["Cybersecurity", "InfoSec", "Network Security"],
            "countries": ["US", "Israel", "UK"],
            "min_employees": 20,
            "max_employees": 2000,
            "funding_stages": ["Seed", "Series A", "Series B"],
            "tech_stack": ["SIEM", "Zero Trust", "Cloud Security"],
            "hiring_keywords": ["security", "CISO", "compliance"],
        },
        "personas": [
            {
                "name": "CISO",
                "role_keywords": ["CISO", "Chief Security Officer"],
                "departments": ["Security"],
                "priority": 1,
            },
            {
                "name": "VP Security",
                "role_keywords": ["VP Security", "Head of Security"],
                "departments": ["Security"],
                "priority": 2,
            },
        ],
        "scoring": {
            "funding_weight": 15,
            "hiring_weight": 15,
            "revenue_weight": 15,
            "icp_match_weight": 30,
            "tech_stack_weight": 15,
            "growth_weight": 10,
        },
    },
}


def get_preset(name: str) -> dict:
    """
    Get a preset configuration by name.
    Raises ValueError if name not found.
    """
    if name not in PRESET_CONFIGS:
        raise ValueError(
            f"Preset '{name}' not found. Available: {list(PRESET_CONFIGS.keys())}"
        )
    return PRESET_CONFIGS[name]
