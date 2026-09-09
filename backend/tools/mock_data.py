"""
Dynamic mock data generator for AgentForge AI.

When USE_MOCK_DATA=true or SERPAPI_KEY is empty, this module generates
realistic companies matching the campaign ICP — no external API keys needed.
"""

import random
import uuid
from datetime import datetime, timezone, timedelta

# ─── Seeded randomness for reproducibility ──────────────────────────────────

_rng = random.Random(42)


def _reseed():
    """Re-seed for each generation call so the output varies by timestamp."""
    _rng.seed(datetime.now(timezone.utc).timestamp())


# ─── Industry-linked data pools ────────────────────────────────────────────

INDUSTRIES = [
    "SaaS", "Fintech", "HealthTech", "CyberSecurity",
    "EdTech", "HRTech", "ECommerce", "EnterpriseSoftware",
    "AI/ML", "CloudInfrastructure", "DataAnalytics", "IoT",
    "AdTech", "LegalTech", "RealEstateTech", "CleanTech",
]

INDUSTRY_TECH_STACKS: dict[str, list[list[str]]] = {
    "SaaS": [
        ["Python", "FastAPI", "React", "PostgreSQL", "Redis"],
        ["TypeScript", "Next.js", "Prisma", "Vercel", "Stripe"],
        ["Go", "gRPC", "Kubernetes", "MongoDB", "Terraform"],
        ["Ruby", "Rails", "Sidekiq", "PostgreSQL", "Redis"],
        ["Node.js", "Express", "React", "MongoDB", "Docker"],
    ],
    "Fintech": [
        ["Java", "Spring Boot", "Kafka", "PostgreSQL", "Docker"],
        ["Kotlin", "AWS", "React", "Redis", "Terraform"],
        ["Python", "FastAPI", "Kafka", "TimescaleDB", "Kubernetes"],
        ["Rust", "AWS Lambda", "DynamoDB", "React", "CDK"],
        ["Go", "gRPC", "Redis", "PostgreSQL", "Istio"],
    ],
    "HealthTech": [
        ["Python", "PyTorch", "FastAPI", "PostgreSQL", "GCP"],
        ["TypeScript", "React", "Node.js", "MongoDB", "AWS"],
        ["Python", "Django", "React", "HIPAA", "AWS"],
        ["Swift", "Kotlin", "Firebase", "Node.js", "GCP"],
        ["Java", "Spring", "React", "Elasticsearch", "Docker"],
    ],
    "CyberSecurity": [
        ["Rust", "Python", "Elasticsearch", "Docker", "AWS"],
        ["Go", "Kubernetes", "Redis", "PostgreSQL", "Terraform"],
        ["C++", "Python", "AWS", "Kubernetes", "Chrome"],
        ["Python", "GCP", "TensorFlow", "Go", "Elasticsearch"],
        ["Rust", "AWS", "Lambda", "DynamoDB", "React"],
    ],
    "EdTech": [
        ["Python", "Django", "React", "PostgreSQL", "Docker"],
        ["TypeScript", "Next.js", "Supabase", "Vercel", "Tailwind"],
        ["Java", "Spring", "Angular", "MongoDB", "AWS"],
        ["React Native", "Firebase", "Node.js", "GCP"],
        ["Python", "FastAPI", "React", "Docker", "Redis"],
    ],
    "HRTech": [
        ["Python", "TensorFlow", "React", "PostgreSQL", "Redis"],
        ["Ruby", "Rails", "PostgreSQL", "Heroku", "React"],
        ["Python", "FastAPI", "React", "ChromaDB", "Docker"],
        ["TypeScript", "React", "Node.js", "PostgreSQL", "Tailwind"],
        ["Java", "Spring", "Angular", "MySQL", "Docker"],
    ],
    "ECommerce": [
        ["Python", "Django", "PostgreSQL", "Redis", "Celery"],
        ["Ruby", "Rails", "Sidekiq", "PostgreSQL", "Stimulus"],
        ["TypeScript", "Next.js", "Prisma", "PostgreSQL", "Vercel"],
        ["Java", "Spring Boot", "Kafka", "MongoDB", "Docker"],
        ["Go", "React", "PostgreSQL", "Redis", "Kubernetes"],
    ],
    "EnterpriseSoftware": [
        ["Java", "Spring", "PostgreSQL", "Kubernetes", "Kafka"],
        ["C#", ".NET Core", "SQL Server", "Azure", "React"],
        ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
        ["Go", "gRPC", "Kubernetes", "MongoDB", "Terraform"],
        ["TypeScript", "Node.js", "PostgreSQL", "Docker", "AWS"],
    ],
    "AI/ML": [
        ["Python", "PyTorch", "FastAPI", "PostgreSQL", "GCP"],
        ["Python", "TensorFlow", "Kubernetes", "Redis", "AWS"],
        ["TypeScript", "Next.js", "Python", "ChromaDB", "Vercel"],
        ["Python", "JAX", "Flax", "GCP", "Docker"],
        ["Rust", "Python", "ONNX", "Kubernetes", "AWS"],
    ],
    "CloudInfrastructure": [
        ["Go", "Kubernetes", "Terraform", "Redis", "AWS"],
        ["Rust", "AWS CDK", "TypeScript", "DynamoDB", "Docker"],
        ["Python", "Django", "PostgreSQL", "GCP", "Prometheus"],
        ["Java", "Spring", "Kafka", "Cassandra", "Docker"],
        ["Go", "gRPC", "etcd", "Redis", "Linux"],
    ],
    "DataAnalytics": [
        ["Python", "Spark", "Kafka", "PostgreSQL", "AWS"],
        ["Scala", "Spark", "Flink", "Kafka", "Hadoop"],
        ["TypeScript", "React", "Node.js", "ClickHouse", "Docker"],
        ["Python", "Dask", "FastAPI", "Redis", "GCP"],
        ["R", "Python", "Shiny", "PostgreSQL", "Docker"],
    ],
    "IoT": [
        ["Rust", "MQTT", "InfluxDB", "Docker", "Azure"],
        ["Python", "C++", "AWS IoT", "DynamoDB", "Kafka"],
        ["Go", "gRPC", "TimescaleDB", "Redis", "Arduino"],
        ["TypeScript", "Node.js", "MQTT", "PostgreSQL", "GCP"],
        ["Python", "TensorFlow Lite", "Docker", "AWS", "React"],
    ],
    "AdTech": [
        ["Go", "Kafka", "Redis", "PostgreSQL", "AWS"],
        ["Python", "FastAPI", "Redis", "Kafka", "GCP"],
        ["Java", "Spring", "Cassandra", "Kafka", "React"],
        ["C++", "Python", "AWS", "Redis", "Docker"],
        ["Rust", "Kafka", "ClickHouse", "Docker", "AWS"],
    ],
    "LegalTech": [
        ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        ["TypeScript", "Next.js", "Supabase", "Vercel", "OpenAI"],
        ["Java", "Spring", "Elasticsearch", "PostgreSQL", "AWS"],
        ["Python", "Django", "React", "Docker", "GCP"],
        ["Ruby", "Rails", "PostgreSQL", "Heroku", "React"],
    ],
    "RealEstateTech": [
        ["Python", "Django", "PostgreSQL", "Redis", "Docker"],
        ["TypeScript", "React", "Node.js", "MongoDB", "AWS"],
        ["Ruby", "Rails", "PostgreSQL", "Heroku", "React"],
        ["Java", "Spring", "PostgreSQL", "GCP", "Docker"],
        ["Python", "FastAPI", "React", "PostgreSQL", "Kubernetes"],
    ],
    "CleanTech": [
        ["Python", "Django", "PostgreSQL", "AWS", "Docker"],
        ["Rust", "Python", "InfluxDB", "GCP", "Kubernetes"],
        ["TypeScript", "React", "Node.js", "PostgreSQL", "Tailwind"],
        ["Python", "FastAPI", "React", "TimescaleDB", "Docker"],
        ["Go", "gRPC", "PostgreSQL", "Redis", "IoT"],
    ],
}

