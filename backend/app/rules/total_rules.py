"""
TRACE - Total and Tax Calculation Verification Rules
Validates mathematical integrity of line item sums, GST tax components, and grand totals.
"""

from decimal import Decimal
from typing import Dict, List, Any
from app.rules.base import BaseReconciliationRule, DiscrepancyResult, RuleEvidenceItem
from app.extraction.normalizer import normalize_decimal

class TotalMismatchRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "TOTAL_MISMATCH"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        docs = transaction_data.get("documents_by_type", {})
        inv_doc = docs.get("INVOICE")

        if not inv_doc:
            return discrepancies

        inv_data = inv_doc.get("parsed_data", {})
        items = inv_data.get("items", [])
        stated_subtotal = normalize_decimal(inv_data.get("subtotal"))
        stated_tax = normalize_decimal(inv_data.get("tax_total"))
        stated_grand = normalize_decimal(inv_data.get("grand_total"))

        if items:
            calculated_subtotal = sum(normalize_decimal(it.get("total_amount")) for it in items)
            # Check subtotal math
            if stated_subtotal > 0 and abs(calculated_subtotal - stated_subtotal) > Decimal("1.00"):
                diff = abs(calculated_subtotal - stated_subtotal)
                discrepancies.append(DiscrepancyResult(
                    rule_code=self.rule_code,
                    discrepancy_type="SUBTOTAL_CALCULATION_ERROR",
                    title=f"Subtotal Mismatch: Sum of items (INR {calculated_subtotal}) != Stated subtotal (INR {stated_subtotal})",
                    description=f"The sum of invoice line items (INR {calculated_subtotal:.2f}) does not match the stated taxable subtotal (INR {stated_subtotal:.2f}).",
                    severity="HIGH",
                    confidence=0.99,
                    difference_amount=diff,
                    expected_value=f"₹{calculated_subtotal:.2f}",
                    actual_value=f"₹{stated_subtotal:.2f}",
                    difference_value=f"₹{diff:.2f} math error",
                    evidences=[
                        RuleEvidenceItem(
                            document_id=inv_doc.get("id", "INV"),
                            document_name=inv_doc.get("filename", "Invoice.pdf"),
                            page_number=1,
                            field_name="subtotal",
                            exact_value=f"INR {stated_subtotal}",
                            snippet=f"Stated Taxable Subtotal: INR {stated_subtotal}",
                            relevance_score=1.0
                        )
                    ]
                ))

            # Check Grand Total = Subtotal + Tax
            if stated_grand > 0 and stated_subtotal > 0:
                expected_grand = stated_subtotal + stated_tax
                if abs(stated_grand - expected_grand) > Decimal("1.00"):
                    diff = abs(stated_grand - expected_grand)
                    discrepancies.append(DiscrepancyResult(
                        rule_code=self.rule_code,
                        discrepancy_type="GRAND_TOTAL_MATH_ERROR",
                        title=f"Grand Total Math Error: INR {stated_grand} != Subtotal + Tax (INR {expected_grand})",
                        description=f"Invoice grand total (INR {stated_grand:.2f}) differs from Subtotal (INR {stated_subtotal:.2f}) + Tax (INR {stated_tax:.2f}).",
                        severity="HIGH",
                        confidence=0.99,
                        difference_amount=diff,
                        expected_value=f"₹{expected_grand:.2f}",
                        actual_value=f"₹{stated_grand:.2f}",
                        difference_value=f"₹{diff:.2f} summation error",
                        evidences=[
                            RuleEvidenceItem(
                                document_id=inv_doc.get("id", "INV"),
                                document_name=inv_doc.get("filename", "Invoice.pdf"),
                                page_number=1,
                                field_name="grand_total",
                                exact_value=f"INR {stated_grand}",
                                snippet=f"Stated Grand Total: INR {stated_grand}",
                                relevance_score=1.0
                            )
                        ]
                    ))

        return discrepancies


class TaxMismatchRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "TAX_MISMATCH"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        docs = transaction_data.get("documents_by_type", {})
        inv_doc = docs.get("INVOICE")

        if not inv_doc:
            return discrepancies

        inv_data = inv_doc.get("parsed_data", {})
        stated_subtotal = normalize_decimal(inv_data.get("subtotal"))
        stated_tax = normalize_decimal(inv_data.get("tax_total"))
        items = inv_data.get("items", []) or []

        # Check line item tax sum vs stated tax total
        calc_tax = Decimal("0.00")
        has_item_tax = False
        for it in items:
            t_amt = it.get("tax_amount")
            t_rate = it.get("tax_rate")
            it_tot = normalize_decimal(it.get("total_amount"))
            if t_amt is not None and normalize_decimal(t_amt) > Decimal("0.00"):
                calc_tax += normalize_decimal(t_amt)
                has_item_tax = True
            elif t_rate is not None and normalize_decimal(t_rate) > Decimal("0.00"):
                calc_tax += (it_tot * (normalize_decimal(t_rate) / Decimal("100.00"))).quantize(Decimal("0.01"))
                has_item_tax = True

        if has_item_tax and abs(stated_tax - calc_tax) > Decimal("1.00"):
            diff = abs(stated_tax - calc_tax)
            discrepancies.append(DiscrepancyResult(
                rule_code=self.rule_code,
                discrepancy_type="TAX_CALCULATION_MISMATCH",
                title=f"Tax Calculation Mismatch: Stated INR {stated_tax} != Line Items Tax (INR {calc_tax})",
                description=f"Invoice stated tax total (INR {stated_tax:.2f}) does not match the sum of tax calculated from line item tax rates (INR {calc_tax:.2f}).",
                severity="HIGH",
                confidence=0.98,
                difference_amount=diff,
                expected_value=f"₹{calc_tax:.2f}",
                actual_value=f"₹{stated_tax:.2f}",
                difference_value=f"₹{diff:.2f} tax variance",
                evidences=[
                    RuleEvidenceItem(
                        document_id=inv_doc.get("id", "INV"),
                        document_name=inv_doc.get("filename", "Invoice.pdf"),
                        page_number=1,
                        field_name="tax_total",
                        exact_value=f"INR {stated_tax}",
                        snippet=f"Stated Tax Total: INR {stated_tax}",
                        relevance_score=1.0
                    )
                ]
            ))

        elif stated_subtotal > Decimal("0.00") and stated_tax > Decimal("0.00"):
            # Standard GST rates in India: 5%, 12%, 18%, 28%
            valid_gst_rates = [Decimal("0.05"), Decimal("0.12"), Decimal("0.18"), Decimal("0.28"), Decimal("0.00")]
            effective_rate = (stated_tax / stated_subtotal).quantize(Decimal("0.01"))
            
            # Check if effective rate matches standard slab within 1% rounding
            matched_slab = any(abs(effective_rate - rate) <= Decimal("0.01") for rate in valid_gst_rates)
            if not matched_slab:
                discrepancies.append(DiscrepancyResult(
                    rule_code=self.rule_code,
                    discrepancy_type="INVALID_TAX_CALCULATION",
                    title=f"Unusual Tax Rate: Effective GST is {effective_rate * Decimal('100.0')}%",
                    description=(
                        f"Invoice taxable value is INR {stated_subtotal:.2f} and stated tax is INR {stated_tax:.2f}, "
                        f"resulting in an effective tax rate of {effective_rate * Decimal('100.0')}%, which deviates from standard GST slabs (5%, 12%, 18%, 28%)."
                    ),
                    severity="MEDIUM",
                    confidence=0.88,
                    difference_amount=Decimal("0.00"),
                    expected_value="5%, 12%, 18%, or 28% Standard GST",
                    actual_value=f"{effective_rate * Decimal('100.0'):.1f}% Effective Rate",
                    difference_value="Non-standard tax slab",
                    evidences=[
                        RuleEvidenceItem(
                            document_id=inv_doc.get("id", "INV"),
                            document_name=inv_doc.get("filename", "Invoice.pdf"),
                            page_number=1,
                            field_name="tax_total",
                            exact_value=f"INR {stated_tax}",
                            snippet=f"Stated GST Tax Amount: INR {stated_tax}",
                            relevance_score=1.0
                        )
                    ]
                ))

        return discrepancies
