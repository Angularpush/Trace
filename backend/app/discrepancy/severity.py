"""
TRACE - Severity Calculator
Calculates transparent, rule-driven severity levels (LOW, MEDIUM, HIGH, CRITICAL).
"""

from decimal import Decimal
from typing import Dict, Any

class SeverityCalculator:
    @staticmethod
    def calculate_severity(
        rule_code: str,
        difference_amount: Decimal,
        percent_difference: Decimal = Decimal("0.0"),
        extra_context: Dict[str, Any] = None
    ) -> str:
        """
        Determines severity according to transparent thresholds:
        - CRITICAL: Missing invoice for payment, quantity overbilling > 20% or > ₹5000, supplier identity mismatch.
        - HIGH: Price variance > 5% or > ₹1000, payment shortfall > ₹1000, missing delivery note, unordered items.
        - MEDIUM: Price/quantity variance 1-5%, partial delivery shortfall, delivery delay, tax slab irregularity.
        - LOW: Formatting/rounding differences (< ₹1.00), informational variances.
        """
        extra_context = extra_context or {}

        if rule_code in ["SUPPLIER_MISMATCH", "MISSING_INVOICE_FOR_PAYMENT"]:
            return "CRITICAL"

        if rule_code == "QUANTITY_MISMATCH":
            if extra_context.get("discrepancy_type") == "INVOICE_EXCEEDS_DELIVERY":
                if difference_amount > Decimal("2000.00") or percent_difference > Decimal("15.0"):
                    return "CRITICAL"
                return "HIGH"
            elif extra_context.get("discrepancy_type") == "PARTIAL_DELIVERY_SHORTFALL":
                return "MEDIUM"

        if rule_code == "PRICE_MISMATCH":
            if percent_difference > Decimal("10.0") or difference_amount > Decimal("5000.00"):
                return "CRITICAL"
            elif percent_difference > Decimal("3.0") or difference_amount > Decimal("1000.00"):
                return "HIGH"
            elif percent_difference > Decimal("1.0"):
                return "MEDIUM"
            return "LOW"

        if rule_code == "PAYMENT_MISMATCH":
            if difference_amount > Decimal("5000.00"):
                return "CRITICAL"
            elif difference_amount > Decimal("500.00"):
                return "HIGH"
            return "MEDIUM"

        if rule_code in ["TOTAL_MISMATCH", "UNAUTHORIZED_INVOICE_ITEM"]:
            return "HIGH" if difference_amount > Decimal("500.00") else "MEDIUM"

        if rule_code == "MISSING_DOCUMENT":
            return "HIGH"

        if rule_code in ["DATE_MISMATCH", "TAX_MISMATCH"]:
            return "MEDIUM"

        return "LOW"
