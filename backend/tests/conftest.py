"""
Pytest fixtures — in-memory SQLite database, test client, seed helpers.
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database.base import Base
import backend.models
from backend.models.user import User
from backend.models.company import Company
from backend.models.workflow import Workflow
from backend.models.configuration import Configuration
from backend.services.auth_service import hash_password


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_client(test_db):
    """FastAPI TestClient with test_db injected as the get_db dependency."""
    from backend.main import app
    from backend.utils.dependencies import get_db

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_users(test_db):
    """Insert admin + sales users, return dict with both."""
    admin = User(
        id=str(uuid.uuid4()),
        email="admin@test.com",
        password_hash=hash_password("test1234"),
        role="admin",
    )
    sales = User(
        id=str(uuid.uuid4()),
        email="sales@test.com",
        password_hash=hash_password("test1234"),
        role="sales",
    )
    test_db.add(admin)
    test_db.add(sales)
    test_db.commit()
    return {"admin": admin, "sales": sales}


@pytest.fixture
def seed_companies(test_db, seed_users):
    """Insert 5 Company rows with known IDs, return list of company_ids."""
    # First create a config and workflow
    admin = seed_users["admin"]

    config = Configuration(
        id=str(uuid.uuid4()),
        user_id=admin.id,
        name="Test ICP",
        type="icp",
        config_json={
            "industries": ["SaaS", "Cloud"],
            "countries": ["United States"],
            "min_employees": 10,
            "max_employees": 1000,
            "funding_stages": ["Series A", "Series B"],
            "tech_stack": ["Python", "React"],
            "hiring_keywords": ["engineer"],
        },
    )
    test_db.add(config)
    test_db.flush()

    workflow = Workflow(
        id=str(uuid.uuid4()),
        user_id=admin.id,
        configuration_id=config.id,
        status="running",
    )
    test_db.add(workflow)
    test_db.flush()

    company_ids = []
    companies_data = [
        ("TestCo Alpha", "testco-alpha.io", "SaaS", "United States", 100, "Series A"),
        ("TestCo Beta", "testco-beta.com", "SaaS", "United States", 200, "Series B"),
        ("TestCo Gamma", "testco-gamma.dev", "Cloud", "United States", 75, "Series A"),
        ("TestCo Delta", "testco-delta.io", "Fintech", "Germany", 300, "Series C"),
        ("TestCo Epsilon", "testco-epsilon.co", "HRTech", "India", 25, "Seed"),
    ]

    for name, domain, industry, country, emp, funding in companies_data:
        has_desc = industry in ("SaaS", "Cloud")
        company = Company(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            name=name,
            domain=domain,
            industry=industry,
            country=country,
            city="San Francisco" if country == "United States" else None,
            employee_count=emp,
            revenue_range="$5M-$10M",
            funding_stage=funding,
            tech_stack_json=["Python", "React"],
            description=(
                f"{name} is a leading {industry} company providing innovative solutions "
                f"to enterprise customers across North America."
            ) if has_desc else None,
            hiring_keywords_json=["engineer", "python", "react"] if has_desc else None,
            qualification_score=None,
            status="pending",
        )
        test_db.add(company)
        company_ids.append(company.id)

    test_db.commit()
    return company_ids
