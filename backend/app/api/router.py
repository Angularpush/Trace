"""
TRACE - API Router Aggregation
"""

from fastapi import APIRouter
from app.api.v1.documents import router as documents_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.reconciliation import router as reconciliation_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.evidence import router as evidence_router

api_router = APIRouter()
api_router.include_router(documents_router)
api_router.include_router(transactions_router)
api_router.include_router(reconciliation_router)
api_router.include_router(evaluation_router)
api_router.include_router(dashboard_router)
api_router.include_router(evidence_router)
