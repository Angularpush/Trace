"""
TRACE - Dataset Generator for Document Classification & Semantic Entity Matching
Generates realistic MSME transaction text samples and labelled evaluation pairs.
"""

import csv
import os
import random

def generate_classification_dataset(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    po_templates = [
        "PURCHASE ORDER\nPO Number: {po_num}\nDate: {date}\nVendor: {vendor}\nDelivery Address: {address}\nPayment Terms: Net 30 Days\nLine Items:\n1. {item} - Qty: {qty} @ INR {price}/unit = INR {total}\nAuthorized Signatory\nTerms & Conditions: Goods must be delivered within 15 days.",
        "ORDER CONFIRMATION / PO\nPurchase Order Ref: {po_num}\nIssued To: {vendor}\nShip To: {address}\nOrder Date: {date}\nRequired Delivery Date: {due_date}\nItems Ordered:\n- {item} | Quantity: {qty} {unit} | Unit Rate: Rs. {price} | Total: Rs. {total}\nFreight: Extra at actuals\nGST: 18% extra\nPrepared by: Purchase Dept",
        "STANDARD PURCHASE ORDER\nPO No: {po_num}\nBuyer: MSME Manufacturing Works\nSupplier: {vendor}\nGSTIN: {gstin}\nItem Details:\nItem Code: {code}, Description: {item}, Quantity: {qty}, Rate: {price}, Taxable Value: {total}\nTotal Order Value: INR {total}\nSpecial Instructions: Deliver with inspection certificate and warranty.",
        "COMMERCIAL PURCHASE ORDER\nOrder ID: {po_num}\nVendor Name: {vendor}\nBilling Address: Plot 45, Industrial Estate, Pune\nDate of Order: {date}\nScope of Supply:\n- {item} (Qty: {qty}, Unit Price: {price}, Amount: {total})\nPayment: 100% against Delivery Note and Tax Invoice.\nAuthorized by Procurement Manager.",
        "PURCHASE ORDER CONTRACT\nPO#: {po_num}\nDate: {date}\nTo: {vendor}\nShipment Mode: By Road\nDelivery Location: Warehouse 4, Sector 12, Manesar\nLine Item 1: {item} - {qty} Nos @ Rs. {price} each.\nSubtotal: Rs. {total}\nApplicable GST: 18%\nGrand Total: Rs. {grand_total}\nSignature: Head of SCM"
    ]
    
    invoice_templates = [
        "TAX INVOICE\nInvoice Number: {inv_num}\nInvoice Date: {date}\nPO Reference: {po_num}\nSeller: {vendor}\nGSTIN: {gstin}\nBuyer: MSME Precision Components Ltd\nBuyer GSTIN: 27AAACM1234F1Z5\nDescription of Goods: {item}\nHSN Code: 84818030\nQty: {qty} {unit}\nUnit Rate: INR {price}\nTaxable Value: INR {total}\nCGST 9%: INR {cgst}\nSGST 9%: INR {sgst}\nTotal Invoice Amount: INR {grand_total}\nBank Account: HDFC Bank, IFSC: HDFC0001234, A/c: 5020001928374\nFor {vendor} - Authorized Signatory",
        "COMMERCIAL TAX INVOICE\nBill No: {inv_num}\nBill Date: {date}\nAgainst PO No: {po_num}\nSupplier: {vendor}\nState: Maharashtra, Code: 27\nConsignee: Global MSME Solutions\nLine Items:\n1. {item} | {qty} {unit} | Rate: Rs. {price} | Taxable: Rs. {total} | IGST 18%: Rs. {igst} | Total: Rs. {grand_total}\nAmount in Words: INR {grand_total} only\nE-Way Bill No: 541098234712\nDeclaration: Certified that particulars given above are true and correct.",
        "INVOICE\nDoc No: {inv_num}\nDate: {date}\nRef Purchase Order: {po_num}\nFrom: {vendor}\nTo: Bharat Engineering MSME\nSummary:\nItem: {item}\nQuantity Supplied: {qty}\nPrice per unit: Rs. {price}\nNet Amount: Rs. {total}\nAdd GST 18%: Rs. {igst}\nInvoice Total: Rs. {grand_total}\nPayment Due Date: {due_date}\nPlease remit payment to State Bank of India A/c: 30981723481",
        "ORIGINAL TAX INVOICE (FOR RECIPIENT)\nInvoice No: {inv_num}\nDate of Issue: {date}\nPO Ref: {po_num}\nSupplier Name: {vendor}\nPAN: AABCP9871M\nGSTIN/UIN: {gstin}\nPlace of Supply: 27-Maharashtra\nTable of Supplies:\nSI No | Item Description | Qty | Rate | Amount\n01 | {item} | {qty} | {price} | {total}\nTotal Taxable: {total}\nIGST @ 18%: {igst}\nGross Total: {grand_total}\nSubject to Pune Jurisdiction only."
    ]
    
    delivery_templates = [
        "DELIVERY NOTE / CHALLAN\nDelivery Challan No: {dn_num}\nDate of Dispatch: {date}\nAgainst PO No: {po_num}\nConsignor: {vendor}\nConsignee: MSME Manufacturing Plant\nVehicle No: MH-12-RN-8821\nTransporter: Apex Logistics\nDriver Name: Suresh Patil (Mob: 9876543210)\nMaterials Dispatched:\n1. {item} - Dispatched Qty: {qty} {unit} (Packages: 4 Wooden Crates)\nCondition of Goods: Good condition, sealed boxes.\nReceived by: Stores In-charge (Signature & Date)\nGoods received in full and sound condition.",
        "GOODS DELIVERY CHALLAN\nChallan Ref: {dn_num}\nDate: {date}\nPO Reference: {po_num}\nFrom: {vendor}\nTo: MSME Engineering Works, Plot 8, MIDC Pune\nMode of Transport: Tempo MH-14-BT-1122\nLR / GC No: 994821\nParticulars:\n- {item} : Quantity Delivered: {qty} {unit}\nRemarks: Material subject to quality inspection at gate.\nInspected & Received in good order.",
        "DELIVERY RECEIPT & DISPATCH SLIP\nDN Number: {dn_num}\nDispatch Date: {date}\nPurchase Order: {po_num}\nSupplier: {vendor}\nDestination: Industrial Warehouse Sector 5\nList of Items:\nItem: {item} | Qty Delivered: {qty} | Unit: {unit} | Batch No: B-2024-09\nSecurity Gate Entry No: G-4412\nStorekeeper Signature: _____________\nDate & Time Received: {date} 14:30 hrs",
        "MATERIAL DISPATCH NOTE\nDispatch Memo: {dn_num}\nDate: {date}\nRef PO: {po_num}\nVendor: {vendor}\nDelivered To: Central Stores, Unit II\nDescription: {item}\nQuantity Sent: {qty} {unit}\nNo of Cartons: 10\nReceived Ok by Stores Department."
    ]
    
    payment_templates = [
        "PAYMENT RECEIPT / VOUCHER\nReceipt No: {pay_num}\nPayment Date: {date}\nPaid To: {vendor}\nPaid By: MSME Auto Components Ltd\nPayment Method: NEFT / RTGS Transfer\nBank Transaction Ref / UTR: UTR-HDFC-99182374192\nInvoice Reference: {inv_num}\nAmount Paid: INR {paid_amount}\nAmount in Words: INR {paid_amount} only\nPayment towards full/part settlement of Invoice {inv_num}\nAuthorized Accounts Officer: Rajeev Kumar",
        "BANK PAYMENT CONFIRMATION RECEIPT\nVoucher ID: {pay_num}\nDate: {date}\nBeneficiary Name: {vendor}\nBeneficiary A/c: {vendor_acc}\nTransaction ID: CMS2024091800492\nSettlement for Tax Invoice: {inv_num}\nPO Number Ref: {po_num}\nNet Remitted: Rs. {paid_amount}\nStatus: SUCCESS - Transferred to beneficiary account.\nAccounts Department Signature",
        "PAYMENT ADVICE & RECEIPT\nPayment Slip Ref: {pay_num}\nDate of Remittance: {date}\nVendor: {vendor}\nAgainst Bill/Invoice No: {inv_num}\nCheque/NEFT No: 882910\nPaid Amount: INR {paid_amount}\nDeductions (TDS/Retention): Rs. 0.00\nTotal Cleared: INR {paid_amount}\nReceived with thanks from MSME Industries."
    ]
    
    quotation_templates = [
        "QUOTATION / PRICE ESTIMATE\nQuotation Ref: {quote_num}\nQuote Date: {date}\nValid Until: {valid_date}\nTo: Procurement Team, MSME Works\nFrom: {vendor}\nDear Sir, We are pleased to quote our lowest rates:\nItem: {item}\nOffered Unit Price: Rs. {price} per {unit}\nLead Time: 10 working days from PO confirmation.\nPayment Terms: 30 days credit from invoice date.\nValidity: 30 days from quote date.\nLooking forward to your valued Purchase Order.\nBest Regards, Sales Manager, {vendor}",
        "FORMAL PRICE PROPOSAL\nQuote ID: {quote_num}\nDate: {date}\nCustomer: MSME Manufacturing\nSupplier: {vendor}\nEstimated Schedule of Rates:\n1. {item} - Unit Rate: INR {price} (MOQ: 50 {unit})\nGST: 18% extra\nDelivery: Ex-works Pune\nWarranty: 12 months from delivery date.\nCommercial Terms: 100% against delivery.\nAuthorized Signatory: {vendor}"
    ]
    
    credit_note_templates = [
        "CREDIT NOTE\nCredit Note No: {cn_num}\nCredit Note Date: {date}\nOriginal Tax Invoice Ref: {inv_num}\nOriginal Invoice Date: {inv_date}\nIssued By: {vendor}\nGSTIN: {gstin}\nIssued To: MSME Manufacturing Ltd\nReason for Credit: Rate difference / Return of damaged goods / Post-sale discount\nParticulars:\nItem: {item}\nQuantity Returned / Adjusted: {qty} {unit}\nUnit Rate: Rs. {price}\nCredit Amount (Taxable): Rs. {adj_amount}\nCGST 9%: Rs. {cgst_adj}\nSGST 9%: Rs. {sgst_adj}\nTotal Credit Note Amount: Rs. {total_adj}\nWe have credited your account with the above amount.",
        "TAX CREDIT MEMORANDUM\nCN Number: {cn_num}\nDate: {date}\nRef Invoice: {inv_num}\nVendor: {vendor}\nCustomer: MSME Works\nAdjustment Details:\nPrice reduction agreed on {item} - Difference INR {adj_amount}\nIGST Adjustment: INR {igst_adj}\nNet Credit Allowed: INR {total_adj}\nAuthorized Signatory, Accounts Department"
    ]
    
    debit_note_templates = [
        "DEBIT NOTE\nDebit Note No: {dn_num}\nDebit Note Date: {date}\nAgainst Original Invoice: {inv_num}\nIssued By: {vendor}\nGSTIN: {gstin}\nIssued To: MSME Precision Tools\nReason for Debit: Price undercharged in original invoice / Supplementary freight charges / Unbilled additional quantities\nDescription: {item}\nUnderbilled Amount: Rs. {adj_amount}\nApplicable GST (18%): Rs. {igst_adj}\nTotal Debit Value: Rs. {total_adj}\nWe have debited your account with the above mentioned sum.\nAuthorized Signatory"
    ]
    
    unknown_templates = [
        "SAFETY MANUAL & PROTOCOL\nSection 4: General Workshop Safety Guidelines.\n1. Personal Protective Equipment (PPE) including safety helmets, steel-toe shoes and goggles must be worn.\n2. Machine emergency stop buttons must be inspected daily.\n3. In case of fire, evacuate through Gate 2.",
        "EMPLOYEE LEAVE APPLICATION\nEmployee Name: Ramesh Shinde\nDepartment: Assembly Line B\nLeave Dates: 10th Oct to 12th Oct\nReason: Personal family function.\nApproved by Plant Supervisor.",
        "MEETING MINUTES - PRODUCT DESIGN REVIEW\nDate: 12-09-2024\nAttendees: Engineering Team, Quality Team\nAgenda: Review tolerances for new hydraulic valve housing prototype.\nAction Items: Update CAD model with revised bore dimensions.",
        "INTERNAL MEMORANDUM\nTo: All Plant Staff\nFrom: Operations Director\nSubject: Scheduled maintenance of Power Generator DG-2 on coming Sunday.\nAll departments are requested to plan production accordingly.",
        "VISITOR PASS - RECEPTION\nVisitor Name: Ananya Sharma\nCompany: Tech Audit Consultants\nPerson to meet: Finance Manager\nEntry Time: 10:15 AM\nExit Time: 12:45 PM"
    ]
    
    vendors = [
        "Apex Industrial Tools Pvt Ltd", "Kirloskar Engineering Supplies", "Bharat Precision Fasteners",
        "Mahindra Tooling & Forging Ltd", "Shree Ganesh Hydraulic Spares", "National Electricals & Controls",
        "Vanguard Steel & Alloys Corp", "Omkar Industrial Hardware", "TechnoMech Automation Solutions",
        "Sunrise Rubber & Polymer Components", "Premier Bearings & Power Transmission", "Swaraj Pneumatic Systems"
    ]
    
    items = [
        ("Stainless Steel Hex Bolt M10x50mm", "PCS", 45.0),
        ("High Tensile Flange Nut M12", "PCS", 18.5),
        ("Industrial Ball Bearing 6205-2RS", "NOS", 320.0),
        ("Hydraulic Pressure Relief Valve 1/2 inch", "NOS", 1850.0),
        ("Nitrile Rubber O-Ring Kit 200pcs", "SET", 480.0),
        ("Pneumatic Cylinder Double Acting 50mm Bore", "NOS", 2750.0),
        ("Carbon Steel Seamless Pipe 2 inch NB", "MTR", 620.0),
        ("Tungsten Carbide Milling Insert TNMG160408", "BOX", 1450.0),
        ("Viton Seal Gasket 100mm OD", "PCS", 95.0),
        ("Digital Vernier Caliper 0-150mm", "NOS", 1250.0)
    ]
    
    rows = []
    
    def format_money(val: float) -> str:
        return f"{val:.2f}"
    
    doc_types = [
        ("PURCHASE_ORDER", po_templates, 160),
        ("INVOICE", invoice_templates, 160),
        ("DELIVERY_NOTE", delivery_templates, 160),
        ("PAYMENT_RECEIPT", payment_templates, 160),
        ("QUOTATION", quotation_templates, 160),
        ("CREDIT_NOTE", credit_note_templates, 140),
        ("DEBIT_NOTE", debit_note_templates, 140),
        ("UNKNOWN", unknown_templates, 120)
    ]
    
    for label, templates, count in doc_types:
        for i in range(count):
            tmpl = random.choice(templates)
            vendor = random.choice(vendors)
            item_desc, unit, base_price = random.choice(items)
            qty = random.choice([10, 20, 50, 100, 200, 500])
            price = round(base_price * random.uniform(0.9, 1.1), 2)
            total = round(qty * price, 2)
            cgst = round(total * 0.09, 2)
            sgst = round(total * 0.09, 2)
            igst = round(total * 0.18, 2)
            grand_total = round(total + igst, 2)
            
            po_num = f"PO-2024-{random.randint(1000, 9999)}"
            inv_num = f"INV-2425-{random.randint(10000, 99999)}"
            dn_num = f"DC-{random.randint(5000, 9999)}"
            pay_num = f"PAY-REC-{random.randint(100000, 999999)}"
            quote_num = f"QUO-2024-{random.randint(200, 999)}"
            cn_num = f"CN-2425-{random.randint(100, 999)}"
            
            adj_amount = round(total * random.uniform(0.05, 0.2), 2)
            cgst_adj = round(adj_amount * 0.09, 2)
            sgst_adj = round(adj_amount * 0.09, 2)
            igst_adj = round(adj_amount * 0.18, 2)
            total_adj = round(adj_amount + igst_adj, 2)
            
            text = tmpl.format(
                po_num=po_num,
                inv_num=inv_num,
                dn_num=dn_num,
                pay_num=pay_num,
                quote_num=quote_num,
                cn_num=cn_num,
                date=f"{random.randint(1, 28):02d}-0{random.randint(1, 9)}-2024",
                due_date=f"{random.randint(1, 28):02d}-10-2024",
                valid_date=f"{random.randint(1, 28):02d}-11-2024",
                inv_date=f"{random.randint(1, 28):02d}-08-2024",
                vendor=vendor,
                gstin=f"27AABC{random.randint(1000,9999)}A1Z{random.randint(1,9)}",
                address="Plot 102, Chakan Industrial Area, Pune 410501",
                item=item_desc,
                code=f"ITM-{random.randint(100, 999)}",
                qty=qty,
                unit=unit,
                price=format_money(price),
                total=format_money(total),
                cgst=format_money(cgst),
                sgst=format_money(sgst),
                igst=format_money(igst),
                grand_total=format_money(grand_total),
                paid_amount=format_money(grand_total if random.random() > 0.3 else round(grand_total * 0.8, 2)),
                vendor_acc=f"002901{random.randint(1000000, 9999999)}",
                adj_amount=format_money(adj_amount),
                cgst_adj=format_money(cgst_adj),
                sgst_adj=format_money(sgst_adj),
                igst_adj=format_money(igst_adj),
                total_adj=format_money(total_adj)
            )
            rows.append({"text": text, "label": label})
            
    random.shuffle(rows)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} samples in {output_path}")

