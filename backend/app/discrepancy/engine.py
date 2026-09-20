"""
TRACE - Discrepancy Engine
Executes deterministic financial rules, aligns evidence, and scores severity & confidence.
"""

from decimal import Decimal
from typing import Dict, List, Any
from app.rules import ALL_RULES, BaseReconciliationRule
from app.rules.base import DiscrepancyResult
from app.discrepancy.severity import SeverityCalculator
from app.discrepancy.confidence import ConfidenceCalculator
from app.semantic.matcher import semantic_matcher

class DiscrepancyEngine:
    def __init__(self, rules: List[BaseReconciliationRule] = None):
        self.rules = rules or ALL_RULES

    def run_reconciliation(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        """
        1. Aligns line items across documents using semantic matcher
        2. Evaluates all registered deterministic financial rules
        3. Recalibrates severity and confidence with complete transaction context
        """
        docs = transaction_data.get("documents_by_type", {})
        po_doc = docs.get("PURCHASE_ORDER")
        inv_doc = docs.get("INVOICE")
        dn_doc = docs.get("DELIVERY_NOTE")

        po_items = po_doc.get("parsed_data", {}).get("items", []) if po_doc else []
        inv_items = inv_doc.get("parsed_data", {}).get("items", []) if inv_doc else []
        dn_items = dn_doc.get("parsed_data", {}).get("items", []) if dn_doc else []

        # Align line items across documents
        aligned_items = semantic_matcher.align_line_items(po_items, inv_items, dn_items)
        transaction_data["aligned_items"] = aligned_items

        results: List[DiscrepancyResult] = []

        for rule in self.rules:
            try:
                rule_discrepancies = rule.evaluate(transaction_data)
                for disc in rule_discrepancies:
                    # Deterministic confidence recalibration
                    ext_conf = 0.95
                    has_id_match = bool(po_doc and inv_doc and (
                        po_doc.get("parsed_data", {}).get("document_number") == inv_doc.get("parsed_data", {}).get("po_reference")
                    ))
                    sem_sim = float(disc.metadata.get("semantic_similarity", 0.90))
                    ev_count = len(disc.evidences)

                    disc.confidence = ConfidenceCalculator.calculate_confidence(
                        extraction_confidence=ext_conf,
                        has_exact_identifier_match=has_id_match,
                        semantic_similarity=sem_sim,
                        evidence_count=ev_count,
                        rule_agreement=True
                    )
                    results.append(disc)
            except Exception as e:
                print(f"[DiscrepancyEngine] Error executing rule {rule.rule_code}: {e}")

        return results

discrepancy_engine = DiscrepancyEngine()
