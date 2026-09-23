"""
TRACE - ReconciliationRun and ReconciliationFinding Models
Stores experimental executions and discrepancy findings across the 3 approaches:
1. RULE_BASED
2. AI_LLM
3. HYBRID
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id = Column(String, primary_key=True, index=True)
    transaction_id = Column(String, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    approach = Column(String, nullable=False, index=True)  # RULE_BASED, AI_LLM, HYBRID
    run_time = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String, default="1.0.0")
    configuration = Column(JSON, default=dict)
    overall_result = Column(String, default="RECONCILED")  # RECONCILED, DISCREPANCIES_FOUND, ERROR
    execution_time_ms = Column(Float, default=0.0)
    cost_usd = Column(Float, default=0.0)
    findings_count = Column(Integer, default=0)

    transaction = relationship("Transaction", back_populates="reconciliation_runs")
    findings = relationship("ReconciliationFinding", back_populates="reconciliation_run", cascade="all, delete-orphan")


class ReconciliationFinding(Base):
    __tablename__ = "reconciliation_findings"

    id = Column(String, primary_key=True, index=True)
    reconciliation_run_id = Column(String, ForeignKey("reconciliation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    discrepancy_type = Column(String, nullable=False, index=True)
    # QUANTITY_MISMATCH, PRICE_MISMATCH, TAX_MISMATCH, TOTAL_MISMATCH, PAYMENT_MISMATCH,
    # DATE_MISMATCH, SUPPLIER_MISMATCH, CUSTOMER_MISMATCH, ITEM_MISMATCH,
    # MISSING_DOCUMENT, DUPLICATE_DOCUMENT, DOCUMENT_LINKING_ERROR, OTHER
    
    severity = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    expected_value = Column(String, default="")
    actual_value = Column(String, default="")
    difference_value = Column(String, default="")
    explanation = Column(Text, default="")
    confidence = Column(Float, default=1.0)
    evidence = Column(JSON, default=list)  # list of snippet dicts: [{document_id, document_name, page_number, field_name, exact_value, snippet}]
    source_documents = Column(JSON, default=list)  # list of document IDs involved
    provenance = Column(String, default="rule")  # rule, semantic, llm
    created_at = Column(DateTime, default=datetime.utcnow)

    reconciliation_run = relationship("ReconciliationRun", back_populates="findings")
