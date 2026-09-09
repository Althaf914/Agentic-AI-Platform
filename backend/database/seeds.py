"""
Seed data — creates test users, preset configurations, campaigns, and a demo workflow
with companies, contacts, recommendations, approvals, and memory entries.
"""

import uuid
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from backend.config.presets import PRESET_CONFIGS
from backend.tools.mock_dataset import get_mock_companies
from backend.models.user import User
from backend.models.campaign import Campaign
from backend.models.configuration import Configuration
from backend.models.workflow import Workflow
from backend.models.company import Company
from backend.models.contact import Contact
from backend.models.recommendation import Recommendation
from backend.models.approval import Approval
from backend.models.memory import Memory
from backend.services.auth_service import hash_password
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# ─── Main Entry Point ────────────────────────────────────────────────────────

def seed_all(db: Session):
    """Run all seed functions in order."""
    seed_users(db)
    seed_configurations(db)      # keep existing configs for backward compat
    seed_campaigns(db)           # new Campaign-based configs
    seed_demo_workflow(db)
    logger.info("Database seeding completed successfully")


# ─── Users ───────────────────────────────────────────────────────────────────

def seed_users(db: Session):
    """Create 3 test users if they don't already exist."""
    users_data = [
        {"email": "admin@agentforge.ai", "password": "demo1234", "role": "admin"},
        {"email": "sales@agentforge.ai", "password": "demo1234", "role": "sales"},
        {"email": "viewer@agentforge.ai", "password": "demo1234", "role": "viewer"},
    ]

    for user_data in users_data:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            continue

        user = User(
            id=str(uuid.uuid4()),
            email=user_data["email"],
            password_hash=hash_password(user_data["password"]),
            role=user_data["role"],
        )
        db.add(user)

    db.commit()
    logger.info("Seeded 3 users (admin, sales, viewer)")


# ─── Configurations (legacy) ─────────────────────────────────────────────────

def seed_configurations(db: Session):
    """
    Create 9 configuration rows (3 per preset: ICP, Persona, Scoring).
    Assigned to the admin user.
    """
    admin = db.query(User).filter(User.email == "admin@agentforge.ai").first()
    if not admin:
        logger.warning("Admin user not found, skipping configuration seeding")
        return

    # Check if already seeded
    existing_count = db.query(Configuration).filter(Configuration.user_id == admin.id).count()
    if existing_count >= 9:
        logger.info("Configurations already seeded, skipping")
        return

    for preset_name, preset in PRESET_CONFIGS.items():
        display_name = preset_name.replace("_", " ").title()

        # ICP config
        icp_config = Configuration(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            name=f"{display_name} - ICP",
            type="icp",
            config_json=preset["icp"],
        )
        db.add(icp_config)

        # Persona config
        persona_config = Configuration(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            name=f"{display_name} - Personas",
            type="persona",
            config_json={"personas": preset["personas"]},
        )
        db.add(persona_config)

        # Scoring config
        scoring_config = Configuration(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            name=f"{display_name} - Scoring",
            type="scoring",
            config_json=preset["scoring"],
        )
        db.add(scoring_config)

    db.commit()
    logger.info("Seeded 9 configuration rows (3 presets × 3 types)")


# ─── Campaigns ──────────────────────────────────────────────────────────────

