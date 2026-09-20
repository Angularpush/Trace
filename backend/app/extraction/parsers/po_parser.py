"""
TRACE - Purchase Order Parser
Extracts PO Number, Vendor, Date, Required Delivery Date, Line Items, and Totals.
"""

import re
from decimal import Decimal
from typing import Dict, Any, List
from app.extraction.normalizer import normalize_decimal, normalize_date, clean_item_description

class PurchaseOrderParser:
    @staticmethod
    def parse(extracted: Dict[str, Any]) -> Dict[str, Any]:
        text = extracted.get("raw_text", "")
        pages = extracted.get("pages", [])
        
        data: Dict[str, Any] = {
            "document_number": None,
            "document_date": None,
            "due_date": None,
            "supplier_name": None,
            "supplier_gstin": None,
            "customer_name": None,
            "delivery_address": None,
            "items": [],
            "subtotal": "0.00",
            "tax_total": "0.00",
            "grand_total": "0.00",
            "extra_metadata": {}
        }
        
        # 1. PO Number / Reference
        po_match = re.search(r"(?:PO\s*(?:Number|No\.?|#)|Purchase\s*Order\s*(?:Number|No\.?|#)|PO\s*Ref)[:\s]*[:=]?\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if po_match:
            data["document_number"] = po_match.group(1).strip()
            
        # 2. Date
        date_match = re.search(r"(?:(?:Order\s*)?Date[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            data["document_date"] = normalize_date(date_match.group(1))

        # 3. Delivery / Due Date
        due_match = re.search(r"(?:(?:Required\s*Delivery\s*Date|Due\s*Date|Delivery\s*By)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if due_match:
            data["due_date"] = normalize_date(due_match.group(1))

        # 4. Vendor / Supplier
        vendor_match = re.search(r"(?:(?:Vendor|Supplier|Issued\s*To|To)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
        if vendor_match:
            data["supplier_name"] = vendor_match.group(1).strip()

        # 5. GSTIN
        gst_match = re.search(r"(?:GSTIN(?:/UIN)?[:\s]+)([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})", text, re.IGNORECASE)
        if gst_match:
            data["supplier_gstin"] = gst_match.group(1).strip()

        # 6. Delivery Address
        addr_match = re.search(r"(?:(?:Delivery\s*Address|Ship\s*To|Delivery\s*Location)[:\s]+)([^\n]+(?:\n[^\n]+)?)", text, re.IGNORECASE)
        if addr_match:
            data["delivery_address"] = addr_match.group(1).strip()

        # 7. Line Items Extraction (Horizontal and Vertical table formats)
        items: List[Dict[str, Any]] = []
        for p_idx, p in enumerate(pages):
            page_num = p.get("page_number", p_idx + 1)
            lines = p.get("lines", [])
            
            # A. Try horizontal single-line format
            for line in lines:
                item_match = re.search(
                    r"(?:^\d+[\.\)]|\-)?\s*(?P<desc>[A-Za-z0-9\s\"\'\-\/\(\)]+?)(?:[\:\-\|]\s*|\s+)(?:Qty|Quantity)[:\s]*(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z]+)?.*?(?:@|Rate|Price|Unit\s*Price|Rate:)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*(?P<price>\d+(?:\.\d+)?).*?(?:=|Total|Amount)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*(?P<total>\d+(?:\.\d+)?)",
                    line,
                    re.IGNORECASE
                )
                if item_match:
                    desc = item_match.group("desc").strip(" -:|,")
                    if len(desc) > 3 and not any(k in desc.lower() for k in ["subtotal", "grand total", "cgst", "sgst", "igst", "terms"]):
                        qty = normalize_decimal(item_match.group("qty"))
                        price = normalize_decimal(item_match.group("price"))
                        total = normalize_decimal(item_match.group("total"))
                        unit = (item_match.group("unit") or "PCS").strip().upper()
                        if total == Decimal("0.00") and qty > 0 and price > 0:
                            total = (qty * price).quantize(Decimal("0.01"))

                        items.append({
                            "description": desc,
                            "normalized_description": clean_item_description(desc),
                            "quantity": str(qty),
                            "unit": unit,
                            "unit_price": str(price),
                            "discount": "0.00",
                            "tax_rate": "18.00",
                            "tax_amount": str((total * Decimal("0.18")).quantize(Decimal("0.01"))),
                            "total_amount": str(total),
                            "evidence_snippet": line,
                            "page_number": page_num
                        })

            # B. If no horizontal items found, try sequential vertical table scan
            if not items and len(lines) >= 4:
                for idx, line in enumerate(lines):
                    if line.strip() in ["1", "01"] and idx + 3 < len(lines):
                        desc = lines[idx + 1].strip()
                        if len(desc) > 2 and not any(k in desc.lower() for k in ["total", "subtotal", "signatory"]):
                            # Next token may be "100" or "100 PCS"
                            next_token = lines[idx + 2].strip()
                            qty_val = re.search(r"(\d+(?:\.\d+)?)", next_token)
                            unit_val = re.search(r"([A-Za-z]+)", next_token)
                            
                            qty = normalize_decimal(qty_val.group(1)) if qty_val else Decimal("1")
                            unit = unit_val.group(1).upper() if unit_val else "PCS"
                            
                            # Next line might be Unit or Price
                            price = Decimal("0.00")
                            total = Decimal("0.00")
                            
                            for offset in range(3, 6):
                                if idx + offset < len(lines):
                                    cand = lines[idx + offset].strip()
                                    if cand.upper() in ["PCS", "NOS", "SETS", "KG", "MTR"]:
                                        unit = cand.upper()
                                    elif "INR" in cand or "RS" in cand or "₹" in cand or re.match(r"^\d+\.\d{2}$", cand):
                                        amt = normalize_decimal(cand)
                                        if price == Decimal("0.00"):
                                            price = amt
                                        elif total == Decimal("0.00"):
                                            total = amt

                            if total == Decimal("0.00") and price > 0:
                                total = (qty * price).quantize(Decimal("0.01"))
                            elif price == Decimal("0.00") and qty > 0 and total > 0:
                                price = (total / qty).quantize(Decimal("0.01"))

                            items.append({
                                "description": desc,
                                "normalized_description": clean_item_description(desc),
                                "quantity": str(qty),
                                "unit": unit,
                                "unit_price": str(price),
                                "discount": "0.00",
                                "tax_rate": "18.00",
                                "tax_amount": str((total * Decimal("0.18")).quantize(Decimal("0.01"))),
                                "total_amount": str(total),
                                "evidence_snippet": f"{desc} | {qty} {unit} @ {price}",
                                "page_number": page_num
                            })

        # 8. Totals
        subtotal_match = re.search(r"(?:Subtotal|Taxable\s*Value|Total\s*Taxable)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if subtotal_match:
            data["subtotal"] = str(normalize_decimal(subtotal_match.group(1)))

        grand_match = re.search(r"(?:Grand\s*Total|Total\s*Order\s*Value|Gross\s*Total|Total)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if grand_match:
            data["grand_total"] = str(normalize_decimal(grand_match.group(1)))

        if items and data["grand_total"] == "0.00":
            calc_sub = sum(Decimal(it["total_amount"]) for it in items)
            data["subtotal"] = str(calc_sub)
            data["grand_total"] = str(calc_sub)

        data["items"] = items
        return data
