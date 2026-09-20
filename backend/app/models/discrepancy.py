"""
TRACE - Discrepancy & Evidence Models
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Discrepancy(Base):
    __tablename__ = "discrepancies"

    id = Column(String, primary_key=True, index=True)
    transaction_id = Column(String, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    rule_code = Column(String, nullable=False)  # PRICE_MISMATCH, QUANTITY_MISMATCH, etc.
    discrepancy_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    difference_amount = Column(Float, default=0.0)
    expected_value = Column(String, default="")
    actual_value = Column(String, default="")
    difference_value = Column(String, default="")
    llm_explanation = Column(Text, default="")
    status = Column(String, default="OPEN")  # OPEN, INVESTIGATING, RESOLVED, DISMISSED
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="discrepancies")
    evidences = relationship("Evidence", back_populates="discrepancy", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(String, primary_key=True, index=True)
    discrepancy_id = Column(String, ForeignKey("discrepancies.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String, nullable=False)
    document_name = Column(String, nullable=False)
    page_number = Column(Integer, default=1)
    field_name = Column(String, nullable=False)
    exact_value = Column(String, default="")
    snippet = Column(Text, nullable=False)
    relevance_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    discrepancy = relationship("Discrepancy", back_populates="evidences")
