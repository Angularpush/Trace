# TRACE System Performance & Accuracy Evaluation Benchmark

This directory contains the independent empirical benchmark suite for the **TRACE** project (_Document-Level MSME Transaction Reconciliation & Discrepancy Detection System_).

---

## Directory Structure

```
evaluation/
├── test_data/                    # Isolated synthetic & sample PDF test files
│   ├── TXN_001_clean/
│   ├── TXN_002_qty_mismatch/
│   ├── TXN_003_price_mismatch/
│   ├── TXN_004_tax_mismatch/
│   ├── TXN_005_total_mismatch/
│   ├── TXN_006_payment_mismatch/
│   ├── TXN_007_date_mismatch/
│   ├── TXN_008_missing_doc/
│   ├── TXN_009_duplicate_invoice/
│   ├── TXN_010_supplier_mismatch/
│   ├── TXN_011_item_mismatch/
│   ├── TXN_012_noisy_ocr/
│   └── TXN_013_multipage_pdf/
├── ground_truth/
│   └── ground_truth.json        # Ground truth labels for all 13 transactions
├── predictions/                  # TRACE pipeline outputs per transaction
├── results/                      # Output metrics and visualizations
│   ├── evaluation_report.json
│   ├── evaluation_report.csv
│   ├── EVALUATION_REPORT.md
│   └── document_classification_confusion_matrix.png
├── scripts/
│   ├── generate_test_data.py    # Generates isolated test PDFs & ground truth
│   └── run_evaluation.py        # Master evaluation harness
└── README.md
```

---

## How to Run the Benchmark

### 1. (Optional) Re-generate the Test Dataset & Ground Truth

```powershell
python evaluation/scripts/generate_test_data.py
```

### 2. Execute the Full Evaluation Pipeline

```powershell
python evaluation/scripts/run_evaluation.py
```

---

## Test Scenarios Covered

1. **`TXN_001_clean`**: Perfect 4-way match (PO, DN, Tax Invoice, Payment Receipt).
2. **`TXN_002_qty_mismatch`**: Quantity mismatch between Delivery Challan (80 units) and Invoice (100 units).
3. **`TXN_003_price_mismatch`**: Unit rate mismatch between Purchase Order (₹500) and Invoice (₹600).
4. **`TXN_004_tax_mismatch`**: Non-standard GST tax computation (24% billed vs 18% standard).
5. **`TXN_005_total_mismatch`**: Mathematical summation error on invoice (Subtotal + Tax != Grand Total).
6. **`TXN_006_payment_mismatch`**: Payment remittance shortfall against invoice total.
7. **`TXN_007_date_mismatch`**: Chronological violation (Invoice date predates Purchase Order date).
8. **`TXN_008_missing_doc`**: Invoiced without proof of delivery / Delivery Note.
9. **`TXN_009_duplicate_invoice`**: Duplicate submission of invoice with identical invoice number.
10. **`TXN_010_supplier_mismatch`**: Vendor identity mismatch between PO and Invoice.
11. **`TXN_011_item_mismatch`**: Unordered / unaligned line item on invoice.
12. **`TXN_012_noisy_ocr`**: Extraction resilience against OCR font glyphs (`■`, `₹`, `I`, `?`).
13. **`TXN_013_multipage_pdf`**: Single 4-page PDF containing PO, Invoice, Delivery Challan, and Payment.

---

## Output Artifacts

- **`results/evaluation_report.json`**: Machine-readable JSON summary of all measured metrics.
- **`results/evaluation_report.csv`**: Tabular CSV report of all key performance indicators.
- **`results/EVALUATION_REPORT.md`**: Human-readable Markdown summary with tables and failure analysis.
- **`results/document_classification_confusion_matrix.png`**: Visual confusion matrix across all document classes.
- **`predictions/<TXN_ID>.json`**: Detailed execution trace for every test transaction.
