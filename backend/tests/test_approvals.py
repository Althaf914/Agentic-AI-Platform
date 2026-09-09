import uuid
import pytest
from fastapi.testclient import TestClient

from backend.models.approval import Approval
from backend.models.recommendation import Recommendation
from backend.utils.dependencies import get_current_user
from backend.main import app

def test_list_approvals_endpoint(test_client, test_db, seed_users, seed_companies):
    admin = seed_users["admin"]
    app.dependency_overrides[get_current_user] = lambda: admin

    # Setup recommendation + approval linked to seeded company
    company_id = seed_companies[0]

    rec = Recommendation(
        id=str(uuid.uuid4()),
        company_id=company_id,
        priority="high",
        reason="Good fit",
        suggested_action="outreach",
        outreach_template="Hello {{first_name}}",
    )
    test_db.add(rec)
    test_db.flush()

    appr = Approval(
        id=str(uuid.uuid4()),
        recommendation_id=rec.id,
        status="pending",
    )
    test_db.add(appr)
    test_db.commit()

    response = test_client.get("/api/v1/approvals?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "pending"

def test_decide_approval_approve(test_client, test_db, seed_users, seed_companies):
    admin = seed_users["admin"]
    app.dependency_overrides[get_current_user] = lambda: admin

    # Setup recommendation + approval linked to seeded company
    company_id = seed_companies[0]

    rec = Recommendation(
        id=str(uuid.uuid4()),
        company_id=company_id,
        priority="high",
        reason="Good fit",
        suggested_action="outreach",
        outreach_template="Hello {{first_name}}",
    )
    test_db.add(rec)
    test_db.flush()

    appr = Approval(
        id=str(uuid.uuid4()),
        recommendation_id=rec.id,
        status="pending",
    )
    test_db.add(appr)
    test_db.commit()

    # Call POST to decide approval (approve)
    payload = {
        "status": "approved",
        "comment": "Looks good!",
        "channel": "email",
        "scheduled_at": "now",
    }
    response = test_client.post(f"/api/v1/approvals/{appr.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["comment"] == "Looks good!"

    # Verify state in DB
    db_approval = test_db.query(Approval).filter(Approval.id == appr.id).first()
    assert db_approval.status == "approved"
    assert db_approval.comment == "Looks good!"

def test_decide_approval_reject(test_client, test_db, seed_users, seed_companies):
    admin = seed_users["admin"]
    app.dependency_overrides[get_current_user] = lambda: admin

    # Setup recommendation + approval linked to seeded company
    company_id = seed_companies[0]

    rec = Recommendation(
        id=str(uuid.uuid4()),
        company_id=company_id,
        priority="high",
        reason="Good fit",
        suggested_action="outreach",
        outreach_template="Hello {{first_name}}",
    )
    test_db.add(rec)
    test_db.flush()

    appr = Approval(
        id=str(uuid.uuid4()),
        recommendation_id=rec.id,
        status="pending",
    )
    test_db.add(appr)
    test_db.commit()

    # Call POST to decide approval (reject)
    payload = {
        "status": "rejected",
        "rejection_reason": "not_in_target_market",
        "comment": "Wrong industry",
    }
    response = test_client.post(f"/api/v1/approvals/{appr.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["rejection_reason"] == "not_in_target_market"

    # Verify state in DB
    db_approval = test_db.query(Approval).filter(Approval.id == appr.id).first()
    assert db_approval.status == "rejected"
    assert db_approval.comment == "Wrong industry"