# Fallback tech stacks for unknown industries
FALLBACK_TECH_STACKS = [
    ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
    ["TypeScript", "Next.js", "Node.js", "MongoDB", "AWS"],
    ["Go", "Kubernetes", "Redis", "PostgreSQL", "Terraform"],
    ["Java", "Spring Boot", "React", "Kafka", "Docker"],
    ["Ruby", "Rails", "Sidekiq", "PostgreSQL", "Redis"],
]

COMPANY_PREFIXES = [
    "Cloud", "Data", "Smart", "Next", "Agile", "Rapid", "Core", "Nova",
    "Apex", "Orbit", "Pulse", "Titan", "Front", "Quantum", "Logic", "Fuse",
    "Vault", "Scale", "Flux", "Nexus", "Zenith", "Encore", "Stratus", "Prism",
]

COMPANY_SUFFIXES = [
    "Sync", "Flow", "Forge", "Stack", "Labs", "Hub", "Edge", "Works",
    "Connect", "Ops", "Mind", "Point", "Shift", "Bridge", "Link", "Pro",
    "Sphere", "Trace", "Path", "Scope", "Grid", "Stream", "Phase", "Dash",
]

ORGANIC_SUFFIXES = [
    "Technologies", "Systems", "Solutions", "Platforms", "Digital",
    "Analytics", "Networks", "Inc.", "Corp.", "Labs", "Ventures", "Global",
]

