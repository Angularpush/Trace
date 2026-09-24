"""
TRACE - Reconciliation Engines Package
Exports RuleBasedReconciliationEngine, AILlmReconciliationEngine,
HybridReconciliationEngine, and ReconciliationComparator.
"""

from app.reconciliation.engines.base import (
    BaseReconciliationEngine,
    EngineResult,
    EngineFinding,
    EngineEvidence
)
from app.reconciliation.engines.rule_based import rule_based_engine, RuleBasedReconciliationEngine
from app.reconciliation.engines.ai_llm import ai_llm_engine, AILlmReconciliationEngine
from app.reconciliation.engines.hybrid import hybrid_engine, HybridReconciliationEngine
from app.reconciliation.engines.comparator import reconciliation_comparator, ReconciliationComparator

__all__ = [
    "BaseReconciliationEngine",
    "EngineResult",
    "EngineFinding",
    "EngineEvidence",
    "rule_based_engine",
    "RuleBasedReconciliationEngine",
    "ai_llm_engine",
    "AILlmReconciliationEngine",
    "hybrid_engine",
    "HybridReconciliationEngine",
    "reconciliation_comparator",
    "ReconciliationComparator"
]

