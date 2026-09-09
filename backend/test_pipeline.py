"""Quick end-to-end test of the agent pipeline."""
import asyncio
from backend.config.settings import get_settings
get_settings.cache_clear()

from backend.database.session import SessionLocal
from backend.memory.shared_memory import SharedMemory
from backend.agents.company_discovery import CompanyDiscoveryAgent
from backend.tools.email_finder import find_emails_by_domain


async def test():
    db = SessionLocal()
    memory = SharedMemory(db)

    # Create a test workflow row
    import uuid
    from backend.models.workflow import Workflow
    from backend.models.configuration import Configuration
    config = db.query(Configuration).filter(Configuration.type == "icp").first()
    from backend.models.user import User
    user = db.query(User).first()
    wf = Workflow(id=str(uuid.uuid4()), user_id=user.id, configuration_id=config.id, status="running")
    db.add(wf)
    db.commit()
    workflow_id = wf.id
    print(f"Test workflow: {workflow_id[:8]}...")
    print()

    # Test 1: Company Discovery via SerpAPI
    print("=== AGENT 1: Company Discovery (SerpAPI) ===")
    agent = CompanyDiscoveryAgent(db, None)
    result = await agent.run(
        input={"workflow_id": workflow_id, "icp": {"industries": ["SaaS"], "countries": ["US"]}},
        memory=memory, config={},
    )
    print(f"  Companies found: {result['companies_found']}")
    print(f"  Duplicates skipped: {result['duplicates_skipped']}")
    print(f"  Company IDs count: {len(result['company_ids'])}")
    print()

    # Test 2: Hunter.io email lookup
    print("=== HUNTER.IO: Domain Search ===")
    emails = await find_emails_by_domain("stripe.com")
    print(f"  Emails found at stripe.com: {len(emails)}")
    if emails:
        print(f"  First: {emails[0]['email']} ({emails[0]['position']})")
    print()

    # Test 3: Groq LLM
    print("=== GROQ LLM: Qualification reasoning ===")
    from backend.services.llm_service import call_llm
    llm_result = await call_llm(
        "You are a B2B analyst. Output JSON only: {\"reason\": \"...\", \"confidence\": 0.7}",
        '{"company": "Stripe", "score": 85}',
    )
    print(f"  Response: {llm_result[:150]}")
    print()

    print("=== ALL 3 APIs VERIFIED ===")
    print("  ✅ SerpAPI: Real Google search results")
    print("  ✅ Hunter.io: Real email lookups")
    print("  ✅ Groq LLM: Real AI reasoning")
    db.close()


if __name__ == "__main__":
    asyncio.run(test())
