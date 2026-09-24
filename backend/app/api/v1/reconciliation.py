"""
TRACE - Reconciliation API Endpoints
Runs and compares the three reconciliation approaches:
1. RULE_BASED
2. AI_LLM
3. HYBRID
"""

import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.reconciliation import ReconciliationRun, ReconciliationFinding
from app.models.discrepancy import Discrepancy, Evidence
from app.schemas.reconciliation import (
    ReconciliationRunRequest,
    ReconciliationRunResponse,
    ComparisonResultResponse
)
from app.schemas.transaction import ReconciliationRequest, ReconciliationSummaryReport
from app.schemas.discrepancy import DiscrepancyResponse
from app.reconciliation.engines.rule_based import rule_based_engine
from app.reconciliation.engines.ai_llm import ai_llm_engine
from app.reconciliation.engines.hybrid import hybrid_engine
from app.reconciliation.engines.comparator import reconciliation_comparator
from app.reconciliation.orchestrator import reconciliation_orchestrator

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])

def _build_transaction_context(txn: Transaction) -> Dict[str, Any]:
    docs = txn.documents
    doc_dicts = [
        {
            "id": d.id,
            "filename": d.filename,
            "document_type": getattr(d, "document_type", d.doc_type),
            "doc_type": d.doc_type,
            "page_start": getattr(d, "page_start", 1),
            "page_end": getattr(d, "page_end", 1),
            "parsed_data": d.parsed_data or d.structured_data or {},
            "raw_text": d.raw_text or d.extracted_text or "",
            "page_count": d.page_count
        }
        for d in docs
    ]
    return {
        "id": txn.id,
        "transaction_id": txn.id,
        "transaction_reference": txn.transaction_reference or txn.transaction_ref,
        "transaction_ref": txn.transaction_ref,
        "supplier": txn.supplier or txn.supplier_name,
        "customer": txn.customer or txn.customer_name,
        "supplier_name": txn.supplier_name,
        "customer_name": txn.customer_name,
        "total_amount": txn.total_amount,
        "documents": doc_dicts
    }

