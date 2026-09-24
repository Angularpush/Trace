"""
TRACE - Transactions API Endpoints
Manages multi-document transactions, graph visualization, links, and reports.
"""

from datetime import datetime
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.document import TransactionDocument, Document
from app.models.discrepancy import Discrepancy
from app.schemas.transaction import TransactionResponse, ReconciliationRequest, ReconciliationSummaryReport
from app.schemas.discrepancy import DiscrepancyResponse
from app.reconciliation.linker import transaction_linker
from app.reconciliation.engines.comparator import reconciliation_comparator

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

@router.get("/{txn_id}/graph")
def get_transaction_graph(txn_id: str, db: Session = Depends(get_db)):
    """
    Returns nodes (documents) and edges (provenance links) for visual linking graph display.
    Shows linking methods (exact_identifier, metadata_match, semantic_match, hybrid) and confidence scores.
    """
    graph = transaction_linker.get_transaction_graph(txn_id, db)
    if not graph.get("nodes"):
        raise HTTPException(status_code=404, detail="Transaction not found or has no linked documents")
    return graph

@router.post("/match", response_model=List[TransactionResponse])
@router.post("/auto-link", response_model=List[TransactionResponse])
def match_transactions(db: Session = Depends(get_db)):
    """
    Scans all unlinked/linked documents and clusters them into multi-document transactions using multi-signal graph.
    """
    return transaction_linker.link_database_documents(db)

