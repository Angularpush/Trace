"""
TRACE Financial Rule Engine Registry
"""

from typing import List
from app.rules.base import BaseReconciliationRule
from app.rules.price_rules import PriceMismatchRule
from app.rules.quantity_rules import QuantityMismatchRule
from app.rules.total_rules import TotalMismatchRule, TaxMismatchRule
from app.rules.payment_rules import PaymentMismatchRule
from app.rules.date_rules import DateMismatchRule
from app.rules.missing_doc_rules import MissingDocumentRule
from app.rules.entity_rules import SupplierMismatchRule, CustomerMismatchRule, ItemMismatchRule

ALL_RULES: List[BaseReconciliationRule] = [
    PriceMismatchRule(),
    QuantityMismatchRule(),
    TotalMismatchRule(),
    TaxMismatchRule(),
    PaymentMismatchRule(),
    DateMismatchRule(),
    MissingDocumentRule(),
    SupplierMismatchRule(),
    CustomerMismatchRule(),
    ItemMismatchRule()
]

__all__ = [
    "BaseReconciliationRule", "ALL_RULES",
    "PriceMismatchRule", "QuantityMismatchRule", "TotalMismatchRule",
    "TaxMismatchRule", "PaymentMismatchRule", "DateMismatchRule",
    "MissingDocumentRule", "SupplierMismatchRule", "CustomerMismatchRule", "ItemMismatchRule"
]