@router.post("/compare", response_model=ComparisonResultResponse)
def compare_three_approaches(
    req: ReconciliationRunRequest,
    db: Session = Depends(get_db)
):
    """
    Executes all three approaches (RULE_BASED, AI_LLM, HYBRID) on the transaction,
    aligns findings, evaluates consensus vs conflict, and persists execution runs.
    """
    txn = db.query(Transaction).filter(Transaction.id == req.transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn_context = _build_transaction_context(txn)
    comparison = reconciliation_comparator.compare_transaction(txn_context, db=db)
    return comparison

@router.post("/rule", response_model=ReconciliationRunResponse)
def run_rule_based_reconciliation(
    req: ReconciliationRunRequest,
    db: Session = Depends(get_db)
):
    """
    Executes pure deterministic Rule-Based reconciliation (0 LLM calls, $0.00 cost).
    """
    txn = db.query(Transaction).filter(Transaction.id == req.transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn_context = _build_transaction_context(txn)
    result = rule_based_engine.reconcile(txn_context)

    # Persist run
    run_id = f"run_{uuid.uuid4().hex[:10]}"
    db_run = ReconciliationRun(
        id=run_id,
        transaction_id=txn.id,
        approach="RULE_BASED",
        model_version=result.model_version,
        configuration=result.configuration,
        overall_result=result.overall_result,
        execution_time_ms=result.execution_time_ms,
        cost_usd=result.cost_usd,
        findings_count=len(result.findings)
    )
    db.add(db_run)
    db.flush()

    for f in result.findings:
        fnd_id = f"fnd_{uuid.uuid4().hex[:10]}"
        db_f = ReconciliationFinding(
            id=fnd_id,
            reconciliation_run_id=run_id,
            discrepancy_type=f.discrepancy_type,
            severity=f.severity,
            expected_value=f.expected_value,
            actual_value=f.actual_value,
            difference_value=f.difference_value,
            explanation=f.explanation,
            confidence=f.confidence,
            evidence=[e.to_dict() for e in f.evidence],
            source_documents=f.source_documents,
            provenance="rule"
        )
        db.add(db_f)

    db.commit()
    db.refresh(db_run)
    return db_run

@router.post("/ai", response_model=ReconciliationRunResponse)
def run_ai_llm_reconciliation(
    req: ReconciliationRunRequest,
    db: Session = Depends(get_db)
):
    """
    Executes AI/LLM structured prompt reconciliation.
    """
    txn = db.query(Transaction).filter(Transaction.id == req.transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn_context = _build_transaction_context(txn)
    result = ai_llm_engine.reconcile(txn_context)

    run_id = f"run_{uuid.uuid4().hex[:10]}"
    db_run = ReconciliationRun(
        id=run_id,
        transaction_id=txn.id,
        approach="AI_LLM",
        model_version=result.model_version,
        configuration=result.configuration,
        overall_result=result.overall_result,
        execution_time_ms=result.execution_time_ms,
        cost_usd=result.cost_usd,
        findings_count=len(result.findings)
    )
    db.add(db_run)
    db.flush()

    for f in result.findings:
        fnd_id = f"fnd_{uuid.uuid4().hex[:10]}"
        db_f = ReconciliationFinding(
            id=fnd_id,
            reconciliation_run_id=run_id,
            discrepancy_type=f.discrepancy_type,
            severity=f.severity,
            expected_value=f.expected_value,
            actual_value=f.actual_value,
            difference_value=f.difference_value,
            explanation=f.explanation,
            confidence=f.confidence,
            evidence=[e.to_dict() for e in f.evidence],
            source_documents=f.source_documents,
            provenance="llm"
        )
        db.add(db_f)

    db.commit()
    db.refresh(db_run)
    return db_run

@router.post("/hybrid", response_model=ReconciliationRunResponse)
def run_hybrid_reconciliation(
    req: ReconciliationRunRequest,
    db: Session = Depends(get_db)
):
    """
    Executes Hybrid reconciliation combining deterministic rules + semantic embeddings + LLM reasoning.
    """
    txn = db.query(Transaction).filter(Transaction.id == req.transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn_context = _build_transaction_context(txn)
    result = hybrid_engine.reconcile(txn_context)

    run_id = f"run_{uuid.uuid4().hex[:10]}"
    db_run = ReconciliationRun(
        id=run_id,
        transaction_id=txn.id,
        approach="HYBRID",
        model_version=result.model_version,
        configuration=result.configuration,
        overall_result=result.overall_result,
        execution_time_ms=result.execution_time_ms,
        cost_usd=result.cost_usd,
        findings_count=len(result.findings)
    )
    db.add(db_run)
    db.flush()

    for f in result.findings:
        fnd_id = f"fnd_{uuid.uuid4().hex[:10]}"
        db_f = ReconciliationFinding(
            id=fnd_id,
            reconciliation_run_id=run_id,
            discrepancy_type=f.discrepancy_type,
            severity=f.severity,
            expected_value=f.expected_value,
            actual_value=f.actual_value,
            difference_value=f.difference_value,
            explanation=f.explanation,
            confidence=f.confidence,
            evidence=[e.to_dict() for e in f.evidence],
            source_documents=f.source_documents,
            provenance=f.provenance
        )
        db.add(db_f)

    db.commit()
    db.refresh(db_run)
    return db_run

@router.get("/transaction/{txn_id}/comparison", response_model=ComparisonResultResponse)
def get_transaction_comparison(txn_id: str, db: Session = Depends(get_db)):
    """
    Fetches the comparison results between Rule-Based, AI/LLM, and Hybrid runs for a transaction.
    """
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn_context = _build_transaction_context(txn)
    comparison = reconciliation_comparator.compare_transaction(txn_context, db=db)
    return comparison

# Backward-compatible run endpoint
@router.post("/run", response_model=ReconciliationSummaryReport)
def run_reconciliation(
    req: ReconciliationRequest,
    db: Session = Depends(get_db)
):
    txn = db.query(Transaction).filter(Transaction.id == req.transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Run 3-way compare to keep everything synchronized
    txn_context = _build_transaction_context(txn)
    reconciliation_comparator.compare_transaction(txn_context, db=db)

    # Return standard summary report
    doc_dicts = txn_context["documents"]
    result = reconciliation_orchestrator.reconcile_transaction(
        transaction_ref=txn.transaction_reference or txn.transaction_ref,
        documents=doc_dicts,
        mode=req.mode,
        llm_provider_name=req.llm_provider
    )
    return ReconciliationSummaryReport(
        transaction_id=txn.id,
        transaction_ref=txn.transaction_reference or txn.transaction_ref,
        reconciliation_status=txn.status,
        mode_used=req.mode,
        total_documents=len(doc_dicts),
        documents_summary=result.get("documents_summary", []),
        total_discrepancies=len(txn.discrepancies),
        discrepancies_by_severity={
            "CRITICAL": sum(1 for d in txn.discrepancies if d.severity == "CRITICAL"),
            "HIGH": sum(1 for d in txn.discrepancies if d.severity == "HIGH"),
            "MEDIUM": sum(1 for d in txn.discrepancies if d.severity == "MEDIUM"),
            "LOW": sum(1 for d in txn.discrepancies if d.severity == "LOW")
        },
        discrepancies=[DiscrepancyResponse.model_validate(d) for d in txn.discrepancies],
        financial_variance_amount=result.get("financial_variance_amount", 0.0),
        ai_grounded_explanation=result.get("ai_grounded_explanation", ""),
        generated_at=result.get("reconciled_at")
    )
