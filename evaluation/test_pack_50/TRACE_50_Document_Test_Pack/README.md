# TRACE 50-Document Test Pack

This pack contains EXACTLY 50 synthetic PDF business documents across 15 transactions.

## Important
These PDFs are synthetic and intentionally labelled for controlled testing. The ground truth is the expected answer and must NOT be supplied to TRACE during prediction. Do not report results from this pack as real-world accuracy.

## Test coverage
- Clean transaction
- Quantity mismatch
- Unit-price mismatch
- GST/tax mismatch
- Grand-total mismatch
- Payment mismatch
- Date mismatch
- Supplier mismatch
- Item mismatch
- Duplicate invoice number
- Missing delivery note + payment
- Missing payment
- Missing invoice
- Invoice-only case
- Clean partial transaction

## Ground truth
`ground_truth/ground_truth.json` contains expected discrepancies.
`ground_truth/document_manifest.csv` maps every PDF to its transaction.

## Recommended evaluation
Run TRACE on `documents/`, save predictions separately, then compare predictions with the ground truth.
Measure document classification accuracy/F1, field extraction accuracy, transaction-linking accuracy, discrepancy precision/recall/F1, reconciliation accuracy, and evidence accuracy.
Never hard-code or invent results.
