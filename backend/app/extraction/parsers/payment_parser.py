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
        pay_match = re.search(r"(?:Payment\s*Receipt\s*(?:No\.?|Number|#)|Receipt\s*No\.?|Voucher\s*(?:ID|No\.?|#)|Payment\s*Slip\s*Ref)[:\s]*[:=]?\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if pay_match:
            data["document_number"] = pay_match.group(1).strip()

        # 2. Date
        date_match = re.search(r"(?:(?:Payment\s*Date|Date\s*of\s*Remittance|Date)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            data["document_date"] = normalize_date(date_match.group(1))

        # 3. Paid To / Beneficiary / Vendor
        paid_to_match = re.search(r"(?:(?:Paid\s*To|Beneficiary\s*Name|Vendor)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
        if paid_to_match:
            data["supplier_name"] = paid_to_match.group(1).strip()

        # 4. Invoice Reference
        inv_ref_match = re.search(r"(?:Settlement\s*for\s*(?:Tax\s*)?Invoice|Against\s*Invoice\s*(?:No\.?|Number|#)?|Invoice\s*(?:Reference|Ref\.?|No\.?)|Against\s*Bill/Invoice\s*No\.?)[:\s]*[:=]?\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if inv_ref_match:
            data["invoice_reference"] = inv_ref_match.group(1).strip()

        # 5. PO Reference
        po_ref_match = re.search(r"(?:(?:PO\s*Number\s*Ref|PO\s*Ref|Against\s*PO\s*No\.?)[:\s]+)([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if po_ref_match:
            data["po_reference"] = po_ref_match.group(1).strip()

        # 6. Transaction / UTR ID
        utr_match = re.search(r"(?:(?:Bank\s*Transaction\s*Ref\s*/\s*UTR|Transaction\s*ID|Cheque/NEFT\s*No|UTR)[:\s]+)([A-Z0-9_\-]+)", text, re.IGNORECASE)
        if utr_match:
            data["transaction_reference"] = utr_match.group(1).strip()

        # 7. Amount Paid
        amount_match = re.search(r"(?:(?:Amount\s*Paid|Net\s*Remitted|Paid\s*Amount|Total\s*Cleared)[:\s]*)(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if amount_match:
            amt = normalize_decimal(amount_match.group(1))
            data["payment_amount"] = str(amt)
            data["grand_total"] = str(amt)

        return data
