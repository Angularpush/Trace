"""
TRACE - Transaction Pydantic Schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.document import DocumentResponse, TransactionDocumentLinkResponse
from app.schemas.discrepancy import DiscrepancyResponse
from app.schemas.reconciliation import ReconciliationRunResponse

class TransactionResponse(BaseModel):
    id: str
    transaction_reference: Optional[str] = None
    supplier: Optional[str] = ""
    customer: Optional[str] = ""
    transaction_date: Optional[datetime] = None
    currency: str = "INR"
    status: str = "PENDING"
    total_amount: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Backwards-compatible aliases
    transaction_ref: Optional[str] = ""
    title: Optional[str] = ""
    supplier_name: Optional[str] = ""
    customer_name: Optional[str] = ""
    reconciliation_status: Optional[str] = "PENDING"
    reconciliation_summary: Optional[str] = ""
    metadata_json: Dict[str, Any] = {}

    documents: List[DocumentResponse] = []
    document_links: List[TransactionDocumentLinkResponse] = []
    discrepancies: List[DiscrepancyResponse] = []
    reconciliation_runs: List[ReconciliationRunResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ReconciliationRequest(BaseModel):
    transaction_id: str
    mode: str = "HYBRID"  # RULE_BASED, AI_LLM, HYBRID
    llm_provider: Optional[str] = None

class ReconciliationSummaryReport(BaseModel):
    transaction_id: str
    transaction_ref: str
    reconciliation_status: str
    mode_used: str
    total_documents: int
    documents_summary: List[Dict[str, Any]]
    total_discrepancies: int
    discrepancies_by_severity: Dict[str, int]
    discrepancies: List[DiscrepancyResponse]
    financial_variance_amount: float
    ai_grounded_explanation: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
