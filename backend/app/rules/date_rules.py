"""
TRACE - Date Reconciliation Rule
Validates chronological sequence of transaction documents (PO -> Delivery -> Invoice -> Payment).
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any
from app.rules.base import BaseReconciliationRule, DiscrepancyResult, RuleEvidenceItem

class DateMismatchRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "DATE_MISMATCH"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        docs = transaction_data.get("documents_by_type", {})
        po_doc = docs.get("PURCHASE_ORDER")
        inv_doc = docs.get("INVOICE")
        dn_doc = docs.get("DELIVERY_NOTE")
        pay_doc = docs.get("PAYMENT_RECEIPT")

        po_date_str = po_doc.get("parsed_data", {}).get("document_date") if po_doc else None
        inv_date_str = inv_doc.get("parsed_data", {}).get("document_date") if inv_doc else None
        dn_date_str = dn_doc.get("parsed_data", {}).get("document_date") if dn_doc else None
        due_date_str = po_doc.get("parsed_data", {}).get("due_date") if po_doc else None

        # Check 1: Invoice date precedes PO date (Anachronistic billing)
        if po_date_str and inv_date_str:
            try:
                po_dt = datetime.strptime(po_date_str, "%Y-%m-%d")
                inv_dt = datetime.strptime(inv_date_str, "%Y-%m-%d")
                if inv_dt < po_dt:
                    discrepancies.append(DiscrepancyResult(
                        rule_code=self.rule_code,
                        discrepancy_type="INVOICE_PREDATES_PO",
                        title=f"Chronology Error: Invoice dated ({inv_date_str}) before PO ({po_date_str})",
                        description=f"Invoice date ({inv_date_str}) is prior to the Purchase Order issue date ({po_date_str}).",
                        severity="HIGH",
                        confidence=0.96,
                        difference_amount=Decimal("0.00"),
                        expected_value=f"On/after PO Date ({po_date_str})",
                        actual_value=f"Invoice Date ({inv_date_str})",
                        difference_value="Anachronistic / Backward chronology",
                        evidences=[
                            RuleEvidenceItem(
                                document_id=po_doc.get("id", "PO"),
                                document_name=po_doc.get("filename", "PO.pdf"),
                                page_number=1,
                                field_name="document_date",
                                exact_value=po_date_str,
                                snippet=f"PO Date: {po_date_str}",
                                relevance_score=1.0
                            ),
                            RuleEvidenceItem(
                                document_id=inv_doc.get("id", "INV"),
                                document_name=inv_doc.get("filename", "Invoice.pdf"),
                                page_number=1,
                                field_name="document_date",
                                exact_value=inv_date_str,
                                snippet=f"Invoice Date: {inv_date_str}",
                                relevance_score=1.0
                            )
                        ]
                    ))
            except Exception:
                pass

        # Check 2: Delivery Date after PO Required Delivery Date (Delayed Delivery)
        if due_date_str and dn_date_str:
            try:
                due_dt = datetime.strptime(due_date_str, "%Y-%m-%d")
                dn_dt = datetime.strptime(dn_date_str, "%Y-%m-%d")
                if dn_dt > due_dt:
                    delay_days = (dn_dt - due_dt).days
                    severity = "HIGH" if delay_days > 14 else "MEDIUM"
                    discrepancies.append(DiscrepancyResult(
                        rule_code=self.rule_code,
                        discrepancy_type="DELIVERY_OVERDUE",
                        title=f"Delivery Delay: Delivered {delay_days} days after due date",
                        description=f"Goods dispatched on {dn_date_str}, exceeding agreed delivery deadline of {due_date_str} by {delay_days} days.",
                        severity=severity,
                        confidence=0.95,
                        difference_amount=Decimal("0.00"),
                        expected_value=f"On/before Due Date ({due_date_str})",
                        actual_value=f"Delivered on ({dn_date_str})",
                        difference_value=f"{delay_days} days delayed",
                        evidences=[
                            RuleEvidenceItem(
                                document_id=po_doc.get("id", "PO"),
                                document_name=po_doc.get("filename", "PO.pdf"),
                                page_number=1,
                                field_name="due_date",
                                exact_value=due_date_str,
                                snippet=f"PO Required Delivery Date: {due_date_str}",
                                relevance_score=1.0
                            ),
                            RuleEvidenceItem(
                                document_id=dn_doc.get("id", "DN"),
                                document_name=dn_doc.get("filename", "Delivery_Note.pdf"),
                                page_number=1,
                                field_name="document_date",
                                exact_value=dn_date_str,
                                snippet=f"Dispatch Date: {dn_date_str}",
                                relevance_score=1.0
                            )
                        ]
                    ))
            except Exception:
                pass

        return discrepancies
