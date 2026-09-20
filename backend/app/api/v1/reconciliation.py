"""
TRACE - Reconciliation API Endpoints
Runs multi-document financial reconciliation, discrepancy detection, and evidence retrieval.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.discrepancy import Discrepancy, Evidence
from app.schemas.reconciliation import ReconciliationRequest, ReconciliationSummaryReport
from app.reconciliation.orchestrator import reconciliation_orchestrator

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])

@router.post("/run", response_model=ReconciliationSummaryReport)
def run_reconciliation(
    req: ReconciliationRequest,
    db: Session = Depends(get_db)
):
    """
    Executes transaction reconciliation across all linked documents.
    Generates discrepancies, evaluates severity and confidence, retrieves source evidence,
    and constructs grounded LLM explanations.
    """
    txn = db.query(Transaction).filter(Transaction.id == req.transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    docs = txn.documents
    if not docs:
        raise HTTPException(status_code=400, detail="Transaction has no linked documents")

    doc_dicts = [
        {
            "id": d.id,
            "filename": d.filename,
            "doc_type": d.doc_type,
            "parsed_data": d.parsed_data or {},
            "raw_text": d.raw_text,
            "page_count": d.page_count
        }
        for d in docs
    ]

    # Run orchestrator
    result = reconciliation_orchestrator.reconcile_transaction(
        transaction_ref=txn.transaction_ref,
        documents=doc_dicts,
        mode=req.mode,
        llm_provider_name=req.llm_provider
    )

    # Clear old discrepancies for this transaction
    db.query(Discrepancy).filter(Discrepancy.transaction_id == txn.id).delete()

    # Save new discrepancies and evidence
    for disc_data in result.get("discrepancies", []):
        disc_id = f"disc_{uuid.uuid4().hex[:10]}"
        disc_record = Discrepancy(
            id=disc_id,
            transaction_id=txn.id,
            rule_code=disc_data.get("rule_code", "UNKNOWN"),
            discrepancy_type=disc_data.get("discrepancy_type", "GENERAL"),
            severity=disc_data.get("severity", "MEDIUM"),
            confidence=float(disc_data.get("confidence", 0.9)),
            title=disc_data.get("title", ""),
            description=disc_data.get("description", ""),
            difference_amount=float(disc_data.get("difference_amount", 0.0)),
            expected_value=disc_data.get("expected_value", ""),
            actual_value=disc_data.get("actual_value", ""),
            difference_value=disc_data.get("difference_value", ""),
            llm_explanation=disc_data.get("llm_explanation", ""),
            status="OPEN"
        )
        db.add(disc_record)

        # Add evidence
        for ev in disc_data.get("evidences", []):
            ev_id = f"ev_{uuid.uuid4().hex[:10]}"
            ev_record = Evidence(
                id=ev_id,
                discrepancy_id=disc_id,
                document_id=ev.get("document_id", "DOC"),
                document_name=ev.get("document_name", "Document"),
                page_number=ev.get("page_number", 1),
                field_name=ev.get("field_name", "Field"),
                exact_value=str(ev.get("exact_value", "")),
                snippet=ev.get("snippet", ""),
                relevance_score=float(ev.get("relevance_score", 1.0))
            )
            db.add(ev_record)

    # Update Transaction Status and Summary
    txn.reconciliation_status = result.get("reconciliation_status", "PENDING")
    txn.reconciliation_summary = result.get("ai_grounded_explanation", "")
    db.commit()
    db.refresh(txn)

    # Build report response
    return ReconciliationSummaryReport(
        transaction_id=txn.id,
        transaction_ref=txn.transaction_ref,
        reconciliation_status=txn.reconciliation_status,
        mode_used=result["mode_used"],
        total_documents=len(docs),
        documents_summary=result["documents_summary"],
        total_discrepancies=result["total_discrepancies"],
        discrepancies_by_severity=result["discrepancies_by_severity"],
        discrepancies=txn.discrepancies,
        financial_variance_amount=result["financial_variance_amount"],
        ai_grounded_explanation=txn.reconciliation_summary,
        generated_at=result["reconciled_at"]
    )

@router.get("/{txn_id}/report", response_model=ReconciliationSummaryReport)
def get_reconciliation_report(txn_id: str, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    docs = txn.documents
    discs = txn.discrepancies
    docs_summary = [
        {"filename": d.filename, "doc_type": d.doc_type, "status": d.status}
        for d in docs
    ]

    total_var = sum(float(d.difference_amount) for d in discs)
    discs_by_sev = {
        "CRITICAL": sum(1 for d in discs if d.severity == "CRITICAL"),
        "HIGH": sum(1 for d in discs if d.severity == "HIGH"),
        "MEDIUM": sum(1 for d in discs if d.severity == "MEDIUM"),
        "LOW": sum(1 for d in discs if d.severity == "LOW")
    }

    return ReconciliationSummaryReport(
        transaction_id=txn.id,
        transaction_ref=txn.transaction_ref,
        reconciliation_status=txn.reconciliation_status,
        mode_used="HYBRID",
        total_documents=len(docs),
        documents_summary=docs_summary,
        total_discrepancies=len(discs),
        discrepancies_by_severity=discs_by_sev,
        discrepancies=discs,
        financial_variance_amount=round(total_var, 2),
        ai_grounded_explanation=txn.reconciliation_summary or "Reconciliation pending.",
        generated_at=txn.updated_at
    )
