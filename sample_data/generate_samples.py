"""
TRACE - Realistic Sample MSME PDF & Data Generator
Generates PDF business documents using ReportLab for demonstration and testing.
"""

import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_pdf(file_path: str, title: str, lines: list):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e3a8a'),
        alignment=1
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1f2937')
    )

    story = [
        Paragraph(title, title_style),
        Spacer(1, 15)
    ]

    for line in lines:
        if isinstance(line, list):  # Table data
            t = Table(line, hAlign='LEFT')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))
        else:
            story.append(Paragraph(str(line).replace("\n", "<br/>"), body_style))
            story.append(Spacer(1, 6))

    doc.build(story)
    print(f"Generated PDF: {file_path}")

def generate_sample_cases():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, "raw_documents")
    
    # -------------------------------------------------------------
    # CASE 1: TXN-2024-001 (Clean Transaction)
    # -------------------------------------------------------------
    c1_po = [
        "<b>PO Number:</b> PO-2024-001<br/><b>Date:</b> 01-08-2024<br/><b>Required Delivery Date:</b> 20-08-2024",
        "<b>Supplier:</b> Apex Industrial Tools Pvt Ltd<br/><b>GSTIN:</b> 27AABCU9812A1Z5",
        "<b>Buyer:</b> Precision MSME Engineering Works<br/><b>Delivery Address:</b> Plot 45, Chakan MIDC, Pune 410501",
        "<b>Scope of Supply:</b>",
        [
            ["SI", "Item Description", "Qty", "Unit", "Unit Price", "Total (INR)"],
            ["1", "Stainless Steel Bolt M10", "100", "PCS", "INR 500.00", "INR 50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00<br/><b>Payment Terms:</b> Net 30 Days from invoice.<br/>Authorized Signatory: Head of Procurement"
    ]
    create_pdf(os.path.join(raw_dir, "TXN-001_PO.pdf"), "PURCHASE ORDER", c1_po)

    c1_dn = [
        "<b>Delivery Challan No:</b> DC-8810<br/><b>Date of Dispatch:</b> 10-08-2024<br/><b>Against PO Ref:</b> PO-2024-001",
        "<b>Consignor:</b> Apex Industrial Tools Pvt Ltd<br/><b>Consignee:</b> Precision MSME Engineering Works",
        "<b>Vehicle No:</b> MH-12-RN-4411 | <b>Transporter:</b> Apex Logistics",
        "<b>Materials Dispatched:</b>",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "SS Bolt 10mm", "100", "PCS"]
        ],
        "<b>Condition:</b> Received in sound and full condition.<br/>Stores Receiver Signature: Suresh P. (Date: 10-08-2024)"
    ]
    create_pdf(os.path.join(raw_dir, "TXN-001_Delivery_Note.pdf"), "DELIVERY NOTE / CHALLAN", c1_dn)

    c1_inv = [
        "<b>Tax Invoice No:</b> INV-2425-5001<br/><b>Invoice Date:</b> 11-08-2024<br/><b>PO Reference:</b> PO-2024-001",
        "<b>Seller:</b> Apex Industrial Tools Pvt Ltd<br/><b>GSTIN:</b> 27AABCU9812A1Z5",
        "<b>Buyer:</b> Precision MSME Engineering Works<br/><b>GSTIN:</b> 27AAACM1234F1Z5",
        "<b>Line Items:</b>",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value", "CGST (9%)", "SGST (9%)", "Total"],
            ["1", "SS Bolt 10mm", "100 PCS", "INR 500.00", "INR 50000.00", "INR 4500.00", "INR 4500.00", "INR 59000.00"]
        ],
        "<b>Taxable Subtotal:</b> INR 50000.00<br/><b>Total Tax (18% GST):</b> INR 9000.00<br/><b>Total Invoice Amount:</b> INR 59000.00",
        "Bank Details: HDFC Bank, A/c: 5020001928374, IFSC: HDFC0001234"
    ]
    create_pdf(os.path.join(raw_dir, "TXN-001_Tax_Invoice.pdf"), "TAX INVOICE", c1_inv)

    c1_pay = [
        "<b>Payment Receipt No:</b> PAY-9912<br/><b>Payment Date:</b> 25-08-2024<br/><b>Settlement for Invoice:</b> INV-2425-5001",
        "<b>Paid To:</b> Apex Industrial Tools Pvt Ltd<br/><b>Paid By:</b> Precision MSME Engineering Works",
        "<b>UTR / Bank Ref:</b> UTR-HDFC-99182374192 | <b>Method:</b> NEFT",
        "<b>Amount Paid:</b> INR 59000.00<br/><b>Status:</b> SUCCESS - Account fully settled.<br/>Accounts Officer: Rajeev Kumar"
    ]
    create_pdf(os.path.join(raw_dir, "TXN-001_Payment_Receipt.pdf"), "PAYMENT RECEIPT", c1_pay)

    # -------------------------------------------------------------
    # CASE 2: TXN-2024-002 (Classic MSME Multi-Discrepancy Case)
    # Price Mismatch (₹500 -> ₹550), Qty Overbilled (100 billed vs 90 delivered), Payment Shortfall (₹45000 paid vs ₹55000)
    # -------------------------------------------------------------
    c2_po = [
        "<b>PO Number:</b> PO-2024-002<br/><b>Order Date:</b> 05-08-2024<br/><b>Required Delivery Date:</b> 25-08-2024",
        "<b>Supplier:</b> Kirloskar Engineering Supplies<br/><b>GSTIN:</b> 27AAACK4412B1Z1",
        "<b>Buyer:</b> Bharat Auto MSME Works",
        "<b>Item Schedule:</b>",
        [
            ["SI", "Item Description", "Qty", "Unit Rate", "Total Value"],
            ["1", "Industrial Nut M10", "100 PCS", "INR 500.00", "INR 50000.00"]
        ],
        "<b>Total Order Value:</b> INR 50000.00<br/>Authorized Signatory: Procurement Manager"
    ]
    create_pdf(os.path.join(raw_dir, "TXN-002_PO.pdf"), "PURCHASE ORDER", c2_po)

    c2_dn = [
        "<b>Delivery Challan No:</b> DC-9944<br/><b>Dispatch Date:</b> 12-08-2024<br/><b>Against PO No:</b> PO-2024-002",
        "<b>Supplier:</b> Kirloskar Engineering Supplies<br/><b>Consignee:</b> Bharat Auto MSME Works",
        "<b>Materials Dispatched:</b>",
        [
            ["SI", "Item Description", "Quantity Delivered", "Unit"],
            ["1", "M10 Industrial Nut", "90", "PCS"]
        ],
        "<b>Remarks:</b> Only 90 units dispatched due to stock limitation at factory.<br/>Received by: Stores In-charge"
    ]
    create_pdf(os.path.join(raw_dir, "TXN-002_Delivery_Note.pdf"), "DELIVERY CHALLAN", c2_dn)

    c2_inv = [
        "<b>Tax Invoice No:</b> INV-2425-6602<br/><b>Invoice Date:</b> 14-08-2024<br/><b>PO Reference:</b> PO-2024-002",
        "<b>Seller:</b> Kirloskar Engineering Supplies<br/><b>GSTIN:</b> 27AAACK4412B1Z1",
        "<b>Buyer:</b> Bharat Auto MSME Works",
        "<b>Line Items:</b>",
        [
            ["SI", "Description", "Qty", "Unit Rate", "Taxable Value", "Total"],
            ["1", "M10 Industrial Nut", "100 PCS", "INR 550.00", "INR 55000.00", "INR 55000.00"]
        ],
        "<b>Total Invoice Amount:</b> INR 55000.00<br/>Authorized Signatory: Kirloskar Supplies"
    ]
    create_pdf(os.path.join(raw_dir, "TXN-002_Tax_Invoice.pdf"), "TAX INVOICE", c2_inv)

    c2_pay = [
        "<b>Payment Receipt No:</b> PAY-8802<br/><b>Date:</b> 30-08-2024<br/><b>Against Invoice No:</b> INV-2425-6602",
        "<b>Vendor:</b> Kirloskar Engineering Supplies<br/><b>Paid By:</b> Bharat Auto MSME Works",
        "<b>UTR:</b> CMS991823741<br/><b>Amount Paid:</b> INR 45000.00<br/><b>Remarks:</b> Partial remittance."
    ]
    create_pdf(os.path.join(raw_dir, "TXN-002_Payment_Receipt.pdf"), "PAYMENT RECEIPT", c2_pay)

    print("Sample PDF generation complete!")

if __name__ == "__main__":
    generate_sample_cases()
