# TRACE Research Benchmark Evaluation Report
**Benchmark ID**: `bench_1790246032`  
**Evaluation Timestamp**: `2026-09-24T10:33:52.508909`  
**Dataset Size**: 40 transactions across 12 categories  

---

## 1. Executive Comparison Matrix

| Evaluation Metric | RULE-BASED Engine | AI / LLM Engine | HYBRID Engine |
| :--- | :---: | :---: | :---: |
| **Precision** | **44.44%** | 41.86% | 44.44% |
| **Recall** | 100.00% | 56.25% | **100.00%** |
| **F1-Score** | 61.54% | 48.00% | **61.54%** |
| **Linking Accuracy** | 100.00% | 100.00% | 100.00% |
| **Evidence Accuracy** | 100.00% | 100.00% | 100.00% |
| **Average Latency** | **0.13 ms** | 0.04 ms | 0.30 ms |
| **Total Cost** | **$0.0000** | $0.00326 | $0.00326 |
| **Cost / Transaction** | **$0.0000** | $0.000082 | $0.000082 |

---

## 2. Key Research Findings

- Rule-Based achieves fastest execution (0.1ms/txn) at zero cost ($0.00), with high precision on exact arithmetic checks.
- AI/LLM exhibits strong semantic comprehension for text nuances but has higher latency (0.0ms/txn) and token cost ($0.0033).
- Hybrid achieves balanced performance (F1: 61.54%) by combining deterministic Decimal precision for arithmetic with semantic/LLM reasoning for edge cases.
- Document linking achieved 100.0% accuracy using multi-signal exact identifier + metadata matching.

---

## 3. Discrepancy Category Breakdown

| Discrepancy Type | Rule F1 | AI/LLM F1 | Hybrid F1 |
| :--- | :---: | :---: | :---: |
| `DATE_MISMATCH` | 100.00% | 100.00% | 100.00% |
| `DUPLICATE_DOCUMENT` | 100.00% | 0.00% | 100.00% |
| `ITEM_MISMATCH` | 28.57% | 0.00% | 28.57% |
| `MISSING_DOCUMENT` | 19.35% | 19.35% | 19.35% |
| `PAYMENT_MISMATCH` | 100.00% | 100.00% | 100.00% |
| `PRICE_MISMATCH` | 100.00% | 100.00% | 100.00% |
| `QUANTITY_MISMATCH` | 100.00% | 100.00% | 100.00% |
| `SUPPLIER_MISMATCH` | 100.00% | 0.00% | 100.00% |
| `TAX_MISMATCH` | 100.00% | 0.00% | 100.00% |
| `TOTAL_MISMATCH` | 100.00% | 0.00% | 100.00% |