COUNTRIES = [
    "United States", "United Kingdom", "Canada", "Germany", "India",
    "Australia", "Singapore", "Israel", "France", "Netherlands",
    "Switzerland", "Sweden", "Ireland", "Japan", "Spain",
]

CITIES: dict[str, list[str]] = {
    "United States": [
        "San Francisco", "New York", "Austin", "Seattle", "Boston",
        "Chicago", "Denver", "Miami", "Los Angeles", "Portland",
        "Raleigh", "Atlanta", "Dallas", "San Diego", "Palo Alto",
    ],
    "United Kingdom": [
        "London", "Cambridge", "Manchester", "Edinburgh", "Oxford",
        "Bristol", "Birmingham", "Leeds", "Glasgow", "Liverpool",
    ],
    "Canada": [
        "Toronto", "Vancouver", "Montreal", "Ottawa", "Calgary",
        "Waterloo", "Quebec City", "Edmonton", "Halifax", "Winnipeg",
    ],
    "Germany": [
        "Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne",
        "Stuttgart", "Dusseldorf", "Leipzig", "Dresden", "Bonn",
    ],
    "India": [
        "Bangalore", "Mumbai", "Hyderabad", "Delhi", "Pune",
        "Chennai", "Gurgaon", "Noida", "Ahmedabad", "Kolkata",
    ],
    "Australia": [
        "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
        "Canberra", "Gold Coast", "Newcastle", "Hobart", "Darwin",
    ],
    "Singapore": ["Singapore"],
    "Israel": ["Tel Aviv", "Haifa", "Jerusalem", "Herzliya", "Netanya"],
    "France": [
        "Paris", "Lyon", "Marseille", "Toulouse", "Bordeaux",
        "Lille", "Grenoble", "Montpellier", "Nantes", "Strasbourg",
    ],
    "Netherlands": [
        "Amsterdam", "Rotterdam", "Utrecht", "The Hague", "Eindhoven",
        "Groningen", "Maastricht", "Leiden", "Delft", "Arnhem",
    ],
}

FUNDING_STAGES = ["Seed", "Series A", "Series B", "Series C", "Series D", "Public"]
FUNDING_MULTIPLIERS: dict[str, tuple[int, int]] = {
    "Seed": (1, 5),
    "Series A": (5, 15),
    "Series B": (15, 40),
    "Series C": (40, 100),
    "Series D": (100, 300),
    "Public": (500, 5000),
}

REVENUE_RANGES: dict[str, str] = {
    "Seed": "$1M-$5M",
    "Series A": "$5M-$15M",
    "Series B": "$15M-$50M",
    "Series C": "$50M-$150M",
    "Series D": "$150M-$500M",
    "Public": "$500M+",
}

EMPLOYEE_RANGES: dict[str, tuple[int, int]] = {
    "Seed": (5, 50),
    "Series A": (20, 150),
    "Series B": (80, 400),
    "Series C": (200, 1000),
    "Series D": (500, 3000),
    "Public": (2000, 10000),
}

# ─── Contacts / Personas ───────────────────────────────────────────────────

FIRST_NAMES = [
    "James", "Sarah", "Michael", "Emily", "David", "Jessica", "Daniel",
    "Rachel", "Christopher", "Lauren", "Matthew", "Amanda", "Andrew",
    "Sophia", "Kevin", "Olivia", "Brian", "Emma", "Ryan", "Isabella",
    "Jason", "Ava", "Eric", "Mia", "Alex", "Charlotte", "Nathan", "Luna",
    "Thomas", "Harper", "Kyle", "Evelyn", "Scott", "Abigail", "Aaron",
    "Ella", "Ben", "Scarlett", "Tyler", "Grace", "Jordan", "Chloe",
    "Justin", "Victoria", "Vincent", "Riley", "Priya", "Aisha", "Wei",
    "Aiko", "Carlos", "Fatima", "Omar", "Mei", "Raj", "Sofia", "Liam",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson",
    "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    "Perez", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis",
    "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott",
    "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson",
    "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Patel",
    "Kumar", "Singh", "Chen", "Zhang", "Ibrahim", "Okafor", "Johansson",
]

ROLES_POOL = [
    "CEO", "CTO", "VP Engineering", "Chief Product Officer", "COO",
    "Chief Revenue Officer", "VP Sales", "VP Marketing", "VP of Growth",
    "Head of Engineering", "Engineering Manager", "Technical Lead",
    "Chief Data Officer", "VP of Data Science", "Head of Product",
    "Chief Innovation Officer", "Director of Sales", "Head of Partnerships",
    "VP of Customer Success", "Chief Strategy Officer", "CFO",
]

HIRING_KEYWORDS = [
    "backend engineer", "frontend developer", "full stack developer",
    "devops engineer", "data scientist", "SRE", "product manager",
    "ML engineer", "platform engineer", "security engineer",
    "solutions architect", "sales engineer", "customer success manager",
    "UX designer", "data analyst", "developer advocate",
]

