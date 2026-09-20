"""
TRACE - Document Model
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

transaction_documents = Table(
    "transaction_documents",
    Base.metadata,
    Column("transaction_id", String, ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", String, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
)

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, default="pdf")
    doc_type = Column(String, nullable=False, default="UNKNOWN")  # PURCHASE_ORDER, INVOICE, etc.
    classification_confidence = Column(Float, default=0.0)
    page_count = Column(Integer, default=1)
    raw_text = Column(Text, default="")
    parsed_data = Column(JSON, default=dict)  # Structured extracted metadata & items
    status = Column(String, default="processed")  # uploaded, processing, processed, error
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", secondary=transaction_documents, back_populates="documents")
