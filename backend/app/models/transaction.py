"""
TRACE - Transaction Model
Central business entity linking heterogeneous documents (PO, Invoice, Delivery Note, Payment Receipt, etc.)
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.document import transaction_documents

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    # Research Data Model Fields
    transaction_reference = Column(String, index=True, nullable=False)  # Primary business reference like PO-1001 or TXN-1001
    supplier = Column(String, default="")
    customer = Column(String, default="")
    transaction_date = Column(DateTime, nullable=True)
    currency = Column(String, default="INR")
    status = Column(String, default="PENDING")  # PENDING, RECONCILED, DISCREPANCIES_FOUND
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Legacy / Backwards-compatibility columns
    title = Column(String, default="")
    supplier_name = Column(String, default="")
    customer_name = Column(String, default="")
    transaction_ref = Column(String, default="")
    reconciliation_status = Column(String, default="PENDING")
    reconciliation_summary = Column(Text, default="")
    metadata_json = Column(JSON, default=dict)

    # Relationships
    documents = relationship("Document", secondary=transaction_documents, back_populates="transactions")
    document_links = relationship("TransactionDocument", back_populates="transaction", cascade="all, delete-orphan")
    reconciliation_runs = relationship("ReconciliationRun", back_populates="transaction", cascade="all, delete-orphan")
    discrepancies = relationship("Discrepancy", back_populates="transaction", cascade="all, delete-orphan")