# ─── Market Signal Data ────────────────────────────────────────────────────

FUNDING_AMOUNTS = ["$3M", "$5M", "$8M", "$12M", "$15M", "$25M", "$40M", "$60M", "$100M", "$250M"]
FUNDING_ROUNDS = ["Seed", "Series A", "Series B", "Series C", "Series D"]
NEWS_CATEGORIES = ["product_launch", "expansion", "partnership", "award", "acquisition", "other"]

SIGNAL_HEADLINES: dict[str, list[str]] = {
    "funding": [
        "Raised {amount} {round} to accelerate growth",
        "Secures {amount} in {round} funding round",
        "Closes {amount} {round} to expand market presence",
        "Announces {amount} {round} funding for product development",
        "Raises {amount} {round} to scale engineering team",
    ],
    "news": [
        "{company} launches new AI-powered platform",
        "{company} announces strategic partnership with leading enterprise",
        "{company} recognized as industry leader in annual report",
        "{company} expands product suite with new capabilities",
        "{company} awarded best platform in annual awards",
    ],
    "expansion": [
        "{company} opens new office in {city}, expanding global footprint",
        "{company} expanding operations to {region} market",
        "{company} establishes new headquarters in {city}",
        "{company} launches in {region}, hiring local team",
        "{company} expands to {country} with new regional hub",
    ],
    "leadership": [
        "{company} appoints new CTO to lead engineering vision",
        "{company} hires new VP of Engineering from {competitor}",
        "{company} welcomes new Chief Product Officer",
        "{company} adds veteran industry executive to leadership team",
        "{company} names new CEO to drive next phase of growth",
    ],
    "hiring": [
        "{company} hiring {count} engineers for new product initiative",
        "{company} planning major hiring push with {count} open positions",
        "{company} growing rapidly, seeks {count} new team members",
        "{company} invests in R&D with {count} new engineering roles",
        "{company} building new team, hiring {count} across departments",
    ],
}

COMPETITOR_NAMES = [
    "Salesforce", "HubSpot", "Oracle", "SAP", "Microsoft", "Google",
    "Amazon", "Datadog", "Snowflake", "Atlassian", "Slack", "Zoom",
    "Palantir", "CrowdStrike", "Okta", "Twilio", "Shopify", "Stripe",
]

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]


# ─── Dynamic Company Generator ─────────────────────────────────────────────

def _choose_industry(icp: dict) -> str:
    """Pick a random industry influenced by ICP."""
    preferred = icp.get("industries") or icp.get("industry")
    if preferred:
        if isinstance(preferred, str):
            preferred = [preferred]
        valid = [i for i in preferred if i in INDUSTRIES]
        if valid:
            return _rng.choice(valid)
    return _rng.choice(INDUSTRIES)


def _choose_country(icp: dict) -> str:
    """Pick a random country influenced by ICP."""
    preferred = icp.get("countries") or icp.get("country")
    if preferred:
        if isinstance(preferred, str):
            preferred = [preferred]
        valid = [c for c in preferred if c in COUNTRIES]
        if valid:
            return _rng.choice(valid)
    return _rng.choice(COUNTRIES)


def _choose_city(country: str) -> str:
    """Pick a city for the given country."""
    cities = CITIES.get(country, CITIES["United States"])
    return _rng.choice(cities)


def _choose_funding_stage(icp: dict) -> str:
    """Pick a random funding stage influenced by ICP."""
    preferred = icp.get("funding_stages")
    if preferred:
        if isinstance(preferred, str):
            preferred = [preferred]
        valid = [f for f in preferred if f in FUNDING_STAGES]
        if valid:
            return _rng.choice(valid)
    # Default distribution: weighted towards earlier stages
    return _rng.choices(
        FUNDING_STAGES,
        weights=[25, 30, 20, 15, 7, 3],
    )[0]


def _choose_employee_count(funding_stage: str) -> int:
    """Realistic employee count based on funding stage."""
    lo, hi = EMPLOYEE_RANGES.get(funding_stage, (10, 200))
    return _rng.randint(lo, hi)


