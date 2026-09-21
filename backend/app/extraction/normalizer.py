"""
TRACE - Normalization Utilities
Handles Decimal precision for monetary amounts, date normalization, and text entity cleaning.
"""

import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Optional, Any
from datetime import datetime
from dateutil import parser as date_parser

def normalize_decimal(val: Any) -> Decimal:
    """
    Converts inputs (str, int, float) to strict Decimal quantized to 2 decimal places.
    Strips currency symbols (₹, Rs., INR, $, USD, EUR), OCR glyph variants (■, ▪, ?, I immediately before digits),
    commas, whitespace while preserving decimal points and signs.
    """
    if val is None:
        return Decimal("0.00")
    if isinstance(val, (int, float)):
        return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if isinstance(val, Decimal):
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    val_str = str(val).strip()
    
    # 1. Remove text-based currency names (INR, Rs., Rs, Rupees, USD, EUR, etc.)
    val_str = re.sub(r"(?i)\b(?:inr|rupees?|usd|eur|gbp)\b", "", val_str)
    val_str = re.sub(r"(?i)\brs\.?", "", val_str)
    
    # 2. Remove OCR square glyphs and symbols (■, ▪, □, ₹, $, €, £, ?, |)
    val_str = re.sub(r"[₹\$\€\£\u20b9\u25a0\u25aa\u25a1\u25fe\u25fd\?]", "", val_str)
    
    # 3. Strip leading OCR font artifacts like 'I' or '|' preceding digits (e.g. 'I52,000', 'I3,30,990')
    val_str = re.sub(r"^[I\|l](?=\s*\d)", "", val_str.strip())
    # Also strip 'I' or '|' after whitespace or symbols if preceding digits
    val_str = re.sub(r"(?<=\s)[I\|l](?=\d)", "", val_str)
    
    # 4. Remove commas and whitespace
    val_str = re.sub(r"[\s,]", "", val_str)
    
    # 5. Remove any remaining non-digit characters except '-' and '.'
    val_str = re.sub(r"[^\d\.\-]", "", val_str)
    
    if not val_str or val_str in [".", "-", "-.", "+", "+."]:
        return Decimal("0.00")
    
    try:
        d = Decimal(val_str)
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        match = re.search(r"[-+]?\d+(?:\.\d+)?", val_str)
        if match:
            try:
                return Decimal(match.group(0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            except Exception:
                pass
        return Decimal("0.00")

def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """
    Normalizes diverse date formats (DD-MM-YYYY, DD/MM/YYYY, 19-Sep-2026, 15th Aug 2024, ISO) to YYYY-MM-DD.
    """
    if not date_str or not str(date_str).strip():
        return None
    cleaned = str(date_str).strip()
    # Strip ordinal suffixes (1st, 2nd, 3rd, 4th)
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", cleaned, flags=re.IGNORECASE)
    
    # ISO pattern match YYYY-MM-DD
    iso_m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", cleaned)
    if iso_m:
        y, m, d = iso_m.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

    # Indian numeric format DD-MM-YYYY or DD/MM/YYYY
    dmy_m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})$", cleaned)
    if dmy_m:
        d, m, y = dmy_m.groups()
        if len(y) == 2:
            y = f"20{y}"
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

    # Format like 19-Sep-2026 or 19 Sep 2026 or 19/Sep/2026
    month_names = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    alpha_m = re.match(r"^(\d{1,2})[-\s/]+([A-Za-z]+)[-\s/]+(\d{2,4})$", cleaned)
    if alpha_m:
        d, mon, y = alpha_m.groups()
        mon_lower = mon.lower()
        if mon_lower in month_names:
            m_num = month_names[mon_lower]
            if len(y) == 2:
                y = f"20{y}"
            return f"{int(y):04d}-{m_num:02d}-{int(d):02d}"

    try:
        dt = date_parser.parse(cleaned, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return cleaned

def clean_entity_name(name: Optional[str]) -> str:
    """
    Normalizes company / vendor / customer names for standardized indexing.
    """
    if not name:
        return ""
    text = str(name).strip()
    # Remove common company legal designations and generic corporate suffixes
    text = re.sub(r"(?i)\b(pvt|private|ltd|limited|corp|corporation|co|inc|company|enterprises|industries|industrial|works|group|holdings|traders|trading|solutions|technologies|services)\b", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip().title()
    return text

def clean_item_description(desc: Optional[str]) -> str:
    """
    Cleans and standardizes line item descriptions.
    """
    if not desc:
        return ""
    text = str(desc).strip()
    # Standardize common abbreviations
    text = re.sub(r"(?i)\bss\b", "Stainless Steel", text)
    text = re.sub(r"(?i)\bcs\b", "Carbon Steel", text)
    text = re.sub(r"(?i)\bgr\b", "Grade", text)
    text = re.sub(r"(?i)\bnos\b", "Pieces", text)
    text = re.sub(r"(?i)\bpcs\b", "Pieces", text)
    # Metric fastener size equivalence: 10mm <-> M10, 12mm <-> M12, 16mm <-> M16
    text = re.sub(r"(?i)\b(\d+)mm\b", r"M\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
