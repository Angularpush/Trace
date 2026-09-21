# TRACE 50-Document Baseline Empirical Evaluation Report

## 1. Dataset Description

- **Total Documents Tested**: 50
- **Total Transactions**: 15
- **Dataset Source**: `TRACE_50_Document_Test_Pack` (Controlled synthetic benchmark)
- **Evaluation Date**: 2026-09-21 07:42:25 UTC

## 2. Test Methodology

1. **Zero Ground Truth Contamination**: All 50 PDF files were executed through TRACE's production extraction, classification, linking, and hybrid reconciliation pipeline without supplying expected values.
2. **Raw Predictions Preserved**: System predictions were dumped to `evaluation/predictions/trace_predictions.json` before loading ground truth.
3. **Direct Comparison**: Ground truth annotations were evaluated post-hoc to calculate mathematically exact metrics.

## 3. Document Classification Results

- **Overall Accuracy**: **76.00%** (38/50)
- **Macro Precision**: **63.46%**
- **Macro Recall**: **75.00%**
- **Macro F1-Score**: **67.50%**

| Document Class | Actual Count | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: |
| `PURCHASE_ORDER` | 14 | 53.85% | 100.00% | 70.00% |
| `INVOICE` | 14 | 100.00% | 100.00% | 100.00% |
| `DELIVERY_NOTE` | 12 | 0.00% | 0.00% | 0.00% |
| `PAYMENT_RECEIPT` | 10 | 100.00% | 100.00% | 100.00% |

### Confusion Matrix

```
Actual \ Pred    PURCHASE  INVOICE  DELIVERY  PAYMENT_
PURCHASE_ORDER      14       0       0       0
INVOICE              0      14       0       0
DELIVERY_NOTE       12       0       0       0
PAYMENT_RECEIP       0       0       0      10
```

## 4. Structured Field Extraction Results

- **Field Extraction Accuracy**: **62.09%** (226/364)
- **Correct Fields**: 226
- **Missing Fields**: 134
- **Incorrect Fields**: 4

| Field Name | Total Expected | Correct | Missing | Incorrect | Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `invoice_number` | 14 | 14 | 0 | 0 | 100.00% |
| `invoice_date` | 50 | 50 | 0 | 0 | 100.00% |
| `supplier` | 50 | 46 | 0 | 4 | 92.00% |
| `customer` | 50 | 50 | 0 | 0 | 100.00% |
| `gstin` | 14 | 14 | 0 | 0 | 100.00% |
| `po_number` | 14 | 14 | 0 | 0 | 100.00% |
| `item_description` | 40 | 0 | 40 | 0 | 0.00% |
| `quantity` | 40 | 0 | 40 | 0 | 0.00% |
| `unit_price` | 40 | 0 | 40 | 0 | 0.00% |
| `subtotal` | 14 | 14 | 0 | 0 | 100.00% |
| `gst` | 14 | 0 | 14 | 0 | 0.00% |
| `grand_total` | 14 | 14 | 0 | 0 | 100.00% |
| `payment_amount` | 10 | 10 | 0 | 0 | 100.00% |

## 5. Transaction Linking Results

- **Linking Accuracy**: **60.00%**
- **Total Expected Links**: 35
- **Correct Links**: 21
- **Missed Links**: 14
- **False Links**: 14

## 6. Discrepancy Detection Results

- **Overall Precision**: **23.81%**
- **Overall Recall**: **38.46%**
- **Overall F1-Score**: **29.41%**

| Discrepancy Category | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `Quantity mismatch` | 0 | 0 | 1 | 0.0% | 0.0% | **0.0%** |
| `Unit-price mismatch` | 0 | 0 | 1 | 0.0% | 0.0% | **0.0%** |
| `Tax/GST mismatch` | 0 | 0 | 1 | 0.0% | 0.0% | **0.0%** |
| `Total mismatch` | 0 | 0 | 1 | 0.0% | 0.0% | **0.0%** |
| `Payment mismatch` | 1 | 4 | 0 | 20.0% | 100.0% | **33.3%** |
| `Date mismatch` | 0 | 0 | 1 | 0.0% | 0.0% | **0.0%** |
| `Supplier mismatch` | 1 | 0 | 0 | 100.0% | 100.0% | **100.0%** |
| `Item mismatch` | 0 | 0 | 1 | 0.0% | 0.0% | **0.0%** |
| `Duplicate invoice` | 0 | 0 | 1 | 0.0% | 0.0% | **0.0%** |
| `Missing document` | 3 | 12 | 1 | 20.0% | 75.0% | **31.6%** |

## 7. Reconciliation Accuracy

- **Reconciliation Accuracy**: **86.67%** (13/15)
- **Correct Reconciliation Decisions**: 13
- **Incorrect Reconciliation Decisions**: 2

## 8. Evidence Accuracy

- **Evidence Grounding Accuracy**: **100.00%** (21/21)
- **Supported Findings**: 21
- **Total Findings**: 21

## 9. Error Analysis & Taxonomy

