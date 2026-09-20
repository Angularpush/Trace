"""
TRACE - Payment Mismatch Rule
Reconciles Invoice Total vs Payment Receipts (adjusting for Credit/Debit notes).
"""

from decimal import Decimal
from typing import Dict, List, Any
from app.rules.base import BaseReconciliationRule, DiscrepancyResult, RuleEvidenceItem
from app.extraction.normalizer import normalize_decimal

class PaymentMismatchRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "PAYMENT_MISMATCH"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        docs = transaction_data.get("documents_by_type", {})
        inv_doc = docs.get("INVOICE")
        pay_doc = docs.get("PAYMENT_RECEIPT")
        cn_doc = docs.get("CREDIT_NOTE")
        dn_doc = docs.get("DEBIT_NOTE")

        if not inv_doc or not pay_doc:
            return discrepancies

        inv_data = inv_doc.get("parsed_data", {})
        pay_data = pay_doc.get("parsed_data", {})
        
        inv_total = normalize_decimal(inv_data.get("grand_total"))
        paid_amount = normalize_decimal(pay_data.get("payment_amount") or pay_data.get("grand_total"))
        credit_adj = normalize_decimal(cn_doc.get("parsed_data", {}).get("adjustment_amount")) if cn_doc else Decimal("0.00")
        debit_adj = normalize_decimal(dn_doc.get("parsed_data", {}).get("adjustment_amount")) if dn_doc else Decimal("0.00")

        expected_payment = inv_total - credit_adj + debit_adj
        diff = paid_amount - expected_payment

        if abs(diff) > Decimal("1.00"):
            evidences = [
                RuleEvidenceItem(
                    document_id=inv_doc.get("id", "INV"),
                    document_name=inv_doc.get("filename", "Invoice.pdf"),
                    page_number=1,
                    field_name="grand_total",
                    exact_value=f"INR {inv_total}",
                    snippet=f"Invoice Grand Total: INR {inv_total}",
                    relevance_score=1.0
                ),
                RuleEvidenceItem(
                    document_id=pay_doc.get("id", "PAY"),
                    document_name=pay_doc.get("filename", "Payment_Receipt.pdf"),
                    page_number=1,
                    field_name="payment_amount",
                    exact_value=f"INR {paid_amount}",
                    snippet=f"Paid Amount / Remitted: INR {paid_amount}",
                    relevance_score=1.0
                )
            ]

            if cn_doc and credit_adj > 0:
                evidences.append(RuleEvidenceItem(
                    document_id=cn_doc.get("id", "CN"),
                    document_name=cn_doc.get("filename", "Credit_Note.pdf"),
                    page_number=1,
                    field_name="adjustment_amount",
                    exact_value=f"INR {credit_adj}",
                    snippet=f"Credit Note Adjustment: INR {credit_adj}",
                    relevance_score=1.0
                ))

            if diff < 0:
                # Underpaid
                shortfall = abs(diff)
                severity = "HIGH" if shortfall > Decimal("1000.00") else "MEDIUM"
                desc = (
                    f"Payment shortfall detected. Expected payment is INR {expected_payment:.2f} "
                    f"(Invoice: INR {inv_total:.2f}"
                    f"{f' - Credit Note: INR {credit_adj:.2f}' if credit_adj > 0 else ''}"
                    f"{f' + Debit Note: INR {debit_adj:.2f}' if debit_adj > 0 else ''}), "
                    f"but payment record indicates INR {paid_amount:.2f} paid (Shortfall: INR {shortfall:.2f})."
                )
                discrepancies.append(DiscrepancyResult(
                    rule_code=self.rule_code,
                    discrepancy_type="PAYMENT_SHORTFALL",
                    title=f"Payment Shortfall: INR {shortfall:.2f} remaining unpaid",
                    description=desc,
                    severity=severity,
                    confidence=0.99,
                    difference_amount=shortfall,
                    expected_value=f"₹{expected_payment:.2f}",
                    actual_value=f"₹{paid_amount:.2f}",
                    difference_value=f"-₹{shortfall:.2f} unpaid balance",
                    evidences=evidences,
                    metadata={"expected_payment": str(expected_payment), "paid_amount": str(paid_amount), "shortfall": str(shortfall)}
                ))
            else:
                # Overpaid
                overpaid = diff
                severity = "HIGH"
                desc = (
                    f"Overpayment detected. Total invoice liability is INR {expected_payment:.2f}, "
                    f"but INR {paid_amount:.2f} was remitted (Excess paid: INR {overpaid:.2f})."
                )
                discrepancies.append(DiscrepancyResult(
                    rule_code=self.rule_code,
                    discrepancy_type="OVERPAYMENT",
                    title=f"Overpayment: INR {overpaid:.2f} excess remitted",
                    description=desc,
                    severity=severity,
                    confidence=0.99,
                    difference_amount=overpaid,
                    expected_value=f"₹{expected_payment:.2f}",
                    actual_value=f"₹{paid_amount:.2f}",
                    difference_value=f"+₹{overpaid:.2f} excess remitted",
                    evidences=evidences,
                    metadata={"expected_payment": str(expected_payment), "paid_amount": str(paid_amount), "excess": str(overpaid)}
                ))

        return discrepancies
