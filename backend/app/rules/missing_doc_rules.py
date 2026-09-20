"""
TRACE - Missing Document Verification Rule
Validates standard 3-Way and 4-Way Match document completeness.
"""

from decimal import Decimal
from typing import Dict, List, Any
from app.rules.base import BaseReconciliationRule, DiscrepancyResult, RuleEvidenceItem

class MissingDocumentRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "MISSING_DOCUMENT"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        docs = transaction_data.get("documents_by_type", {})
        po_doc = docs.get("PURCHASE_ORDER")
        inv_doc = docs.get("INVOICE")
        dn_doc = docs.get("DELIVERY_NOTE")
        pay_doc = docs.get("PAYMENT_RECEIPT")

        # 1. Invoice present with no Delivery Note (Unverified receipt)
        if inv_doc and not dn_doc:
            discrepancies.append(DiscrepancyResult(
                rule_code=self.rule_code,
                discrepancy_type="MISSING_DELIVERY_NOTE",
                title="Missing Delivery Note: Invoiced without proof of delivery",
                description="Tax Invoice is present but no Delivery Note / Challan was uploaded to verify physical receipt of goods.",
                severity="HIGH",
                confidence=0.95,
                difference_amount=Decimal("0.00"),
                expected_value="Delivery Note / Goods Receipt Proof Present",
                actual_value="Missing / Not Uploaded",
                difference_value="Unverified Goods Receipt",
                evidences=[
                    RuleEvidenceItem(
                        document_id=inv_doc.get("id", "INV"),
                        document_name=inv_doc.get("filename", "Invoice.pdf"),
                        page_number=1,
                        field_name="document_number",
                        exact_value=inv_doc.get("parsed_data", {}).get("document_number", "Invoice"),
                        snippet=f"Invoice No: {inv_doc.get('parsed_data', {}).get('document_number')}",
                        relevance_score=1.0
                    )
                ]
            ))

        # 2. Payment made without an Invoice
        if pay_doc and not inv_doc:
            discrepancies.append(DiscrepancyResult(
                rule_code=self.rule_code,
                discrepancy_type="MISSING_INVOICE_FOR_PAYMENT",
                title="Missing Invoice: Payment made without corresponding Invoice",
                description="A Payment Receipt exists but there is no underlying Tax Invoice to validate the tax and line item breakdown.",
                severity="CRITICAL",
                confidence=0.98,
                difference_amount=Decimal("0.00"),
                expected_value="Underlying Tax Invoice Present",
                actual_value="Missing / Not Uploaded",
                difference_value="Unverified Payment Liability",
                evidences=[
                    RuleEvidenceItem(
                        document_id=pay_doc.get("id", "PAY"),
                        document_name=pay_doc.get("filename", "Payment_Receipt.pdf"),
                        page_number=1,
                        field_name="payment_amount",
                        exact_value=str(pay_doc.get("parsed_data", {}).get("payment_amount", "")),
                        snippet=f"Payment Voucher: {pay_doc.get('parsed_data', {}).get('document_number')}",
                        relevance_score=1.0
                    )
                ]
            ))

        # 3. Invoice without Purchase Order
        if inv_doc and not po_doc:
            discrepancies.append(DiscrepancyResult(
                rule_code=self.rule_code,
                discrepancy_type="MISSING_PURCHASE_ORDER",
                title="Missing Purchase Order: Invoice issued without authorized PO",
                description="An Invoice was submitted but no matching Purchase Order contract exists to verify agreed rates and authorization.",
                severity="MEDIUM",
                confidence=0.90,
                difference_amount=Decimal("0.00"),
                expected_value="Authorized Purchase Order Contract Present",
                actual_value="Missing / Not Uploaded",
                difference_value="Unauthorized Invoice Submission",
                evidences=[
                    RuleEvidenceItem(
                        document_id=inv_doc.get("id", "INV"),
                        document_name=inv_doc.get("filename", "Invoice.pdf"),
                        page_number=1,
                        field_name="document_number",
                        exact_value=str(inv_doc.get("parsed_data", {}).get("document_number", "")),
                        snippet=f"Invoice No: {inv_doc.get('parsed_data', {}).get('document_number')}",
                        relevance_score=1.0
                    )
                ]
            ))

        return discrepancies
