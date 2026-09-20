"""
TRACE - Quantity Mismatch Rule
Detects quantity variances across Purchase Orders, Delivery Notes, and Invoices.
"""

from decimal import Decimal
from typing import Dict, List, Any
from app.rules.base import BaseReconciliationRule, DiscrepancyResult, RuleEvidenceItem
from app.extraction.normalizer import normalize_decimal

class QuantityMismatchRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "QUANTITY_MISMATCH"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        aligned_items = transaction_data.get("aligned_items", [])
        docs = transaction_data.get("documents_by_type", {})
        po_doc = docs.get("PURCHASE_ORDER")
        inv_doc = docs.get("INVOICE")
        dn_doc = docs.get("DELIVERY_NOTE")

        for item_pair in aligned_items:
            po_item = item_pair.get("po_item")
            inv_item = item_pair.get("invoice_item")
            dn_item = item_pair.get("delivery_item")

            po_qty = normalize_decimal(po_item.get("quantity")) if po_item else None
            inv_qty = normalize_decimal(inv_item.get("quantity")) if inv_item else None
            dn_qty = normalize_decimal(dn_item.get("quantity")) if dn_item else None
            unit_price = normalize_decimal(inv_item.get("unit_price")) if inv_item else (normalize_decimal(po_item.get("unit_price")) if po_item else Decimal("0.00"))
            item_name = (po_item.get("description") if po_item else (inv_item.get("description") if inv_item else "Item"))

            # Case 1: Invoiced Qty vs Delivered Qty (Overbilling check)
            if inv_qty is not None and dn_qty is not None and inv_qty != dn_qty:
                diff = inv_qty - dn_qty
                evidences = []
                if inv_doc and inv_item:
                    evidences.append(RuleEvidenceItem(
                        document_id=inv_doc.get("id", "INV"),
                        document_name=inv_doc.get("filename", "Invoice.pdf"),
                        page_number=inv_item.get("page_number", 1),
                        field_name="quantity",
                        exact_value=f"{inv_qty} {inv_item.get('unit', 'PCS')}",
                        snippet=inv_item.get("evidence_snippet") or f"Invoice Quantity: {inv_qty}",
                        relevance_score=1.0
                    ))
                if dn_doc and dn_item:
                    evidences.append(RuleEvidenceItem(
                        document_id=dn_doc.get("id", "DN"),
                        document_name=dn_doc.get("filename", "Delivery_Note.pdf"),
                        page_number=dn_item.get("page_number", 1),
                        field_name="quantity",
                        exact_value=f"{dn_qty} {dn_item.get('unit', 'PCS')}",
                        snippet=dn_item.get("evidence_snippet") or f"Delivered Quantity: {dn_qty}",
                        relevance_score=1.0
                    ))

                if diff > 0:
                    # Invoiced more than delivered
                    variance_amt = diff * unit_price
                    severity = "CRITICAL" if variance_amt > Decimal("1000.00") or diff > Decimal("10") else "HIGH"
                    desc = (
                        f"Overbilling quantity mismatch for '{item_name}'. "
                        f"Invoice billed {inv_qty} units, but Delivery Note records only {dn_qty} units delivered "
                        f"(Excess billed: {diff} units, unearned amount: INR {variance_amt:.2f})."
                    )
                    discrepancies.append(DiscrepancyResult(
                        rule_code=self.rule_code,
                        discrepancy_type="INVOICE_EXCEEDS_DELIVERY",
                        title=f"Quantity Overbilled: {item_name} ({diff} units unreceived)",
                        description=desc,
                        severity=severity,
                        confidence=0.98,
                        difference_amount=variance_amt,
                        expected_value=f"{dn_qty} {inv_item.get('unit', 'PCS') if inv_item else 'units'}",
                        actual_value=f"{inv_qty} {inv_item.get('unit', 'PCS') if inv_item else 'units'}",
                        difference_value=f"+{diff} {inv_item.get('unit', 'PCS') if inv_item else 'units'} excess (₹{variance_amt:.2f})",
                        evidences=evidences,
                        metadata={"invoiced_qty": str(inv_qty), "delivered_qty": str(dn_qty), "difference_qty": str(diff)}
                    ))
                else:
                    # Delivered more than invoiced
                    desc = f"Delivery Note shows {dn_qty} units delivered, whereas Invoice only billed {inv_qty} units."
                    discrepancies.append(DiscrepancyResult(
                        rule_code=self.rule_code,
                        discrepancy_type="DELIVERY_EXCEEDS_INVOICE",
                        title=f"Underbilled Quantity: {item_name} ({abs(diff)} extra units received)",
                        description=desc,
                        severity="LOW",
                        confidence=0.92,
                        difference_amount=Decimal("0.00"),
                        expected_value=f"{dn_qty} {dn_item.get('unit', 'PCS') if dn_item else 'units'}",
                        actual_value=f"{inv_qty} {inv_item.get('unit', 'PCS') if inv_item else 'units'}",
                        difference_value=f"{abs(diff)} {dn_item.get('unit', 'PCS') if dn_item else 'units'} unbilled",
                        evidences=evidences,
                        metadata={"invoiced_qty": str(inv_qty), "delivered_qty": str(dn_qty)}
                    ))

            # Case 2: Delivered Qty vs PO Qty (Shortfall check)
            if po_qty is not None and dn_qty is not None and dn_qty < po_qty and (inv_qty is None or inv_qty == dn_qty):
                shortfall = po_qty - dn_qty
                evidences = []
                if po_doc and po_item:
                    evidences.append(RuleEvidenceItem(
                        document_id=po_doc.get("id", "PO"),
                        document_name=po_doc.get("filename", "Purchase_Order.pdf"),
                        page_number=po_item.get("page_number", 1),
                        field_name="quantity",
                        exact_value=f"{po_qty} {po_item.get('unit', 'PCS')}",
                        snippet=po_item.get("evidence_snippet") or f"PO Ordered Qty: {po_qty}",
                        relevance_score=1.0
                    ))
                if dn_doc and dn_item:
                    evidences.append(RuleEvidenceItem(
                        document_id=dn_doc.get("id", "DN"),
                        document_name=dn_doc.get("filename", "Delivery_Note.pdf"),
                        page_number=dn_item.get("page_number", 1),
                        field_name="quantity",
                        exact_value=f"{dn_qty} {dn_item.get('unit', 'PCS')}",
                        snippet=dn_item.get("evidence_snippet") or f"Delivered Qty: {dn_qty}",
                        relevance_score=1.0
                    ))

                desc = f"Partial delivery detected for '{item_name}'. Purchase Order ordered {po_qty} units, but only {dn_qty} units delivered (Shortfall: {shortfall} units)."
                discrepancies.append(DiscrepancyResult(
                    rule_code=self.rule_code,
                    discrepancy_type="PARTIAL_DELIVERY_SHORTFALL",
                    title=f"Partial Delivery: {item_name} ({shortfall} units pending)",
                    description=desc,
                    severity="MEDIUM",
                    confidence=0.95,
                    difference_amount=shortfall * unit_price,
                    expected_value=f"{po_qty} {po_item.get('unit', 'PCS') if po_item else 'units'}",
                    actual_value=f"{dn_qty} {dn_item.get('unit', 'PCS') if dn_item else 'units'}",
                    difference_value=f"-{shortfall} {po_item.get('unit', 'PCS') if po_item else 'units'} shortfall",
                    evidences=evidences,
                    metadata={"po_qty": str(po_qty), "delivered_qty": str(dn_qty), "shortfall_qty": str(shortfall)}
                ))

        return discrepancies
