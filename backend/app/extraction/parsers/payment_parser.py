"""
TRACE - Payment Receipt / Voucher Parser
Extracts Payment Receipt No, Payment Date, Vendor, Invoice Reference, PO Reference, Payment Method, UTR, and Amount Paid.
"""

import re
from decimal import Decimal
from typing import Dict, Any, Optional
from app.extraction.normalizer import normalize_decimal, normalize_date, clean_entity_name

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
            "customer_name": None,
            "payment_amount": None,
            "payment_method": "BANK_TRANSFER",
            "transaction_reference": None,
            "grand_total": None,
            "extra_metadata": {}
        }
        
        # 1. Receipt / Voucher / Payment Reference No
        doc_num_patterns = [
            r"(?:Document\s*(?:No\.?|Number|#)|Doc\s*No\.?)[:\s\-]*([A-Z0-9_\-\/]+)",
            r"(?:Payment\s*(?:Reference|Ref\.?|No\.?|Number|#)|Payment\s*Receipt\s*(?:No\.?|Number|#)|Receipt\s*(?:No\.?|Number|#)|Voucher\s*(?:ID|No\.?|#)|Payment\s*Slip\s*Ref)[:\s]*[:=]?\n*\s*([A-Z0-9_\-\/]+)",
            r"\b(PAY[-_]\d{4}[-_]\d+)\b",
        ]
        for p in doc_num_patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if any(c.isdigit() for c in val) and not any(k in val.lower() for k in ["date", "amount", "supplier", "eived", "eipt", "seller", "buyer"]):
                    data["document_number"] = val
                    break

        # 2. Date
        date_match = re.search(r"(?:(?:Payment\s*Date|Date\s*of\s*Remittance|Date)[:\s]*\n*)\s*(\d{4}[-\s/.]\d{1,2}[-\s/.]\d{1,2}|\d{1,2}[-\s/.][A-Za-z0-9]+[-\s/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            raw_d = date_match.group(1).strip()
            data["document_date"] = normalize_date(raw_d)
            data["extra_metadata"]["raw_date"] = raw_d

        # 3. Supplier / Vendor & Customer / Payer
        for l in all_lines[:8]:
            clean_l = re.sub(r"^(?:Supplier\s*/\s*Seller|Supplier|Seller|Vendor|Consignor|From|Beneficiary\s*Name|Paid\s*To)[:\s\-]*", "", l.strip(), flags=re.IGNORECASE).strip()
            if any(k in clean_l.lower() for k in ["pvt", "ltd", "limited", "technologies", "solutions", "corporation", "enterprises", "engineering", "works", "fasteners", "supplies"]):
                if not any(k in clean_l.lower() for k in ["document information", "delivery / reference", "delivery location", "sample", "test", "actual", "synthetic"]):
                    data["supplier_name"] = clean_l
                    break

        paid_to_match = re.search(r"(?:(?:Paid\s*To|Beneficiary\s*Name|Vendor|Received\s*From)[:\s]*\n*)\s*([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division|Technologies)?)", text, re.IGNORECASE)
        if paid_to_match and not data["supplier_name"]:
            cand = re.sub(r"^(?:Paid\s*To|Beneficiary\s*Name|Vendor|Received\s*From)[:\s\-]*", "", paid_to_match.group(1).strip(), flags=re.IGNORECASE).strip()
            if not any(k in cand.lower() for k in ["sample", "test", "actual", "synthetic"]):
                data["supplier_name"] = cand

        cust_m = re.search(r"(?:Bill\s*To\s*/\s*Customer|Bill\s*To\s*/\s*Buyer|Bill\s*To|Buyer|Consignee|Customer|Paid\s*By|Remitter)[:\s]*\n+(?:Delivery\s*/\s*Reference\n+)?([^\n,]+(?:Pvt|Ltd|Limited|Solutions|Corp|Enterprises|Supplies|Fasteners|Systems|Technologies|Works|Engineering)?)", text, re.IGNORECASE)
        if cust_m:
            cand = re.sub(r"^(?:Bill\s*To\s*/\s*Customer|Bill\s*To\s*/\s*Buyer|Bill\s*To|Buyer|Customer|Consignee|To|Issued\s*To)[:\s\-]*", "", cust_m.group(1).strip(), flags=re.IGNORECASE).strip()
            if not any(k in cand.lower() for k in ["delivery / reference", "document information", "reference:"]):
                data["customer_name"] = cand

        if not data["customer_name"]:
            for l in all_lines[4:25]:
                clean_l = re.sub(r"^(?:Bill\s*To\s*/\s*Customer|Bill\s*To\s*/\s*Buyer|Bill\s*To|Buyer|Customer|Consignee|To|Issued\s*To|Supplier\s*/\s*Seller|Supplier|Seller|Vendor|Consignor|From)[:\s\-]*", "", l.strip(), flags=re.IGNORECASE).strip()
                if any(k in clean_l.lower() for k in ["pvt", "ltd", "limited", "technologies", "solutions", "corporation", "enterprises", "engineering", "works", "fasteners", "supplies"]):
                    if clean_l.lower() != (data["supplier_name"] or "").lower() and not any(k in clean_l.lower() for k in ["document information", "delivery / reference", "delivery location", "bank details", "declaration"]):
                        data["customer_name"] = clean_l
                        break

        # 4. References (Compound and Individual)
        comb_m = re.search(r"(?:Against\s*(?:Invoice|PO)\s*/\s*(?:Invoice|PO)|(?:Invoice|PO)\s*/\s*(?:Invoice|PO)\s*Ref)[:\s=]*\n*\s*([^\n]+)", text, re.IGNORECASE)
        if comb_m:
            tokens = [t.strip() for t in re.split(r"[/,]", comb_m.group(1)) if t.strip()]
            for t in tokens:
                if re.search(r"PO|PURCHASE|ORD", t, re.I) or t.upper().startswith("PO"):
                    data["po_reference"] = t
                elif re.search(r"INV|TAX|BILL", t, re.I) or t.upper().startswith("INV"):
                    data["invoice_reference"] = t

        if not data["invoice_reference"]:
            inv_ref_match = re.search(r"(?:Settlement\s*for\s*(?:Tax\s*)?Invoice|Against\s*Invoice\s*(?:No\.?|Number|#)?|Invoice\s*(?:Reference|Ref\.?|No\.?|#)|Against\s*Bill/Invoice\s*No\.?)[:\s]*[:=]?\n*\s*([A-Z0-9_\-]+)", text, re.IGNORECASE)
            if inv_ref_match and any(c.isdigit() for c in inv_ref_match.group(1)):
                data["invoice_reference"] = inv_ref_match.group(1).strip()
            else:
                full_inv = re.search(r"\b(INV[-_]\d{4}[-_]\d+)\b", text, re.IGNORECASE)
                if full_inv:
                    data["invoice_reference"] = full_inv.group(1)

        if not data["po_reference"]:
            po_ref_match = re.search(r"(?:(?:PO\s*Number\s*Ref|PO\s*Ref|Against\s*PO\s*No\.?|Against\s*PO|Ref\s*PO)[:\s=]*\n*)\s*([A-Z0-9_\-]+)", text, re.IGNORECASE)
            if po_ref_match and any(c.isdigit() for c in po_ref_match.group(1)):
                data["po_reference"] = po_ref_match.group(1).strip()
            else:
                full_po = re.search(r"\b(PO[-_]\d{4}[-_]\d+)\b", text, re.IGNORECASE)
                if full_po:
                    data["po_reference"] = full_po.group(1)

        # 5. Transaction / UTR ID
        utr_match = re.search(r"(?:(?:Bank\s*Transaction\s*Ref\s*/\s*UTR|Transaction\s*(?:Reference|ID|Ref)|Cheque/NEFT\s*No|UTR)[:\s]*\n*)\s*([A-Z0-9_\-]+)", text, re.IGNORECASE)
        if utr_match:
            data["transaction_reference"] = utr_match.group(1).strip()

        # 6. Payment Mode
        mode_match = re.search(r"(?:Payment\s*Mode|Mode\s*of\s*Payment|Payment\s*Method)[:\s]*\n*\s*([^\n]+)", text, re.IGNORECASE)
        if mode_match:
            data["payment_method"] = mode_match.group(1).strip()

        # 7. Amount Paid / Amount Received
        amt_labels = r"(?:Amount\s*Received|Amount\s*Paid|Paid\s*Amount|Payment\s*Amount|Amount\s*Remitted|Amount\s*Transferred|Remitted\s*Amount|Net\s*Remitted|Total\s*Cleared|Settlement\s*Amount)"
        amt_pattern = rf"({amt_labels}(?:\s*\([^)]+\))?[:\s]*\n*(?:\([^)]+\)\n*)?\s*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?))"
        amount_match = re.search(amt_pattern, text, re.IGNORECASE)

        if amount_match:
            raw_snippet = amount_match.group(1).replace("\n", " ").strip()
            raw_amt_str = amount_match.group(2).strip()
            amt_decimal = normalize_decimal(raw_amt_str)
            if amt_decimal > 0:
                data["payment_amount"] = str(amt_decimal)
                data["grand_total"] = str(amt_decimal)
                data["extra_metadata"]["amount_snippet"] = raw_snippet
                data["extra_metadata"]["extracted_amount_str"] = raw_amt_str
                data["extra_metadata"]["extraction_status"] = "SUCCESS"
            else:
                data["payment_amount"] = None
                data["grand_total"] = None
                data["extra_metadata"]["extraction_status"] = "ZERO_VALUE"
        else:
            fallback_m = re.search(r"(?:INR|Rs\.|Rs|₹)\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
            if fallback_m:
                amt_decimal = normalize_decimal(fallback_m.group(1))
                if amt_decimal > 0:
                    data["payment_amount"] = str(amt_decimal)
                    data["grand_total"] = str(amt_decimal)
                    data["extra_metadata"]["amount_snippet"] = fallback_m.group(0)
                    data["extra_metadata"]["extraction_status"] = "FALLBACK_SUCCESS"
            
            if not data["payment_amount"]:
                data["payment_amount"] = None
                data["grand_total"] = None
                data["extra_metadata"]["extraction_status"] = "FAILED"
                data["extra_metadata"]["amount_snippet"] = None

        return data