def _generate_company_name(industry: str) -> tuple[str, str]:
    """Generate a realistic company name and domain."""
    style = _rng.randint(0, 2)
    if style == 0:
        # prefix + suffix (e.g., CloudSync)
        prefix = _rng.choice(COMPANY_PREFIXES)
        suffix = _rng.choice(COMPANY_SUFFIXES)
        name = f"{prefix}{suffix}"
    elif style == 1:
        # prefix + industry-verb + organic suffix (e.g., DataForge Technologies)
        prefix = _rng.choice(COMPANY_PREFIXES)
        suffix = _rng.choice(ORGANIC_SUFFIXES)
        name = f"{prefix}{suffix}"
    else:
        # Word + industry (e.g., NextGen AI)
        adj = _rng.choice(["NextGen", "Advanced", "Intelligent", "Dynamic", "Elite"])
        name = f"{adj} {industry.replace('/', '')}" if _rng.random() > 0.3 else _rng.choice(ORGANIC_SUFFIXES)

    # Generate domain
    slug = name.lower().replace(" ", "").replace("/", "").replace(".", "")
    tld = _rng.choice(["io", "com", "ai", "app", "co", "tech"])
    domain = f"{slug}.{tld}"

    return name, domain


def _generate_description(name: str, industry: str, funding_stage: str, employee_count: int) -> str:
    """Generate realistic company description."""
    templates = [
        f"{name} is a leading {industry} company that helps businesses "
        f"{_rng.choice(['streamline operations', 'accelerate growth', 'improve efficiency', 'drive innovation'])}. "
        f"With {employee_count}+ employees and {funding_stage.lower()} funding, "
        f"they serve {_rng.choice(['enterprise clients', 'mid-market companies', 'fast-growing startups'])} "
        f"across {_rng.choice(['North America', 'global markets', 'multiple industries'])}.",

        f"Founded in {_rng.randint(2015, 2024)}, {name} is a fast-growing {industry} startup "
        f"that {_rng.choice(['transforms how companies', 'revolutionizes the way teams', 'reimagines how businesses'])} "
        f"{_rng.choice(['manage data', 'deploy software', 'automate workflows', 'drive revenue'])}. "
        f"The company recently raised {funding_stage.lower()} funding to scale.",

        f"{name} provides an enterprise {industry} platform used by "
        f"{_rng.choice(['hundreds', 'thousands', 'leading enterprises'])} worldwide. "
        f"At {employee_count} employees, they are {_rng.choice(['rapidly expanding', 'scaling operations', 'growing market share'])} "
        f"and recently completed a {funding_stage.lower()} round.",
    ]
    return _rng.choice(templates)


def _choose_tech_stack(industry: str) -> list[str]:
    """Pick a realistic tech stack for the industry."""
    stacks = INDUSTRY_TECH_STACKS.get(industry, FALLBACK_TECH_STACKS)
    tech_list = list(_rng.choice(stacks))
    # Add some randomness: occasionally remove an item, sometimes add ChromaDB
    if _rng.random() > 0.7:
        tech_list.append("ChromaDB")
    if _rng.random() > 0.8:
        tech_list.append("Redis")
    if _rng.random() > 0.85:
        tech_list.append("Docker")
    return tech_list


def _generate_signals(company_name: str, industry: str, city: str, country: str) -> dict:
    """Generate varied market signals for a company."""
    signals = {}
    signal_weights = [35, 50, 25, 20, 40]  # funding, news, hiring, expansion, leadership

    # Funding signal (35% chance)
    if _rng.random() < 0.35:
        amount = _rng.choice(FUNDING_AMOUNTS)
        round_type = _rng.choice(FUNDING_ROUNDS)
        headline_template = _rng.choice(SIGNAL_HEADLINES["funding"])
        signals["funding"] = {
            "detected": True,
            "amount": amount,
            "round": round_type,
            "date": f"2025-{_rng.randint(1, 6):02d}",
            "source_url": "https://techcrunch.com",
            "headline": headline_template.format(amount=amount, round=round_type),
        }

    # News signal (50% chance)
    if _rng.random() < 0.50:
        category = _rng.choice(NEWS_CATEGORIES)
        headline = _rng.choice(SIGNAL_HEADLINES["news"]).format(company=company_name)
        signals["news"] = {
            "detected": True,
            "headlines": [
                {"title": headline, "url": "https://techcrunch.com", "snippet": f"{company_name} continues to expand in the {industry} space."},
            ],
            "category": category,
            "article_count": _rng.randint(1, 4),
        }

    # Hiring signal (25% chance, but higher for early-stage)
    if _rng.random() < 0.25:
        count = _rng.randint(3, 50)
        headline = _rng.choice(SIGNAL_HEADLINES["hiring"]).format(company=company_name, count=count)
        signals["hiring"] = {
            "detected": True,
            "hiring_surge": count > 10,
            "hiring_count_estimate": count,
            "headline": headline,
        }

    # Expansion signal (20% chance)
    if _rng.random() < 0.20:
        new_city = _rng.choice(_rng.choice(list(CITIES.values())))
        headline = _rng.choice(SIGNAL_HEADLINES["expansion"]).format(
            company=company_name, city=new_city,
            region=_rng.choice(REGIONS),
            country=_rng.choice(COUNTRIES),
        )
        signals["expansion"] = {
            "detected": True,
            "new_location": new_city,
            "detail": headline,
        }

    # Leadership signal (40% chance)
    if _rng.random() < 0.40:
        role = _rng.choice(["CTO", "VP Engineering", "Chief Product Officer", "CEO", "CRO"])
        competitor = _rng.choice(COMPETITOR_NAMES)
        headline = _rng.choice(SIGNAL_HEADLINES["leadership"]).format(
            company=company_name, competitor=competitor,
        )
        signals["leadership"] = {
            "detected": True,
            "leadership_change": True,
            "new_role": role,
            "detail": headline,
        }

    # Trigger summary (LLM-synthesized in production, rule-based here)
    trigger_reasons = []
    if "funding" in signals:
        trigger_reasons.append(f"recent {signals['funding']['round']} funding")
    if "hiring" in signals:
        trigger_reasons.append("active hiring push")
    if "expansion" in signals:
        trigger_reasons.append(f"geographic expansion to {signals['expansion']['new_location']}")
    if "leadership" in signals:
        trigger_reasons.append(f"new {signals['leadership']['new_role']} appointment")
    if "news" in signals:
        trigger_reasons.append("recent press coverage")

    if trigger_reasons:
        signals["trigger_summary"] = (
            f"{company_name} shows {' and '.join(trigger_reasons)}. "
            "This indicates active growth — an ideal time for outreach."
        )
        signals["urgency"] = "high" if ("funding" in signals or "hiring" in signals) else "medium"
    else:
        signals["trigger_summary"] = (
            f"{company_name} is in a steady state with no major trigger signals detected."
        )
        signals["urgency"] = "low"

    signals["last_updated"] = "2026-06"
    return signals


