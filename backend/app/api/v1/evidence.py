"""
TRACE - Evidence API Endpoints
Retrieves grounded evidence items and citations for audit verification.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.discrepancy import Evidence
from app.schemas.discrepancy import EvidenceResponse

router = APIRouter(prefix="/evidence", tags=["evidence"])

@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a single grounded evidence citation by its unique ID.
    """
    ev = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"Evidence citation '{evidence_id}' not found")
    return ev