@router.post("/{txn_id}/links/{link_id}/confirm")
def confirm_document_link(txn_id: str, link_id: str, db: Session = Depends(get_db)):
    """
    Human-in-the-loop link confirmation: confirms or locks a document link.
    """
    link = db.query(TransactionDocument).filter(
        TransactionDocument.id == link_id,
        TransactionDocument.transaction_id == txn_id
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link record not found")
    
    link.confirmed = True
    link.link_method = "user_confirmed"
    link.link_confidence = 1.0
    db.commit()
    return {"status": "confirmed", "link_id": link_id}

@router.delete("/{txn_id}/links/{link_id}")
def remove_document_link(txn_id: str, link_id: str, db: Session = Depends(get_db)):
    """
    Detaches a document from a transaction cluster.
    """
    link = db.query(TransactionDocument).filter(
        TransactionDocument.id == link_id,
        TransactionDocument.transaction_id == txn_id
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link record not found")
    
    doc = db.query(Document).filter(Document.id == link.document_id).first()
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if doc and txn and doc in txn.documents:
        txn.documents.remove(doc)

    db.delete(link)
    db.commit()
    return {"status": "unlinked", "link_id": link_id}

@router.get("/{txn_id}/discrepancies", response_model=List[DiscrepancyResponse])
def get_transaction_discrepancies(txn_id: str, db: Session = Depends(get_db)):
    """
    Retrieves all discrepancies detected for a specific transaction.
    """
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction '{txn_id}' not found")
    return txn.discrepancies

@router.get("/{txn_id}/report", response_model=ReconciliationSummaryReport)
def get_transaction_report(txn_id: str, db: Session = Depends(get_db)):
    """
    Returns audit report for the transaction.
    """
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction '{txn_id}' not found")
    
    doc_dicts = [
        {
            "id": d.id,
            "filename": d.filename,
            "doc_type": d.doc_type,
            "document_type": getattr(d, "document_type", d.doc_type),
            "parsed_data": d.parsed_data or d.structured_data or {}
        }
        for d in txn.documents
    ]
    
    variance = sum(d.difference_amount or 0.0 for d in txn.discrepancies)
    
    return ReconciliationSummaryReport(
        transaction_id=txn.id,
        transaction_ref=txn.transaction_reference or txn.transaction_ref,
        reconciliation_status=txn.status,
        mode_used="HYBRID",
        total_documents=len(txn.documents),
        documents_summary=doc_dicts,
        total_discrepancies=len(txn.discrepancies),
        discrepancies_by_severity={
            "CRITICAL": sum(1 for d in txn.discrepancies if d.severity == "CRITICAL"),
            "HIGH": sum(1 for d in txn.discrepancies if d.severity == "HIGH"),
            "MEDIUM": sum(1 for d in txn.discrepancies if d.severity == "MEDIUM"),
            "LOW": sum(1 for d in txn.discrepancies if d.severity == "LOW")
        },
        discrepancies=[DiscrepancyResponse.model_validate(d) for d in txn.discrepancies],
        financial_variance_amount=variance,
        ai_grounded_explanation=getattr(txn, "reconciliation_summary", "") or (f"Automated multi-document audit identified {len(txn.discrepancies)} discrepancy findings." if txn.discrepancies else "Full consistency verified across all transaction documents."),
        generated_at=datetime.utcnow()
    )

@router.post("/{txn_id}/reconcile", response_model=ReconciliationSummaryReport)
def reconcile_single_transaction(
    txn_id: str,
    mode: str = "HYBRID",
    llm_provider: str = "offline",
    db: Session = Depends(get_db)
):
    """
    Executes reconciliation for a single transaction cluster.
    Runs 3-way comparator and returns the standard ReconciliationSummaryReport.
    """
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn_context = {
        "id": txn.id,
        "transaction_id": txn.id,
        "transaction_reference": txn.transaction_reference or txn.transaction_ref,
        "transaction_ref": txn.transaction_ref,
        "supplier": txn.supplier or txn.supplier_name,
        "customer": txn.customer or txn.customer_name,
        "supplier_name": txn.supplier_name,
        "customer_name": txn.customer_name,
        "total_amount": txn.total_amount,
        "documents": [
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
            for d in txn.documents
        ]
    }
    
    # Run comparator
    reconciliation_comparator.compare_transaction(txn_context, db=db)
    db.refresh(txn)

    doc_dicts = [
        {
            "id": d.id,
            "filename": d.filename,
            "doc_type": d.doc_type,
            "document_type": getattr(d, "document_type", d.doc_type),
            "parsed_data": d.parsed_data or d.structured_data or {}
        }
        for d in txn.documents
    ]
    variance = sum(d.difference_amount or 0.0 for d in txn.discrepancies)

    return ReconciliationSummaryReport(
        transaction_id=txn.id,
        transaction_ref=txn.transaction_reference or txn.transaction_ref,
        reconciliation_status=txn.status or txn.reconciliation_status,
        mode_used=mode,
        total_documents=len(txn.documents),
        documents_summary=doc_dicts,
        total_discrepancies=len(txn.discrepancies),
        discrepancies_by_severity={
            "CRITICAL": sum(1 for d in txn.discrepancies if d.severity == "CRITICAL"),
            "HIGH": sum(1 for d in txn.discrepancies if d.severity == "HIGH"),
            "MEDIUM": sum(1 for d in txn.discrepancies if d.severity == "MEDIUM"),
            "LOW": sum(1 for d in txn.discrepancies if d.severity == "LOW")
        },
        discrepancies=[DiscrepancyResponse.model_validate(d) for d in txn.discrepancies],
        financial_variance_amount=variance,
        ai_grounded_explanation=getattr(txn, "reconciliation_summary", "") or (f"Multi-document audit identified {len(txn.discrepancies)} findings." if txn.discrepancies else "Full consistency verified."),
        generated_at=datetime.utcnow()
    )

@router.delete("/cleanup-empty")
def cleanup_empty_transactions(db: Session = Depends(get_db)):
    """
    Removes empty or zero-total orphaned transactions.
    """
    zero_txns = db.query(Transaction).filter(
        (Transaction.total_amount == 0.0) | (Transaction.transaction_ref.like("TXN-DOC%"))
    ).all()
    deleted_count = len(zero_txns)
    for txn in zero_txns:
        db.delete(txn)
    db.commit()
    return {"status": "success", "deleted_count": deleted_count}

@router.get("/{txn_id}/dispute-notice")
def generate_vendor_dispute_notice(txn_id: str, db: Session = Depends(get_db)):
    """
    Generates a formal, printable Vendor Dispute & Audit Notice with legal citations and itemized variances.
    """
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    supp = txn.supplier or txn.supplier_name or "Vendor / Supplier"
    cust = txn.customer or txn.customer_name or "Buyer Organization"
    txn_ref = txn.transaction_reference or txn.transaction_ref
    today_str = datetime.utcnow().strftime("%d-%B-%Y")
    disp_ref = f"AUDIT-DISP-{txn_ref}-{int(time.time())}"

    variance = sum(d.difference_amount or 0.0 for d in txn.discrepancies)
    
    # Format items table
    discrepancy_rows = []
    for d in txn.discrepancies:
        discrepancy_rows.append({
            "title": d.title,
            "discrepancy_type": d.discrepancy_type,
            "severity": d.severity,
            "expected_value": d.expected_value or "Agreed Contract Rate / Terms",
            "actual_value": d.actual_value or "Billed on Invoice",
            "variance_amount": f"₹{d.difference_amount:,.2f}" if d.difference_amount else "Non-monetary",
            "explanation": d.llm_explanation or d.description,
            "statutory_rule": d.rule_code or d.discrepancy_type
        })

    letter_text = f"""# FORMAL AUDIT DISCREPANCY & DISPUTE NOTICE

**Date**: {today_str}  
**Notice Reference**: `{disp_ref}`  
**Transaction Reference**: `{txn_ref}`  

**TO**:  
**{supp}**  
Accounts Receivable & Billing Department  

**FROM**:  
**{cust}**  
Internal Audit & Accounts Payable Division  

---

### SUBJECT: Formal Notice of Invoice Discrepancy & Withholding Notice for {txn_ref}

Dear Vendor Billing Team,

During the automated 3-way financial and documentary audit of transaction **{txn_ref}**, our audit verification system (**TRACE**) identified **{len(txn.discrepancies)} actionable discrepancy finding(s)** resulting in a cumulative financial variance of **₹{variance:,.2f}**.

### 1. Itemized Summary of Audit Findings

"""
    for idx, r in enumerate(discrepancy_rows, 1):
        letter_text += f"""#### [{idx}] {r['title']} ({r['severity']} Severity)
- **Category**: `{r['discrepancy_type']}`
- **Authorized / Expected**: {r['expected_value']}
- **Billed / Actual**: {r['actual_value']}
- **Disputed Financial Variance**: **{r['variance_amount']}**
- **Audit Explanation**: {r['explanation']}

"""

    letter_text += f"""---

### 2. Action Required & Settlement Conditions

In accordance with standard commercial procurement terms and Indian statutory financial controls:

1. **Payment Withholding**: Payment in the amount of **₹{variance:,.2f}** is withheld pending resolution.
2. **Credit Note Issuance**: Please issue an immediate **Credit Note** for the disputed sum of **₹{variance:,.2f}** within five (5) business days.
3. **Document Rectification**: Provide signed Goods Received Notes (GRN) or amended invoices matching the purchase order authorizations.

Thank you for your prompt cooperation.

Sincerely,  
**Accounts Payable & Internal Audit Committee**  
*{cust}*  
*Generated automatically by TRACE Multi-Document Reconciliation Engine*
"""

    return {
        "dispute_reference": disp_ref,
        "transaction_id": txn.id,
        "transaction_reference": txn_ref,
        "audit_date": today_str,
        "supplier_name": supp,
        "customer_name": cust,
        "total_discrepancies": len(txn.discrepancies),
        "total_variance_amount": variance,
        "discrepancies": discrepancy_rows,
        "formal_letter_markdown": letter_text
    }
