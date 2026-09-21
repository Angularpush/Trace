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
        all_lines = []
        for p in pages:
            all_lines.extend(p.get("lines", []))
        if not all_lines:
            all_lines = [l.strip() for l in text.split("\n") if l.strip()]
        
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
        date_match = re.search(r"(?:(?:Order\s*)?Date[:\s]+)(\d{1,2}[-\s/.][A-Za-z0-9]+[-\s/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            data["document_date"] = normalize_date(date_match.group(1))
            raw_d = date_match.group(1).strip()
            data["document_date"] = normalize_date(raw_d)
            data["extra_metadata"]["raw_date"] = raw_d

        # 3. Delivery / Due Date
        due_match = re.search(r"(?:(?:Required\s*Delivery\s*Date|Due\s*Date|Delivery\s*By)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        due_match = re.search(r"(?:(?:Required\s*Delivery\s*Date|Due\s*Date|Delivery\s*By)[:\s]+)(\d{1,2}[-\s/.][A-Za-z0-9]+[-\s/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if due_match:
            data["due_date"] = normalize_date(due_match.group(1))

        # 4. Vendor / Supplier
        vendor_match = re.search(r"(?:(?:Vendor|Supplier|Issued\s*To|To)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
        if vendor_match:
            data["supplier_name"] = vendor_match.group(1).strip()
        # 4. Vendor / Supplier & Buyer / Customer
        supp_m = re.search(r"(?:Supplier|Seller|Vendor|From)[:\s]*\n+([^\n,]+(?:Pvt|Ltd|Limited|Solutions|Corp|Enterprises|Supplies|Fasteners|Systems|Technologies|Works|Engineering)?)", text, re.IGNORECASE)
        if supp_m and not any(k in supp_m.group(1).lower() for k in ["buyer", "sample", "test", "actual", "synthetic", "bill to"]):
            data["supplier_name"] = supp_m.group(1).strip()

        buyer_m = re.search(r"(?:Bill\s*To\s*/\s*Buyer|Buyer|Bill\s*To|Consignee|To|Customer)[:\s]*\n+([^\n,]+(?:Pvt|Ltd|Limited|Solutions|Corp|Enterprises|Supplies|Fasteners|Systems|Technologies|Works|Engineering)?)", text, re.IGNORECASE)
        if buyer_m and not any(k in buyer_m.group(1).lower() for k in ["supplier", "sample", "test", "actual", "synthetic", "seller"]):
            data["customer_name"] = buyer_m.group(1).strip()

        if not data["supplier_name"]:
            vendor_match = re.search(r"(?:(?:Vendor|Supplier|Issued\s*To|To)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
            if vendor_match and not any(k in vendor_match.group(1).lower() for k in ["sample", "test", "actual", "synthetic"]):
                data["supplier_name"] = vendor_match.group(1).strip()
            else:
                for l in all_lines[:10]:
                    if any(k in l.lower() for k in ["pvt", "ltd", "limited", "solutions", "technologies", "engineering", "works", "supplies"]) and not any(k in l.lower() for k in ["sample", "test", "actual", "synthetic"]):
                        data["supplier_name"] = l.strip()
                        break

        # 5. GSTIN
        gst_matches = re.findall(r"(?:GSTIN(?:/UIN)?[:\s]+)?([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})", text, re.IGNORECASE)
        if len(gst_matches) >= 1:
            data["supplier_gstin"] = gst_matches[0]

        # 6. Delivery Address
        addr_match = re.search(r"(?:(?:Delivery\s*Address|Ship\s*To|Delivery\s*Location)[:\s]+)([^\n]+(?:\n[^\n]+)?)", text, re.IGNORECASE)
        if addr_match:
            data["delivery_address"] = addr_match.group(1).strip()

        # 7. Line Items Extraction (Horizontal and Vertical table formats)
        items: List[Dict[str, Any]] = []

        # Strategy A: Multi-row vertical token table (1, 2, 3...)
        row_starts = []
        for idx, line in enumerate(all_lines):
            clean_l = line.strip()
            if re.match(r"^\d+$", clean_l) and int(clean_l) == len(row_starts) + 1:
                if int(clean_l) <= 50 and idx + 1 < len(all_lines):
                    next_l = all_lines[idx + 1].strip()
                    if not any(k in next_l.lower() for k in ["subtotal", "taxable", "total", "page"]):
                        row_starts.append((int(clean_l), idx))

        if row_starts:
            for r_idx, (item_no, line_idx) in enumerate(row_starts):
                next_line_idx = row_starts[r_idx + 1][1] if r_idx + 1 < len(row_starts) else len(all_lines)
                chunk = [l.strip() for l in all_lines[line_idx + 1 : next_line_idx] if l.strip()]
                clean_chunk = []
                for c in chunk:
                    if any(k in c.lower() for k in ["subtotal", "grand total", "taxable amount", "taxable value", "total", "terms:", "purpose:", "authorized"]):
                        break
                    clean_chunk.append(c)

                if clean_chunk:
                    desc = clean_chunk[0]
                    qty = Decimal("1.00")
                    unit = "PCS"
                    unit_price = Decimal("0.00")
                    taxable = Decimal("0.00")
                    total = Decimal("0.00")

                    numeric_vals = []
                    for token in clean_chunk[1:]:
                        if token.upper() in ["PCS", "NOS", "SETS", "KG", "MTR", "UNITS", "BOX"]:
                            unit = token.upper()
                            continue
                        dec = normalize_decimal(token)
                        if dec > 0:
                            numeric_vals.append(dec)

                    if len(numeric_vals) >= 1:
                        qty = numeric_vals[0]
                    if len(numeric_vals) >= 2:
                        unit_price = numeric_vals[1]
                    if len(numeric_vals) >= 3:
                        taxable = numeric_vals[2]
                    if len(numeric_vals) >= 4:
                        total = numeric_vals[3]
                    elif taxable > 0:
                        total = taxable
                    elif qty > 0 and unit_price > 0:
                        total = (qty * unit_price).quantize(Decimal("0.01"))

                    items.append({
                        "description": desc,
                        "normalized_description": clean_item_description(desc),
                        "quantity": str(qty),
                        "unit": unit,
                        "unit_price": str(unit_price),
                        "discount": "0.00",
                        "tax_rate": "18.00",
                        "tax_amount": str((total * Decimal("0.18")).quantize(Decimal("0.01"))),
                        "total_amount": str(total),
                        "evidence_snippet": f"{desc} | {qty} {unit} @ {unit_price}",
                        "page_number": pages[0].get("page_number", 1) if pages else 1
                    })

        # Strategy B: Single-line horizontal table format fallback
        if not items:
            for p_idx, p in enumerate(pages):
                page_num = p.get("page_number", p_idx + 1)
                lines = p.get("lines", [])
                for line in lines:
                    item_match = re.search(
                        r"(?:^\d+[\.\)]|\-)?\s*(?P<desc>[A-Za-z0-9\s\"\'\-\/\(\)]+?)(?:[\:\-\|]\s*|\s+)(?:Qty|Quantity)?[:\s]*(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z]+)?.*?(?:@|Rate|Price|Unit\s*Price|Rate:)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*(?P<price>[\d,]+(?:\.\d+)?).*?(?:=|Total|Amount)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*(?P<total>[\d,]+(?:\.\d+)?)",
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
                                "evidence_snippet": line,
                                "page_number": page_num
                            })

        # 8. Totals
        subtotal_match = re.search(r"(?:Subtotal|Taxable\s*Value|Total\s*Taxable)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        grand_match = re.search(r"(?:Grand\s*Total|Gross\s*Total|Total\s*Invoice\s*Amount|Total\s*Order\s*Value)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if grand_match:
            data["grand_total"] = str(normalize_decimal(grand_match.group(1)))

        subtotal_match = re.search(r"(?:Subtotal|Taxable\s*Value|Total\s*Taxable)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if subtotal_match:
            data["subtotal"] = str(normalize_decimal(subtotal_match.group(1)))

        grand_match = re.search(r"(?:Grand\s*Total|Total\s*Order\s*Value|Gross\s*Total|Total)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if grand_match:
            data["grand_total"] = str(normalize_decimal(grand_match.group(1)))
        tax_m = re.search(r"(?:GST\s*\(\d+%\)|Total\s*Tax|Tax)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if tax_m:
            data["tax_total"] = str(normalize_decimal(tax_m.group(1)))

        if not grand_match:
            total_fallback = re.search(r"(?:Total)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
            if total_fallback:
                data["grand_total"] = str(normalize_decimal(total_fallback.group(1)))

        if items and data["grand_total"] == "0.00":
            calc_sub = sum(Decimal(it["total_amount"]) for it in items)
            data["subtotal"] = str(calc_sub)
            data["grand_total"] = str(calc_sub)

        data["items"] = items
        return data
