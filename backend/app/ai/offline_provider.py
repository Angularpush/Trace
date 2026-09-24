"""
TRACE - Offline Deterministic AI Explanation Provider
Generates evidence-grounded, structured audit summaries locally without external API dependencies.
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
        diff = float(discrepancy.get("difference_amount", 0.0))
        severity = discrepancy.get("severity", "MEDIUM")
        meta = discrepancy.get("metadata", {}) or {}
        
        # Format citations
        doc_names = list(dict.fromkeys([ev.get("document_name") for ev in evidence_items if ev.get("document_name")]))
        doc_ref_str = " and ".join(doc_names) if doc_names else "source document records"

        if rule_code == "PRICE_MISMATCH":
            item = meta.get("item_description") or discrepancy.get("title", "").replace("Price Mismatch: ", "")
            po_p = meta.get("po_unit_price") or discrepancy.get("expected_value", "")
            inv_p = meta.get("inv_unit_price") or discrepancy.get("actual_value", "")
            qty = meta.get("quantity", "all")
            return (
                f"**Root Cause**: Unit price rate inflation detected between {doc_ref_str}. "
                f"The Purchase Order contracted rate is {po_p}, but the Tax Invoice billed at {inv_p}.\n\n"
                f"**Financial Impact**: Total unauthorized price variance of **₹{diff:,.2f}** across {qty} units.\n\n"
                f"**Recommended Action**: Request an immediate Credit Note of ₹{diff:,.2f} from the supplier or deduct this difference before authorizing final payout."
            )

        elif rule_code == "QUANTITY_MISMATCH":
            diff_qty = meta.get("difference_qty") or discrepancy.get("difference_value") or "items"
            inv_qty = meta.get("invoiced_qty") or discrepancy.get("actual_value", "")
            del_qty = meta.get("delivered_qty") or discrepancy.get("expected_value", "")
            if "Overbilled" in title or "EXCEEDS" in discrepancy.get("discrepancy_type", ""):
                return (
                    f"**Root Cause**: Invoiced quantity exceeds physically delivered and verified goods between {doc_ref_str}. "
                    f"The invoice billed {inv_qty}, whereas goods receipt confirms only {del_qty} were delivered ({diff_qty} missing).\n\n"
                    f"**Financial Impact**: Unearned / premature billing risk of **₹{diff:,.2f}** for undelivered inventory.\n\n"
                    f"**Recommended Action**: Withhold payment of ₹{diff:,.2f} until the supplier delivers the remaining units or issues an amended invoice."
                )
            else:
                return (
                    f"**Root Cause**: Physical delivery ({del_qty}) exceeds invoiced quantity ({inv_qty}) between {doc_ref_str}.\n\n"
                    f"**Financial Impact**: Excess inventory received without corresponding invoice charge.\n\n"
                    f"**Recommended Action**: Notify procurement and request supplementary billing for delivered excess."
                )

        elif rule_code in ["PAYMENT_MISMATCH", "PAYMENT_SHORTFALL"]:
            return (
                f"**Root Cause**: Remittance gap between billed invoice total and payment transaction records ({doc_ref_str}).\n\n"
                f"**Financial Impact**: Outstanding unpaid settlement balance of **₹{diff:,.2f}**.\n\n"
                f"**Recommended Action**: Verify whether the ₹{diff:,.2f} variance represents a deliberate withholding (e.g. for defects/credit notes) or schedule the remaining balance remittance."
            )

        elif rule_code == "MISSING_DOCUMENT":
            doc_type = meta.get("missing_type", "mandatory document")
            return (
                f"**Root Cause**: Required 3-way compliance document ({doc_type}) is missing from this transaction.\n\n"
                f"**Audit Risk**: Approving payment without signed delivery verification or commercial invoice violates standard internal AP controls.\n\n"
                f"**Recommended Action**: Request the missing {doc_type} from the vendor / warehouse team before releasing funds."
            )

        elif rule_code == "DUPLICATE_DOCUMENT":
            doc_no = meta.get("duplicate_number", "invoice")
            return (
                f"**Root Cause**: Duplicate document submission detected. Document '{doc_no}' appears multiple times in transaction records.\n\n"
                f"**Financial Risk**: High risk of duplicate double-payment of **₹{diff:,.2f}**.\n\n"
                f"**Recommended Action**: Immediately reject and cancel the duplicate voucher to prevent duplicate cash outflow."
            )

        elif rule_code == "TAX_MISMATCH":
            return (
                f"**Root Cause**: Tax calculation divergence identified between line-item rates and total GST reported in {doc_ref_str}.\n\n"
                f"**Tax Risk**: Potential GST input tax credit (ITC) mismatch of **₹{diff:,.2f}** on GSTR-2B filing.\n\n"
                f"**Recommended Action**: Re-verify HSN/SAC code and applicable CGST/SGST/IGST tax rates with the vendor's billing department."
            )

        elif rule_code == "DATE_MISMATCH":
            return (
                f"**Root Cause**: Chronological sequence anomaly detected between {doc_ref_str}.\n\n"
                f"**Audit Finding**: {desc}\n\n"
                f"**Recommended Action**: Review timestamp log to ensure invoice was not issued prior to purchase order authorization."
            )

        elif rule_code == "ENTITY_MISMATCH" or rule_code == "SUPPLIER_MISMATCH":
            return (
                f"**Root Cause**: Entity legal name or GSTIN number mismatch across {doc_ref_str}.\n\n"
                f"**Compliance Risk**: {desc}\n\n"
                f"**Recommended Action**: Verify vendor Master Data and validate GSTIN on the GST portal to prevent ITC loss."
            )

        else:
            return (
                f"**Root Cause**: Discrepancy detected across {doc_ref_str}: {desc}\n\n"
                f"**Financial Impact**: Variance amount: **₹{diff:,.2f}**.\n\n"
                f"**Recommended Action**: Review attached evidence snippets and adjust transaction records accordingly."
            )

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
                f"Clean 3-Way Reconciliation: All {doc_count} documents for Transaction {transaction_ref} "
                f"(Purchase Order, Delivery Challan, Tax Invoice, Payment) match with 100% mathematical and line-item accuracy. "
                f"No price, quantity, tax, or payment variance detected (Net Variance: ₹0.00). Approved for complete financial settlement."
            )

        critical_count = sum(1 for d in discrepancies if d.get("severity") == "CRITICAL")
        high_count = sum(1 for d in discrepancies if d.get("severity") == "HIGH")
        issues_summary = "; ".join([d.get("title", "") for d in discrepancies[:3]])

        return (
            f"Audit Action Required: Transaction {transaction_ref} has {disc_count} detected discrepancies "
            f"({critical_count} CRITICAL, {high_count} HIGH) totaling a net financial exposure of ₹{financial_variance:,.2f} across {doc_count} documents. "
            f"Primary findings: {issues_summary}. "
            f"Decision Support: Place payment on hold and request vendor credit adjustments / delivery verification as outlined in the discrepancy breakdown."
        )
