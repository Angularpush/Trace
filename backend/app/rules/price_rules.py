"""
TRACE - Price Mismatch Rule
Detects unit price discrepancies between Purchase Orders and Invoices using Decimal.
"""

from decimal import Decimal
from typing import Dict, List, Any
from app.rules.base import BaseReconciliationRule, DiscrepancyResult, RuleEvidenceItem
from app.extraction.normalizer import normalize_decimal

class PriceMismatchRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "PRICE_MISMATCH"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        aligned_items = transaction_data.get("aligned_items", [])
        po_doc = transaction_data.get("documents_by_type", {}).get("PURCHASE_ORDER")
        inv_doc = transaction_data.get("documents_by_type", {}).get("INVOICE")

        if not po_doc or not inv_doc:
            return discrepancies

        for item_pair in aligned_items:
            po_item = item_pair.get("po_item")
            inv_item = item_pair.get("invoice_item")

            if not po_item or not inv_item:
                continue

            po_price = normalize_decimal(po_item.get("unit_price"))
            inv_price = normalize_decimal(inv_item.get("unit_price"))
            inv_qty = normalize_decimal(inv_item.get("quantity"))

            price_diff = inv_price - po_price

            # Check if difference exceeds tolerance
            if abs(price_diff) > Decimal("0.01"):
                # Total variance for this item line
                total_variance = abs(price_diff * inv_qty)
                percent_diff = (abs(price_diff) / po_price * Decimal("100.0")) if po_price > 0 else Decimal("100.0")

                # Determine Severity
                if percent_diff > Decimal("10.0") or total_variance > Decimal("5000.00"):
                    severity = "CRITICAL"
                elif percent_diff > Decimal("3.0") or total_variance > Decimal("1000.00"):
                    severity = "HIGH"
                elif percent_diff > Decimal("1.0"):
                    severity = "MEDIUM"
                else:
                    severity = "LOW"

                item_name = po_item.get("description", "Item")
                evidences = [
                    RuleEvidenceItem(
                        document_id=po_doc.get("id", "PO"),
                        document_name=po_doc.get("filename", "Purchase_Order.pdf"),
                        page_number=po_item.get("page_number", 1),
                        field_name="unit_price",
                        exact_value=f"INR {po_price}",
                        snippet=po_item.get("evidence_snippet") or f"PO Unit Price: INR {po_price}",
                        relevance_score=1.0
                    ),
                    RuleEvidenceItem(
                        document_id=inv_doc.get("id", "INV"),
                        document_name=inv_doc.get("filename", "Invoice.pdf"),
                        page_number=inv_item.get("page_number", 1),
                        field_name="unit_price",
                        exact_value=f"INR {inv_price}",
                        snippet=inv_item.get("evidence_snippet") or f"Invoice Unit Price: INR {inv_price}",
                        relevance_score=1.0
                    )
                ]

                diff_direction = "overcharged" if price_diff > 0 else "undercharged"
                desc = (
                    f"Unit price mismatch detected for item '{item_name}'. "
                    f"Purchase Order agreed price is INR {po_price}/unit, but Invoice billed INR {inv_price}/unit "
                    f"({diff_direction} by INR {abs(price_diff):.2f}/unit, total line variance: INR {total_variance:.2f})."
                )

                discrepancies.append(DiscrepancyResult(
                    rule_code=self.rule_code,
                    discrepancy_type="UNIT_PRICE_VARIANCE",
                    title=f"Price Mismatch: {item_name} ({diff_direction.capitalize()} by INR {abs(price_diff):.2f})",
                    description=desc,
                    severity=severity,
                    confidence=0.95,
                    difference_amount=total_variance,
                    expected_value=f"₹{po_price:.2f}",
                    actual_value=f"₹{inv_price:.2f}",
                    difference_value=f"₹{abs(price_diff):.2f}/unit (Total: ₹{total_variance:.2f})",
                    evidences=evidences,
                    metadata={
                        "po_unit_price": str(po_price),
                        "inv_unit_price": str(inv_price),
                        "variance_per_unit": str(price_diff),
                        "quantity": str(inv_qty)
                    }
                ))

        return discrepancies
