"""
Unit tests for all 6 agents using test_db fixture and mock websocket_manager=None.
"""

import uuid
import pytest
import asyncio

from backend.agents.company_discovery import CompanyDiscoveryAgent
from backend.agents.validation_agent import CompanyValidationAgent
from backend.agents.contact_enrichment import ContactEnrichmentAgent
from backend.agents.qualification import QualificationAgent
from backend.models.company import Company
from backend.models.contact import Contact
from backend.models.recommendation import Recommendation
from backend.models.workflow import Workflow
from backend.models.configuration import Configuration
from backend.memory.shared_memory import SharedMemory


def run_async(coro):
    """Helper to run async functions in sync tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestCompanyDiscoveryAgent:
    def test_company_discovery_returns_companies(self, test_db, seed_users):
        """CompanyDiscoveryAgent should discover companies matching ICP."""
        admin = seed_users["admin"]

        # Create workflow
        config = Configuration(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            name="Test",
            type="icp",
            config_json={"industries": ["SaaS"]},
        )
        test_db.add(config)
        wf = Workflow(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            configuration_id=config.id,
            status="running",
        )
        test_db.add(wf)
        test_db.commit()

        agent = CompanyDiscoveryAgent(test_db, websocket_manager=None)
        result = run_async(agent.run(
            input={"workflow_id": wf.id, "icp": {"industries": ["SaaS"]}},
            memory=None,
            config={},
        ))

        assert len(result["company_ids"]) > 0
        assert result["companies_found"] > 0

        # Verify DB rows
        companies = test_db.query(Company).filter(Company.workflow_id == wf.id).all()
        assert len(companies) == result["companies_found"]

    def test_company_discovery_skips_duplicates(self, test_db, seed_users):
        """CompanyDiscoveryAgent should skip companies already in memory."""
        admin = seed_users["admin"]

        config = Configuration(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            name="Test",
            type="icp",
            config_json={"industries": ["SaaS"]},
        )
        test_db.add(config)
        wf = Workflow(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            configuration_id=config.id,
            status="running",
        )
        test_db.add(wf)
        test_db.commit()

        # Pre-write a known domain to memory
        memory = SharedMemory(test_db)
        run_async(memory.write(
            entity_type="company",
            entity_id="existing-co",
            summary="CloudSync Pro already processed",
            metadata={"domain": "cloudsyncpro.io"},
        ))

        agent = CompanyDiscoveryAgent(test_db, websocket_manager=None)
        result = run_async(agent.run(
            input={"workflow_id": wf.id, "icp": {"industries": ["SaaS"]}},
            memory=memory,
            config={},
        ))

        # cloudsyncpro.io should not be in results
        discovered_companies = test_db.query(Company).filter(Company.workflow_id == wf.id).all()
        domains = [c.domain for c in discovered_companies]
        assert "cloudsyncpro.io" not in domains


class TestValidationAgent:
    def test_validation_approves_matching_companies(self, test_db, seed_companies):
        """CompanyValidationAgent should approve companies matching ICP, reject others."""
        import random
        from backend.config.settings import get_settings

        random.seed(42)  # Deterministic for tests

        # Enable mock mode for test environment (no real network calls)
        test_settings = get_settings()
        original_mock = test_settings.USE_MOCK_DATA
        test_settings.USE_MOCK_DATA = True

        company_ids = seed_companies

        # Companies 0,1,2 are SaaS/Cloud + US + valid employee range
        # Company 3 is Fintech + Germany (mismatch)
        # Company 4 is HRTech + India (mismatch)
        icp = {
            "industries": ["SaaS", "Cloud"],
            "countries": ["United States"],
            "min_employees": 10,
            "max_employees": 1000,
        }

        agent = CompanyValidationAgent(test_db, websocket_manager=None)
        # Use workflow_id from the first company
        company = test_db.query(Company).filter(Company.id == company_ids[0]).first()

        result = run_async(agent.run(
            input={
                "workflow_id": company.workflow_id,
                "company_ids": company_ids,
                "icp": icp,
                "pass_threshold": 11,
            },
            memory=None,
            config={},
        ))

        # At least 1 ICP-matching company validated, non-matching ones rejected
        assert result["validated"] >= 1
        assert result["rejected"] >= 2  # At least Delta + Epsilon

        # Verify status updates in DB
        for cid in result["company_ids"]:
            c = test_db.query(Company).filter(Company.id == cid).first()
            assert c.status == "validated"

        # Rejected companies should have status=rejected
        all_cids = company_ids
        validated_set = set(result["company_ids"])
        rejected_cids = [c for c in all_cids if c not in validated_set]
        for cid in rejected_cids:
            c = test_db.query(Company).filter(Company.id == cid).first()
            assert c.status == "rejected"

        # Restore original mock setting
        test_settings.USE_MOCK_DATA = original_mock


class TestContactEnrichmentAgent:
    def test_contact_enrichment_adds_email(self, test_db, seed_companies):
        """ContactEnrichmentAgent should fill email, phone, linkedin for contacts."""
        company_ids = seed_companies
        company = test_db.query(Company).filter(Company.id == company_ids[0]).first()

        # Insert contacts with no email
        contact_ids = []
        for name in ["John Smith", "Jane Doe"]:
            contact = Contact(
                id=str(uuid.uuid4()),
                company_id=company.id,
                full_name=name,
                role="VP Engineering",
                department="Engineering",
                email=None,
                phone=None,
                linkedin_url=None,
                confidence_score=0.0,
            )
            test_db.add(contact)
            contact_ids.append(contact.id)
        test_db.commit()

        agent = ContactEnrichmentAgent(test_db, websocket_manager=None)
        result = run_async(agent.run(
            input={"workflow_id": company.workflow_id, "contact_ids": contact_ids},
            memory=None,
            config={},
        ))

        assert len(result["enriched_contact_ids"]) == 2

        for cid in contact_ids:
            contact = test_db.query(Contact).filter(Contact.id == cid).first()
            assert contact.email is not None
            assert "@" in contact.email
            assert contact.confidence_score > 0


class TestQualificationAgent:
    def test_qualification_score_in_range(self, test_db, seed_companies):
        """QualificationAgent should produce scores between 0 and 100."""
        company_ids = seed_companies
        company = test_db.query(Company).filter(Company.id == company_ids[0]).first()

        scoring = {
            "funding_weight": 0.167,
            "hiring_weight": 0.167,
            "revenue_weight": 0.167,
            "icp_match_weight": 0.167,
            "tech_stack_weight": 0.167,
            "growth_weight": 0.165,
        }

        agent = QualificationAgent(test_db, websocket_manager=None)
        result = run_async(agent.run(
            input={
                "workflow_id": company.workflow_id,
                "company_ids": company_ids,
                "scoring_config": scoring,
                "icp": {"industries": ["SaaS", "Cloud"], "countries": ["United States"]},
            },
            memory=None,
            config={},
        ))

        assert len(result["scored_company_ids"]) == 5

        for cid in result["scored_company_ids"]:
            c = test_db.query(Company).filter(Company.id == cid).first()
            assert c.qualification_score is not None
            assert 0 <= c.qualification_score <= 100

    def test_qualification_creates_recommendations(self, test_db, seed_companies):
        """QualificationAgent should create Recommendation rows."""
        company_ids = seed_companies
        company = test_db.query(Company).filter(Company.id == company_ids[0]).first()

        agent = QualificationAgent(test_db, websocket_manager=None)
        result = run_async(agent.run(
            input={
                "workflow_id": company.workflow_id,
                "company_ids": company_ids,
                "scoring_config": {},
                "icp": {},
            },
            memory=None,
            config={},
        ))

        assert len(result["recommendation_ids"]) == 5

        for rid in result["recommendation_ids"]:
            rec = test_db.query(Recommendation).filter(Recommendation.id == rid).first()
            assert rec is not None
            assert rec.priority in ["high", "medium", "low"]