Total logged error items: 27

| Transaction ID | Document | Error Category | Expected | Predicted | Root Cause |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TXN-001` | `TXN-001_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 28.1%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-002` | `TXN-002_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 29.4%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-003` | `TXN-003_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 30.7%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-004` | `TXN-004_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 28.8%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-005` | `TXN-005_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 28.1%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-006` | `TXN-006_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 32.6%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-007` | `TXN-007_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 31.0%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-008` | `TXN-008_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 29.5%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-009` | `TXN-009_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 31.9%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-010` | `TXN-010_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 28.7%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-012` | `TXN-012_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 33.1%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-013` | `TXN-013_delivery_note.pdf` | Classification error | `DELIVERY_NOTE` | `PURCHASE_ORDER` | TF-IDF classifier misidentified DELIVERY_NOTE as PURCHASE_ORDER (confidence: 32.6%) because the test pack delivery notes contain financial headers (Tax %, Unit Price, Line Total) that heavily weight towards PO/Invoice. |
| `TXN-001` | `TXN-001_delivery_note.pdf` | Missing-document detection error (Cascading from Classification error) | `Delivery Note present and recognized` | `MISSING_DELIVERY_NOTE` | Delivery note was misclassified as PURCHASE_ORDER during Step 2, so the reconciliation engine observed a missing delivery document. |
| `TXN-002` | `TXN-002_delivery_note.pdf` | Missing-document detection error (Cascading from Classification error) | `Delivery Note present and recognized` | `MISSING_DELIVERY_NOTE` | Delivery note was misclassified as PURCHASE_ORDER during Step 2, so the reconciliation engine observed a missing delivery document. |
| `TXN-002` | `TXN-002_invoice.pdf` | Rule error | `QUANTITY_MISMATCH` | `['PAYMENT_MISMATCH', 'MISSING_DOCUMENT']` | Multi-row line items in vertical token format were not aligned due to delivery note misclassification. |
| `TXN-003` | `TXN-003_delivery_note.pdf` | Missing-document detection error (Cascading from Classification error) | `Delivery Note present and recognized` | `MISSING_DELIVERY_NOTE` | Delivery note was misclassified as PURCHASE_ORDER during Step 2, so the reconciliation engine observed a missing delivery document. |
| `TXN-003` | `TXN-003_invoice.pdf` | Rule error | `PRICE_MISMATCH` | `['PAYMENT_MISMATCH', 'MISSING_DOCUMENT']` | Vertical table line items were not extracted into structured item list due to missing horizontal delimiter. |
| `TXN-004` | `TXN-004_delivery_note.pdf` | Missing-document detection error (Cascading from Classification error) | `Delivery Note present and recognized` | `MISSING_DELIVERY_NOTE` | Delivery note was misclassified as PURCHASE_ORDER during Step 2, so the reconciliation engine observed a missing delivery document. |
| `TXN-005` | `TXN-005_delivery_note.pdf` | Missing-document detection error (Cascading from Classification error) | `Delivery Note present and recognized` | `MISSING_DELIVERY_NOTE` | Delivery note was misclassified as PURCHASE_ORDER during Step 2, so the reconciliation engine observed a missing delivery document. |
| `TXN-006` | `TXN-006_delivery_note.pdf` | Missing-document detection error (Cascading from Classification error) | `Delivery Note present and recognized` | `MISSING_DELIVERY_NOTE` | Delivery note was misclassified as PURCHASE_ORDER during Step 2, so the reconciliation engine observed a missing delivery document. |
| `TXN-007` | `TXN-007_delivery_note.pdf` | Missing-document detection error (Cascading from Classification error) | `Delivery Note present and recognized` | `MISSING_DELIVERY_NOTE` | Delivery note was misclassified as PURCHASE_ORDER during Step 2, so the reconciliation engine observed a missing delivery document. |
| `TXN-007` | `TXN-007_invoice.pdf` | Rule error | `DATE_MISMATCH` | `['MISSING_DOCUMENT']` | Date format on separate lines was extracted but chronology rule required PO reference link. |
| `TXN-008` | `TXN-008_delivery_note.pdf` | Missing-document detection error (Cascading from Classification error) | `Delivery Note present and recognized` | `MISSING_DELIVERY_NOTE` | Delivery note was misclassified as PURCHASE_ORDER during Step 2, so the reconciliation engine observed a missing delivery document. |
| `TXN-009` | `TXN-009_delivery_note.pdf` | Missing-document detection error (Cascading from Classification error) | `Delivery Note present and recognized` | `MISSING_DELIVERY_NOTE` | Delivery note was misclassified as PURCHASE_ORDER during Step 2, so the reconciliation engine observed a missing delivery document. |
| `TXN-010` | `TXN-010_delivery_note.pdf` | Missing-document detection error (Cascading from Classification error) | `Delivery Note present and recognized` | `MISSING_DELIVERY_NOTE` | Delivery note was misclassified as PURCHASE_ORDER during Step 2, so the reconciliation engine observed a missing delivery document. |

