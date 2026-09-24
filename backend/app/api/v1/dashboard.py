"""
TRACE - Dashboard Analytics API Endpoints
Aggregates real-time metrics across documents, transactions, and discrepancies,
plus the 3-way approach comparison matrix for research analytics.
"""

import os
import json
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.document import Document
from app.models.transaction import Transaction
from app.models.discrepancy import Discrepancy
from app.models.reconciliation import ReconciliationRun

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Computes real operational KPI metrics and loads 3-way approach benchmark comparison.
    """
    total_txns = db.query(Transaction).count()
    reconciled_txns = db.query(Transaction).filter(
        (Transaction.reconciliation_status == "RECONCILED") | (Transaction.status == "RECONCILED")
    ).count()
    discrepancy_txns = db.query(Transaction).filter(
        (Transaction.reconciliation_status == "DISCREPANCY_FOUND") | (Transaction.status == "DISCREPANCIES_FOUND")
    ).count()
    needs_review_txns = db.query(Transaction).filter(
        Transaction.status.in_(["INCOMPLETE", "MINOR_VARIANCE", "PENDING"])
    ).count()

    total_docs = db.query(Document).count()
    all_discrepancies = db.query(Discrepancy).all()

    # Total outstanding payment shortfall
    payment_shortfalls = [
        d.difference_amount for d in all_discrepancies 
        if d.rule_code == "PAYMENT_MISMATCH" or "SHORTFALL" in d.discrepancy_type.upper()
    ]
    total_outstanding = sum(payment_shortfalls) if payment_shortfalls else 0.0
    total_invoiced = db.query(func.sum(Transaction.total_amount)).scalar() or 0.0

    # Discrepancies by Type
    type_counts: Dict[str, int] = {}
    for d in all_discrepancies:
        t = d.discrepancy_type
        type_counts[t] = type_counts.get(t, 0) + 1

    # Severity distribution
    severity_counts = {
        "CRITICAL": sum(1 for d in all_discrepancies if d.severity == "CRITICAL"),
        "HIGH": sum(1 for d in all_discrepancies if d.severity == "HIGH"),
        "MEDIUM": sum(1 for d in all_discrepancies if d.severity == "MEDIUM"),
        "LOW": sum(1 for d in all_discrepancies if d.severity == "LOW"),
    }

    # Load 3-way approach benchmark metrics
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    report_path = os.path.join(base_dir, "data", "ground_truth", "latest_evaluation_report.json")
    benchmark_summary = None
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                benchmark_summary = json.load(f)
        except Exception:
            pass

    status_distribution = {
        "RECONCILED": reconciled_txns,
        "DISCREPANCY_FOUND": discrepancy_txns,
        "NEEDS_REVIEW": needs_review_txns
    }

    return {
        "total_transactions": total_txns,
        "reconciled_transactions": reconciled_txns,
        "discrepancy_transactions": discrepancy_txns,
        "needs_review_transactions": needs_review_txns,
        "status_distribution": status_distribution,
        "total_documents": total_docs,
        "total_outstanding_amount": round(total_outstanding, 2),
        "total_invoiced_amount": round(total_invoiced, 2),
        "total_discrepancies": len(all_discrepancies),
        "discrepancies_by_type": type_counts,
        "discrepancies_by_severity": severity_counts,
        "benchmark_summary": benchmark_summary
    }
