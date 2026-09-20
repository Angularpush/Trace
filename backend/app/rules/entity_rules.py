"""
TRACE - Entity & Item Mismatch Verification Rules
Validates supplier/vendor identities, buyer/customer information, and unbilled/unmatched items.
"""

from decimal import Decimal
from typing import Dict, List, Any
from app.rules.base import BaseReconciliationRule, DiscrepancyResult, RuleEvidenceItem
from app.semantic.matcher import semantic_matcher

class SupplierMismatchRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "SUPPLIER_MISMATCH"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        docs = transaction_data.get("documents_by_type", {})
        po_doc = docs.get("PURCHASE_ORDER")
        inv_doc = docs.get("INVOICE")

        if not po_doc or not inv_doc:
            return discrepancies

        po_supp = po_doc.get("parsed_data", {}).get("supplier_name")
        inv_supp = inv_doc.get("parsed_data", {}).get("supplier_name")

        if po_supp and inv_supp:
            sim, is_match = semantic_matcher.match_supplier(po_supp, inv_supp)
            if not is_match:
                discrepancies.append(DiscrepancyResult(
                    rule_code=self.rule_code,
                    discrepancy_type="UNMATCHED_SUPPLIER",
                    title=f"Supplier Name Mismatch: '{po_supp}' vs '{inv_supp}'",
                    description=(
                        f"Supplier identified in Purchase Order ('{po_supp}') does not match "
                        f"the issuing seller on the Tax Invoice ('{inv_supp}') (Semantic similarity: {sim:.2f})."
                    ),
                    severity="CRITICAL",
                    confidence=round(1.0 - sim, 2),
                    difference_amount=Decimal("0.00"),
                    expected_value=po_supp,
                    actual_value=inv_supp,
                    difference_value=f"Entity Identity Mismatch (Sim: {sim:.2f})",
                    evidences=[
                        RuleEvidenceItem(
                            document_id=po_doc.get("id", "PO"),
                            document_name=po_doc.get("filename", "PO.pdf"),
                            page_number=1,
                            field_name="supplier_name",
                            exact_value=po_supp,
                            snippet=f"PO Vendor: {po_supp}",
                            relevance_score=1.0
                        ),
                        RuleEvidenceItem(
                            document_id=inv_doc.get("id", "INV"),
                            document_name=inv_doc.get("filename", "Invoice.pdf"),
                            page_number=1,
                            field_name="supplier_name",
                            exact_value=inv_supp,
                            snippet=f"Invoice Seller: {inv_supp}",
                            relevance_score=1.0
                        )
                    ]
                ))

        return discrepancies


class CustomerMismatchRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "CUSTOMER_MISMATCH"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        docs = transaction_data.get("documents_by_type", {})
        po_doc = docs.get("PURCHASE_ORDER")
        inv_doc = docs.get("INVOICE")

        if not po_doc or not inv_doc:
            return discrepancies

        po_cust = po_doc.get("parsed_data", {}).get("customer_name")
        inv_cust = inv_doc.get("parsed_data", {}).get("customer_name")

        if po_cust and inv_cust:
            sim, is_match = semantic_matcher.match_customer(po_cust, inv_cust)
            if not is_match:
                discrepancies.append(DiscrepancyResult(
                    rule_code=self.rule_code,
                    discrepancy_type="UNMATCHED_CUSTOMER",
                    title=f"Customer/Buyer Mismatch: '{po_cust}' vs '{inv_cust}'",
                    description=f"Buyer name on PO ('{po_cust}') does not align with Invoice consignee ('{inv_cust}').",
                    severity="HIGH",
                    confidence=round(1.0 - sim, 2),
                    difference_amount=Decimal("0.00"),
                    expected_value=po_cust,
                    actual_value=inv_cust,
                    difference_value=f"Buyer Identity Mismatch (Sim: {sim:.2f})",
                    evidences=[
                        RuleEvidenceItem(
                            document_id=po_doc.get("id", "PO"),
                            document_name=po_doc.get("filename", "PO.pdf"),
                            page_number=1,
                            field_name="customer_name",
                            exact_value=po_cust,
                            snippet=f"PO Buyer: {po_cust}",
                            relevance_score=1.0
                        ),
                        RuleEvidenceItem(
                            document_id=inv_doc.get("id", "INV"),
                            document_name=inv_doc.get("filename", "Invoice.pdf"),
                            page_number=1,
                            field_name="customer_name",
                            exact_value=inv_cust,
                            snippet=f"Invoice Consignee: {inv_cust}",
                            relevance_score=1.0
                        )
                    ]
                ))

        return discrepancies


class ItemMismatchRule(BaseReconciliationRule):
    @property
    def rule_code(self) -> str:
        return "ITEM_MISMATCH"

    def evaluate(self, transaction_data: Dict[str, Any]) -> List[DiscrepancyResult]:
        discrepancies: List[DiscrepancyResult] = []
        aligned_items = transaction_data.get("aligned_items", [])
        inv_doc = transaction_data.get("documents_by_type", {}).get("INVOICE")

        if not inv_doc:
            return discrepancies

        for item_pair in aligned_items:
            po_item = item_pair.get("po_item")
            inv_item = item_pair.get("invoice_item")

            # Invoiced item with no matching PO item
            if inv_item and not po_item:
                item_desc = inv_item.get("description", "Unknown Item")
                item_val = inv_item.get("total_amount", "0.00")
                discrepancies.append(DiscrepancyResult(
                    rule_code=self.rule_code,
                    discrepancy_type="UNAUTHORIZED_INVOICE_ITEM",
                    title=f"Unordered Item in Invoice: '{item_desc}'",
                    description=f"Item '{item_desc}' was billed on Invoice for INR {item_val} but was never included in the authorized Purchase Order.",
                    severity="HIGH",
                    confidence=0.92,
                    difference_amount=Decimal(item_val),
                    expected_value="Authorized Line Item in PO",
                    actual_value=f"Unordered Item: {item_desc}",
                    difference_value=f"₹{item_val} uncontracted charge",
                    evidences=[
                        RuleEvidenceItem(
                            document_id=inv_doc.get("id", "INV"),
                            document_name=inv_doc.get("filename", "Invoice.pdf"),
                            page_number=inv_item.get("page_number", 1),
                            field_name="description",
                            exact_value=item_desc,
                            snippet=inv_item.get("evidence_snippet") or f"Billed Item: {item_desc}",
                            relevance_score=1.0
                        )
                    ]
                ))

        return discrepancies