def seed_campaigns(db: Session):
    """
    Create 3 campaign rows with fully populated config_json.
    Assigned to the admin user.
    """
    admin = db.query(User).filter(User.email == "admin@agentforge.ai").first()
    if not admin:
        logger.warning("Admin user not found, skipping campaign seeding")
        return

    # Check if already seeded
    existing_count = db.query(Campaign).filter(Campaign.user_id == admin.id).count()
    if existing_count >= 3:
        logger.info("Campaigns already seeded, skipping")
        return

    campaigns_data = [
        {
            "name": "B2B SaaS AI Tools",
            "domain": "b2b_saas",
            "config_json": {
                "business": {
                    "description": "AI-powered platform that automates sales workflows and lead enrichment for B2B companies using machine learning.",
                    "product_category": "ai_platform",
                    "value_proposition": "Reduce manual prospecting time by 80% with AI-driven lead scoring and intent data.",
                },
                "geography": {
                    "countries": ["US", "UK", "Canada"],
                    "states": ["California", "New York", "Texas", "Illinois"],
                    "cities": ["San Francisco", "New York", "Austin", "Chicago", "London"],
                },
                "company_filters": {
                    "industries": ["SaaS", "Cloud", "Developer Tools", "Enterprise Software"],
                    "min_employees": 50,
                    "max_employees": 5000,
                    "funding_stages": ["Seed", "Series A", "Series B", "Series C"],
                    "min_revenue": "$1M",
                    "max_revenue": "$500M",
                    "company_age_min_years": 2,
                    "exclude_keywords": ["outsourcing", "consulting", "agency"],
                },
                "technology_filters": {
                    "required_tech": ["Python", "React", "AWS", "Kubernetes", "PostgreSQL"],
                    "nice_to_have_tech": ["TensorFlow", "PyTorch", "Snowflake", "Databricks"],
                    "exclude_tech": ["PHP", "ColdFusion", "ASP.NET WebForms"],
                    "cloud_providers": ["AWS", "GCP", "Azure"],
                },
                "hiring_signals": {
                    "keywords": ["machine learning", "AI", "data science", "engineering", "growth"],
                    "job_titles": ["Software Engineer", "Data Scientist", "ML Engineer", "VP Engineering", "CTO"],
                    "departments": ["Engineering", "Data", "Product"],
                },
                "buying_committee": {
                    "primary_persona": {"title": "CTO", "seniority": "C-Suite", "department": "Engineering"},
                    "secondary_personas": [
                        {"title": "VP Engineering", "seniority": "VP", "department": "Engineering"},
                        {"title": "Head of Product", "seniority": "Director", "department": "Product"},
                    ],
                    "influencers": ["Lead Architect", "Engineering Manager", "Data Science Lead"],
                },
                "scoring_weights": {
                    "industry_match": 25,
                    "location_match": 10,
                    "hiring_signals": 15,
                    "tech_stack_match": 15,
                    "funding_stage": 15,
                    "revenue_tier": 5,
                    "employee_range": 10,
                    "decision_makers_found": 5,
                },
            },
        },
        {
            "name": "Cybersecurity Platform",
            "domain": "cybersecurity",
            "config_json": {
                "business": {
                    "description": "Next-gen cloud security platform providing zero-trust network access, threat detection, and compliance automation for enterprises.",
                    "product_category": "security_tool",
                    "value_proposition": "Detect and respond to threats in under 5 minutes with AI-powered security orchestration.",
                },
                "geography": {
                    "countries": ["US", "Israel", "UK", "Germany"],
                    "states": ["California", "Virginia", "Texas", "New York"],
                    "cities": ["Tel Aviv", "San Francisco", "Arlington", "Austin", "London", "Berlin"],
                },
                "company_filters": {
                    "industries": ["Cybersecurity", "InfoSec", "Network Security", "Compliance", "Defense"],
                    "min_employees": 20,
                    "max_employees": 2000,
                    "funding_stages": ["Seed", "Series A", "Series B"],
                    "min_revenue": "$500K",
                    "max_revenue": "$200M",
                    "company_age_min_years": 1,
                    "exclude_keywords": ["penetration testing only", "MSSP"],
                },
                "technology_filters": {
                    "required_tech": ["SIEM", "Zero Trust", "Cloud Security", "IDP"],
                    "nice_to_have_tech": ["SOAR", "EDR", "XDR", "CASB"],
                    "exclude_tech": ["Legacy AV", "On-premise only"],
                    "cloud_providers": ["AWS", "Azure", "GCP"],
                },
                "hiring_signals": {
                    "keywords": ["security", "CISO", "compliance", "threat detection", "incident response"],
                    "job_titles": ["CISO", "Security Engineer", "SOC Analyst", "Compliance Manager", "Security Architect"],
                    "departments": ["Security", "Compliance", "IT", "Engineering"],
                },
                "buying_committee": {
                    "primary_persona": {"title": "CISO", "seniority": "C-Suite", "department": "Security"},
                    "secondary_personas": [
                        {"title": "VP Security", "seniority": "VP", "department": "Security"},
                        {"title": "Compliance Officer", "seniority": "Director", "department": "Compliance"},
                    ],
                    "influencers": ["Security Architect", "IT Director", "Network Engineer"],
                },
                "scoring_weights": {
                    "industry_match": 25,
                    "location_match": 10,
                    "hiring_signals": 15,
                    "tech_stack_match": 15,
                    "funding_stage": 15,
                    "revenue_tier": 5,
                    "employee_range": 10,
                    "decision_makers_found": 5,
                },
            },
        },
        {
            "name": "Staffing Tech",
            "domain": "staffing",
            "config_json": {
                "business": {
                    "description": "AI-driven recruitment and talent acquisition platform that matches candidates to roles using natural language processing and behavioral analytics.",
                    "product_category": "hr_software",
                    "value_proposition": "Fill roles 3x faster with AI-powered candidate matching and automated interview scheduling.",
                },
                "geography": {
                    "countries": ["US", "UK", "Australia", "Canada"],
                    "states": ["California", "New York", "Illinois", "Texas"],
                    "cities": ["New York", "San Francisco", "Chicago", "Sydney", "Austin", "London"],
                },
                "company_filters": {
                    "industries": ["HR", "Recruiting", "Staffing", "Talent Management", "Workforce Solutions"],
                    "min_employees": 10,
                    "max_employees": 500,
                    "funding_stages": ["Seed", "Series A"],
                    "min_revenue": "$100K",
                    "max_revenue": "$50M",
                    "company_age_min_years": 1,
                    "exclude_keywords": ["manual staffing", "temp agency only"],
                },
                "technology_filters": {
                    "required_tech": ["ATS", "Salesforce", "LinkedIn", "HRIS"],
                    "nice_to_have_tech": ["Greenhouse", "Lever", "Workday", "BambooHR"],
                    "exclude_tech": ["Legacy PeopleSoft", "Homegrown ATS"],
                    "cloud_providers": ["AWS", "GCP"],
                },
                "hiring_signals": {
                    "keywords": ["recruiter", "talent acquisition", "HR", "people operations", "hiring manager"],
                    "job_titles": ["Head of Talent", "Recruiter", "HR Manager", "Talent Director", "People Ops Lead"],
                    "departments": ["HR", "Talent Acquisition", "People Operations"],
                },
                "buying_committee": {
                    "primary_persona": {"title": "Head of Talent", "seniority": "Director", "department": "HR"},
                    "secondary_personas": [
                        {"title": "CEO", "seniority": "C-Suite", "department": "Executive"},
                        {"title": "HR Operations Manager", "seniority": "Manager", "department": "HR"},
                    ],
                    "influencers": ["VP People", "Recruiting Team Lead", "Hiring Manager"],
                },
                "scoring_weights": {
                    "industry_match": 25,
                    "location_match": 10,
                    "hiring_signals": 15,
                    "tech_stack_match": 15,
                    "funding_stage": 15,
                    "revenue_tier": 5,
                    "employee_range": 10,
                    "decision_makers_found": 5,
                },
            },
        },
    ]

    for camp_data in campaigns_data:
        campaign = Campaign(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            name=camp_data["name"],
            status="draft",
            domain=camp_data["domain"],
            wizard_step_completed=6,
            config_json=camp_data["config_json"],
        )
        db.add(campaign)

    db.commit()
    logger.info("Seeded 3 campaign rows (B2B SaaS, Cybersecurity, Staffing Tech)")


