"""
TRACE - Transaction and Reconciliation Pydantic Schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.document import DocumentResponse
from app.schemas.discrepancy import DiscrepancyResponse

class TransactionResponse(BaseModel):
    id: str
    transaction_ref: str
    title: str
    supplier_name: str
    customer_name: str
    total_amount: float
    reconciliation_status: str
    reconciliation_summary: str
    metadata_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentResponse] = []
    discrepancies: List[DiscrepancyResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ReconciliationRequest(BaseModel):
    transaction_id: str
    mode: str = "HYBRID"  # RULE_BASED, AI_ONLY, HYBRID
    llm_provider: Optional[str] = None  # offline, openai, anthropic

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