def generate_supplier_pairs(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pairs = [
        ("Apex Industrial Tools Pvt Ltd", "Apex Ind. Tools Private Limited", 1),
        ("Kirloskar Engineering Supplies", "Kirloskar Engg Supplies", 1),
        ("Bharat Precision Fasteners Co.", "Bharat Precision Fasteners", 1),
        ("Mahindra Tooling & Forging Ltd", "Mahindra Tooling & Forgings", 1),
        ("Shree Ganesh Hydraulic Spares", "Shri Ganesh Hydraulics", 1),
        ("National Electricals & Controls", "National Electricals Controls Pvt Ltd", 1),
        ("Vanguard Steel & Alloys Corp", "Vanguard Steel and Alloys Corporation", 1),
        ("Omkar Industrial Hardware", "Omkar Ind. Hardware Store", 1),
        ("TechnoMech Automation Solutions", "Techno Mech Automation", 1),
        ("Premier Bearings & Power Transmission", "Premier Bearings and Power Trans.", 1),
        ("Tata Steel Processing and Distribution Ltd", "Tata Steel Processing & Dist. Ltd", 1),
        ("Godrej Tooling Division", "Godrej & Boyce Tooling Div", 1),
        ("L&T Electrical & Automation", "Larsen & Toubro Electrical Automation", 1),
        ("Bosch Rexroth India Pvt Ltd", "Bosch Rexroth (India) Private Limited", 1),
        ("SKF India Limited", "SKF India Ltd", 1),
        ("FAG Bearings India", "FAG Bearings (Schaeffler Group)", 1),
        ("Schneider Electric India", "Schneider Electric Ind Pvt Ltd", 1),
        ("Havells India Ltd", "Havells India Limited", 1),
        ("Finolex Cables Limited", "Finolex Cables Ltd", 1),
        ("Polycab India Limited", "Polycab Wires & Cables", 1),
        ("Apex Industrial Tools Pvt Ltd", "Premier Bearings & Power Transmission", 0),
        ("Kirloskar Engineering Supplies", "Bharat Precision Fasteners", 0),
        ("Mahindra Tooling & Forging Ltd", "Omkar Industrial Hardware", 0),
        ("Shree Ganesh Hydraulic Spares", "TechnoMech Automation Solutions", 0),
        ("National Electricals & Controls", "Vanguard Steel & Alloys Corp", 0),
        ("Tata Steel Processing and Distribution Ltd", "Godrej Tooling Division", 0),
        ("SKF India Limited", "Bosch Rexroth India Pvt Ltd", 0),
        ("Schneider Electric India", "Finolex Cables Limited", 0),
        ("Havells India Ltd", "Polycab India Limited", 0),
        ("Omkar Industrial Hardware", "Apex Ind. Tools Private Limited", 0),
        ("Bharat Precision Fasteners", "Tata Steel Processing & Dist. Ltd", 0),
        ("Kirloskar Engg Supplies", "L&T Electrical & Automation", 0),
        ("FAG Bearings India", "Shri Ganesh Hydraulics", 0),
        ("National Electricals Controls Pvt Ltd", "Mahindra Tooling & Forgings", 0),
        ("Vanguard Steel and Alloys Corporation", "Schneider Electric India", 0),
        ("Premier Bearings and Power Trans.", "Havells India Ltd", 0),
        ("Techno Mech Automation", "SKF India Ltd", 0),
        ("Godrej & Boyce Tooling Div", "Apex Industrial Tools Pvt Ltd", 0),
        ("Larsen & Toubro Electrical Automation", "Omkar Ind. Hardware Store", 0),
        ("Polycab Wires & Cables", "Finolex Cables Limited", 0)
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text_a", "text_b", "label"])
        writer.writerows(pairs)
    print(f"Generated {len(pairs)} supplier pairs in {output_path}")

def generate_item_pairs(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pairs = [
        ("Stainless Steel Bolt M10", "SS Bolt 10mm", 1),
        ("Industrial Nut M10", "M10 Industrial Nut", 1),
        ("Hex Head Bolt M12x50 Grade 8.8", "M12x50 Hex Bolt Gr 8.8", 1),
        ("Ball Bearing 6205-2RS Deep Groove", "Deep Groove Ball Bearing 6205 2RS", 1),
        ("Hydraulic Pressure Relief Valve 1/2\"", "1/2 Inch Hydraulic Relief Valve", 1),
        ("Nitrile Rubber O-Ring 50x3mm", "NBR O Ring 50mm x 3mm", 1),
        ("Double Acting Pneumatic Cylinder 50 Bore", "Pneumatic Cylinder Double Acting 50mm", 1),
        ("Carbon Steel Seamless Pipe 2\" NB Sch 40", "CS Seamless Pipe 2 Inch Sch40", 1),
        ("Tungsten Carbide Insert TNMG 160408", "Carbide Milling Insert TNMG160408", 1),
        ("Viton Rubber Gasket 100mm OD", "100mm OD Viton Gasket Seal", 1),
        ("Digital Vernier Caliper 150mm / 6 inch", "Vernier Caliper Digital 0-150mm", 1),
        ("Helical Gear 24 Teeth Module 2.5", "24T Helical Pinion Gear Mod 2.5", 1),
        ("Alloy Steel Stud M16x100mm", "M16 x 100 mm Alloy Stud", 1),
        ("Teflon Sheet 3mm Thick 1x1m", "PTFE Sheet 3mm Thickness 1000x1000mm", 1),
        ("High Pressure Hydraulic Hose 1/2\" 2SN", "1/2 inch 2-Wire Hydraulic Hose", 1),
        ("Steel Washer M10", "Plastic Washer M10", 0),
        ("Stainless Steel Bolt M10", "Stainless Steel Bolt M12", 0),
        ("Ball Bearing 6205-2RS", "Ball Bearing 6206-2RS", 0),
        ("Nitrile Rubber O-Ring 50x3mm", "Viton Rubber O-Ring 50x3mm", 0),
        ("Pneumatic Cylinder 50 Bore", "Hydraulic Cylinder 50 Bore", 0),
        ("Carbon Steel Seamless Pipe 2\"", "Stainless Steel Seamless Pipe 2\"", 0),
        ("Tungsten Carbide Insert TNMG 160408", "Carbide Insert WNMG 080408", 0),
        ("Digital Vernier Caliper 150mm", "Digital Micrometer 0-25mm", 0),
        ("Alloy Steel Stud M16x100mm", "Alloy Steel Stud M16x150mm", 0),
        ("High Pressure Hydraulic Hose 1/2\"", "High Pressure Hydraulic Hose 3/4\"", 0),
        ("Hex Nut M10 Brass", "Hex Nut M10 Stainless Steel", 0),
        ("Helical Gear 24 Teeth", "Spur Gear 24 Teeth", 0),
        ("Teflon Sheet 3mm Thick", "Rubber Sheet 3mm Thick", 0),
        ("Pressure Relief Valve 1/2\"", "Flow Control Valve 1/2\"", 0),
        ("Deep Groove Ball Bearing 6205", "Taper Roller Bearing 30205", 0)
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text_a", "text_b", "label"])
        writer.writerows(pairs)
    print(f"Generated {len(pairs)} item pairs in {output_path}")

def generate_document_pairs(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pairs = [
        ("Purchase Order PO-2024-1001 for 100 units SS Bolts M10", "Tax Invoice INV-2024-501 against PO PO-2024-1001 for SS Bolts", 1),
        ("Delivery Challan DC-8812 delivering 100 units SS Bolts PO-2024-1001", "Tax Invoice INV-2024-501 referencing PO PO-2024-1001", 1),
        ("Payment Receipt PAY-9912 paying INR 55,000 for Invoice INV-2024-501", "Tax Invoice INV-2024-501 total amount INR 55,000", 1),
        ("Quotation QUO-2024-301 for Ball Bearings 6205-2RS", "Purchase Order PO-2024-1002 referencing Quote QUO-2024-301", 1),
        ("Credit Note CN-102 for rate adjustment on Invoice INV-2024-501", "Tax Invoice INV-2024-501 from Apex Industrial Tools", 1),
        ("Purchase Order PO-2024-1001 for 100 units SS Bolts M10", "Tax Invoice INV-2024-999 for Hydraulic Cylinders against PO-8877", 0),
        ("Delivery Challan DC-4411 for Kirloskar Pumps", "Payment Receipt PAY-1200 for Apex Fasteners", 0),
        ("Quotation QUO-2024-888 for Electrical Panels", "Credit Note CN-501 for Rubber O-Rings", 0),
        ("Tax Invoice INV-2024-101 for Bearing Assemblies", "Purchase Order PO-2024-909 for Viton Gaskets", 0),
        ("Payment Receipt PAY-555 for Rs 12,000", "Tax Invoice INV-2024-777 for Rs 850,000", 0)
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text_a", "text_b", "label"])
        writer.writerows(pairs)
    print(f"Generated {len(pairs)} document pairs in {output_path}")

if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ds_dir = os.path.join(base, "datasets")
    generate_classification_dataset(os.path.join(ds_dir, "doc_classification.csv"))
    generate_supplier_pairs(os.path.join(ds_dir, "supplier_pairs.csv"))
    generate_item_pairs(os.path.join(ds_dir, "item_pairs.csv"))
    generate_document_pairs(os.path.join(ds_dir, "document_pairs.csv"))
