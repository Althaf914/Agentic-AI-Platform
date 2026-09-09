"""
50 realistic mock companies for demo and testing.
"""

MOCK_COMPANIES = [
    {"name": "CloudSync Pro", "domain": "cloudsyncpro.io", "industry": "SaaS", "country": "United States", "employee_count": 120, "revenue_range": "$10M-$25M", "funding_stage": "Series B", "tech_stack": ["Python", "AWS", "React", "PostgreSQL"], "hiring_keywords": ["backend engineer", "devops"], "founded_year": 2018, "growth_rate": 45},
    {"name": "DevFlow Labs", "domain": "devflowlabs.com", "industry": "SaaS", "country": "United States", "employee_count": 85, "revenue_range": "$5M-$10M", "funding_stage": "Series A", "tech_stack": ["Go", "Kubernetes", "gRPC", "Redis"], "hiring_keywords": ["platform engineer", "SRE"], "founded_year": 2020, "growth_rate": 60},
    {"name": "PaymentStack", "domain": "paymentstack.io", "industry": "Fintech", "country": "United Kingdom", "employee_count": 200, "revenue_range": "$25M-$50M", "funding_stage": "Series C", "tech_stack": ["Java", "AWS", "Kafka", "React"], "hiring_keywords": ["compliance engineer", "backend developer"], "founded_year": 2016, "growth_rate": 35},
    {"name": "LedgerAI", "domain": "ledgerai.com", "industry": "Fintech", "country": "United States", "employee_count": 60, "revenue_range": "$3M-$8M", "funding_stage": "Series A", "tech_stack": ["Python", "TensorFlow", "GCP", "Vue.js"], "hiring_keywords": ["ML engineer", "data scientist"], "founded_year": 2021, "growth_rate": 80},
    {"name": "MedVault", "domain": "medvault.health", "industry": "HealthTech", "country": "United States", "employee_count": 150, "revenue_range": "$15M-$30M", "funding_stage": "Series B", "tech_stack": ["Python", "HIPAA", "AWS", "React"], "hiring_keywords": ["health data engineer", "full stack developer"], "founded_year": 2017, "growth_rate": 40},
    {"name": "CareConnect", "domain": "careconnect.io", "industry": "HealthTech", "country": "Canada", "employee_count": 45, "revenue_range": "$2M-$5M", "funding_stage": "Seed", "tech_stack": ["Node.js", "React Native", "Firebase"], "hiring_keywords": ["mobile developer", "product manager"], "founded_year": 2022, "growth_rate": 90},
    {"name": "SecureVault Inc", "domain": "securevault.io", "industry": "CyberSecurity", "country": "Israel", "employee_count": 250, "revenue_range": "$25M-$50M", "funding_stage": "Series C", "tech_stack": ["Rust", "AWS", "Elasticsearch", "C++"], "hiring_keywords": ["threat researcher", "security engineer"], "founded_year": 2015, "growth_rate": 30},
    {"name": "ZeroTrust Shield", "domain": "zerotrustshield.com", "industry": "CyberSecurity", "country": "United States", "employee_count": 400, "revenue_range": "$50M-$100M", "funding_stage": "Series D", "tech_stack": ["C++", "Python", "Azure", "Kubernetes"], "hiring_keywords": ["SIEM engineer", "cloud security architect"], "founded_year": 2014, "growth_rate": 25},
    {"name": "LearnFlow", "domain": "learnflow.edu", "industry": "EdTech", "country": "United States", "employee_count": 70, "revenue_range": "$5M-$10M", "funding_stage": "Series A", "tech_stack": ["Python", "Django", "React", "PostgreSQL"], "hiring_keywords": ["curriculum designer", "frontend developer"], "founded_year": 2019, "growth_rate": 55},
    {"name": "SkillForge", "domain": "skillforge.io", "industry": "EdTech", "country": "India", "employee_count": 130, "revenue_range": "$8M-$15M", "funding_stage": "Series B", "tech_stack": ["Java", "Spring", "Angular", "MongoDB"], "hiring_keywords": ["content engineer", "data analyst"], "founded_year": 2018, "growth_rate": 50},
    {"name": "TalentBridge AI", "domain": "talentbridge.ai", "industry": "HRTech", "country": "United States", "employee_count": 45, "revenue_range": "$2M-$5M", "funding_stage": "Seed", "tech_stack": ["Python", "TensorFlow", "React", "PostgreSQL"], "hiring_keywords": ["AI engineer", "recruiter"], "founded_year": 2022, "growth_rate": 95},
    {"name": "HireRight Now", "domain": "hirerightnow.com", "industry": "HRTech", "country": "Australia", "employee_count": 30, "revenue_range": "$1M-$2M", "funding_stage": "Seed", "tech_stack": ["Ruby", "Rails", "PostgreSQL", "Heroku"], "hiring_keywords": ["full stack developer"], "founded_year": 2023, "growth_rate": 70},
    {"name": "DataPipe Systems", "domain": "datapipe.dev", "industry": "SaaS", "country": "United Kingdom", "employee_count": 200, "revenue_range": "$15M-$30M", "funding_stage": "Series B", "tech_stack": ["Scala", "Spark", "Kafka", "AWS"], "hiring_keywords": ["data engineer", "platform architect"], "founded_year": 2017, "growth_rate": 38},
    {"name": "APIForge", "domain": "apiforge.io", "industry": "SaaS", "country": "Canada", "employee_count": 60, "revenue_range": "$5M-$10M", "funding_stage": "Series A", "tech_stack": ["Node.js", "TypeScript", "MongoDB", "Docker"], "hiring_keywords": ["API engineer", "developer advocate"], "founded_year": 2020, "growth_rate": 65},
    {"name": "CloudGuard AI", "domain": "cloudguard.ai", "industry": "CyberSecurity", "country": "Germany", "employee_count": 180, "revenue_range": "$20M-$40M", "funding_stage": "Series C", "tech_stack": ["Python", "GCP", "TensorFlow", "Go"], "hiring_keywords": ["ML security engineer", "cloud architect"], "founded_year": 2016, "growth_rate": 42},
    {"name": "FinConnect", "domain": "finconnect.io", "industry": "Fintech", "country": "Singapore", "employee_count": 90, "revenue_range": "$8M-$15M", "funding_stage": "Series A", "tech_stack": ["Java", "Spring Boot", "React", "PostgreSQL"], "hiring_keywords": ["backend engineer", "compliance analyst"], "founded_year": 2019, "growth_rate": 55},
    {"name": "WealthBot", "domain": "wealthbot.finance", "industry": "Fintech", "country": "United States", "employee_count": 110, "revenue_range": "$12M-$20M", "funding_stage": "Series B", "tech_stack": ["Python", "FastAPI", "React", "AWS"], "hiring_keywords": ["quant developer", "financial engineer"], "founded_year": 2018, "growth_rate": 48},
    {"name": "HealthSync", "domain": "healthsync.app", "industry": "HealthTech", "country": "Germany", "employee_count": 80, "revenue_range": "$6M-$12M", "funding_stage": "Series A", "tech_stack": ["Python", "Django", "React", "GCP"], "hiring_keywords": ["health informatics", "full stack developer"], "founded_year": 2020, "growth_rate": 62},
    {"name": "PharmaFlow", "domain": "pharmaflow.io", "industry": "HealthTech", "country": "United States", "employee_count": 300, "revenue_range": "$30M-$60M", "funding_stage": "Series C", "tech_stack": ["Java", "AWS", "React", "Elasticsearch"], "hiring_keywords": ["clinical data engineer", "regulatory specialist"], "founded_year": 2015, "growth_rate": 28},
    {"name": "ThreatHunter Pro", "domain": "threathunter.pro", "industry": "CyberSecurity", "country": "United States", "employee_count": 320, "revenue_range": "$30M-$60M", "funding_stage": "Series C", "tech_stack": ["Go", "Elasticsearch", "Docker", "Python"], "hiring_keywords": ["threat intelligence", "SOC analyst"], "founded_year": 2016, "growth_rate": 33},
    {"name": "EndpointShield", "domain": "endpointshield.com", "industry": "CyberSecurity", "country": "United States", "employee_count": 280, "revenue_range": "$35M-$70M", "funding_stage": "Series C", "tech_stack": ["C", "Linux", "Docker", "Python"], "hiring_keywords": ["endpoint engineer", "kernel developer"], "founded_year": 2015, "growth_rate": 30},
    {"name": "StudyHub", "domain": "studyhub.co", "industry": "EdTech", "country": "United Kingdom", "employee_count": 55, "revenue_range": "$3M-$6M", "funding_stage": "Seed", "tech_stack": ["TypeScript", "Next.js", "Supabase"], "hiring_keywords": ["frontend developer", "UX designer"], "founded_year": 2021, "growth_rate": 75},
    {"name": "CodeAcademy Pro", "domain": "codeacademypro.io", "industry": "EdTech", "country": "United States", "employee_count": 160, "revenue_range": "$12M-$25M", "funding_stage": "Series B", "tech_stack": ["Python", "React", "AWS", "Docker"], "hiring_keywords": ["curriculum developer", "platform engineer"], "founded_year": 2017, "growth_rate": 40},
    {"name": "RecruitFlow", "domain": "recruitflow.co", "industry": "HRTech", "country": "India", "employee_count": 75, "revenue_range": "$3M-$5M", "funding_stage": "Series A", "tech_stack": ["Java", "Spring", "Angular", "MySQL"], "hiring_keywords": ["full stack developer", "ML engineer"], "founded_year": 2020, "growth_rate": 58},
    {"name": "WorkforceHub", "domain": "workforcehub.io", "industry": "HRTech", "country": "United States", "employee_count": 55, "revenue_range": "$2M-$5M", "funding_stage": "Seed", "tech_stack": ["Python", "Django", "Vue.js", "PostgreSQL"], "hiring_keywords": ["backend developer", "product designer"], "founded_year": 2021, "growth_rate": 68},
    {"name": "SaaSMetrics", "domain": "saasmetrics.com", "industry": "SaaS", "country": "United States", "employee_count": 90, "revenue_range": "$8M-$15M", "funding_stage": "Series A", "tech_stack": ["Python", "React", "PostgreSQL", "Redis"], "hiring_keywords": ["analytics engineer", "frontend developer"], "founded_year": 2019, "growth_rate": 52},
    {"name": "PlatformX", "domain": "platformx.dev", "industry": "SaaS", "country": "United States", "employee_count": 150, "revenue_range": "$12M-$25M", "funding_stage": "Series B", "tech_stack": ["Rust", "WebAssembly", "React", "AWS"], "hiring_keywords": ["systems engineer", "developer relations"], "founded_year": 2018, "growth_rate": 45},
    {"name": "AutoPipeline", "domain": "autopipeline.io", "industry": "SaaS", "country": "Canada", "employee_count": 110, "revenue_range": "$10M-$20M", "funding_stage": "Series B", "tech_stack": ["Go", "Terraform", "GCP", "React"], "hiring_keywords": ["DevOps engineer", "platform lead"], "founded_year": 2019, "growth_rate": 50},
    {"name": "InfraStack", "domain": "infrastack.dev", "industry": "SaaS", "country": "United States", "employee_count": 95, "revenue_range": "$7M-$15M", "funding_stage": "Series A", "tech_stack": ["TypeScript", "AWS CDK", "React", "Node.js"], "hiring_keywords": ["cloud engineer", "solutions architect"], "founded_year": 2020, "growth_rate": 58},
    {"name": "CryptoLedger", "domain": "cryptoledger.finance", "industry": "Fintech", "country": "Switzerland", "employee_count": 70, "revenue_range": "$5M-$12M", "funding_stage": "Series A", "tech_stack": ["Rust", "Solidity", "React", "AWS"], "hiring_keywords": ["blockchain developer", "smart contract engineer"], "founded_year": 2020, "growth_rate": 72},
    {"name": "InsurTech360", "domain": "insurtech360.com", "industry": "Fintech", "country": "United States", "employee_count": 140, "revenue_range": "$10M-$20M", "funding_stage": "Series B", "tech_stack": ["Java", "AWS", "React", "Kafka"], "hiring_keywords": ["actuarial engineer", "backend developer"], "founded_year": 2018, "growth_rate": 38},
    {"name": "DiagnosAI", "domain": "diagnosai.health", "industry": "HealthTech", "country": "United States", "employee_count": 65, "revenue_range": "$4M-$8M", "funding_stage": "Series A", "tech_stack": ["Python", "PyTorch", "FastAPI", "GCP"], "hiring_keywords": ["ML research scientist", "clinical AI engineer"], "founded_year": 2021, "growth_rate": 85},
    {"name": "TeleHealth Plus", "domain": "telehealthplus.io", "industry": "HealthTech", "country": "Canada", "employee_count": 95, "revenue_range": "$7M-$14M", "funding_stage": "Series A", "tech_stack": ["TypeScript", "React", "AWS", "WebRTC"], "hiring_keywords": ["video engineer", "full stack developer"], "founded_year": 2019, "growth_rate": 60},
    {"name": "CyberSentinel", "domain": "cybersentinel.ai", "industry": "CyberSecurity", "country": "Israel", "employee_count": 500, "revenue_range": "$60M-$100M", "funding_stage": "Series D", "tech_stack": ["Python", "ML", "AWS", "Go"], "hiring_keywords": ["AI security researcher", "principal engineer"], "founded_year": 2013, "growth_rate": 22},
    {"name": "MentorEd", "domain": "mentored.app", "industry": "EdTech", "country": "United States", "employee_count": 40, "revenue_range": "$1M-$3M", "funding_stage": "Seed", "tech_stack": ["React Native", "Firebase", "Node.js"], "hiring_keywords": ["mobile developer", "growth marketer"], "founded_year": 2022, "growth_rate": 100},
    {"name": "ClassroomIQ", "domain": "classroomiq.com", "industry": "EdTech", "country": "Australia", "employee_count": 85, "revenue_range": "$6M-$10M", "funding_stage": "Series A", "tech_stack": ["Python", "Django", "React", "AWS"], "hiring_keywords": ["data scientist", "product manager"], "founded_year": 2019, "growth_rate": 48},
    {"name": "PeopleOps AI", "domain": "peopleops.ai", "industry": "HRTech", "country": "United States", "employee_count": 100, "revenue_range": "$8M-$15M", "funding_stage": "Series A", "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL"], "hiring_keywords": ["NLP engineer", "product designer"], "founded_year": 2020, "growth_rate": 62},
    {"name": "TalentScout AI", "domain": "talentscout.ai", "industry": "HRTech", "country": "United Kingdom", "employee_count": 65, "revenue_range": "$4M-$8M", "funding_stage": "Series A", "tech_stack": ["Python", "FastAPI", "React", "ChromaDB"], "hiring_keywords": ["AI researcher", "backend developer"], "founded_year": 2021, "growth_rate": 70},
    {"name": "FormStack AI", "domain": "formstackai.com", "industry": "SaaS", "country": "United States", "employee_count": 75, "revenue_range": "$6M-$12M", "funding_stage": "Series A", "tech_stack": ["TypeScript", "Next.js", "Prisma", "Vercel"], "hiring_keywords": ["full stack developer", "AI engineer"], "founded_year": 2021, "growth_rate": 72},
    {"name": "NotionFlow", "domain": "notionflow.io", "industry": "SaaS", "country": "United States", "employee_count": 50, "revenue_range": "$3M-$6M", "funding_stage": "Seed", "tech_stack": ["TypeScript", "React", "Supabase", "Tailwind"], "hiring_keywords": ["frontend engineer", "design engineer"], "founded_year": 2022, "growth_rate": 88},
    {"name": "BankBridge", "domain": "bankbridge.io", "industry": "Fintech", "country": "United Kingdom", "employee_count": 175, "revenue_range": "$15M-$30M", "funding_stage": "Series B", "tech_stack": ["Java", "Spring", "React", "AWS", "Kafka"], "hiring_keywords": ["payments engineer", "risk analyst"], "founded_year": 2017, "growth_rate": 35},
    {"name": "NeoBank Labs", "domain": "neobanklabs.com", "industry": "Fintech", "country": "Germany", "employee_count": 220, "revenue_range": "$20M-$40M", "funding_stage": "Series C", "tech_stack": ["Kotlin", "AWS", "React", "PostgreSQL"], "hiring_keywords": ["mobile engineer", "financial product manager"], "founded_year": 2016, "growth_rate": 30},
    {"name": "VitalSign AI", "domain": "vitalsign.ai", "industry": "HealthTech", "country": "United States", "employee_count": 50, "revenue_range": "$2M-$5M", "funding_stage": "Seed", "tech_stack": ["Python", "PyTorch", "React", "AWS"], "hiring_keywords": ["biomedical engineer", "data scientist"], "founded_year": 2022, "growth_rate": 92},
    {"name": "PhysiTrack", "domain": "physitrack.health", "industry": "HealthTech", "country": "Australia", "employee_count": 110, "revenue_range": "$9M-$18M", "funding_stage": "Series B", "tech_stack": ["Swift", "Kotlin", "Node.js", "GCP"], "hiring_keywords": ["mobile engineer", "health product manager"], "founded_year": 2018, "growth_rate": 42},
    {"name": "NetSentinel", "domain": "netsentinel.io", "industry": "CyberSecurity", "country": "United States", "employee_count": 160, "revenue_range": "$15M-$30M", "funding_stage": "Series B", "tech_stack": ["Go", "Rust", "AWS", "Terraform"], "hiring_keywords": ["network security engineer", "DevSecOps"], "founded_year": 2017, "growth_rate": 40},
    {"name": "PrivacyGuard", "domain": "privacyguard.eu", "industry": "CyberSecurity", "country": "Germany", "employee_count": 90, "revenue_range": "$7M-$14M", "funding_stage": "Series A", "tech_stack": ["Python", "Kubernetes", "GCP", "React"], "hiring_keywords": ["privacy engineer", "compliance specialist"], "founded_year": 2019, "growth_rate": 55},
    {"name": "QuizMaster", "domain": "quizmaster.io", "industry": "EdTech", "country": "India", "employee_count": 60, "revenue_range": "$2M-$5M", "funding_stage": "Seed", "tech_stack": ["React Native", "Node.js", "MongoDB", "AWS"], "hiring_keywords": ["mobile developer", "gamification designer"], "founded_year": 2021, "growth_rate": 78},
    {"name": "LabSkills", "domain": "labskills.edu", "industry": "EdTech", "country": "United States", "employee_count": 35, "revenue_range": "$1M-$3M", "funding_stage": "Seed", "tech_stack": ["Python", "FastAPI", "React", "Docker"], "hiring_keywords": ["content creator", "full stack developer"], "founded_year": 2023, "growth_rate": 110},
    {"name": "StaffingEdge", "domain": "staffingedge.net", "industry": "HRTech", "country": "United States", "employee_count": 40, "revenue_range": "$1M-$3M", "funding_stage": "Seed", "tech_stack": ["PHP", "Laravel", "MySQL", "Vue.js"], "hiring_keywords": ["full stack developer", "recruiter"], "founded_year": 2022, "growth_rate": 65},
    {"name": "TeamPulse", "domain": "teampulse.io", "industry": "HRTech", "country": "Canada", "employee_count": 85, "revenue_range": "$5M-$10M", "funding_stage": "Series A", "tech_stack": ["TypeScript", "React", "Node.js", "PostgreSQL"], "hiring_keywords": ["product engineer", "people analytics"], "founded_year": 2020, "growth_rate": 55},
]


