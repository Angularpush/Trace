"""
TRACE - Offline Deterministic AI Explanation Provider
Generates evidence-grounded natural language audit summaries locally without external API dependencies.
"""

from typing import Dict, List, Any
from app.ai.base import LLMProvider

class OfflineProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "offline"

    def generate_explanation(
        self,
        discrepancy: Dict[str, Any],
        evidence_items: List[Dict[str, Any]],
        transaction_context: Dict[str, Any]
    ) -> str:
        if not evidence_items and not discrepancy.get("description"):
            return "Insufficient evidence to determine this discrepancy."

        rule_code = discrepancy.get("rule_code", "")
        title = discrepancy.get("title", "")
        desc = discrepancy.get("description", "")
        diff = discrepancy.get("difference_amount", 0.0)
        severity = discrepancy.get("severity", "MEDIUM")

        # Build citation text from evidence items
        citations = []
        for ev in evidence_items:
            doc_name = ev.get("document_name", "Document")
            field = ev.get("field_name", "Field")
            val = ev.get("exact_value", "")
            citations.append(f"{doc_name} ({field}: '{val}')")

        citation_str = "; ".join(citations) if citations else "source document records"

        if rule_code == "PRICE_MISMATCH":
            return (
                f"[Audit Finding - {severity}]: A unit price discrepancy was verified against {citation_str}. "
                f"{desc} This results in a financial exposure of INR {float(diff):,.2f} for human auditor review."
            )
        elif rule_code == "QUANTITY_MISMATCH":
            return (
                f"[Audit Finding - {severity}]: Physical delivery records diverge from billed quantities according to {citation_str}. "
                f"{desc} Potential unearned billing / pending shortfall amount is INR {float(diff):,.2f}."
            )
        elif rule_code == "PAYMENT_MISMATCH":
            return (
                f"[Audit Finding - {severity}]: Settlement reconciliation discrepancy verified against {citation_str}. "
                f"{desc} Variance amount: INR {float(diff):,.2f}."
            )
        elif rule_code == "MISSING_DOCUMENT":
            return (
                f"[Compliance Risk - {severity}]: Transaction lacks mandatory supporting documentation. "
                f"{desc} Recommended action: Request missing challan / invoice before approving payment."
            )
        elif rule_code == "DATE_MISMATCH":
            return (
                f"[Timeline Audit - {severity}]: Chronological sequence violation identified between {citation_str}. "
                f"{desc}"
            )
        elif rule_code == "TAX_MISMATCH":
            return (
                f"[Tax Compliance - {severity}]: GST calculation discrepancy identified in {citation_str}. "
                f"{desc} Verify correct HSN tax slab applicability."
            )
        else:
            return f"[Audit Note - {severity}]: {desc} (Grounding: {citation_str})."

    def generate_reconciliation_summary(
        self,
        transaction_ref: str,
        discrepancies: List[Dict[str, Any]],
        documents_summary: List[Dict[str, Any]],
        financial_variance: float
    ) -> str:
        doc_count = len(documents_summary)
        disc_count = len(discrepancies)

        if disc_count == 0:
            return (
                f"Transaction {transaction_ref} is FULLY RECONCILED. All {doc_count} documents "
                f"(Purchase Order, Delivery Challan, Tax Invoice, Payment) match with 100% mathematical "
                f"and semantic consistency. Net financial variance: INR 0.00."
            )

        critical_count = sum(1 for d in discrepancies if d.get("severity") == "CRITICAL")
        high_count = sum(1 for d in discrepancies if d.get("severity") == "HIGH")

        return (
            f"Reconciliation audit for Transaction {transaction_ref} completed across {doc_count} documents. "
            f"Detected {disc_count} discrepancies ({critical_count} CRITICAL, {high_count} HIGH) "
            f"with a cumulative net financial variance of INR {financial_variance:,.2f}. "
            f"Primary discrepancies involve {discrepancies[0].get('title', 'discrepancy items')}. "
            f"Decision Support Recommendation: Halt payment disbursement pending credit note or quantity clarification from vendor."
        )
