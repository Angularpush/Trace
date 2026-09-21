"""
TRACE - Delivery Note / Challan Parser
Extracts Delivery Challan Number, PO Reference, Dispatch Date, Transport info, Items, and Delivered Quantities.
"""

import re
from decimal import Decimal
from typing import Dict, Any, List
from app.extraction.normalizer import normalize_decimal, normalize_date, clean_item_description

class DeliveryNoteParser:
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
            "supplier_name": None,
            "customer_name": None,
            "items": [],
            "extra_metadata": {}
        }
        
        # 1. Delivery Challan / Note No
        dn_match = re.search(r"(?:Delivery\s*(?:Challan|Note)\s*(?:No\.?|Number|#)|Challan\s*No\.?|DN\s*No\.?|Dispatch\s*Memo)[:\s]*[:=]?\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if dn_match:
            data["document_number"] = dn_match.group(1).strip()

        # 2. PO Reference
        po_match = re.search(r"(?:Against\s*PO\s*(?:Ref\.?|No\.?|Number)?|PO\s*(?:Reference|Ref\.?|No\.?|Number)|Ref\s*PO)[:\s]*[:=]?\s*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        po_match = re.search(r"(?:Against\s*PO\s*Ref\.?|Against\s*PO\s*No\.?|Against\s*PO\s*Number|Against\s*PO|PO\s*Reference|PO\s*Ref\.?|PO\s*No\.?|PO\s*Number|Ref\s*PO)[:\s=]*([A-Z0-9_\-\/]+)", text, re.IGNORECASE)
        if po_match:
            data["po_reference"] = po_match.group(1).strip()
            cand_po = po_match.group(1).strip(" -:=")
            if cand_po.startswith("20") or not cand_po.upper().startswith("PO"):
                # Check if full PO-xxxx exists
                full_po_m = re.search(r"\b(PO[-_]\d{4}[-_]\d+)\b", text, re.IGNORECASE)
                if full_po_m:
                    cand_po = full_po_m.group(1)
                elif cand_po.startswith("-"):
                    cand_po = f"PO{cand_po}"
            data["po_reference"] = cand_po
        else:
            full_po_m = re.search(r"\b(PO[-_]\d{4}[-_]\d+)\b", text, re.IGNORECASE)
            if full_po_m:
                data["po_reference"] = full_po_m.group(1)

        # 3. Date of Dispatch
        date_match = re.search(r"(?:(?:Date\s*of\s*Dispatch|Dispatch\s*Date|Date)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        date_match = re.search(r"(?:(?:Date\s*of\s*Dispatch|Dispatch\s*Date|Date)[:\s]+)(\d{1,2}[-\s/.][A-Za-z0-9]+[-\s/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            data["document_date"] = normalize_date(date_match.group(1))
            raw_d = date_match.group(1).strip()
            data["document_date"] = normalize_date(raw_d)
            data["extra_metadata"]["raw_date"] = raw_d

        # 4. Consignor / Supplier
        consignor_match = re.search(r"(?:(?:Consignor|From|Supplier|Vendor)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
        if consignor_match:
            data["supplier_name"] = consignor_match.group(1).strip()
        # 4. Consignor / Supplier & Consignee / Customer
        supp_m = re.search(r"(?:Supplier|Seller|Vendor|Consignor|From)[:\s]*\n+([^\n,]+(?:Pvt|Ltd|Limited|Solutions|Corp|Enterprises|Supplies|Fasteners|Systems|Technologies|Works|Engineering)?)", text, re.IGNORECASE)
        if supp_m and not any(k in supp_m.group(1).lower() for k in ["buyer", "sample", "test", "actual", "synthetic", "bill to", "consignee"]):
            data["supplier_name"] = supp_m.group(1).strip()

        # 5. Consignee / Customer
        consignee_match = re.search(r"(?:(?:Consignee|To|Delivered\s*To)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Works|MSME|Industries|Plant|Stores)?)", text, re.IGNORECASE)
        if consignee_match:
            data["customer_name"] = consignee_match.group(1).strip()
        buyer_m = re.search(r"(?:Bill\s*To\s*/\s*Buyer|Buyer|Bill\s*To|Consignee|To|Customer|Delivered\s*To)[:\s]*\n+([^\n,]+(?:Pvt|Ltd|Limited|Solutions|Corp|Enterprises|Supplies|Fasteners|Systems|Technologies|Works|Engineering)?)", text, re.IGNORECASE)
        if buyer_m and not any(k in buyer_m.group(1).lower() for k in ["supplier", "sample", "test", "actual", "synthetic", "consignor"]):
            data["customer_name"] = buyer_m.group(1).strip()

        # 6. Delivered Items
        if not data["supplier_name"]:
            consignor_match = re.search(r"(?:(?:Consignor|From|Supplier|Vendor)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
            if consignor_match and not any(k in consignor_match.group(1).lower() for k in ["sample", "test", "actual", "synthetic"]):
                data["supplier_name"] = consignor_match.group(1).strip()
            else:
                for l in all_lines[:10]:
                    if any(k in l.lower() for k in ["pvt", "ltd", "limited", "solutions", "technologies", "engineering", "works", "supplies"]) and not any(k in l.lower() for k in ["sample", "test", "actual", "synthetic"]):
                        data["supplier_name"] = l.strip()
                        break

        if not data["customer_name"]:
            consignee_match = re.search(r"(?:(?:Consignee|To|Delivered\s*To)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Works|MSME|Industries|Plant|Stores|Technologies)?)", text, re.IGNORECASE)
            if consignee_match and not any(k in consignee_match.group(1).lower() for k in ["sample", "test", "actual", "synthetic"]):
                data["customer_name"] = consignee_match.group(1).strip()

        # 5. Delivered Items Extraction
        items: List[Dict[str, Any]] = []

        # Strategy A: Multi-row vertical token table (1, 2, 3...)
        row_starts = []
        for idx, line in enumerate(all_lines):
            clean_l = line.strip()
            if re.match(r"^\d+$", clean_l) and int(clean_l) == len(row_starts) + 1:
                if int(clean_l) <= 50 and idx + 1 < len(all_lines):
                    next_l = all_lines[idx + 1].strip()
                    if not any(k in next_l.lower() for k in ["purpose", "vehicle", "received", "signature", "prepared"]):
                        row_starts.append((int(clean_l), idx))

        if row_starts:
            for r_idx, (item_no, line_idx) in enumerate(row_starts):
                next_line_idx = row_starts[r_idx + 1][1] if r_idx + 1 < len(row_starts) else len(all_lines)
                chunk = [l.strip() for l in all_lines[line_idx + 1 : next_line_idx] if l.strip()]
                clean_chunk = []
                for c in chunk:
                    if any(k in c.lower() for k in ["purpose:", "prepared by", "received by", "vehicle", "condition:", "stores"]):
                        break
                    clean_chunk.append(c)

                if clean_chunk:
                    desc = clean_chunk[0]
                    qty = Decimal("1.00")
                    unit = "PCS"

                    for token in clean_chunk[1:]:
                        if token.upper() in ["PCS", "NOS", "SETS", "KG", "MTR", "UNITS", "BOX"]:
                            unit = token.upper()
                            continue
                        if token.lower().startswith("against") or token.lower() in ["delivered", "received", "dispatched"]:
                            continue
                        dec = normalize_decimal(token)
                        if dec > 0:
                            qty = dec
                            break

                    items.append({
                        "description": desc,
                        "normalized_description": clean_item_description(desc),
                        "quantity": str(qty),
                        "unit": unit,
                        "unit_price": "0.00",
                        "discount": "0.00",
                        "tax_rate": "0.00",
                        "tax_amount": "0.00",
                        "total_amount": "0.00",
                        "evidence_snippet": f"{desc} | Qty Delivered: {qty} {unit}",
                        "page_number": pages[0].get("page_number", 1) if pages else 1
                    })

        # Strategy B: Single-line horizontal table format fallback
        if not items:
            for p_idx, p in enumerate(pages):
                page_num = p.get("page_number", p_idx + 1)
                lines = p.get("lines", [])
                for line in lines:
                    item_match = re.search(
                        r"(?:^\d+[\.\)]|\-)?\s*(?P<desc>[A-Za-z0-9\s\"\'\-\/\(\)]+?)(?:[\:\-\|]\s*|\s+)(?:Dispatched\s*Qty|Quantity\s*Delivered|Qty\s*Delivered|Quantity\s*Sent|Qty)[:\s]*(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z]+)?",
                        line,
                        re.IGNORECASE
                    )
                    if item_match:
                        desc = item_match.group("desc").strip(" -:|,")
                        if len(desc) > 3 and not any(k in desc.lower() for k in ["vehicle", "transporter", "received", "condition"]):
                            qty = normalize_decimal(item_match.group("qty"))
                            unit = (item_match.group("unit") or "PCS").strip().upper()
                            items.append({
                                "description": desc,
                                "normalized_description": clean_item_description(desc),
                                "quantity": str(qty),
                                "unit": unit,
                                "unit_price": "0.00",
                                "discount": "0.00",
                                "tax_rate": "0.00",
                                "tax_amount": "0.00",
                                "total_amount": "0.00",
                                "evidence_snippet": f"{desc} | Qty Delivered: {qty} {unit}",
                                "evidence_snippet": line,
                                "page_number": page_num
                            })

        data["items"] = items
        return data
