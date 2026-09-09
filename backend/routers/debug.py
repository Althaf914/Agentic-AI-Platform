"""
Diagnostic debug router — DELETE after debugging is complete.
Exposes raw database state per workflow to identify data loss in the pipeline.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.company import Company
from backend.models.contact import Contact
from backend.models.recommendation import Recommendation

router = APIRouter()


@router.get("/debug/workflow/{workflow_id}/summary")
def debug_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Return raw data counts per workflow to debug pipeline data loss."""
    companies = db.query(Company).filter(
        Company.workflow_id == workflow_id
    ).all()

    return {
        "total_companies": len(companies),
        "by_status": {
            "pending": len([c for c in companies if c.status == "pending"]),
            "validated": len([c for c in companies if c.status == "validated"]),
            "rejected": len([c for c in companies if c.status == "rejected"]),
        },
        "with_score": len([c for c in companies if c.qualification_score and c.qualification_score > 0]),
        "with_score_breakdown": len([c for c in companies if c.score_breakdown]),
        "with_contacts": len([c for c in companies if c.contacts]),
        "with_recommendations": len([c for c in companies if c.recommendations]),
        "sample_company": {
            "name": companies[0].name if companies else None,
            "status": companies[0].status if companies else None,
            "score": companies[0].qualification_score if companies else None,
            "score_breakdown_keys": list(companies[0].score_breakdown.keys())
                if companies and companies[0].score_breakdown else [],
        } if companies else None,
    }
