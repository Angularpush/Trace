"""
TRACE - Transaction Model
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.document import transaction_documents

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    transaction_ref = Column(String, index=True, nullable=False)  # Primary reference like PO Number
    title = Column(String, nullable=False)
    supplier_name = Column(String, default="")
    customer_name = Column(String, default="")
    total_amount = Column(Float, default=0.0)
    reconciliation_status = Column(String, default="PENDING")  # RECONCILED, DISCREPANCY_FOUND, INCOMPLETE
    reconciliation_summary = Column(Text, default="")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", secondary=transaction_documents, back_populates="transactions")
    discrepancies = relationship("Discrepancy", back_populates="transaction", cascade="all, delete-orphan")
