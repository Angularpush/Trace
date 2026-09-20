"""
TRACE - Normalizer Unit Tests
"""

from decimal import Decimal
from app.extraction.normalizer import (
    normalize_decimal,
    normalize_date,
    clean_entity_name,
    clean_item_description
)

def test_decimal_normalization():
    assert normalize_decimal("500") == Decimal("500.00")
    assert normalize_decimal("INR 1,25,000.50") == Decimal("125000.50")
    assert normalize_decimal("Rs. 45.75") == Decimal("45.75")
    assert normalize_decimal(50.0) == Decimal("50.00")
    assert normalize_decimal(None) == Decimal("0.00")
    assert normalize_decimal("") == Decimal("0.00")

def test_date_normalization():
    assert normalize_date("01-08-2024") == "2024-08-01"
    assert normalize_date("15/09/2024") == "2024-09-15"
    assert normalize_date("2024-10-05") == "2024-10-05"
    assert normalize_date("15th August 2024") == "2024-08-15"
    assert normalize_date(None) is None

def test_clean_entity_name():
    assert "Apex" in clean_entity_name("Apex Industrial Tools Pvt Ltd")
    assert "Kirloskar" in clean_entity_name("Kirloskar Engineering Supplies Limited")

def test_clean_item_description():
    assert "Stainless Steel" in clean_item_description("SS Hex Bolt M10")
    assert "Carbon Steel" in clean_item_description("CS Pipe 2 inch")
    assert "M10" in clean_item_description("SS Bolt 10mm")
