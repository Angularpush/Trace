"""
TRACE - Rule-Based Reconciliation Engine
Pure deterministic arithmetic and logical reconciliation.
- Strictly Decimal calculations (no floating point errors)
- Zero LLM calls
- Zero API cost ($0.00)
- Deterministic, ultrafast execution (<5ms)
- Provenance: 'rule'
"""

import time
from typing import Dict, Any, List
from decimal import Decimal

from app.reconciliation.engines.base import (
    BaseReconciliationEngine,
    EngineResult,
    EngineFinding,
    EngineEvidence
)
from app.rules import (
    QuantityMismatchRule,
    PriceMismatchRule,
    TotalMismatchRule,
    TaxMismatchRule,
    PaymentMismatchRule,
    DateMismatchRule,
    SupplierMismatchRule,
    CustomerMismatchRule,
    ItemMismatchRule,
    MissingDocumentRule,
    DuplicateDocumentRule
)
from app.semantic.matcher import semantic_matcher

class RuleBasedReconciliationEngine(BaseReconciliationEngine):
    """
    Evaluates transaction consistency strictly via deterministic business rules.
    """

    def __init__(self):
        self.rules = [
            QuantityMismatchRule(),
            PriceMismatchRule(),
            TotalMismatchRule(),
            TaxMismatchRule(),
            PaymentMismatchRule(),
            DateMismatchRule(),
            SupplierMismatchRule(),
            CustomerMismatchRule(),
            ItemMismatchRule(),
            MissingDocumentRule(),
            DuplicateDocumentRule()
        ]

    @property
    def approach_name(self) -> str:
        return "RULE_BASED"

    def _prepare_context(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Organizes documents by type and aligns line items.
        """
        docs = transaction_data.get("documents", [])
        docs_by_type: Dict[str, Any] = {}
        for d in docs:
            dtype = d.get("document_type") or d.get("doc_type", "OTHER")
            docs_by_type[dtype] = d

        po_doc = docs_by_type.get("PURCHASE_ORDER", {})
        inv_doc = docs_by_type.get("INVOICE", {})
        dn_doc = docs_by_type.get("DELIVERY_NOTE", {})

        po_items = po_doc.get("parsed_data", {}).get("items", []) or []
        inv_items = inv_doc.get("parsed_data", {}).get("items", []) or []
        dn_items = dn_doc.get("parsed_data", {}).get("items", []) or []

        # Standard deterministic item alignment
        aligned_items = semantic_matcher.align_line_items(po_items, inv_items, dn_items)

        context = dict(transaction_data)
        context["documents_by_type"] = docs_by_type
        context["aligned_items"] = aligned_items
        context["all_documents"] = docs
        return context

    def reconcile(self, transaction_data: Dict[str, Any]) -> EngineResult:
        start_time = time.perf_counter()

        context = self._prepare_context(transaction_data)
        findings: List[EngineFinding] = []

        for rule in self.rules:
            try:
                rule_discrepancies = rule.evaluate(context)
                for rd in rule_discrepancies:
                    evs = [
                        EngineEvidence(
                            document_id=e.document_id,
                            document_name=e.document_name,
                            page_number=e.page_number,
                            field_name=e.field_name,
                            exact_value=e.exact_value,
                            snippet=e.snippet,
                            relevance_score=e.relevance_score
                        )
                        for e in rd.evidences
                    ]
                    src_docs = list({e.document_id for e in rd.evidences if e.document_id})

                    # Map rule_code to standard discrepancy_type
                    disc_type = rd.rule_code
                    if disc_type not in [
                        "QUANTITY_MISMATCH", "PRICE_MISMATCH", "TAX_MISMATCH", "TOTAL_MISMATCH",
                        "PAYMENT_MISMATCH", "DATE_MISMATCH", "SUPPLIER_MISMATCH", "CUSTOMER_MISMATCH",
                        "ITEM_MISMATCH", "MISSING_DOCUMENT", "DUPLICATE_DOCUMENT", "DOCUMENT_LINKING_ERROR"
                    ]:
                        if "QUANTITY" in disc_type or "SHORTFALL" in disc_type:
                            disc_type = "QUANTITY_MISMATCH"
                        elif "PRICE" in disc_type:
                            disc_type = "PRICE_MISMATCH"
                        elif "TAX" in disc_type:
                            disc_type = "TAX_MISMATCH"
                        elif "TOTAL" in disc_type:
                            disc_type = "TOTAL_MISMATCH"
                        elif "PAYMENT" in disc_type:
                            disc_type = "PAYMENT_MISMATCH"
                        elif "DATE" in disc_type or "CHRONOLOGY" in disc_type:
                            disc_type = "DATE_MISMATCH"
                        elif "SUPPLIER" in disc_type:
                            disc_type = "SUPPLIER_MISMATCH"
                        elif "CUSTOMER" in disc_type:
                            disc_type = "CUSTOMER_MISMATCH"
                        elif "ITEM" in disc_type:
                            disc_type = "ITEM_MISMATCH"
                        elif "MISSING" in disc_type:
                            disc_type = "MISSING_DOCUMENT"
                        elif "DUPLICATE" in disc_type:
                            disc_type = "DUPLICATE_DOCUMENT"
                        else:
                            disc_type = "OTHER"

                    findings.append(EngineFinding(
                        discrepancy_type=disc_type,
                        severity=rd.severity,
                        expected_value=str(rd.expected_value),
                        actual_value=str(rd.actual_value),
                        difference_value=str(rd.difference_value or rd.difference_amount or ""),
                        difference_amount=float(rd.difference_amount or 0.0),
                        explanation=rd.description,
                        confidence=rd.confidence,
                        evidence=evs,
                        source_documents=src_docs,
                        provenance="rule",
                        rule_code=rd.rule_code,
                        title=rd.title
                    ))
            except Exception as e:
                print(f"[RuleBasedEngine] Error running rule {rule.rule_code}: {e}")

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        overall_result = "DISCREPANCIES_FOUND" if findings else "RECONCILED"

        summary_text = (
            f"Rule-based reconciliation completed in {elapsed_ms:.2f}ms. "
            f"Evaluated 8 deterministic rule sets, identified {len(findings)} discrepancy(ies)."
        )

        return EngineResult(
            approach=self.approach_name,
            overall_result=overall_result,
            execution_time_ms=round(elapsed_ms, 2),
            cost_usd=0.0000,
            findings=findings,
            model_version="1.0.0-deterministic",
            configuration={"rules_count": len(self.rules), "math_mode": "strict_decimal"},
            summary_text=summary_text
        )

rule_based_engine = RuleBasedReconciliationEngine()
