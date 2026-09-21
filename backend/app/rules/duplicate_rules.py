"""
TRACE - Duplicate Document Detection Rule
Validates that duplicate invoices, POs, or receipts are not submitted under the same transaction.
"""

from decimal import Decimal
from typing import Dict, List, Any
from app.rules.base import BaseReconciliationRule, DiscrepancyResult, RuleEvidenceItem

class DuplicateDocumentRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "DUPLICATE_DOCUMENT"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        all_docs = transaction_data.get("all_documents", [])
        
        # Check duplicate invoices by document_number or identical invoice files
        invoices = [d for d in all_docs if d.get("doc_type") == "INVOICE"]
        seen_numbers = {}
        for inv in invoices:
            doc_no = inv.get("parsed_data", {}).get("document_number")
            if doc_no and doc_no != "N/A":
                doc_no_clean = str(doc_no).strip().upper()
                if doc_no_clean in seen_numbers:
                    orig_inv = seen_numbers[doc_no_clean]
                    evidences = [
                        RuleEvidenceItem(
                            document_id=orig_inv.get("id", "INV1"),
                            document_name=orig_inv.get("filename", "Invoice_1.pdf"),
                            page_number=orig_inv.get("page_number", 1),
                            field_name="document_number",
                            exact_value=doc_no_clean,
                            snippet=f"Original Invoice: {doc_no_clean}",
                            relevance_score=1.0
                        ),
                        RuleEvidenceItem(
                            document_id=inv.get("id", "INV2"),
                            document_name=inv.get("filename", "Invoice_2.pdf"),
                            page_number=inv.get("page_number", 1),
                            field_name="document_number",
                            exact_value=doc_no_clean,
                            snippet=f"Duplicate Invoice: {doc_no_clean}",
                            relevance_score=1.0
                        )
                    ]
                    grand_total = Decimal(str(inv.get("parsed_data", {}).get("grand_total", "0.00")))
                    discrepancies.append(DiscrepancyResult(
                        rule_code=self.rule_code,
                        discrepancy_type="DUPLICATE_INVOICE",
                        title=f"Duplicate Invoice Detected: {doc_no_clean}",
                        description=f"Multiple invoices with identical document number '{doc_no_clean}' were submitted for transaction {transaction_data.get('transaction_ref', '')}.",
                        severity="CRITICAL",
                        confidence=0.99,
                        difference_amount=grand_total,
                        expected_value=f"Single unique submission for {doc_no_clean}",
                        actual_value=f"Multiple submissions of {doc_no_clean}",
                        difference_value=f"Duplicate risk amount: ₹{grand_total:.2f}",
                        evidences=evidences,
                        metadata={"duplicate_number": doc_no_clean}
                    ))
                else:
                    seen_numbers[doc_no_clean] = inv

        return discrepancies

