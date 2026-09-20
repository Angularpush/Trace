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
        if po_match:
            data["po_reference"] = po_match.group(1).strip()

        # 3. Date of Dispatch
        date_match = re.search(r"(?:(?:Date\s*of\s*Dispatch|Dispatch\s*Date|Date)[:\s]+)(\d{1,2}[-\/.]\d{1,2}[-\/.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
        if date_match:
            data["document_date"] = normalize_date(date_match.group(1))

        # 4. Consignor / Supplier
        consignor_match = re.search(r"(?:(?:Consignor|From|Supplier|Vendor)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Corp|Enterprises|Supplies|Fasteners|Systems|Solutions|Division)?)", text, re.IGNORECASE)
        if consignor_match:
            data["supplier_name"] = consignor_match.group(1).strip()

        # 5. Consignee / Customer
        consignee_match = re.search(r"(?:(?:Consignee|To|Delivered\s*To)[:\s]+)([^\n,]+(?:Pvt|Ltd|Limited|Works|MSME|Industries|Plant|Stores)?)", text, re.IGNORECASE)
        if consignee_match:
            data["customer_name"] = consignee_match.group(1).strip()

        # 6. Delivered Items
        items: List[Dict[str, Any]] = []
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
                            "evidence_snippet": line,
                            "page_number": page_num
                        })

            # Vertical table scan for delivery challan
            if not items and len(lines) >= 3:
                for idx, line in enumerate(lines):
                    if line.strip() in ["1", "01"] and idx + 2 < len(lines):
                        desc = lines[idx + 1].strip()
                        if len(desc) > 2 and not any(k in desc.lower() for k in ["condition", "transporter", "received", "signature"]):
                            next_token = lines[idx + 2].strip()
                            qty_val = re.search(r"(\d+(?:\.\d+)?)", next_token)
                            unit_val = re.search(r"([A-Za-z]+)", next_token)

                            qty = normalize_decimal(qty_val.group(1)) if qty_val else Decimal("1")
                            unit = unit_val.group(1).upper() if unit_val else "PCS"

                            if idx + 3 < len(lines) and lines[idx + 3].strip().upper() in ["PCS", "NOS", "SETS", "KG", "MTR"]:
                                unit = lines[idx + 3].strip().upper()

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
                                "page_number": page_num
                            })

        data["items"] = items
        return data
