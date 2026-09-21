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
        all_lines = []
        for p in pages:
            all_lines.extend(p.get("lines", []))
        if not all_lines:
            all_lines = [l.strip() for l in text.split("\n") if l.strip()]
        
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
        po_ref_match = re.search(r"(?:PO\s*(?:Reference|Ref\.?|No\.?|Number)|Ref\s*Purchase\s*Order|Against\s*PO\s*(?:Ref\.?|No\.?)?)[:\s]*[:=]?\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if po_ref_match:
            data["po_reference"] = po_ref_match.group(1).strip()

        # 3. Invoice Date
        date_match = re.search(r"(?:(?:Invoice|Bill|Issue)?\s*Date[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        date_match = re.search(r"(?:(?:Invoice|Bill|Issue)?\s*Date[:\s]+)(\d{1,2}[-\s/.][A-Za-z0-9]+[-\s/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            data["document_date"] = normalize_date(date_match.group(1))
            raw_d = date_match.group(1).strip()
            data["document_date"] = normalize_date(raw_d)
            data["extra_metadata"]["raw_date"] = raw_d

        # 4. Due Date
        due_match = re.search(r"(?:(?:Payment\s*Due\s*Date|Due\s*Date)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        due_match = re.search(r"(?:(?:Payment\s*Due\s*Date|Due\s*Date)[:\s]+)(\d{1,2}[-\s/.][A-Za-z0-9]+[-\s/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if due_match:
            data["due_date"] = normalize_date(due_match.group(1))

        # 5. Supplier / Seller
        seller_match = re.search(r"(?:(?:Seller|Supplier\s*Name|From|For)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
        if seller_match:
            data["supplier_name"] = seller_match.group(1).strip()
        # 5. Supplier & Customer extraction
        # First check explicit labeled blocks
        supp_m = re.search(r"(?:Supplier|Seller|From)[:\s]*\n+([^\n,]+(?:Pvt|Ltd|Limited|Solutions|Corp|Enterprises|Supplies|Fasteners|Systems|Technologies|Works|Engineering)?)", text, re.IGNORECASE)
        if supp_m and not any(k in supp_m.group(1).lower() for k in ["buyer", "sample", "test", "actual", "synthetic", "bill to"]):
            data["supplier_name"] = supp_m.group(1).strip()

        # 6. Buyer / Customer
        buyer_match = re.search(r"(?:(?:Buyer|Consignee|To)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Works|MSME|Industries|Components)?)", text, re.IGNORECASE)
        if buyer_match:
            data["customer_name"] = buyer_match.group(1).strip()
        buyer_m = re.search(r"(?:Bill\s*To\s*/\s*Buyer|Buyer|Bill\s*To|Consignee|To|Customer)[:\s]*\n+([^\n,]+(?:Pvt|Ltd|Limited|Solutions|Corp|Enterprises|Supplies|Fasteners|Systems|Technologies|Works|Engineering)?)", text, re.IGNORECASE)
        if buyer_m and not any(k in buyer_m.group(1).lower() for k in ["supplier", "sample", "test", "actual", "synthetic", "seller"]):
            data["customer_name"] = buyer_m.group(1).strip()

        # 7. GSTINs
        gst_matches = re.findall(r"(?:GSTIN(?:/UIN)?[:\s]+)([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})", text, re.IGNORECASE)
        # Fallback for header company name
        if not data["supplier_name"]:
            seller_match = re.search(r"(?:(?:Seller|Supplier\s*Name|From)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division|Technologies)?)", text, re.IGNORECASE)
            if seller_match and not any(k in seller_match.group(1).lower() for k in ["sample", "test", "actual", "synthetic"]):
                data["supplier_name"] = seller_match.group(1).strip()
            else:
                for l in all_lines[:10]:
                    if any(k in l.lower() for k in ["pvt", "ltd", "limited", "solutions", "technologies", "engineering", "works", "supplies"]) and not any(k in l.lower() for k in ["sample", "test", "actual", "synthetic"]):
                        data["supplier_name"] = l.strip()
                        break

        if not data["customer_name"]:
            buyer_match = re.search(r"(?:(?:Buyer|Consignee|To)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Works|MSME|Industries|Components|Technologies)?)", text, re.IGNORECASE)
            if buyer_match and not any(k in buyer_match.group(1).lower() for k in ["sample", "test", "actual", "synthetic"]):
                data["customer_name"] = buyer_match.group(1).strip()

        # 6. GSTINs
        gst_matches = re.findall(r"(?:GSTIN(?:/UIN)?[:\s]+)?([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})", text, re.IGNORECASE)
        if len(gst_matches) >= 1:
            data["supplier_gstin"] = gst_matches[0]
        if len(gst_matches) >= 2:
            data["customer_gstin"] = gst_matches[1]

        # 8. Line Items
        # 7. Line Items Extraction
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
        # Strategy A: Sequential multi-row vertical token table (e.g. 1, 2, 3...)
        row_starts = []
        for idx, line in enumerate(all_lines):
            clean_l = line.strip()
            if re.match(r"^\d+$", clean_l) and int(clean_l) == len(row_starts) + 1:
                # verify it's not a year or page number
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
                    if any(k in c.lower() for k in ["subtotal", "grand total", "taxable amount", "taxable value", "invoice total", "terms:", "purpose:", "declaration"]):
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

                    tax_amount = (taxable * Decimal("0.18")).quantize(Decimal("0.01")) if taxable > 0 else (total * Decimal("0.18")).quantize(Decimal("0.01"))

                    items.append({
                        "description": desc,
                        "normalized_description": clean_item_description(desc),
                        "quantity": str(qty),
                        "unit": unit,
                        "unit_price": str(unit_price),
                        "discount": "0.00",
                        "tax_rate": "18.00",
                        "tax_amount": str(tax_amount),
                        "total_amount": str(taxable if taxable > 0 else total),
                        "evidence_snippet": f"{desc} | {qty} {unit} @ {unit_price}",
                        "page_number": pages[0].get("page_number", 1) if pages else 1
                    })

        # Strategy B: Horizontal single-line format fallback
        if not items:
            for p_idx, p in enumerate(pages):
                page_num = p.get("page_number", p_idx + 1)
                lines = p.get("lines", [])
                for line in lines:
                    item_match = re.search(
                        r"(?:^\d+[\.\)]|\-)?\s*(?P<desc>[A-Za-z0-9\s\"\'\-\/\(\)]+?)(?:[\:\-\|]\s*|\s+)(?:Qty|Quantity)?[:\s]*(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z]+)?.*?(?:Rate|Price|Unit\s*Rate|Unit\s*Price)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*(?P<price>[\d,]+(?:\.\d+)?).*?(?:Taxable|Amount|Value)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*(?P<taxable>[\d,]+(?:\.\d+)?)",
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
                                "evidence_snippet": line,
                                "page_number": page_num
                            })

        # 9. Totals and Taxes
        subtotal_match = re.search(r"(?:Taxable\s*Subtotal|Taxable\s*Value|Total\s*Taxable|Subtotal)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        # 8. Totals and Taxes
        subtotal_match = re.search(r"(?:Taxable\s*Amount|Taxable\s*Subtotal|Taxable\s*Value|Total\s*Taxable|Subtotal)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if subtotal_match:
            data["subtotal"] = str(normalize_decimal(subtotal_match.group(1)))

        tax_match = re.search(r"(?:Total\s*Tax[^\n:]*|Total\s*GST[^\n:]*|CGST\s*\+\s*SGST[^\n:]*|IGST[^\n:]*)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        tax_match = re.search(r"(?:Total\s*Tax[^\n:]*|Total\s*GST[^\n:]*|CGST\s*\+\s*SGST[^\n:]*|IGST[^\n:]*)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if tax_match:
            data["tax_total"] = str(normalize_decimal(tax_match.group(1)))
        else:
            # Check individual CGST / SGST sum
            cgst_m = re.search(r"CGST[^\n:]*[:\s]+(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
            sgst_m = re.search(r"SGST[^\n:]*[:\s]+(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
            if cgst_m and sgst_m:
                c_tax = normalize_decimal(cgst_m.group(1))
                s_tax = normalize_decimal(sgst_m.group(1))
                data["tax_total"] = str(c_tax + s_tax)

        grand_match = re.search(r"(?:Total\s*Invoice\s*Amount|Grand\s*Total|Gross\s*Total|Invoice\s*Total)[:\s]*(?:INR|Rs\.|Rs|₹)?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        grand_match = re.search(r"(?:Invoice\s*Total|Total\s*Invoice\s*Amount|Grand\s*Total|Gross\s*Total)[:\s]*(?:INR|Rs\.|Rs|₹|[I\|■\?])?\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
        if grand_match:
            data["grand_total"] = str(normalize_decimal(grand_match.group(1)))

        if items and data["grand_total"] == "0.00":
            calc_sub = sum(Decimal(it["total_amount"]) for it in items)
            calc_tax = (calc_sub * Decimal("0.18")).quantize(Decimal("0.01"))
            calc_tax = Decimal(data["tax_total"]) if Decimal(data["tax_total"]) > 0 else (calc_sub * Decimal("0.18")).quantize(Decimal("0.01"))
            data["subtotal"] = str(calc_sub)
            data["tax_total"] = str(calc_tax)
            data["grand_total"] = str(calc_sub + calc_tax)

        data["items"] = items
        return data
