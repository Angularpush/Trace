"""
TRACE - Supporting Document Parsers (Quotation, Credit Note, Debit Note)
"""

import re
from decimal import Decimal
from typing import Dict, Any, List
from app.extraction.normalizer import normalize_decimal, normalize_date, clean_item_description

class NoteParser:
    @staticmethod
    def parse_quotation(extracted: Dict[str, Any]) -> Dict[str, Any]:
        text = extracted.get("raw_text", "")
        pages = extracted.get("pages", [])
        data: Dict[str, Any] = {
            "document_number": None,
            "document_date": None,
            "due_date": None,
            "supplier_name": None,
            "customer_name": None,
            "items": [],
            "subtotal": "0.00",
            "grand_total": "0.00",
            "extra_metadata": {}
        }
        quote_match = re.search(r"(?:(?:Quotation\s*Ref|Quote\s*ID|Quote\s*No)[:\s]+)([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if quote_match:
            data["document_number"] = quote_match.group(1).strip()
            
        date_match = re.search(r"(?:(?:Quote\s*Date|Date)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            data["document_date"] = normalize_date(date_match.group(1))

        valid_match = re.search(r"(?:(?:Valid\s*Until|Validity)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if valid_match:
            data["due_date"] = normalize_date(valid_match.group(1))

        supplier_match = re.search(r"(?:(?:From|Supplier|Sales\s*Manager)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
        if supplier_match:
            data["supplier_name"] = supplier_match.group(1).strip()

        return data

    @staticmethod
    def parse_credit_note(extracted: Dict[str, Any]) -> Dict[str, Any]:
        text = extracted.get("raw_text", "")
        pages = extracted.get("pages", [])
        data: Dict[str, Any] = {
            "document_number": None,
            "invoice_reference": None,
            "document_date": None,
            "supplier_name": None,
            "adjustment_amount": "0.00",
            "reason_for_adjustment": "Rate Difference / Goods Return",
            "grand_total": "0.00",
            "items": [],
            "extra_metadata": {}
        }
        cn_match = re.search(r"(?:(?:Credit\s*Note\s*No|CN\s*Number)[:\s]+)([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if cn_match:
            data["document_number"] = cn_match.group(1).strip()

        inv_match = re.search(r"(?:(?:Original\s*(?:Tax\s*)?Invoice\s*Ref|Ref\s*Invoice)[:\s]+)([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if inv_match:
            data["invoice_reference"] = inv_match.group(1).strip()

        date_match = re.search(r"(?:(?:Credit\s*Note\s*Date|Date)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            data["document_date"] = normalize_date(date_match.group(1))

        supplier_match = re.search(r"(?:(?:Issued\s*By|Vendor|From)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
        if supplier_match:
            data["supplier_name"] = supplier_match.group(1).strip()

        amt_match = re.search(r"(?:(?:Total\s*Credit\s*Note\s*Amount|Net\s*Credit\s*Allowed|Credit\s*Amount)[:\s]*)(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if amt_match:
            amt = normalize_decimal(amt_match.group(1))
            data["adjustment_amount"] = str(amt)
            data["grand_total"] = str(amt)

        return data

    @staticmethod
    def parse_debit_note(extracted: Dict[str, Any]) -> Dict[str, Any]:
        text = extracted.get("raw_text", "")
        pages = extracted.get("pages", [])
        data: Dict[str, Any] = {
            "document_number": None,
            "invoice_reference": None,
            "document_date": None,
            "supplier_name": None,
            "adjustment_amount": "0.00",
            "reason_for_adjustment": "Underbilling / Supplementary Charges",
            "grand_total": "0.00",
            "items": [],
            "extra_metadata": {}
        }
        dn_match = re.search(r"(?:(?:Debit\s*Note\s*No|DN\s*Number)[:\s]+)([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if dn_match:
            data["document_number"] = dn_match.group(1).strip()

        inv_match = re.search(r"(?:(?:Against\s*Original\s*Invoice|Ref\s*Invoice)[:\s]+)([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if inv_match:
            data["invoice_reference"] = inv_match.group(1).strip()

        date_match = re.search(r"(?:(?:Debit\s*Note\s*Date|Date)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            data["document_date"] = normalize_date(date_match.group(1))

        amt_match = re.search(r"(?:(?:Total\s*Debit\s*Value|Net\s*Debit\s*Amount|Debit\s*Amount)[:\s]*)(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if amt_match:
            amt = normalize_decimal(amt_match.group(1))
            data["adjustment_amount"] = str(amt)
            data["grand_total"] = str(amt)

        return data
