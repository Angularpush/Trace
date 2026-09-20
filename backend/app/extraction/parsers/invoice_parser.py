"""
TRACE - Tax Invoice Parser
Extracts Invoice Number, PO Reference, Dates, Vendor/Buyer GSTINs, Line Items, Taxes, and Grand Total.
"""

import re
from decimal import Decimal
from typing import Dict, Any, List
from app.extraction.normalizer import normalize_decimal, normalize_date, clean_item_description

class InvoiceParser:
    @staticmethod
    def parse(extracted: Dict[str, Any]) -> Dict[str, Any]:
        text = extracted.get("raw_text", "")
        pages = extracted.get("pages", [])
        
        data: Dict[str, Any] = {
            "document_number": None,
            "po_reference": None,
            "document_date": None,
            "due_date": None,
            "supplier_name": None,
            "supplier_gstin": None,
            "customer_name": None,
            "customer_gstin": None,
            "items": [],
            "subtotal": "0.00",
            "tax_total": "0.00",
            "grand_total": "0.00",
            "extra_metadata": {}
        }
        
        # 1. Invoice Number
        inv_match = re.search(r"(?:Tax\s*Invoice\s*(?:No\.?|Number|#)|Invoice\s*(?:No\.?|Number|#)|Bill\s*No\.?|Doc\s*No\.?)[:\s]*[:=]?\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if inv_match:
            data["document_number"] = inv_match.group(1).strip()

        # 2. PO Reference
        po_ref_match = re.search(r"(?:PO\s*(?:Reference|Ref\.?|No\.?|Number)|Ref\s*Purchase\s*Order|Against\s*PO\s*(?:No\.?)?)[:\s]*[:=]?\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if po_ref_match:
            data["po_reference"] = po_ref_match.group(1).strip()

        # 3. Invoice Date
        date_match = re.search(r"(?:(?:Invoice|Bill|Issue)?\s*Date[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            data["document_date"] = normalize_date(date_match.group(1))

        # 4. Due Date
        due_match = re.search(r"(?:(?:Payment\s*Due\s*Date|Due\s*Date)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if due_match:
            data["due_date"] = normalize_date(due_match.group(1))

        # 5. Supplier / Seller
        seller_match = re.search(r"(?:(?:Seller|Supplier\s*Name|From|For)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
        if seller_match:
            data["supplier_name"] = seller_match.group(1).strip()

        # 6. Buyer / Customer
        buyer_match = re.search(r"(?:(?:Buyer|Consignee|To)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Works|MSME|Industries|Components)?)", text, re.IGNORECASE)
        if buyer_match:
            data["customer_name"] = buyer_match.group(1).strip()

        # 7. GSTINs
        gst_matches = re.findall(r"(?:GSTIN(?:/UIN)?[:\s]+)([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})", text, re.IGNORECASE)
        if len(gst_matches) >= 1:
            data["supplier_gstin"] = gst_matches[0]
        if len(gst_matches) >= 2:
            data["customer_gstin"] = gst_matches[1]

        # 8. Line Items
        items: List[Dict[str, Any]] = []
        for p_idx, p in enumerate(pages):
            page_num = p.get("page_number", p_idx + 1)
            lines = p.get("lines", [])
            for line in lines:
                item_match = re.search(
                    r"(?:^\d+[\.\)]|\-)?\s*(?P<desc>[A-Za-z0-9\s\"\'\-\/\(\)]+?)(?:[\:\-\|]\s*|\s+)(?:Qty|Quantity)?[:\s]*(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z]+)?.*?(?:Rate|Price|Unit\s*Rate|Unit\s*Price)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*(?P<price>\d+(?:\.\d+)?).*?(?:Taxable|Amount|Value)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*(?P<taxable>\d+(?:\.\d+)?)",
                    line,
                    re.IGNORECASE
                )
                if item_match:
                    desc = item_match.group("desc").strip(" -:|,")
                    if len(desc) > 3 and not any(k in desc.lower() for k in ["subtotal", "grand total", "cgst", "sgst", "igst", "declaration"]):
                        qty = normalize_decimal(item_match.group("qty"))
                        price = normalize_decimal(item_match.group("price"))
                        taxable = normalize_decimal(item_match.group("taxable"))
                        unit = (item_match.group("unit") or "PCS").strip().upper()
                        if taxable == Decimal("0.00") and qty > 0 and price > 0:
                            taxable = (qty * price).quantize(Decimal("0.01"))

                        tax_amount = (taxable * Decimal("0.18")).quantize(Decimal("0.01"))

                        items.append({
                            "description": desc,
                            "normalized_description": clean_item_description(desc),
                            "quantity": str(qty),
                            "unit": unit,
                            "unit_price": str(price),
                            "discount": "0.00",
                            "tax_rate": "18.00",
                            "tax_amount": str(tax_amount),
                            "total_amount": str(taxable),
                            "evidence_snippet": line,
                            "page_number": page_num
                        })

            # Vertical table cell scan
            if not items and len(lines) >= 4:
                for idx, line in enumerate(lines):
                    if line.strip() in ["1", "01"] and idx + 3 < len(lines):
                        desc = lines[idx + 1].strip()
                        if len(desc) > 2 and not any(k in desc.lower() for k in ["total", "subtotal", "taxable", "signatory"]):
                            next_token = lines[idx + 2].strip()
                            qty_val = re.search(r"(\d+(?:\.\d+)?)", next_token)
                            unit_val = re.search(r"([A-Za-z]+)", next_token)
                            
                            qty = normalize_decimal(qty_val.group(1)) if qty_val else Decimal("1")
                            unit = unit_val.group(1).upper() if unit_val else "PCS"
                            
                            price = Decimal("0.00")
                            taxable = Decimal("0.00")
                            
                            for offset in range(3, 7):
                                if idx + offset < len(lines):
                                    cand = lines[idx + offset].strip()
                                    if cand.upper() in ["PCS", "NOS", "SETS", "KG", "MTR"]:
                                        unit = cand.upper()
                                    elif "INR" in cand or "RS" in cand or "₹" in cand or re.match(r"^\d+\.\d{2}$", cand):
                                        amt = normalize_decimal(cand)
                                        if price == Decimal("0.00"):
                                            price = amt
                                        elif taxable == Decimal("0.00"):
                                            taxable = amt

                            if taxable == Decimal("0.00") and price > 0:
                                taxable = (qty * price).quantize(Decimal("0.01"))
                            elif price == Decimal("0.00") and qty > 0 and taxable > 0:
                                price = (taxable / qty).quantize(Decimal("0.01"))

                            tax_amount = (taxable * Decimal("0.18")).quantize(Decimal("0.01"))

                            items.append({
                                "description": desc,
                                "normalized_description": clean_item_description(desc),
                                "quantity": str(qty),
                                "unit": unit,
                                "unit_price": str(price),
                                "discount": "0.00",
                                "tax_rate": "18.00",
                                "tax_amount": str(tax_amount),
                                "total_amount": str(taxable),
                                "evidence_snippet": f"{desc} | {qty} {unit} @ {price}",
                                "page_number": page_num
                            })

        # 9. Totals and Taxes
        subtotal_match = re.search(r"(?:Taxable\s*Subtotal|Taxable\s*Value|Total\s*Taxable|Subtotal)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if subtotal_match:
            data["subtotal"] = str(normalize_decimal(subtotal_match.group(1)))

        tax_match = re.search(r"(?:Total\s*Tax[^\n:]*|Total\s*GST[^\n:]*|CGST\s*\+\s*SGST[^\n:]*|IGST[^\n:]*)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if tax_match:
            data["tax_total"] = str(normalize_decimal(tax_match.group(1)))

        grand_match = re.search(r"(?:Total\s*Invoice\s*Amount|Grand\s*Total|Gross\s*Total|Invoice\s*Total)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if grand_match:
            data["grand_total"] = str(normalize_decimal(grand_match.group(1)))

        if items and data["grand_total"] == "0.00":
            calc_sub = sum(Decimal(it["total_amount"]) for it in items)
            calc_tax = (calc_sub * Decimal("0.18")).quantize(Decimal("0.01"))
            data["subtotal"] = str(calc_sub)
            data["tax_total"] = str(calc_tax)
            data["grand_total"] = str(calc_sub + calc_tax)

        data["items"] = items
        return data