def _generate_contacts(name: str, domain: str, employee_count: int) -> list[dict]:
    """Generate realistic decision-maker contacts for a company."""
    count = min(max(_rng.randint(1, 4), 1), 4)  # 1-4 contacts

    # Always include at least one senior leader
    senior_roles = ["CEO", "CTO", "VP Engineering", "Chief Product Officer", "CFO"]
    selected_roles = [_rng.choice(senior_roles)]

    # Add additional roles
    extra_count = count - 1
    if extra_count > 0:
        extra_role_pool = [
            "Head of Engineering", "VP Sales", "VP Marketing",
            "Engineering Manager", "Head of Product", "Director of Sales",
            "VP of Customer Success", "Head of Partnerships",
        ]
        selected_roles.extend(_rng.sample(extra_role_pool, min(extra_count, len(extra_role_pool))))

    contacts = []
    for role in selected_roles:
        first = _rng.choice(FIRST_NAMES)
        last = _rng.choice(LAST_NAMES)
        contacts.append({
            "full_name": f"{first} {last}",
            "role": role,
            "email": f"{first.lower()}.{last.lower()}@{domain}",
            "phone": f"+1-{_rng.randint(200, 999)}-{_rng.randint(100, 999)}-{_rng.randint(1000, 9999)}",
            "linkedin_url": f"https://linkedin.com/in/{first.lower()}-{last.lower()}",
            "confidence_score": round(_rng.uniform(0.5, 0.95), 2),
        })

    return contacts


def _generate_score_breakdown() -> dict:
    """Generate 8-dimension scorecard with realistic variation."""
    dimensions = [
        "industry_match", "location_match", "hiring_signals",
        "tech_stack_match", "funding_stage", "revenue_tier",
        "employee_range", "decision_makers_found",
    ]
    breakdown = {}
    for dim in dimensions:
        # Some dimensions tend to score higher
        if dim in ("industry_match", "location_match"):
            base = _rng.uniform(50, 95)
        elif dim in ("tech_stack_match", "decision_makers_found"):
            base = _rng.uniform(30, 90)
        else:
            base = _rng.uniform(20, 85)

        breakdown[dim] = {
            "score": round(base, 1),
            "max_score": 100,
            "weight": round(_rng.uniform(0.08, 0.18), 2),
            "reason": _generate_score_reason(dim),
        }

    return breakdown


def _generate_score_reason(dimension: str) -> str:
    """Generate a realistic LLM-style reason for each score dimension."""
    reasons = {
        "industry_match": [
            "Company operates in target industry vertical",
            "Strong alignment with ICP industry focus",
            "Direct competitor or adjacent industry player",
        ],
        "location_match": [
            "Headquarters in target geographic region",
            "Multiple offices in priority markets",
            "Remote-first with presence in target locations",
        ],
        "hiring_signals": [
            "Active hiring across multiple engineering roles",
            "Recent job postings indicate team expansion",
            "Moderate hiring activity detected",
        ],
        "tech_stack_match": [
            "Tech stack overlaps significantly with target stack",
            "Uses complementary technologies in our ecosystem",
            "Partial tech stack alignment with growth potential",
        ],
        "funding_stage": [
            "Recent funding indicates growth capital available",
            "At ideal stage for our solution's price point",
            "Stable funding with clear expansion plans",
        ],
        "revenue_tier": [
            "Revenue range within ideal customer profile",
            "Sufficient budget for enterprise solution",
            "Growing revenue trajectory suggests expanding budget",
        ],
        "employee_range": [
            "Company size indicates organizational maturity",
            "Large enough to have dedicated decision makers",
            "Growth stage with expanding team structure",
        ],
        "decision_makers_found": [
            "Multiple relevant personas identified at company",
            "Key decision maker in target role confirmed",
            "Partial contact coverage with room for discovery",
        ],
    }
    return _rng.choice(reasons.get(dimension, ["Standard match criteria met"]))


