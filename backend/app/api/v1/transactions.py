"""
TRACE - Transactions API Endpoints
Manages multi-document transactions, matching, reconciliation, reports, and discrepancies.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.discrepancy import Discrepancy
from app.schemas.transaction import TransactionResponse, ReconciliationRequest, ReconciliationSummaryReport
from app.schemas.discrepancy import DiscrepancyResponse
from app.reconciliation.linker import TransactionLinker
from app.reconciliation.orchestrator import reconciliation_orchestrator

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("", response_model=List[TransactionResponse])
@router.get("/", response_model=List[TransactionResponse])
def list_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Returns all transaction clusters ordered by most recent.
    """
    return db.query(Transaction).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{txn_id}", response_model=TransactionResponse)
def get_transaction(txn_id: str, db: Session = Depends(get_db)):
    """
    Retrieves detailed transaction record with linked documents and discrepancies.
    """
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction '{txn_id}' not found")
    return txn

@router.post("/match", response_model=List[TransactionResponse])
@router.post("/auto-link", response_model=List[TransactionResponse])
def match_transactions(db: Session = Depends(get_db)):
    """
    Scans all unlinked/linked documents and clusters them into multi-document transactions.
    """
    return TransactionLinker.link_database_documents(db)

@router.post("/{txn_id}/reconcile", response_model=ReconciliationSummaryReport)
def reconcile_single_transaction(
    txn_id: str,
    mode: str = Query("HYBRID", description="Reconciliation mode: RULE_BASED, AI_ONLY, HYBRID"),
    llm_provider: Optional[str] = Query("offline", description="LLM provider: offline, openai, anthropic"),
    db: Session = Depends(get_db)
):
    """
    Executes deterministic and AI reconciliation for a specific transaction.
    """
    from app.api.v1.reconciliation import run_reconciliation
    req = ReconciliationRequest(transaction_id=txn_id, mode=mode, llm_provider=llm_provider)
    return run_reconciliation(req, db)

@router.get("/{txn_id}/report", response_model=ReconciliationSummaryReport)
def get_transaction_report(txn_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the formal reconciliation audit report for a transaction.
    """
    from app.api.v1.reconciliation import get_reconciliation_report
    return get_reconciliation_report(txn_id, db)

@router.get("/{txn_id}/discrepancies", response_model=List[DiscrepancyResponse])
def get_transaction_discrepancies(txn_id: str, db: Session = Depends(get_db)):
    """
    Retrieves all discrepancies detected for a specific transaction.
    """
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction '{txn_id}' not found")
    return txn.discrepancies

@router.delete("/cleanup-empty")
def cleanup_empty_transactions(db: Session = Depends(get_db)):
    """
    Removes all transactions with 0.00 total amount or no valid documents,
    along with orphaned UNKNOWN documents.
    """
    from app.models.document import Document
    zero_txns = db.query(Transaction).filter(
        (Transaction.total_amount == 0.0) | (Transaction.transaction_ref.like("TXN-DOC%"))
    ).all()
    deleted_count = len(zero_txns)
    for txn in zero_txns:
        db.delete(txn)

    # Clean orphaned UNKNOWN docs
    orphaned_docs = db.query(Document).filter(
        Document.doc_type == "UNKNOWN"
    ).all()
    for doc in orphaned_docs:
        if not doc.transactions:
            db.delete(doc)

    db.commit()
    return {"status": "success", "deleted_transactions": deleted_count}

@router.delete("/{txn_id}")
def delete_transaction(txn_id: str, db: Session = Depends(get_db)):
    """
    Deletes a specific transaction record and its discrepancies.
    """
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction '{txn_id}' not found")
    db.delete(txn)
    db.commit()
    return {"status": "success", "message": f"Transaction '{txn_id}' deleted successfully"}

