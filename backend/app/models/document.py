"""
TRACE - Document & TransactionDocument Models
Enforces the architectural principle: FILE != DOCUMENT != TRANSACTION.
One File may contain multiple Documents (e.g., multi-page scanned PDF).
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table retained for SQLAlchemy secondary queries
transaction_documents = Table(
    "transaction_documents",
    Base.metadata,
    Column("transaction_id", String, ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", String, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("link_method", String, default="exact_identifier"),
    Column("link_confidence", Float, default=1.0),
    Column("confirmed", Boolean, default=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)

class TransactionDocument(Base):
    """
    Explicit entity representation for the link between Transaction and Document.
    Stores matching provenance, linking method, and confidence score.
    """
    __tablename__ = "transaction_document_links"

    id = Column(String, primary_key=True, index=True)
    transaction_id = Column(String, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    link_method = Column(String, default="exact_identifier")  # exact_identifier, metadata_match, semantic_match, user_confirmed, hybrid
    link_confidence = Column(Float, default=1.0)
    confirmed = Column(Boolean, default=False)
    link_details = Column(JSON, default=dict)  # token matches, similarity scores, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="document_links")
    document = relationship("Document", back_populates="transaction_links")


class Document(Base):
    """
    Represents an individual business document extracted from a physical file.
    May span a subset of pages in a multi-document PDF.
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    file_id = Column(String, ForeignKey("files.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Research Data Model Fields
    document_type = Column(String, nullable=False, default="OTHER")  # PURCHASE_ORDER, INVOICE, DELIVERY_NOTE, PAYMENT_RECEIPT, BANK_STATEMENT, CREDIT_NOTE, DEBIT_NOTE, QUOTATION, OTHER
    page_start = Column(Integer, default=1)
    page_end = Column(Integer, default=1)
    document_number = Column(String, nullable=True, index=True)
    confidence = Column(Float, default=1.0)
    extracted_text = Column(Text, default="")
    structured_data = Column(JSON, default=dict)
    classification_method = Column(String, default="ML_CLASSIFIER")  # ML_CLASSIFIER, RULE_HEURISTIC, USER_SPECIFIED

    # Backwards-compatible fields
    filename = Column(String, nullable=False, default="")
    file_path = Column(String, nullable=False, default="")
    file_type = Column(String, default="pdf")
    doc_type = Column(String, nullable=False, default="UNKNOWN")
    classification_confidence = Column(Float, default=0.0)
    original_pdf_id = Column(String, nullable=True, index=True)
    page_number = Column(Integer, default=1)
    page_count = Column(Integer, default=1)
    raw_text = Column(Text, default="")
    parsed_data = Column(JSON, default=dict)
    status = Column(String, default="processed")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    file = relationship("File", back_populates="documents")
    transaction_links = relationship("TransactionDocument", back_populates="document", cascade="all, delete-orphan")
    transactions = relationship("Transaction", secondary=transaction_documents, back_populates="documents")