def _calculate_qualification_score(breakdown: dict) -> float:
    """Weighted average of all 8 dimension scores."""
    total_weight = sum(d["weight"] for d in breakdown.values())
    if total_weight == 0:
        return 50.0
    weighted = sum(d["score"] * d["weight"] for d in breakdown.values())
    return round(weighted / total_weight, 1)


def _generate_outreach_recommendation(company_name: str, contacts: list[dict],
                                       signals: dict, industry: str) -> dict:
    """Generate personalized outreach content."""
    primary_contact = contacts[0] if contacts else {}
    market_trigger = signals.get("trigger_summary", f"Growing company in the {industry} space")

    return {
        "priority": "high" if signals.get("urgency") == "high" else "medium",
        "reason": (
            f"{company_name} scores well across multiple dimensions. "
            f"{market_trigger}"
        ),
        "suggested_action": (
            f"Send personalized outreach to {primary_contact.get('role', 'key decision maker')} "
            f"at {company_name}"
        ),
        "outreach_subject": f"Helping {company_name} scale {industry} efforts",
        "outreach_template": (
            f"Hi {{{{first_name}}}},\n\n"
            f"I noticed {company_name} has been {'hiring aggressively' if signals.get('hiring') else 'expanding recently'}. "
            f"Our platform helps {industry} companies like yours accelerate growth.\n\n"
            f"{market_trigger}\n\n"
            f"Would you be open to a 15-minute chat next week?\n\n"
            f"Best,\n{{{{sender_name}}}}"
        ),
        "linkedin_message": (
            f"Hi {{{{first_name}}}}, I've been following {company_name}'s growth in the {industry} space. "
            f"{'Congrats on the recent funding!' if signals.get('funding') else 'Impressive growth!'} "
            f"Would love to connect and share how we help similar companies."
        ),
        "confidence": round(_rng.uniform(0.55, 0.95), 2),
        "market_trigger": market_trigger,
        "buying_committee": [
            {
                "role": c["role"],
                "name": c["full_name"],
                "influence": "decision_maker" if c.get("role") in ("CEO", "CTO", "CFO") else "influencer",
            }
            for c in contacts[:3]
        ],
        "talking_points": [
            f"Growing team with {_rng.randint(3, 30)}+ open positions",
            f"Recent {signals.get('funding', {}).get('round', 'growth')} funding round" if signals.get("funding") else f"Strong market position in {industry}",
            f"Tech stack includes {_rng.choice(['modern cloud infrastructure', 'AI/ML capabilities', 'scalable architecture'])}",
            f"Expanding into new markets and geographies",
        ],
        "outreach_channel": _rng.choice(["email", "linkedin", "both"]),
        "follow_up_sequence": [
            {"day": 1, "action": "Send initial email", "template": "Personalized value proposition"},
            {"day": 3, "action": "Follow up with case study", "template": "Relevant customer success story"},
            {"day": 7, "action": "LinkedIn connection request", "template": "Mention specific trigger event"},
            {"day": 14, "action": "Final follow-up", "template": "Offer free assessment or demo"},
        ],
    }


# ─── Public API ────────────────────────────────────────────────────────────