def get_mock_companies(icp_filter: dict) -> list[dict]:
    """
    Filter mock companies by ICP criteria.

    Supported filters in icp_filter:
        - industry / industries: list[str]
        - country / countries: list[str]
        - min_employees: int
        - max_employees: int
        - funding_stages: list[str]
        - tech_stack: list[str] (matches if any overlap)
    """
    results = MOCK_COMPANIES[:]

    # Industry filter
    industries = icp_filter.get("industries") or icp_filter.get("industry")
    if industries:
        if isinstance(industries, str):
            industries = [industries]
        industries_lower = [i.lower() for i in industries]
        results = [c for c in results if c["industry"].lower() in industries_lower]

    # Country filter
    countries = icp_filter.get("countries") or icp_filter.get("country")
    if countries:
        if isinstance(countries, str):
            countries = [countries]
        countries_lower = [co.lower() for co in countries]
        results = [c for c in results if c["country"].lower() in countries_lower]

    # Employee count filter
    min_emp = icp_filter.get("min_employees")
    max_emp = icp_filter.get("max_employees")
    if min_emp is not None:
        results = [c for c in results if c["employee_count"] >= min_emp]
    if max_emp is not None:
        results = [c for c in results if c["employee_count"] <= max_emp]

    # Funding stage filter
    funding_stages = icp_filter.get("funding_stages")
    if funding_stages:
        stages_lower = [f.lower().replace(" ", "_") for f in funding_stages]
        results = [c for c in results if c["funding_stage"].lower().replace(" ", "_") in stages_lower]

    # Tech stack overlap filter
    tech_stack = icp_filter.get("tech_stack")
    if tech_stack:
        tech_lower = [t.lower() for t in tech_stack]
        results = [
            c for c in results
            if any(t.lower() in tech_lower for t in c.get("tech_stack", []))
        ]

    return results