# ─── Demo Workflow ───────────────────────────────────────────────────────────

FIRST_NAMES = ["James", "Sarah", "Michael", "Emily", "David", "Jessica", "Alex", "Maria", "Chris", "Lisa"]
LAST_NAMES = ["Johnson", "Williams", "Brown", "Garcia", "Miller", "Davis", "Rodriguez", "Wilson", "Anderson", "Taylor"]
ROLES_POOL = ["CTO", "VP Engineering", "Head of Product", "Director of Sales", "CEO"]
DEPARTMENTS_POOL = ["Engineering", "Product", "Sales", "Executive"]


def seed_demo_workflow(db: Session):
    """
    Create a completed demo workflow with:
    - 20 companies from mock dataset (SaaS industry)
    - 2 contacts per company (40 total)
    - 15 recommendations + approvals (5 pending, 5 approved, 5 rejected)
    - Memory entries for all 20 companies
    """
    sales_user = db.query(User).filter(User.email == "sales@agentforge.ai").first()
    if not sales_user:
        logger.warning("Sales user not found, skipping demo workflow")
        return

    # Check if demo workflow already exists
    existing_wf = db.query(Workflow).filter(
        Workflow.user_id == sales_user.id,
        Workflow.status == "completed",
    ).first()
    if existing_wf:
        logger.info("Demo workflow already exists, skipping")
        return

    # Get the B2B SaaS campaign
    admin = db.query(User).filter(User.email == "admin@agentforge.ai").first()
    b2b_saas_campaign = db.query(Campaign).filter(
        Campaign.user_id == admin.id,
        Campaign.domain == "b2b_saas",
    ).first()

    # Fallback: find any campaign
    if not b2b_saas_campaign:
        b2b_saas_campaign = db.query(Campaign).first()

    if not b2b_saas_campaign:
        logger.warning("No campaign found, skipping demo workflow")
        return

    # Also grab an ICP config for the legacy FK
    icp_config = db.query(Configuration).filter(
        Configuration.user_id == admin.id,
        Configuration.name == "B2B Saas - ICP",
    ).first()
    if not icp_config:
        icp_config = db.query(Configuration).filter(Configuration.type == "icp").first()

    if not icp_config:
        logger.warning("No ICP configuration found, skipping demo workflow")
        return

    # Create workflow
    now = datetime.now(timezone.utc)
    workflow = Workflow(
        id=str(uuid.uuid4()),
        user_id=sales_user.id,
        configuration_id=icp_config.id,
        campaign_id=b2b_saas_campaign.id,
        status="completed",
        started_at=now - timedelta(minutes=12),
        completed_at=now - timedelta(minutes=2),
    )
    db.add(workflow)
    db.flush()

    # Get 20 mock companies (SaaS filtered)
    mock_companies = get_mock_companies({"industries": ["SaaS"]})[:20]

    # If less than 20, pad with unfiltered
    if len(mock_companies) < 20:
        all_companies = get_mock_companies({})
        for c in all_companies:
            if len(mock_companies) >= 20:
                break
            if c not in mock_companies:
                mock_companies.append(c)

    company_ids = []
    for company_data in mock_companies:
        score = round(random.uniform(25, 95), 1)
        status = "validated" if score >= 40 else "rejected"

        company = Company(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            name=company_data["name"],
            domain=company_data["domain"],
            industry=company_data["industry"],
            country=company_data["country"],
            employee_count=company_data["employee_count"],
            revenue_range=company_data.get("revenue_range"),
            funding_stage=company_data.get("funding_stage"),
            tech_stack_json=company_data.get("tech_stack", []),
            qualification_score=score,
            status=status,
        )
        db.add(company)
        db.flush()
        company_ids.append(company.id)

        # Create 2 contacts per company
        for _ in range(2):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            role = random.choice(ROLES_POOL)
            dept = random.choice(DEPARTMENTS_POOL)
            domain = company_data["domain"]

            contact = Contact(
                id=str(uuid.uuid4()),
                company_id=company.id,
                full_name=f"{first} {last}",
                role=role,
                department=dept,
                email=f"{first.lower()}.{last.lower()}@{domain}",
                phone=f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
                linkedin_url=f"https://linkedin.com/in/{first.lower()}-{last.lower()}",
                confidence_score=round(random.uniform(0.5, 0.95), 2),
            )
            db.add(contact)

    db.flush()

    # Create recommendations + approvals for first 15 companies
    recommendation_companies = company_ids[:15]

    for i, company_id in enumerate(recommendation_companies):
        company = db.query(Company).filter(Company.id == company_id).first()
        score = company.qualification_score or 50

        # Determine priority
        if score > 70:
            priority = "high"
        elif score >= 40:
            priority = "medium"
        else:
            priority = "low"

        rec = Recommendation(
            id=str(uuid.uuid4()),
            company_id=company_id,
            priority=priority,
            reason=(
                f"{company.name} scores {score:.0f}/100. "
                f"Strong alignment in {company.industry} with "
                f"{company.employee_count} employees at {company.funding_stage} stage."
            ),
            suggested_action=f"Send personalized outreach to decision makers at {company.name}",
            outreach_template=(
                f"Hi {{contact_name}},\n\n"
                f"I noticed {company.name} recently raised {company.funding_stage} funding. "
                f"As a {company.industry} company with {company.employee_count} employees, "
                f"you're likely scaling. We can help accelerate your pipeline.\n\n"
                f"Open to a 15-min call?\n\nBest,\n{{sender_name}}"
            ),
            confidence=round(min(score / 100, 0.95), 2),
        )
        db.add(rec)
        db.flush()

        # Approval: first 5 pending, next 5 approved, last 5 rejected
        if i < 5:
            approval_status = "pending"
            decided_at = None
            comment = None
        elif i < 10:
            approval_status = "approved"
            decided_at = now - timedelta(hours=random.randint(1, 24))
            comment = None
        else:
            approval_status = "rejected"
            decided_at = now - timedelta(hours=random.randint(1, 24))
            comment = "Does not meet minimum threshold for outreach"

        approval = Approval(
            id=str(uuid.uuid4()),
            recommendation_id=rec.id,
            reviewer_id=sales_user.id if approval_status != "pending" else None,
            status=approval_status,
            comment=comment,
            decided_at=decided_at,
        )
        db.add(approval)

    db.flush()

    # Write memory entries for all 20 companies
    for company_id in company_ids:
        company = db.query(Company).filter(Company.id == company_id).first()

        memory_entry = Memory(
            id=str(uuid.uuid4()),
            entity_type="company",
            entity_id=company_id,
            summary=(
                f"Discovered and processed {company.name} ({company.domain}). "
                f"Industry: {company.industry}, Score: {company.qualification_score}, "
                f"Status: {company.status}."
            ),
            embedding_id=None,
            last_seen=now,
            metadata_json={
                "domain": company.domain,
                "industry": company.industry,
                "score": company.qualification_score,
                "status": company.status,
                "workflow_id": workflow.id,
            },
        )
        db.add(memory_entry)

    db.commit()
    logger.info(
        f"Seeded demo workflow: {len(company_ids)} companies, "
        f"{len(company_ids) * 2} contacts, 15 recommendations, "
        f"15 approvals, {len(company_ids)} memory entries"
    )
