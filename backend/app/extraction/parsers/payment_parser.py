"""
TRACE - Payment Receipt / Voucher Parser
Extracts Payment Receipt No, Payment Date, Vendor, Invoice Reference, and Amount Paid.
"""

import re
from decimal import Decimal
from typing import Dict, Any
from app.extraction.normalizer import normalize_decimal, normalize_date

class PaymentReceiptParser:
    @staticmethod
    def parse(extracted: Dict[str, Any]) -> Dict[str, Any]:
        text = extracted.get("raw_text", "")
        pages = extracted.get("pages", [])
        all_lines = []
        for p in pages:
            all_lines.extend(p.get("lines", []))
        if not all_lines:
            all_lines = [l.strip() for l in text.split("\n") if l.strip()]
        
        data: Dict[str, Any] = {
            "document_number": None,
            "invoice_reference": None,
            "po_reference": None,
            "document_date": None,
            "supplier_name": None,
            "payment_amount": "0.00",
            "payment_method": "BANK_TRANSFER",
            "transaction_reference": None,
            "grand_total": "0.00",
            "extra_metadata": {}
        }
        
        # 1. Receipt / Voucher No
        pay_match = re.search(r"(?:Payment\s*Receipt\s*(?:No\.?|Number|#)|Receipt\s*(?:No\.?|Number|#)|Voucher\s*(?:ID|No\.?|#)|Payment\s*Slip\s*Ref)[:\s]*[:=]?\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if pay_match:
            data["document_number"] = pay_match.group(1).strip()

        # 2. Date
        date_match = re.search(r"(?:(?:Payment\s*Date|Date\s*of\s*Remittance|Date)[:\s]*\n*)\s*(\d{4}[-\s/.]\d{1,2}[-\s/.]\d{1,2}|\d{1,2}[-\s/.][A-Za-z0-9]+[-\s/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            raw_d = date_match.group(1).strip()
            data["document_date"] = normalize_date(raw_d)
            data["extra_metadata"]["raw_date"] = raw_d

        # 3. Beneficiary / Paid To / Received From
        paid_to_match = re.search(r"(?:(?:Paid\s*To|Beneficiary\s*Name|Vendor|Received\s*From)[:\s]*\n*)\s*([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division|Technologies)?)", text, re.IGNORECASE)
        if paid_to_match and not any(k in paid_to_match.group(1).lower() for k in ["sample", "test", "actual", "synthetic"]):
            data["supplier_name"] = paid_to_match.group(1).strip()

        if not data["supplier_name"]:
            for l in all_lines[:10]:
                if any(k in l.lower() for k in ["pvt", "ltd", "limited", "solutions", "technologies", "engineering", "works", "supplies"]) and not any(k in l.lower() for k in ["sample", "test", "actual", "synthetic"]):
                    data["supplier_name"] = l.strip()
                    break

        # 4. Invoice Reference
        inv_ref_match = re.search(r"(?:Settlement\s*for\s*(?:Tax\s*)?Invoice|Against\s*Invoice\s*(?:No\.?|Number|#)?|Invoice\s*(?:Reference|Ref\.?|No\.?)|Against\s*Bill/Invoice\s*No\.?)[:\s]*[:=]?\n*\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if inv_ref_match:
            data["invoice_reference"] = inv_ref_match.group(1).strip()

        # 5. PO Reference
        po_ref_match = re.search(r"(?:(?:PO\s*Number\s*Ref|PO\s*Ref|Against\s*PO\s*No\.?)[:\s]*\n*)\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if po_ref_match:
            data["po_reference"] = po_ref_match.group(1).strip()

        # 6. Transaction / UTR ID
        utr_match = re.search(r"(?:(?:Bank\s*Transaction\s*Ref\s*/\s*UTR|Transaction\s*(?:Reference|ID|Ref)|Cheque/NEFT\s*No|UTR)[:\s]*\n*)\s*([A-Z0-9_\-]+)", text, re.IGNORECASE)
        if utr_match:
            data["transaction_reference"] = utr_match.group(1).strip()

        # 7. Payment Mode
        mode_match = re.search(r"(?:Payment\s*Mode|Mode\s*of\s*Payment)[:\s]*\n*\s*([^\n]+)", text, re.IGNORECASE)
        if mode_match:
            data["payment_method"] = mode_match.group(1).strip()

        # 8. Amount Paid / Amount Received
        amount_match = re.search(r"(?:(?:Amount\s*Received|Amount\s*Paid|Net\s*Remitted|Paid\s*Amount|Total\s*Cleared|Settlement\s*Amount)[:\s]*\n*)\s*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if amount_match:
            amt = normalize_decimal(amount_match.group(1))
            data["payment_amount"] = str(amt)
            data["grand_total"] = str(amt)

        return data