def generate_mock_companies(icp: dict | None = None, count: int = 20) -> list[dict]:
    """
    Generate realistic mock companies matching the given ICP.

    Args:
        icp: Dictionary with optional keys:
            - industries / industry: list[str] | str
            - countries / country: list[str] | str
            - funding_stages: list[str]
            - min_employees: int
            - max_employees: int
            - tech_stack: list[str]
        count: Number of companies to generate (default 20).

    Returns:
        List of company dicts with full detail for all agents and the frontend.
    """
    _reseed()
    icp = icp or {}
    count = min(max(count, 1), 100)  # clamp 1–100

    now = datetime.now(timezone.utc)
    companies = []

    for _ in range(count):
        industry = _choose_industry(icp)
        country = _choose_country(icp)
        city = _choose_city(country)
        funding_stage = _choose_funding_stage(icp)
        name, domain = _generate_company_name(industry)
        employee_count = _choose_employee_count(funding_stage)

        # Enforce ICP employee limits
        min_emp = icp.get("min_employees")
        max_emp = icp.get("max_employees")
        if min_emp is not None:
            employee_count = max(employee_count, min_emp)
        if max_emp is not None:
            employee_count = min(employee_count, max_emp)

        description = _generate_description(name, industry, funding_stage, employee_count)
        tech_stack = _choose_tech_stack(industry)
        signals = _generate_signals(name, industry, city, country)
        contacts = _generate_contacts(name, domain, employee_count)
        score_breakdown = _generate_score_breakdown()
        qual_score = _calculate_qualification_score(score_breakdown)

        revenue_range = REVENUE_RANGES.get(funding_stage, "$5M-$15M")
        growth_rate = _rng.randint(15, 120)
        founded_year = _rng.randint(2013, 2024)

        # Tier based on score
        if qual_score >= 75:
            tier = "A"
        elif qual_score >= 50:
            tier = "B"
        elif qual_score >= 30:
            tier = "C"
        else:
            tier = "D"

        company = {
            # Core identity
            "name": name,
            "domain": domain,
            "industry": industry,
            "country": country,
            "city": city,
            "description": description,
            "logo_url": f"https://logo.clearbit.com/{domain}",
            "linkedin_url": f"https://linkedin.com/company/{domain.split('.')[0]}",

            # Size & stage
            "employee_count": employee_count,
            "revenue_range": revenue_range,
            "funding_stage": funding_stage,
            "founded_year": founded_year,
            "growth_rate": growth_rate,
            "domain_age_days": (now - datetime(founded_year, 1, 1, tzinfo=timezone.utc)).days,

            # Tech
            "tech_stack": tech_stack,
            "tech_stack_detected": {
                "confirmed": tech_stack[:3],
                "probable": tech_stack[3:] if len(tech_stack) > 3 else [],
                "required_match": [],
                "nice_to_have_match": [],
                "excluded_tech_found": False,
            },

            # Signals
            "hiring_keywords": _rng.sample(HIRING_KEYWORDS, min(_rng.randint(1, 4), len(HIRING_KEYWORDS))),
            "hiring_signal_score": round(_rng.uniform(0, 1), 2) if _rng.random() < 0.4 else 0,
            "has_linkedin": True,
            "source": "mock_data_generator",
            "source_url": f"https://{domain}",

            # Scores
            "qualification_score": qual_score,
            "tier": tier,
            "score_breakdown": score_breakdown,

            # Market signals
            "market_signals": signals,

            # Validation
            "validation_details": {
                "domain_reachable": True,
                "https_enforced": True,
                "blacklist_check": "passed",
                "industry_keywords": {"passed": True, "confidence": round(_rng.uniform(0.6, 0.95), 2)},
                "location_match": {"passed": True, "confidence": round(_rng.uniform(0.5, 0.95), 2)},
                "hiring_signal": {"passed": _rng.random() < 0.4, "confidence": round(_rng.uniform(0.3, 0.9), 2)},
            },

            # Status
            "status": "validated",

            # Metadata
            "metadata_json": {
                "data_source": "mock",
                "generated_at": now.isoformat(),
                "mock_version": "2.0",
            },
        }

        # Contacts (as separate key for agent use)
        company["contacts"] = contacts

        # Outreach recommendation
        company["recommendation"] = _generate_outreach_recommendation(
            name, contacts, signals, industry
        )

        companies.append(company)

    # Shuffle to avoid alphabetical clustering
    _rng.shuffle(companies)
    return companies


def get_mock_companies_dynamic(icp_filter: dict, count: int = 20) -> list[dict]:
    """
    Drop-in replacement for mock_dataset.get_mock_companies().

    Generates fresh companies matching ICP. Use this when USE_MOCK_DATA=true
    or when no API keys are configured.
    """
    return generate_mock_companies(icp_filter, count)


def generate_mock_signals_for_company(company_name: str, industry: str,
                                       city: str = "San Francisco",
                                       country: str = "United States") -> dict:
    """
    Generate varied market signals for a specific company.
    Useful for agents that need per-company mock signal variation.
    """
    _reseed()
    # Deterministic seed based on company name for stable mock output
    _rng.seed(sum(ord(c) for c in company_name) + 42)
    return _generate_signals(company_name, industry, city, country)


def generate_mock_score_breakdown() -> dict:
    """Generate a fresh 8-dimension scorecard for testing."""
    _reseed()
    return _generate_score_breakdown()


def generate_mock_contacts(name: str, domain: str, employee_count: int) -> list[dict]:
    """Generate realistic mock contacts for a company."""
    _reseed()
    _rng.seed(sum(ord(c) for c in name) + 7)
    return _generate_contacts(name, domain, employee_count)
